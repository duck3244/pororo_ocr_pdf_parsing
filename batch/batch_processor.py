#!/usr/bin/env python3
"""
배치 처리 모듈
대량의 PDF 파일을 효율적으로 처리하는 기능 제공
"""

import os
import argparse
import json
import csv
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from tqdm import tqdm
import shutil

# 프로젝트 모듈 import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_handler import PDFHandler
from core.image_processor import ImageProcessor
from core.ocr_engine import OCREngine
from core.text_postprocessor import TextPostProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    """배치 처리 클래스"""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str = "batch_output",
                 max_workers: Optional[int] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        배치 프로세서 초기화
        
        Args:
            input_dir: 입력 디렉토리
            output_dir: 출력 디렉토리
            max_workers: 최대 워커 수
            config: 처리 설정
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers or min(cpu_count(), 4)
        
        # 기본 설정
        self.config = {
            'dpi': 300,
            'preprocess': True,
            'postprocess': True,
            'keep_images': False,
            'save_individual_results': True,
            'generate_summary': True
        }
        
        if config:
            self.config.update(config)
        
        # 결과 저장
        self.successful_results = []
        self.failed_results = []
        
        self._setup_directories()
        self._initialize_components()
    
    def _setup_directories(self):
        """디렉토리 구조 설정"""
        self.output_dir.mkdir(exist_ok=True)
        
        # 하위 디렉토리 생성
        self.dirs = {
            'individual': self.output_dir / "individual",
            'combined': self.output_dir / "combined",
            'reports': self.output_dir / "reports",
            'logs': self.output_dir / "logs"
        }
        
        for directory in self.dirs.values():
            directory.mkdir(exist_ok=True)
    
    def _initialize_components(self):
        """처리 컴포넌트 초기화"""
        try:
            self.pdf_handler = PDFHandler()
            self.image_processor = ImageProcessor()
            self.ocr_engine = OCREngine()
            self.text_processor = TextPostProcessor()
            logger.info("Batch processor components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise
    
    def find_pdf_files(self) -> List[Path]:
        """PDF 파일 검색"""
        pdf_files = list(self.input_dir.rglob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        return pdf_files
    
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        단일 PDF 처리
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            처리 결과 딕셔너리
        """
        start_time = time.time()
        pdf_name = pdf_path.stem
        
        result_info = {
            'file_path': str(pdf_path),
            'file_name': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'status': 'processing',
            'start_time': datetime.now().isoformat()
        }
        
        try:
            # 1. PDF 유효성 검사
            validation = self.pdf_handler.validate_pdf(str(pdf_path))
            if not validation['is_valid']:
                raise ValueError(f"Invalid PDF: {validation['error_message']}")
            
            # 2. 개별 출력 디렉토리 생성
            if self.config['save_individual_results']:
                individual_output = self.dirs['individual'] / pdf_name
                individual_output.mkdir(exist_ok=True)
                self.pdf_handler.output_dir = individual_output
            else:
                self.pdf_handler.output_dir = self.output_dir / "temp"
                self.pdf_handler.output_dir.mkdir(exist_ok=True)
            
            # 3. PDF 정보 추출
            pdf_info = self.pdf_handler.extract_pdf_info(str(pdf_path))
            
            # 4. PDF를 이미지로 변환
            image_paths = self.pdf_handler.convert_to_images(
                str(pdf_path),
                dpi=self.config['dpi']
            )
            
            # 5. 이미지 전처리 (옵션)
            if self.config['preprocess']:
                preprocess_dir = self.pdf_handler.output_dir / "preprocessed"
                preprocessed_paths = self.image_processor.batch_preprocess(
                    image_paths,
                    str(preprocess_dir)
                )
                final_image_paths = [p for p in preprocessed_paths if p is not None]
            else:
                final_image_paths = image_paths
            
            # 6. OCR 텍스트 추출
            ocr_results = self.ocr_engine.batch_extract(final_image_paths)
            
            # 7. 결과 구성
            pages_data = []
            total_characters = 0
            total_text_regions = 0
            
            for i, image_path in enumerate(final_image_paths):
                page_number = i + 1
                ocr_result = ocr_results.get(image_path, [])
                combined_text = '\n'.join([region['text'] for region in ocr_result])
                
                page_data = {
                    'page_number': page_number,
                    'text_regions': [region['text'] for region in ocr_result],
                    'combined_text': combined_text,
                    'text_count': len(ocr_result)
                }
                
                # 텍스트 후처리 (옵션)
                if self.config['postprocess']:
                    processed_text = self.text_processor.process_page_text(
                        combined_text, page_number
                    )
                    page_data['processed_text'] = processed_text
                
                pages_data.append(page_data)
                total_characters += len(combined_text)
                total_text_regions += len(ocr_result)
            
            # 8. 결과 통합
            processing_result = {
                'pdf_info': pdf_info,
                'pages': pages_data,
                'processing_config': self.config,
                'processed_at': datetime.now().isoformat()
            }
            
            # 문서 요약 생성 (후처리 활성화 시)
            if self.config['postprocess']:
                processed_pages = [
                    page['processed_text'] for page in pages_data 
                    if 'processed_text' in page
                ]
                if processed_pages:
                    document_summary = self.text_processor.generate_document_summary(processed_pages)
                    processing_result['document_summary'] = document_summary
            
            # 9. 개별 결과 저장
            if self.config['save_individual_results']:
                self._save_individual_result(processing_result, individual_output)
            
            # 10. 이미지 정리 (옵션)
            if not self.config['keep_images']:
                self._cleanup_images(image_paths, final_image_paths)
            
            # 결과 정보 업데이트
            processing_time = time.time() - start_time
            result_info.update({
                'status': 'success',
                'processing_time': processing_time,
                'total_pages': len(pages_data),
                'total_characters': total_characters,
                'total_text_regions': total_text_regions,
                'end_time': datetime.now().isoformat()
            })
            
            # 언어 분포 정보 추가 (후처리된 경우)
            if self.config['postprocess'] and 'document_summary' in processing_result:
                lang_dist = processing_result['document_summary']['document_summary'].get('language_distribution', {})
                result_info['language_distribution'] = lang_dist
            
            logger.info(f"Successfully processed {pdf_path.name} in {processing_time:.2f}s")
            
            return {
                'info': result_info,
                'results': processing_result
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            result_info.update({
                'status': 'error',
                'error_message': error_msg,
                'processing_time': processing_time,
                'end_time': datetime.now().isoformat()
            })
            
            logger.error(f"Failed to process {pdf_path.name}: {error_msg}")
            
            return {
                'info': result_info,
                'error': True
            }
    
    def _save_individual_result(self, result: Dict[str, Any], output_dir: Path):
        """개별 결과 저장"""
        try:
            # JSON 저장
            json_path = output_dir / "result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 텍스트 저장
            txt_path = output_dir / "extracted_text.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"OCR 처리 결과\n")
                f.write(f"처리 시간: {result['processed_at']}\n")
                f.write("=" * 50 + "\n\n")
                
                for page in result['pages']:
                    f.write(f"페이지 {page['page_number']}\n")
                    f.write("-" * 20 + "\n")
                    f.write(page['combined_text'])
                    f.write("\n\n")
            
        except Exception as e:
            logger.error(f"Failed to save individual result: {str(e)}")
    
    def _cleanup_images(self, original_paths: List[str], processed_paths: List[str]):
        """이미지 파일 정리"""
        try:
            all_paths = set(original_paths + processed_paths)
            for path in all_paths:
                if os.path.exists(path):
                    os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to cleanup images: {str(e)}")
    
    def process_batch(self, use_multiprocessing: bool = False) -> Dict[str, Any]:
        """
        배치 처리 실행
        
        Args:
            use_multiprocessing: 멀티프로세싱 사용 여부
            
        Returns:
            배치 처리 결과
        """
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return self._generate_empty_summary()
        
        start_time = time.time()
        logger.info(f"Starting batch processing of {len(pdf_files)} files")
        logger.info(f"Using {self.max_workers} workers ({'multiprocessing' if use_multiprocessing else 'threading'})")
        
        # 실행기 선택
        executor_class = ProcessPoolExecutor if use_multiprocessing else ThreadPoolExecutor
        
        with executor_class(max_workers=self.max_workers) as executor:
            # 진행률 표시와 함께 처리
            with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
                # 작업 제출
                future_to_pdf = {
                    executor.submit(self.process_single_pdf, pdf_file): pdf_file
                    for pdf_file in pdf_files
                }
                
                # 결과 수집
                for future in future_to_pdf:
                    try:
                        result = future.result()
                        
                        if 'error' in result:
                            self.failed_results.append(result['info'])
                        else:
                            self.successful_results.append(result)
                        
                        # 진행률 업데이트
                        pbar.update(1)
                        pbar.set_postfix({
                            'Success': len(self.successful_results),
                            'Failed': len(self.failed_results)
                        })
                        
                    except Exception as e:
                        pdf_file = future_to_pdf[future]
                        error_info = {
                            'file_path': str(pdf_file),
                            'file_name': pdf_file.name,
                            'status': 'executor_error',
                            'error_message': f"Executor error: {str(e)}",
                            'end_time': datetime.now().isoformat()
                        }
                        self.failed_results.append(error_info)
                        pbar.update(1)
        
        total_time = time.time() - start_time
        
        # 배치 요약 생성
        batch_summary = self._generate_batch_summary(total_time)
        
        # 결과 저장
        self._save_batch_results(batch_summary)
        
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        logger.info(f"Success: {len(self.successful_results)}, Failed: {len(self.failed_results)}")
        
        return batch_summary
    
    def _generate_empty_summary(self) -> Dict[str, Any]:
        """빈 요약 생성"""
        return {
            'batch_info': {
                'total_files': 0,
                'successful_files': 0,
                'failed_files': 0,
                'success_rate': 0.0,
                'message': 'No PDF files found to process'
            }
        }
    
    def _generate_batch_summary(self, total_time: float) -> Dict[str, Any]:
        """배치 처리 요약 생성"""
        successful_infos = [r['info'] for r in self.successful_results]
        
        total_files = len(self.successful_results) + len(self.failed_results)
        success_rate = (len(self.successful_results) / total_files * 100) if total_files > 0 else 0
        
        # 통계 계산
        if successful_infos:
            total_pages = sum(info['total_pages'] for info in successful_infos)
            total_chars = sum(info['total_characters'] for info in successful_infos)
            total_regions = sum(info['total_text_regions'] for info in successful_infos)
            avg_processing_time = sum(info['processing_time'] for info in successful_infos) / len(successful_infos)
            
            # 파일 크기 통계
            file_sizes = [info['file_size'] for info in successful_infos]
            avg_file_size = sum(file_sizes) / len(file_sizes)
            
            # 언어 분포 집계
            all_languages = {}
            for info in successful_infos:
                if 'language_distribution' in info:
                    for lang, count in info['language_distribution'].items():
                        all_languages[lang] = all_languages.get(lang, 0) + count
        else:
            total_pages = total_chars = total_regions = 0
            avg_processing_time = avg_file_size = 0
            all_languages = {}
        
        return {
            'batch_info': {
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'total_files': total_files,
                'successful_files': len(self.successful_results),
                'failed_files': len(self.failed_results),
                'success_rate': round(success_rate, 2),
                'total_processing_time': round(total_time, 2),
                'average_processing_time': round(avg_processing_time, 2),
                'max_workers': self.max_workers,
                'processed_at': datetime.now().isoformat()
            },
            'content_statistics': {
                'total_pages': total_pages,
                'total_characters': total_chars,
                'total_text_regions': total_regions,
                'average_pages_per_file': round(total_pages / len(successful_infos), 2) if successful_infos else 0,
                'average_chars_per_file': round(total_chars / len(successful_infos), 2) if successful_infos else 0,
                'average_file_size_bytes': round(avg_file_size, 2),
                'language_distribution': all_languages
            },
            'processing_config': self.config,
            'successful_files': successful_infos,
            'failed_files': self.failed_results
        }
    
    def _save_batch_results(self, batch_summary: Dict[str, Any]):
        """배치 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON 요약 저장
        json_path = self.dirs['reports'] / f"batch_summary_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, ensure_ascii=False, indent=2)
        
        # 2. CSV 요약 저장
        csv_path = self.dirs['reports'] / f"batch_details_{timestamp}.csv"
        self._save_csv_summary(batch_summary, csv_path)
        
        # 3. 텍스트 보고서 저장
        report_path = self.dirs['reports'] / f"batch_report_{timestamp}.txt"
        report_content = self._generate_text_report(batch_summary)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # 4. 통합 텍스트 파일 생성 (성공한 파일들만)
        if self.successful_results:
            combined_path = self.dirs['combined'] / f"all_extracted_text_{timestamp}.txt"
            self._save_combined_text(combined_path)
        
        # 5. 처리 설정 저장
        config_path = self.dirs['reports'] / f"processing_config_{timestamp}.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Batch results saved:")
        logger.info(f"  Summary: {json_path}")
        logger.info(f"  Details: {csv_path}")
        logger.info(f"  Report: {report_path}")
        if self.successful_results:
            logger.info(f"  Combined text: {combined_path}")
    
    def _save_csv_summary(self, batch_summary: Dict[str, Any], csv_path: Path):
        """CSV 요약 저장"""
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 헤더
            writer.writerow([
                'File Name', 'Status', 'Pages', 'Characters', 'Text Regions',
                'Processing Time (s)', 'File Size (bytes)', 'Language Distribution', 'Error Message'
            ])
            
            # 성공한 파일들
            for info in batch_summary['successful_files']:
                lang_dist = json.dumps(info.get('language_distribution', {}), ensure_ascii=False)
                writer.writerow([
                    info['file_name'],
                    info['status'],
                    info.get('total_pages', 0),
                    info.get('total_characters', 0),
                    info.get('total_text_regions', 0),
                    f"{info['processing_time']:.2f}",
                    info['file_size'],
                    lang_dist,
                    ''
                ])
            
            # 실패한 파일들
            for info in batch_summary['failed_files']:
                writer.writerow([
                    info['file_name'],
                    info['status'],
                    '', '', '', 
                    f"{info.get('processing_time', 0):.2f}",
                    info.get('file_size', 0),
                    '',
                    info.get('error_message', 'Unknown error')
                ])
    
    def _generate_text_report(self, batch_summary: Dict[str, Any]) -> str:
        """텍스트 보고서 생성"""
        lines = []
        batch_info = batch_summary['batch_info']
        content_stats = batch_summary['content_statistics']
        
        lines.append("=" * 80)
        lines.append("PORORO OCR 배치 처리 보고서")
        lines.append("=" * 80)
        lines.append(f"생성 시간: {batch_info['processed_at']}")
        lines.append(f"입력 디렉토리: {batch_info['input_directory']}")
        lines.append(f"출력 디렉토리: {batch_info['output_directory']}")
        lines.append("")
        
        # 처리 요약
        lines.append("처리 요약:")
        lines.append("-" * 40)
        lines.append(f"  총 파일 수: {batch_info['total_files']:,}")
        lines.append(f"  성공: {batch_info['successful_files']:,} ({batch_info['success_rate']:.1f}%)")
        lines.append(f"  실패: {batch_info['failed_files']:,}")
        lines.append(f"  총 처리 시간: {batch_info['total_processing_time']:.2f}초")
        lines.append(f"  평균 처리 시간: {batch_info['average_processing_time']:.2f}초/파일")
        lines.append(f"  워커 수: {batch_info['max_workers']}")
        lines.append("")
        
        # 내용 통계
        if batch_info['successful_files'] > 0:
            lines.append("내용 통계:")
            lines.append("-" * 40)
            lines.append(f"  총 페이지 수: {content_stats['total_pages']:,}")
            lines.append(f"  총 글자 수: {content_stats['total_characters']:,}")
            lines.append(f"  총 텍스트 영역: {content_stats['total_text_regions']:,}")
            lines.append(f"  파일당 평균 페이지: {content_stats['average_pages_per_file']:.1f}")
            lines.append(f"  파일당 평균 글자 수: {content_stats['average_chars_per_file']:,.0f}")
            lines.append(f"  평균 파일 크기: {content_stats['average_file_size_bytes']:,.0f} bytes")
            lines.append("")
            
            # 언어 분포
            if content_stats['language_distribution']:
                lines.append("언어 분포:")
                lines.append("-" * 40)
                for lang, count in content_stats['language_distribution'].items():
                    lines.append(f"  {lang}: {count:,}페이지")
                lines.append("")
        
        # 성공한 파일들 (최대 20개)
        successful_files = batch_summary['successful_files']
        if successful_files:
            lines.append("성공한 파일들:")
            lines.append("-" * 40)
            for i, info in enumerate(successful_files[:20]):
                lines.append(f"  ✓ {info['file_name']} - {info.get('total_pages', 0)}페이지, {info['processing_time']:.2f}초")
            
            if len(successful_files) > 20:
                lines.append(f"  ... 외 {len(successful_files) - 20}개 파일")
            lines.append("")
        
        # 실패한 파일들
        failed_files = batch_summary['failed_files']
        if failed_files:
            lines.append("실패한 파일들:")
            lines.append("-" * 40)
            for info in failed_files:
                lines.append(f"  ✗ {info['file_name']} - {info.get('error_message', 'Unknown error')}")
            lines.append("")
        
        # 처리 설정
        lines.append("처리 설정:")
        lines.append("-" * 40)
        config = batch_summary['processing_config']
        for key, value in config.items():
            lines.append(f"  {key}: {value}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _save_combined_text(self, output_path: Path):
        """통합 텍스트 파일 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"통합 추출 텍스트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for result in self.successful_results:
                info = result['info']
                pages = result['results']['pages']
                
                f.write(f"파일: {info['file_name']}\n")
                f.write(f"처리 시간: {info['processing_time']:.2f}초\n")
                f.write("-" * 60 + "\n")
                
                for page in pages:
                    f.write(f"\n페이지 {page['page_number']}:\n")
                    f.write(page['combined_text'])
                    f.write("\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """처리 요약 반환"""
        total_files = len(self.successful_results) + len(self.failed_results)
        
        if total_files == 0:
            return {'message': 'No files processed yet'}
        
        successful_infos = [r['info'] for r in self.successful_results]
        
        summary = {
            'total_files': total_files,
            'successful': len(self.successful_results),
            'failed': len(self.failed_results),
            'success_rate': len(self.successful_results) / total_files * 100
        }
        
        if successful_infos:
            summary.update({
                'total_pages': sum(info.get('total_pages', 0) for info in successful_infos),
                'total_characters': sum(info.get('total_characters', 0) for info in successful_infos),
                'average_processing_time': sum(info['processing_time'] for info in successful_infos) / len(successful_infos)
            })
        
        return summary


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Pororo OCR Batch Processor')
    parser.add_argument('input_dir', help='Input directory containing PDF files')
    parser.add_argument('--output-dir', default='batch_output', help='Output directory')
    parser.add_argument('--workers', type=int, help='Number of worker processes/threads')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for image conversion')
    parser.add_argument('--no-preprocess', action='store_true', help='Disable image preprocessing')
    parser.add_argument('--no-postprocess', action='store_true', help='Disable text postprocessing')
    parser.add_argument('--keep-images', action='store_true', help='Keep converted images')
    parser.add_argument('--multiprocessing', action='store_true', help='Use multiprocessing instead of threading')
    parser.add_argument('--config', help='JSON config file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    
    args = parser.parse_args()
    
    # 입력 디렉토리 확인
    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1
    
    # 설정 로드
    config = {
        'dpi': args.dpi,
        'preprocess': not args.no_preprocess,
        'postprocess': not args.no_postprocess,
        'keep_images': args.keep_images
    }
    
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
            logger.info(f"Loaded config from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load config file: {str(e)}")
            return 1
    
    # 배치 프로세서 생성
    try:
        processor = BatchProcessor(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            max_workers=args.workers,
            config=config
        )
        
        # Dry run 모드
        if args.dry_run:
            pdf_files = processor.find_pdf_files()
            print(f"\nDry Run - 처리될 파일들:")
            print("-" * 50)
            for i, pdf_file in enumerate(pdf_files, 1):
                file_size = pdf_file.stat().st_size
                print(f"{i:3d}. {pdf_file.name} ({file_size:,} bytes)")
            
            print(f"\n총 {len(pdf_files)}개 파일이 처리될 예정입니다.")
            print(f"설정: {config}")
            return 0
        
        # 배치 처리 실행
        logger.info("Starting batch processing...")
        start_time = time.time()
        
        batch_summary = processor.process_batch(use_multiprocessing=args.multiprocessing)
        
        # 결과 출력
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print("배치 처리 완료!")
        print(f"{'='*60}")
        print(f"총 처리 시간: {total_time:.2f}초")
        print(f"성공: {batch_summary['batch_info']['successful_files']}개")
        print(f"실패: {batch_summary['batch_info']['failed_files']}개")
        print(f"성공률: {batch_summary['batch_info']['success_rate']:.1f}%")
        
        if batch_summary['batch_info']['successful_files'] > 0:
            content_stats = batch_summary['content_statistics']
            print(f"총 페이지: {content_stats['total_pages']:,}개")
            print(f"총 글자 수: {content_stats['total_characters']:,}개")
        
        print(f"\n결과 저장 위치: {processor.output_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())