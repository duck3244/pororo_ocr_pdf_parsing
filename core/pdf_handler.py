#!/usr/bin/env python3
"""
PDF 처리 모듈
PDF 파일을 이미지로 변환하고 메타데이터를 추출하는 기능 제공
"""

import os
import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFHandler:
    """PDF 파일 처리 클래스"""
    
    def __init__(self, output_dir: str = "output"):
        """
        PDF 핸들러 초기화
        
        Args:
            output_dir: 출력 디렉토리 경로
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 하위 디렉토리 생성
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def extract_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 메타데이터 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            PDF 메타데이터 딕셔너리
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            metadata = doc.metadata
            
            pdf_info = {
                'file_path': pdf_path,
                'file_name': os.path.basename(pdf_path),
                'file_size': os.path.getsize(pdf_path),
                'page_count': len(doc),
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'encrypted': doc.needs_pass,
                'extracted_at': datetime.now().isoformat()
            }
            
            # 페이지별 정보
            pages_info = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_info = {
                    'page_number': page_num + 1,
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'rotation': page.rotation,
                    'has_text': bool(page.get_text().strip()),
                    'has_images': bool(page.get_images()),
                    'has_drawings': bool(page.get_drawings())
                }
                pages_info.append(page_info)
            
            pdf_info['pages'] = pages_info
            
            doc.close()
            logger.info(f"Extracted metadata from {pdf_path}")
            return pdf_info
            
        except Exception as e:
            logger.error(f"Failed to extract PDF info from {pdf_path}: {str(e)}")
            raise
    
    def convert_to_images(self, 
                         pdf_path: str, 
                         dpi: int = 300,
                         image_format: str = "PNG",
                         progress_callback: Optional[callable] = None) -> List[str]:
        """
        PDF를 이미지로 변환
        
        Args:
            pdf_path: PDF 파일 경로
            dpi: 해상도 (DPI)
            image_format: 이미지 형식 (PNG, JPEG)
            progress_callback: 진행률 콜백 함수
            
        Returns:
            생성된 이미지 파일 경로 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            pdf_name = Path(pdf_path).stem
            image_paths = []
            
            # 변환 매트릭스 생성 (DPI 설정)
            mat = fitz.Matrix(dpi/72, dpi/72)
            
            logger.info(f"Converting {pdf_name} to images (DPI: {dpi}, Format: {image_format})")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 페이지를 이미지로 렌더링
                pix = page.get_pixmap(matrix=mat)
                
                # 이미지 파일 경로 생성
                image_filename = f"{pdf_name}_page_{page_num + 1:03d}.{image_format.lower()}"
                image_path = self.images_dir / image_filename
                
                # 이미지 저장
                pix.save(str(image_path))
                image_paths.append(str(image_path))
                
                # 진행률 콜백 호출
                if progress_callback:
                    progress_callback(page_num + 1, len(doc), str(image_path))
                
                logger.debug(f"Converted page {page_num + 1}/{len(doc)}: {image_filename}")
            
            doc.close()
            logger.info(f"Successfully converted {len(image_paths)} pages to images")
            return image_paths
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            raise
    
    def extract_text_direct(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF에서 직접 텍스트 추출 (OCR 없이)
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트 정보
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            pages_text = []
            total_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                page_info = {
                    'page_number': page_num + 1,
                    'text': page_text,
                    'character_count': len(page_text),
                    'word_count': len(page_text.split()) if page_text else 0,
                    'has_text': bool(page_text.strip())
                }
                
                pages_text.append(page_info)
                total_text += page_text + "\n"
            
            doc.close()
            
            result = {
                'file_path': pdf_path,
                'total_pages': len(pages_text),
                'total_characters': len(total_text),
                'total_words': len(total_text.split()),
                'pages': pages_text,
                'combined_text': total_text,
                'extracted_at': datetime.now().isoformat()
            }
            
            logger.info(f"Extracted text directly from {pdf_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise
    
    def split_pdf(self, pdf_path: str, page_ranges: List[Tuple[int, int]]) -> List[str]:
        """
        PDF를 페이지 범위별로 분할
        
        Args:
            pdf_path: PDF 파일 경로
            page_ranges: 페이지 범위 리스트 [(시작, 끝), ...]
            
        Returns:
            분할된 PDF 파일 경로 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            source_doc = fitz.open(pdf_path)
            pdf_name = Path(pdf_path).stem
            split_files = []
            
            for i, (start_page, end_page) in enumerate(page_ranges):
                # 새 문서 생성
                new_doc = fitz.open()
                
                # 페이지 범위 복사
                new_doc.insert_pdf(source_doc, from_page=start_page-1, to_page=end_page-1)
                
                # 분할된 파일 저장
                split_filename = f"{pdf_name}_part_{i+1}_pages_{start_page}-{end_page}.pdf"
                split_path = self.output_dir / split_filename
                new_doc.save(str(split_path))
                new_doc.close()
                
                split_files.append(str(split_path))
                logger.info(f"Created split file: {split_filename}")
            
            source_doc.close()
            return split_files
            
        except Exception as e:
            logger.error(f"Failed to split PDF: {str(e)}")
            raise
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """
        여러 PDF 파일을 하나로 병합
        
        Args:
            pdf_paths: 병합할 PDF 파일 경로 리스트
            output_path: 출력 파일 경로
            
        Returns:
            병합된 PDF 파일 경로
        """
        try:
            merged_doc = fitz.open()
            
            for pdf_path in pdf_paths:
                if not os.path.exists(pdf_path):
                    logger.warning(f"PDF file not found, skipping: {pdf_path}")
                    continue
                
                source_doc = fitz.open(pdf_path)
                merged_doc.insert_pdf(source_doc)
                source_doc.close()
                logger.info(f"Merged: {pdf_path}")
            
            merged_doc.save(output_path)
            merged_doc.close()
            
            logger.info(f"Successfully merged {len(pdf_paths)} PDFs into {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to merge PDFs: {str(e)}")
            raise
    
    def optimize_pdf(self, pdf_path: str, output_path: str = None) -> str:
        """
        PDF 파일 최적화 (크기 줄이기)
        
        Args:
            pdf_path: 입력 PDF 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            최적화된 PDF 파일 경로
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if output_path is None:
            pdf_name = Path(pdf_path).stem
            output_path = self.output_dir / f"{pdf_name}_optimized.pdf"
        
        try:
            doc = fitz.open(pdf_path)
            
            # 최적화 옵션
            doc.save(
                str(output_path),
                garbage=4,  # 가비지 수집
                deflate=True,  # 압축
                clean=True,  # 정리
                linear=True  # 웹 최적화
            )
            
            doc.close()
            
            # 파일 크기 비교
            original_size = os.path.getsize(pdf_path)
            optimized_size = os.path.getsize(output_path)
            reduction = (1 - optimized_size / original_size) * 100
            
            logger.info(f"PDF optimized: {reduction:.1f}% size reduction")
            logger.info(f"Original: {original_size:,} bytes, Optimized: {optimized_size:,} bytes")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to optimize PDF: {str(e)}")
            raise
    
    def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일 유효성 검사
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            검사 결과 딕셔너리
        """
        validation_result = {
            'is_valid': False,
            'file_exists': False,
            'is_pdf': False,
            'is_readable': False,
            'is_encrypted': False,
            'error_message': None
        }
        
        try:
            # 파일 존재 확인
            if not os.path.exists(pdf_path):
                validation_result['error_message'] = "File does not exist"
                return validation_result
            
            validation_result['file_exists'] = True
            
            # PDF 형식 확인
            if not pdf_path.lower().endswith('.pdf'):
                validation_result['error_message'] = "Not a PDF file"
                return validation_result
            
            validation_result['is_pdf'] = True
            
            # PDF 읽기 시도
            doc = fitz.open(pdf_path)
            
            # 암호화 확인
            if doc.needs_pass:
                validation_result['is_encrypted'] = True
                validation_result['error_message'] = "PDF is encrypted"
                doc.close()
                return validation_result
            
            # 페이지 수 확인
            if len(doc) == 0:
                validation_result['error_message'] = "PDF has no pages"
                doc.close()
                return validation_result
            
            validation_result['is_readable'] = True
            validation_result['is_valid'] = True
            
            doc.close()
            
        except Exception as e:
            validation_result['error_message'] = str(e)
        
        return validation_result
    
    def cleanup_images(self):
        """생성된 이미지 파일들 정리"""
        try:
            import shutil
            if self.images_dir.exists():
                shutil.rmtree(self.images_dir)
                self.images_dir.mkdir(exist_ok=True)
                logger.info("Cleaned up image files")
        except Exception as e:
            logger.error(f"Failed to cleanup images: {str(e)}")


# 사용 예제
if __name__ == "__main__":
    # PDF 핸들러 초기화
    pdf_handler = PDFHandler("test_output")
    
    # PDF 파일 경로
    pdf_path = "sample.pdf"
    
    # PDF 유효성 검사
    validation = pdf_handler.validate_pdf(pdf_path)
    if not validation['is_valid']:
        print(f"Invalid PDF: {validation['error_message']}")
        exit(1)
    
    # PDF 정보 추출
    pdf_info = pdf_handler.extract_pdf_info(pdf_path)
    print(f"PDF: {pdf_info['file_name']}")
    print(f"Pages: {pdf_info['page_count']}")
    print(f"Size: {pdf_info['file_size']:,} bytes")
    
    # 이미지로 변환
    def progress_callback(current, total, filename):
        print(f"Converting page {current}/{total}: {filename}")
    
    image_paths = pdf_handler.convert_to_images(
        pdf_path, 
        dpi=300, 
        progress_callback=progress_callback
    )
    
    print(f"Converted to {len(image_paths)} images")
