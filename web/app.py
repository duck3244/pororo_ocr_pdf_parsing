#!/usr/bin/env python3
"""
웹 인터페이스 모듈
Flask 기반 웹 애플리케이션
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import threading
import time

# 프로젝트 모듈 import (경로 조정 필요)
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_handler import PDFHandler
from core.image_processor import ImageProcessor
from core.ocr_engine import OCREngine
from core.text_postprocessor import TextPostProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 설정
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
    UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
    RESULT_FOLDER=os.environ.get('RESULT_FOLDER', 'static/results'),
    PERMANENT_SESSION_LIFETIME=1800  # 30분
)

# 디렉토리 생성
for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULT_FOLDER']]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# 전역 변수로 처리 상태 관리
processing_jobs: Dict[str, Dict[str, Any]] = {}


class OCRProcessor:
    """OCR 처리 통합 클래스"""

    def __init__(self):
        self.pdf_handler = None
        self.image_processor = None
        self.ocr_engine = None
        self.text_processor = None
        self._initialize_components()

    def _initialize_components(self):
        """컴포넌트 초기화"""
        try:
            self.pdf_handler = PDFHandler()
            self.image_processor = ImageProcessor()
            self.ocr_engine = OCREngine()
            self.text_processor = TextPostProcessor()
            logger.info("OCR processor components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OCR components: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str, job_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """PDF 처리 메인 함수"""
        try:
            # 1. PDF 유효성 검사
            self._update_job_status(job_id, 'validating', 5, 'PDF 파일 검증 중...')
            validation = self.pdf_handler.validate_pdf(pdf_path)
            if not validation['is_valid']:
                raise ValueError(f"Invalid PDF: {validation['error_message']}")

            # 2. PDF 정보 추출
            self._update_job_status(job_id, 'extracting_info', 10, 'PDF 메타데이터 추출 중...')
            pdf_info = self.pdf_handler.extract_pdf_info(pdf_path)

            # 3. PDF를 이미지로 변환
            self._update_job_status(job_id, 'converting', 20, 'PDF를 이미지로 변환 중...')

            output_dir = Path(app.config['RESULT_FOLDER']) / job_id
            output_dir.mkdir(exist_ok=True)

            self.pdf_handler.output_dir = output_dir

            def conversion_progress(current, total, filename):
                progress = 20 + (current / total) * 30  # 20% ~ 50%
                self._update_job_status(job_id, 'converting', progress, f'페이지 {current}/{total} 변환 중...')

            image_paths = self.pdf_handler.convert_to_images(
                pdf_path,
                dpi=options.get('dpi', 300),
                progress_callback=conversion_progress
            )

            # 4. 이미지 전처리 (옵션)
            if options.get('preprocess', True):
                self._update_job_status(job_id, 'preprocessing', 50, '이미지 전처리 중...')

                preprocessed_dir = output_dir / 'preprocessed'
                preprocessed_dir.mkdir(exist_ok=True)

                def preprocess_progress(current, total, filename):
                    progress = 50 + (current / total) * 20  # 50% ~ 70%
                    self._update_job_status(job_id, 'preprocessing', progress, f'이미지 {current}/{total} 전처리 중...')

                config = options.get('preprocess_config', {})
                preprocessed_paths = self.image_processor.batch_preprocess(
                    image_paths,
                    str(preprocessed_dir),
                    config=config,
                    progress_callback=preprocess_progress
                )

                # None 값 제거 (실패한 전처리)
                final_image_paths = [path for path in preprocessed_paths if path is not None]
            else:
                final_image_paths = image_paths

            # 5. OCR 텍스트 추출
            self._update_job_status(job_id, 'ocr', 70, 'OCR 텍스트 추출 중...')

            def ocr_progress(current, total, filename):
                progress = 70 + (current / total) * 20  # 70% ~ 90%
                self._update_job_status(job_id, 'ocr', progress, f'OCR {current}/{total} 처리 중...')

            ocr_results = self.ocr_engine.batch_extract(final_image_paths, ocr_progress)

            # 6. 텍스트 후처리 (옵션)
            self._update_job_status(job_id, 'postprocessing', 90, '텍스트 후처리 중...')

            pages_data = []
            for i, image_path in enumerate(final_image_paths):
                page_number = i + 1
                ocr_result = ocr_results.get(image_path, [])

                # OCR 결과 정제 - description과 bounding_poly 키 확인
                text_regions = []
                raw_texts = []  # 디버깅용

                logger.info(f"Processing OCR results for page {page_number}: {len(ocr_result)} regions")

                for idx, region in enumerate(ocr_result):
                    extracted_text = ""

                    if isinstance(region, dict):
                        logger.debug(f"Region {idx} keys: {list(region.keys())}")

                        # Pororo OCR 결과 구조에 맞게 텍스트 추출
                        if 'text' in region and region['text'].strip():
                            extracted_text = region['text'].strip()
                        elif 'description' in region and region['description'].strip():
                            extracted_text = region['description'].strip()
                        elif 'word' in region and region['word'].strip():
                            extracted_text = region['word'].strip()
                        else:
                            # 딕셔너리에서 문자열 값 찾기
                            for key, value in region.items():
                                if isinstance(value, str) and value.strip() and not key.startswith(
                                        'bbox') and not key.startswith('bound'):
                                    extracted_text = value.strip()
                                    break

                    elif isinstance(region, str) and region.strip():
                        extracted_text = region.strip()

                    raw_texts.append(f"Region {idx}: {region}")  # 디버깅용

                    if extracted_text and extracted_text not in ['description', 'bounding_poly', 'boundingPoly',
                                                                 'bbox']:
                        text_regions.append(extracted_text)
                        logger.info(f"Extracted text from region {idx}: '{extracted_text}'")

                # 텍스트 결합
                combined_text = '\n'.join(text_regions) if text_regions else ''

                logger.info(
                    f"Page {page_number} final result: {len(text_regions)} regions, {len(combined_text)} characters")

                page_data = {
                    'page_number': page_number,
                    'image_path': image_path,
                    'text_regions': text_regions,
                    'combined_text': combined_text,
                    'text_count': len(text_regions),
                    'ocr_data': ocr_result,
                    'debug_raw_texts': raw_texts  # 디버깅용
                }

                # 텍스트 후처리 적용
                if options.get('postprocess', True) and combined_text.strip():
                    try:
                        processed_text = self.text_processor.process_page_text(combined_text, page_number)
                        page_data['processed_text'] = processed_text
                    except Exception as e:
                        logger.warning(f"Text postprocessing failed for page {page_number}: {str(e)}")

                pages_data.append(page_data)

            # 7. 결과 통합
            results = {
                'pdf_info': pdf_info,
                'processing_options': options,
                'pages': pages_data,
                'job_id': job_id,
                'processed_at': datetime.now().isoformat()
            }

            # 문서 요약 생성 (후처리 활성화 시)
            if options.get('postprocess', True):
                processed_pages = [page['processed_text'] for page in pages_data if 'processed_text' in page]
                if processed_pages:
                    document_summary = self.text_processor.generate_document_summary(processed_pages)
                    results['document_summary'] = document_summary

            # 8. 결과 저장
            self._save_results(results, output_dir)

            self._update_job_status(job_id, 'completed', 100, '처리 완료!')
            processing_jobs[job_id]['results'] = results

            return results

        except Exception as e:
            error_msg = f"처리 중 오류 발생: {str(e)}"
            self._update_job_status(job_id, 'error', 0, error_msg)
            logger.error(f"Processing failed for job {job_id}: {str(e)}")
            raise

    def _update_job_status(self, job_id: str, status: str, progress: float, message: str):
        """작업 상태 업데이트"""
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'status': status,
                'progress': progress,
                'message': message,
                'updated_at': datetime.now().isoformat()
            })

    def _save_results(self, results: Dict[str, Any], output_dir: Path):
        """결과 파일 저장"""
        # JSON 결과 저장
        json_path = output_dir / 'results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 텍스트 결과 저장
        txt_path = output_dir / 'extracted_text.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"OCR 처리 결과\n")
            f.write(f"처리 시간: {results['processed_at']}\n")
            f.write("=" * 50 + "\n\n")

            for page in results['pages']:
                f.write(f"페이지 {page['page_number']}\n")
                f.write("-" * 20 + "\n")
                f.write(page['combined_text'])
                f.write("\n\n")


# OCR 프로세서 인스턴스
ocr_processor = OCRProcessor()


def process_pdf_async(job_id: str, pdf_path: str, options: Dict[str, Any]):
    """비동기 PDF 처리"""
    try:
        ocr_processor.process_pdf(pdf_path, job_id, options)
    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'error': '파일 크기가 너무 큽니다. 16MB 이하 파일만 업로드 가능합니다.'}), 413


@app.errorhandler(404)
def handle_not_found(e):
    return render_template('error.html',
                           error_code=404,
                           error_message='페이지를 찾을 수 없습니다.'), 404


@app.errorhandler(500)
def handle_internal_error(e):
    return render_template('error.html',
                           error_code=500,
                           error_message='내부 서버 오류가 발생했습니다.'), 500


def allowed_file(filename: str) -> bool:
    """허용된 파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """파일 업로드 및 처리 시작"""
    try:
        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400

        # 파일 저장
        filename = secure_filename(file.filename)
        job_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(file_path)

        # 처리 옵션 가져오기
        options = {
            'dpi': int(request.form.get('dpi', 300)),
            'preprocess': request.form.get('preprocess') == 'true',
            'postprocess': request.form.get('postprocess') == 'true',
            'preprocess_config': {}
        }

        # 작업 상태 초기화
        processing_jobs[job_id] = {
            'job_id': job_id,
            'filename': filename,
            'status': 'queued',
            'progress': 0,
            'message': '처리 대기 중...',
            'created_at': datetime.now().isoformat(),
            'options': options
        }

        # 비동기 처리 시작
        thread = threading.Thread(
            target=process_pdf_async,
            args=(job_id, file_path, options)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'job_id': job_id,
            'message': '파일 업로드 완료. 처리를 시작합니다.',
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/status/<job_id>')
def get_status(job_id: str):
    """처리 상태 조회"""
    if job_id not in processing_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다.'}), 404

    job_data = processing_jobs[job_id].copy()
    # 결과 데이터는 제외 (크기 때문)
    job_data.pop('results', None)

    return jsonify(job_data)


@app.route('/results/<job_id>')
def get_results(job_id: str):
    """처리 결과 페이지"""
    if job_id not in processing_jobs:
        flash('작업을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))

    job = processing_jobs[job_id]
    if job['status'] != 'completed':
        flash('처리가 완료되지 않았습니다.', 'warning')
        return redirect(url_for('index'))

    if 'results' not in job:
        flash('결과 데이터를 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))

    return render_template('results.html',
                           job_id=job_id,
                           results=job['results'],
                           job_info=job)


@app.route('/download/<job_id>/<format>')
def download_results(job_id: str, format: str):
    """결과 파일 다운로드"""
    if job_id not in processing_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다.'}), 404

    job = processing_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': '처리가 완료되지 않았습니다.'}), 400

    results_dir = Path(app.config['RESULT_FOLDER']) / job_id

    try:
        if format == 'json':
            file_path = results_dir / 'results.json'
            if file_path.exists():
                return send_file(file_path, as_attachment=True,
                                 download_name=f"{job['filename']}_results.json")

        elif format == 'txt':
            file_path = results_dir / 'extracted_text.txt'
            if file_path.exists():
                return send_file(file_path, as_attachment=True,
                                 download_name=f"{job['filename']}_text.txt")

        elif format == 'csv':
            # CSV 파일 동적 생성
            if 'results' in job and 'document_summary' in job['results']:
                csv_data = generate_csv_summary(job['results'])

                from io import StringIO, BytesIO
                output = StringIO()
                output.write(csv_data)

                # StringIO를 BytesIO로 변환
                csv_bytes = BytesIO()
                csv_bytes.write(output.getvalue().encode('utf-8-sig'))  # BOM 추가
                csv_bytes.seek(0)

                return send_file(csv_bytes, as_attachment=True,
                                 download_name=f"{job['filename']}_summary.csv",
                                 mimetype='text/csv')

        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'다운로드 중 오류가 발생했습니다: {str(e)}'}), 500


def generate_csv_summary(results: Dict[str, Any]) -> str:
    """CSV 요약 파일 생성"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow([
        '페이지', '글자수', '단어수', '텍스트영역수', '언어', '텍스트미리보기'
    ])

    # 페이지별 데이터
    for page in results.get('pages', []):
        preview = page['combined_text'][:100].replace('\n', ' ') + '...' if len(page['combined_text']) > 100 else page[
            'combined_text'].replace('\n', ' ')

        language = 'unknown'
        if 'processed_text' in page:
            language = page['processed_text'].get('language_info', {}).get('primary_language', 'unknown')

        writer.writerow([
            page['page_number'],
            len(page['combined_text']),
            len(page['combined_text'].split()),
            page['text_count'],
            language,
            preview
        ])

    return output.getvalue()


@app.route('/api/process', methods=['POST'])
def api_process():
    """API 엔드포인트 - 동기 처리"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # 파일 저장
        filename = secure_filename(file.filename)
        job_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(file_path)

        # 처리 옵션
        options = {
            'dpi': int(request.form.get('dpi', 300)),
            'preprocess': request.form.get('preprocess', 'true').lower() == 'true',
            'postprocess': request.form.get('postprocess', 'true').lower() == 'true'
        }

        # 작업 상태 초기화
        processing_jobs[job_id] = {
            'job_id': job_id,
            'filename': filename,
            'status': 'processing',
            'progress': 0,
            'message': 'API 처리 중...',
            'created_at': datetime.now().isoformat()
        }

        # 동기 처리
        results = ocr_processor.process_pdf(file_path, job_id, options)

        # 임시 파일 정리
        try:
            os.remove(file_path)
        except:
            pass

        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'results': results
        })

    except Exception as e:
        logger.error(f"API processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>')
def api_get_status(job_id: str):
    """API 상태 조회"""
    return get_status(job_id)


@app.route('/cleanup')
def cleanup_old_jobs():
    """오래된 작업 정리"""
    try:
        current_time = datetime.now()
        jobs_to_remove = []

        for job_id, job_data in processing_jobs.items():
            created_at = datetime.fromisoformat(job_data['created_at'])
            # 24시간 이상 된 작업 제거
            if (current_time - created_at).total_seconds() > 86400:
                jobs_to_remove.append(job_id)

                # 결과 파일도 제거
                try:
                    results_dir = Path(app.config['RESULT_FOLDER']) / job_id
                    if results_dir.exists():
                        import shutil
                        shutil.rmtree(results_dir)
                except:
                    pass

        for job_id in jobs_to_remove:
            del processing_jobs[job_id]

        return jsonify({
            'message': f'{len(jobs_to_remove)}개의 오래된 작업을 정리했습니다.',
            'removed_jobs': len(jobs_to_remove)
        })

    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 기본 컴포넌트 확인
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'pdf_handler': ocr_processor.pdf_handler is not None,
                'image_processor': ocr_processor.image_processor is not None,
                'ocr_engine': ocr_processor.ocr_engine is not None,
                'text_processor': ocr_processor.text_processor is not None
            },
            'active_jobs': len([job for job in processing_jobs.values() if job['status'] == 'processing']),
            'total_jobs': len(processing_jobs)
        }

        # 모든 컴포넌트가 정상인지 확인
        if not all(status['components'].values()):
            status['status'] = 'degraded'
            return jsonify(status), 503

        return jsonify(status)

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.template_filter('number_format')
def number_format_filter(value):
    """숫자 포맷 필터"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value


@app.template_filter('file_size')
def file_size_filter(size_bytes):
    """파일 크기 포맷 필터"""
    try:
        size = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except (ValueError, TypeError):
        return "Unknown"


def main():
    """웹 애플리케이션 메인 함수"""
    # 개발 서버 실행
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    logger.info(f"Starting Flask app on {host}:{port} (debug={debug_mode})")

    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )


if __name__ == '__main__':
    main()