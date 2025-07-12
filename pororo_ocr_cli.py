#!/usr/bin/env python3
"""
Pororo OCR PDF Parser 통합 CLI
모든 기능을 하나의 인터페이스로 제공
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Optional

# 프로젝트 모듈 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_handler import PDFHandler
from core.image_processor import ImageProcessor
from core.ocr_engine import OCREngine
from core.text_postprocessor import TextPostProcessor
from batch.batch_processor import BatchProcessor
from config.config_manager import ConfigManager, create_default_config_file
from web.app import app


def setup_logging(level: str = "INFO"):
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class PororoOCRCLI:
    """Pororo OCR CLI 메인 클래스"""

    def __init__(self, config_path: Optional[str] = None):
        """CLI 초기화"""
        self.config_manager = ConfigManager(config_path)
        self.config_manager.setup_logging()
        self.logger = logging.getLogger(__name__)

        # 컴포넌트 초기화는 필요할 때만
        self.pdf_handler = None
        self.image_processor = None
        self.ocr_engine = None
        self.text_processor = None

    def _initialize_components(self):
        """처리 컴포넌트 초기화"""
        if not self.pdf_handler:
            self.pdf_handler = PDFHandler()
            self.image_processor = ImageProcessor()
            self.ocr_engine = OCREngine(
                model=self.config_manager.ocr_config.model,
                language=self.config_manager.ocr_config.language
            )
            self.text_processor = TextPostProcessor()
            self.logger.info("Components initialized")

    def process_single_pdf(self, pdf_path: str, output_dir: str = None) -> dict:
        """단일 PDF 처리"""
        self._initialize_components()

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = self.config_manager.output_config.directory

        self.pdf_handler.output_dir = Path(output_dir)
        self.pdf_handler.output_dir.mkdir(exist_ok=True)

        self.logger.info(f"Processing PDF: {pdf_path}")

        try:
            # 1. PDF 정보 추출
            pdf_info = self.pdf_handler.extract_pdf_info(pdf_path)
            self.logger.info(f"PDF has {pdf_info['page_count']} pages")

            # 2. PDF를 이미지로 변환
            image_paths = self.pdf_handler.convert_to_images(
                pdf_path,
                dpi=self.config_manager.pdf_config.dpi
            )

            # 3. 이미지 전처리 (설정에 따라)
            if self.config_manager.pdf_config.preprocessing:
                self.logger.info("Preprocessing images...")
                preprocess_config = self.config_manager.image_config.__dict__
                preprocessed_paths = self.image_processor.batch_preprocess(
                    image_paths,
                    str(self.pdf_handler.output_dir / "preprocessed"),
                    config=preprocess_config
                )
                final_image_paths = [p for p in preprocessed_paths if p is not None]
            else:
                final_image_paths = image_paths

            # 4. OCR 텍스트 추출
            self.logger.info("Extracting text with OCR...")
            ocr_results = self.ocr_engine.batch_extract(final_image_paths)

            # 5. 페이지별 결과 구성
            pages_data = []
            for i, image_path in enumerate(final_image_paths):
                page_number = i + 1
                ocr_result = ocr_results.get(image_path, [])
                combined_text = '\n'.join([region['text'] for region in ocr_result])

                page_data = {
                    'page_number': page_number,
                    'image_path': image_path,
                    'text_regions': [region['text'] for region in ocr_result],
                    'combined_text': combined_text,
                    'text_count': len(ocr_result)
                }

                # 텍스트 후처리 (설정에 따라)
                if self.config_manager.text_config.enable_postprocessing:
                    processed_text = self.text_processor.process_page_text(
                        combined_text, page_number
                    )
                    page_data['processed_text'] = processed_text

                pages_data.append(page_data)

            # 6. 최종 결과 구성
            results = {
                'pdf_info': pdf_info,
                'pages': pages_data,
                'processing_config': self.config_manager.get_processing_config(),
                'processed_at': self.pdf_handler.extract_pdf_info(pdf_path)['extracted_at']
            }

            # 문서 요약 생성 (후처리 활성화 시)
            if self.config_manager.text_config.enable_postprocessing:
                processed_pages = [
                    page['processed_text'] for page in pages_data
                    if 'processed_text' in page
                ]
                if processed_pages:
                    document_summary = self.text_processor.generate_document_summary(processed_pages)
                    results['document_summary'] = document_summary

            # 7. 결과 저장
            self._save_results(results, output_dir)

            # 8. 이미지 정리 (설정에 따라)
            if not self.config_manager.pdf_config.keep_images:
                self._cleanup_images(image_paths + final_image_paths)

            self.logger.info(f"Processing completed: {len(pages_data)} pages processed")
            return results

        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            raise

    def _save_results(self, results: dict, output_dir: str):
        """결과 저장"""
        output_path = Path(output_dir)

        for format_type in self.config_manager.output_config.formats:
            if format_type == 'json':
                json_path = output_path / "results.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f,
                              ensure_ascii=self.config_manager.output_config.ensure_ascii,
                              indent=self.config_manager.output_config.json_indent)
                self.logger.info(f"JSON results saved: {json_path}")

            elif format_type == 'txt':
                txt_path = output_path / "extracted_text.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write("OCR 처리 결과\n")
                    f.write("=" * 50 + "\n\n")
                    for page in results['pages']:
                        f.write(f"페이지 {page['page_number']}\n")
                        f.write("-" * 20 + "\n")
                        f.write(page['combined_text'])
                        f.write("\n\n")
                self.logger.info(f"Text results saved: {txt_path}")

    def _cleanup_images(self, image_paths: list):
        """이미지 파일 정리"""
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove {image_path}: {str(e)}")

    def run_batch_processing(self, input_dir: str, output_dir: str = None, **options) -> dict:
        """배치 처리 실행"""
        if output_dir is None:
            output_dir = "batch_output"

        # 설정 적용
        config = self.config_manager.get_processing_config()
        config.update(options)

        # 배치 프로세서 생성
        processor = BatchProcessor(
            input_dir=input_dir,
            output_dir=output_dir,
            max_workers=self.config_manager.batch_config.max_workers,
            config=config
        )

        # 배치 처리 실행
        results = processor.process_batch(
            use_multiprocessing=options.get('use_multiprocessing', False)
        )

        return results

    def run_web_server(self, **options):
        """웹 서버 실행"""
        web_config = self.config_manager.web_config

        host = options.get('host', web_config.host)
        port = options.get('port', web_config.port)
        debug = options.get('debug', web_config.debug)

        self.logger.info(f"Starting web server on {host}:{port}")

        # Flask 앱 설정 업데이트
        app.config.update({
            'UPLOAD_FOLDER': web_config.upload_folder,
            'MAX_CONTENT_LENGTH': web_config.max_content_length,
            'RESULT_FOLDER': web_config.result_folder
        })

        app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Pororo OCR PDF Parser - 한국어 PDF OCR 통합 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 PDF 처리
  python pororo_ocr_cli.py single document.pdf

  # 배치 처리
  python pororo_ocr_cli.py batch pdf_folder/ --workers 4

  # 웹 서버 실행
  python pororo_ocr_cli.py web --port 8080

  # 설정 파일로 처리
  python pororo_ocr_cli.py single document.pdf --config my_config.yaml
        """
    )

    # 전역 옵션
    parser.add_argument('--config', help='설정 파일 경로')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='로깅 레벨')
    parser.add_argument('--output-dir', help='출력 디렉토리')

    # 서브커맨드
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')

    # single 커맨드
    single_parser = subparsers.add_parser('single', help='단일 PDF 파일 처리')
    single_parser.add_argument('pdf_path', help='처리할 PDF 파일 경로')
    single_parser.add_argument('--dpi', type=int, help='이미지 변환 DPI')
    single_parser.add_argument('--no-preprocess', action='store_true', help='이미지 전처리 비활성화')
    single_parser.add_argument('--no-postprocess', action='store_true', help='텍스트 후처리 비활성화')
    single_parser.add_argument('--keep-images', action='store_true', help='변환된 이미지 보관')

    # batch 커맨드
    batch_parser = subparsers.add_parser('batch', help='배치 처리 (여러 PDF 파일)')
    batch_parser.add_argument('input_dir', help='PDF 파일들이 있는 디렉토리')
    batch_parser.add_argument('--workers', type=int, help='워커 프로세스/스레드 수')
    batch_parser.add_argument('--multiprocessing', action='store_true', help='멀티프로세싱 사용')
    batch_parser.add_argument('--dpi', type=int, help='이미지 변환 DPI')
    batch_parser.add_argument('--no-preprocess', action='store_true', help='이미지 전처리 비활성화')
    batch_parser.add_argument('--no-postprocess', action='store_true', help='텍스트 후처리 비활성화')
    batch_parser.add_argument('--dry-run', action='store_true', help='실제 처리 없이 파일 목록만 표시')

    # web 커맨드
    web_parser = subparsers.add_parser('web', help='웹 서버 실행')
    web_parser.add_argument('--host', default='0.0.0.0', help='서버 호스트')
    web_parser.add_argument('--port', type=int, default=5000, help='서버 포트')
    web_parser.add_argument('--debug', action='store_true', help='디버그 모드')

    # config 커맨드
    config_parser = subparsers.add_parser('config', help='설정 관리')
    config_subparsers = config_parser.add_subparsers(dest='config_action')

    # config create
    create_parser = config_subparsers.add_parser('create', help='기본 설정 파일 생성')
    create_parser.add_argument('--output', default='config.yaml', help='출력 파일 경로')
    create_parser.add_argument('--profile', choices=['fast', 'accurate', 'balanced', 'batch_optimized'],
                               help='프리셋 프로필 사용')

    # config validate
    validate_parser = config_subparsers.add_parser('validate', help='설정 파일 검증')
    validate_parser.add_argument('config_file', help='검증할 설정 파일')

    # config show
    show_parser = config_subparsers.add_parser('show', help='현재 설정 표시')

    # info 커맨드
    info_parser = subparsers.add_parser('info', help='시스템 정보 표시')
    info_parser.add_argument('--pdf', help='PDF 파일 정보 표시')

    args = parser.parse_args()

    # 로깅 설정
    setup_logging(args.log_level)

    try:
        # CLI 인스턴스 생성
        cli = PororoOCRCLI(args.config)

        if args.command == 'single':
            # 단일 PDF 처리
            options = {}
            if args.dpi:
                cli.config_manager.update_config('pdf', dpi=args.dpi)
            if args.no_preprocess:
                cli.config_manager.update_config('pdf', preprocessing=False)
            if args.no_postprocess:
                cli.config_manager.update_config('text_processing', enable_postprocessing=False)
            if args.keep_images:
                cli.config_manager.update_config('pdf', keep_images=True)

            output_dir = args.output_dir or cli.config_manager.output_config.directory

            results = cli.process_single_pdf(args.pdf_path, output_dir)

            # 결과 요약 출력
            print(f"\n{'=' * 60}")
            print("처리 완료!")
            print(f"{'=' * 60}")
            print(f"PDF: {args.pdf_path}")
            print(f"페이지 수: {len(results['pages'])}")

            total_chars = sum(len(page['combined_text']) for page in results['pages'])
            total_regions = sum(page['text_count'] for page in results['pages'])

            print(f"총 글자 수: {total_chars:,}")
            print(f"총 텍스트 영역: {total_regions:,}")
            print(f"출력 위치: {output_dir}")

        elif args.command == 'batch':
            # 배치 처리
            options = {
                'use_multiprocessing': args.multiprocessing,
                'dry_run': args.dry_run
            }

            if args.workers:
                cli.config_manager.update_config('batch', max_workers=args.workers)
            if args.dpi:
                cli.config_manager.update_config('pdf', dpi=args.dpi)
            if args.no_preprocess:
                cli.config_manager.update_config('pdf', preprocessing=False)
            if args.no_postprocess:
                cli.config_manager.update_config('text_processing', enable_postprocessing=False)

            output_dir = args.output_dir or "batch_output"

            if args.dry_run:
                # Dry run 모드
                from batch.batch_processor import BatchProcessor
                processor = BatchProcessor(args.input_dir, output_dir)
                pdf_files = processor.find_pdf_files()

                print(f"\nDry Run - 처리될 파일들:")
                print("-" * 50)
                for i, pdf_file in enumerate(pdf_files, 1):
                    file_size = pdf_file.stat().st_size
                    print(f"{i:3d}. {pdf_file.name} ({file_size:,} bytes)")

                print(f"\n총 {len(pdf_files)}개 파일이 처리될 예정입니다.")
                config = cli.config_manager.get_processing_config()
                print(f"설정: {json.dumps(config, indent=2, ensure_ascii=False)}")
            else:
                results = cli.run_batch_processing(args.input_dir, output_dir, **options)

                # 결과 요약 출력
                batch_info = results['batch_info']
                print(f"\n{'=' * 60}")
                print("배치 처리 완료!")
                print(f"{'=' * 60}")
                print(f"성공: {batch_info['successful_files']}개")
                print(f"실패: {batch_info['failed_files']}개")
                print(f"성공률: {batch_info['success_rate']:.1f}%")
                print(f"총 처리 시간: {batch_info['total_processing_time']:.2f}초")

                if batch_info['successful_files'] > 0:
                    content_stats = results['content_statistics']
                    print(f"총 페이지: {content_stats['total_pages']:,}개")
                    print(f"총 글자 수: {content_stats['total_characters']:,}개")

                print(f"결과 위치: {output_dir}")

        elif args.command == 'web':
            # 웹 서버 실행
            cli.run_web_server(
                host=args.host,
                port=args.port,
                debug=args.debug
            )

        elif args.command == 'config':
            if args.config_action == 'create':
                # 설정 파일 생성
                if args.profile:
                    config_manager = ConfigManager()
                    presets = config_manager.get_profile_presets()
                    if args.profile in presets:
                        profile_config = config_manager.create_profile(args.profile, **presets[args.profile])
                        profile_config.save_config(args.output)
                        print(f"Created {args.profile} profile configuration: {args.output}")
                    else:
                        print(f"Unknown profile: {args.profile}")
                        return 1
                else:
                    success = create_default_config_file(args.output)
                    if not success:
                        return 1

            elif args.config_action == 'validate':
                # 설정 파일 검증
                config_manager = ConfigManager(args.config_file)
                errors = config_manager.validate_config()

                if errors:
                    print("설정 검증 오류:")
                    for section, error_list in errors.items():
                        print(f"  [{section}]:")
                        for error in error_list:
                            print(f"    - {error}")
                    return 1
                else:
                    print("설정이 유효합니다!")

            elif args.config_action == 'show':
                # 현재 설정 표시
                config_dict = cli.config_manager.to_dict()
                print("현재 설정:")
                print(json.dumps(config_dict, indent=2, ensure_ascii=False))

        elif args.command == 'info':
            # 시스템 정보 표시
            print("Pororo OCR PDF Parser 시스템 정보")
            print("=" * 50)

            # 기본 정보
            import torch
            print(f"Python: {sys.version}")
            print(f"PyTorch: {torch.__version__}")
            print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"CUDA 장치 수: {torch.cuda.device_count()}")
                print(f"현재 CUDA 장치: {torch.cuda.current_device()}")

            # CPU 정보
            import multiprocessing
            print(f"CPU 코어 수: {multiprocessing.cpu_count()}")

            # 메모리 정보
            try:
                import psutil
                memory = psutil.virtual_memory()
                print(f"총 메모리: {memory.total / (1024 ** 3):.1f} GB")
                print(f"사용 가능 메모리: {memory.available / (1024 ** 3):.1f} GB")
            except ImportError:
                print("메모리 정보 확인을 위해 psutil 설치 필요")

            # 컴포넌트 상태 확인
            try:
                cli._initialize_components()
                engine_info = cli.ocr_engine.get_engine_info()
                print(f"\nOCR 엔진: {engine_info['engine_type']}")
                print(f"모델: {engine_info['model']}")
                print(f"언어: {engine_info['language']}")
                print(f"지원 형식: {', '.join(engine_info['supported_formats'])}")
            except Exception as e:
                print(f"\nOCR 엔진 초기화 실패: {str(e)}")

            # PDF 정보 (옵션)
            if args.pdf:
                if os.path.exists(args.pdf):
                    try:
                        cli._initialize_components()
                        pdf_info = cli.pdf_handler.extract_pdf_info(args.pdf)
                        print(f"\nPDF 정보: {args.pdf}")
                        print("-" * 30)
                        print(f"파일 크기: {pdf_info['file_size']:,} bytes")
                        print(f"페이지 수: {pdf_info['page_count']}")
                        print(f"제목: {pdf_info['title'] or 'N/A'}")
                        print(f"작성자: {pdf_info['author'] or 'N/A'}")
                        print(f"암호화: {'Yes' if pdf_info['encrypted'] else 'No'}")
                    except Exception as e:
                        print(f"PDF 정보 추출 실패: {str(e)}")
                else:
                    print(f"PDF 파일을 찾을 수 없습니다: {args.pdf}")

        else:
            # 명령어가 지정되지 않은 경우
            parser.print_help()

            # 간단한 사용법 가이드 출력
            print("\n" + "=" * 60)
            print("빠른 시작 가이드:")
            print("=" * 60)
            print("1. 단일 PDF 처리:")
            print("   python pororo_ocr_cli.py single document.pdf")
            print()
            print("2. 여러 PDF 배치 처리:")
            print("   python pororo_ocr_cli.py batch pdf_folder/")
            print()
            print("3. 웹 인터페이스:")
            print("   python pororo_ocr_cli.py web")
            print("   브라우저에서 http://localhost:5000 접속")
            print()
            print("4. 설정 파일 생성:")
            print("   python pororo_ocr_cli.py config create")
            print()
            print("5. 시스템 정보 확인:")
            print("   python pororo_ocr_cli.py info")

        return 0

    except KeyboardInterrupt:
        print("\n처리가 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        logging.getLogger(__name__).error(f"CLI error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())