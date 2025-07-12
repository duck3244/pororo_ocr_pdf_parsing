#!/usr/bin/env python3
"""
완전 수정된 웹 앱 - OCR 결과 파싱 및 표시 문제 해결
web/app.py 파일을 이 내용으로 교체하세요.
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
        """🔥 완전 수정된 PDF 처리 함수"""
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

                final_image_paths = [path for path in preprocessed_paths if path is not None]
            else:
                final_image_paths = image_paths

            # 5. OCR 텍스트 추출 - 🔥 핵심 수정 부분
            self._update_job_status(job_id, 'ocr', 70, 'OCR 텍스트 추출 중...')

            def ocr_progress(current, total, filename):
                progress = 70 + (current / total) * 20  # 70% ~ 90%
                self._update_job_status(job_id, 'ocr', progress, f'OCR {current}/{total} 처리 중...')

            # 개선된 OCR 엔진 사용
            logger.info(f"🚀 개선된 OCR 처리 시작: {len(final_image_paths)}개 이미지")
            ocr_results = self.ocr_engine.batch_extract(final_image_paths, ocr_progress)

            # 6. 텍스트 후처리 - 🔥 결과 처리 완전 수정
            self._update_job_status(job_id, 'postprocessing', 90, '텍스트 후처리 중...')

            pages_data = []
            total_successful_pages = 0
            total_text_regions = 0
            total_characters = 0

            for i, image_path in enumerate(final_image_paths):
                page_number = i + 1
                ocr_result = ocr_results.get(image_path, [])

                logger.info(f"📄 페이지 {page_number} OCR 결과 처리: {len(ocr_result)}개 영역")

                # 🔥 핵심 수정: OCR 결과에서 텍스트 추출
                text_regions = []
                page_has_text = False

                # OCR 결과가 리스트이고 각 항목이 딕셔너리인 경우
                for idx, region in enumerate(ocr_result):
                    if isinstance(region, dict) and 'text' in region:
                        text = region['text'].strip()
                        if text and len(text) > 0:
                            text_regions.append(text)
                            page_has_text = True
                            logger.info(f"    ✅ 영역 {idx + 1}: '{text[:50]}{'...' if len(text) > 50 else ''}'")

                # 텍스트 결합
                combined_text = '\n'.join(text_regions) if text_regions else ''

                # 통계 업데이트
                if page_has_text:
                    total_successful_pages += 1
                    total_text_regions += len(text_regions)
                    total_characters += len(combined_text)

                logger.info(f"✅ 페이지 {page_number} 최종 결과: {len(text_regions)}개 영역, {len(combined_text)}글자")

                # 🔥 핵심: extraction_success 필드 추가 (템플릿에서 필요)
                page_data = {
                    'page_number': page_number,
                    'image_path': image_path,
                    'text_regions': text_regions,
                    'combined_text': combined_text,
                    'text_count': len(text_regions),
                    'has_text': page_has_text,
                    'extraction_success': page_has_text,  # 🔥 중요: 템플릿에서 사용
                    'character_count': len(combined_text),
                    'ocr_data': str(type(ocr_result)),  # 디버그용
                    'debug_info': [
                        f"OCR 결과 타입: {type(ocr_result)}",
                        f"OCR 결과 길이: {len(ocr_result)}",
                        f"추출된 텍스트 영역: {len(text_regions)}",
                        f"총 글자 수: {len(combined_text)}"
                    ]
                }

                # 텍스트 후처리 적용 (텍스트가 있는 경우에만)
                if options.get('postprocess', True) and combined_text.strip():
                    try:
                        processed_text = self.text_processor.process_page_text(combined_text, page_number)
                        page_data['processed_text'] = processed_text
                        logger.debug(f"    후처리 완료: 페이지 {page_number}")
                    except Exception as e:
                        logger.warning(f"⚠️ 페이지 {page_number} 후처리 실패: {str(e)}")

                pages_data.append(page_data)

            # 7. 결과 통합 및 요약
            logger.info(f"🎯 전체 처리 결과:")
            logger.info(f"  - 총 페이지: {len(pages_data)}")
            logger.info(f"  - 텍스트가 있는 페이지: {total_successful_pages}")
            logger.info(f"  - 총 텍스트 영역: {total_text_regions}")
            logger.info(f"  - 총 글자 수: {total_characters}")

            success_rate = (total_successful_pages / len(pages_data) * 100) if pages_data else 0
            logger.info(f"  - 성공률: {success_rate:.1f}%")

            results = {
                'pdf_info': pdf_info,
                'processing_options': options,
                'pages': pages_data,
                'job_id': job_id,
                'processed_at': datetime.now().isoformat(),
                'processing_summary': {
                    'total_pages': len(pages_data),
                    'successful_pages': total_successful_pages,
                    'success_rate': success_rate,
                    'total_text_regions': total_text_regions,
                    'total_characters': total_characters
                }
            }

            # 문서 요약 생성 (후처리 활성화 시)
            if options.get('postprocess', True) and total_successful_pages > 0:
                try:
                    processed_pages = [page['processed_text'] for page in pages_data if 'processed_text' in page]
                    if processed_pages:
                        document_summary = self.text_processor.generate_document_summary(processed_pages)
                        results['document_summary'] = document_summary
                        logger.info("📊 문서 요약 생성 완료")
                except Exception as e:
                    logger.warning(f"⚠️ 문서 요약 생성 실패: {str(e)}")

            # 8. 결과 저장
            self._save_results(results, output_dir)

            # 최종 상태 업데이트
            if total_successful_pages > 0:
                self._update_job_status(job_id, 'completed', 100,
                                        f'처리 완료! ({total_successful_pages}/{len(pages_data)} 페이지 성공)')
            else:
                self._update_job_status(job_id, 'completed', 100, '처리 완료 (텍스트 없음)')

            processing_jobs[job_id]['results'] = results
            return results

        except Exception as e:
            error_msg = f"처리 중 오류 발생: {str(e)}"
            self._update_job_status(job_id, 'error', 0, error_msg)
            logger.error(f"❌ PDF 처리 실패 (Job: {job_id}): {str(e)}")
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
        """결과 파일 저장 - 완전 수정 버전"""
        try:
            # 1. JSON 결과 저장
            json_path = output_dir / 'results.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON 결과 저장: {json_path}")

            # 2. 텍스트 결과 저장
            txt_path = output_dir / 'extracted_text.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"OCR 처리 결과\n")
                f.write(f"처리 시간: {results.get('processed_at', 'Unknown')}\n")
                f.write(f"성공률: {results.get('processing_summary', {}).get('success_rate', 0):.1f}%\n")
                f.write("=" * 50 + "\n\n")

                for page in results.get('pages', []):
                    page_number = page.get('page_number', 'Unknown')
                    f.write(f"페이지 {page_number}\n")
                    f.write("-" * 20 + "\n")

                    # 안전한 텍스트 추출
                    combined_text = page.get('combined_text', '')
                    has_text = page.get('has_text', False)
                    text_count = page.get('text_count', 0)

                    if has_text or combined_text.strip():
                        f.write(f"텍스트 영역 수: {text_count}\n")
                        f.write(f"글자 수: {page.get('character_count', len(combined_text))}\n\n")
                        f.write(combined_text if combined_text.strip() else "텍스트 없음")
                    else:
                        f.write("이 페이지에서는 텍스트를 찾을 수 없습니다.")

                    f.write("\n\n")

            logger.info(f"텍스트 결과 저장: {txt_path}")

            # 3. CSV 요약 저장 (처리 요약이 있는 경우)
            if 'processing_summary' in results:
                csv_path = output_dir / 'summary.csv'
                try:
                    import csv
                    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)

                        # 헤더
                        writer.writerow([
                            '페이지', '텍스트_영역_수', '글자_수', '텍스트_있음', '텍스트_미리보기'
                        ])

                        # 데이터
                        for page in results.get('pages', []):
                            preview = page.get('combined_text', '')[:100].replace('\n', ' ')
                            if len(preview) > 97:
                                preview += '...'

                            writer.writerow([
                                page.get('page_number', 0),
                                page.get('text_count', 0),
                                page.get('character_count', 0),
                                'Y' if page.get('has_text', False) else 'N',
                                preview
                            ])

                    logger.info(f"CSV 요약 저장: {csv_path}")

                except Exception as e:
                    logger.warning(f"CSV 저장 실패: {str(e)}")

            logger.info(f"✅ 모든 결과 저장 완료: {output_dir}")

        except Exception as e:
            logger.error(f"❌ 결과 저장 실패: {str(e)}")
            raise


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
    """🔥 완전 수정된 처리 결과 페이지"""
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

    # 🔥 템플릿 렌더링 시 필요한 모든 데이터 전달
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

        elif format == 'debug':
            file_path = results_dir / 'debug_info.json'
            if file_path.exists():
                return send_file(file_path, as_attachment=True,
                                 download_name=f"{job['filename']}_debug.json")

        elif format == 'csv':
            file_path = results_dir / 'summary.csv'
            if file_path.exists():
                return send_file(file_path, as_attachment=True,
                                 download_name=f"{job['filename']}_summary.csv")

        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'다운로드 중 오류가 발생했습니다: {str(e)}'}), 500


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


# 🔥 Jinja2 필터 추가 (템플릿에서 숫자 포맷팅에 필요)
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