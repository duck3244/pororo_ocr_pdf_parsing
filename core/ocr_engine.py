#!/usr/bin/env python3
"""
핵심 OCR 엔진 모듈
Pororo OCR을 래핑하여 안정적인 텍스트 추출 기능 제공
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class OCREngine:
    """Pororo OCR 엔진 래퍼 클래스"""

    def __init__(self, model: str = "brainocr", language: str = "ko"):
        """
        OCR 엔진 초기화

        Args:
            model: Pororo OCR 모델명
            language: 언어 코드 (ko, en, etc.)
        """
        self.model = model
        self.language = language
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """OCR 모델 초기화"""
        try:
            from pororo import Pororo
            self.ocr = Pororo(
                task="ocr",
                lang=self.language,
                model=self.model
            )
            logger.info(f"OCR engine initialized: {self.model} ({self.language})")
        except ImportError:
            raise ImportError(
                "Pororo library is not installed. "
                "Please install it with: pip install pororo"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {str(e)}")
            raise

    def extract_text(self, image_path: str, detail: bool = True) -> List[Dict[str, Any]]:
        """
        이미지에서 텍스트 추출

        Args:
            image_path: 이미지 파일 경로
            detail: 상세 정보 포함 여부

        Returns:
            추출된 텍스트와 메타데이터 리스트
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            # OCR 실행
            result = self.ocr(image_path, detail=detail)

            # 결과 정규화
            normalized_results = self._normalize_results(result, image_path)

            logger.debug(f"Extracted {len(normalized_results)} text regions from {image_path}")
            return normalized_results

        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            return []

    def _normalize_results(self, raw_results: Any, image_path: str) -> List[Dict[str, Any]]:
        """
        OCR 결과를 표준 형식으로 정규화

        Args:
            raw_results: Pororo OCR 원본 결과
            image_path: 이미지 파일 경로

        Returns:
            정규화된 결과 리스트
        """
        normalized = []

        if not raw_results:
            return normalized

        # Pororo OCR 결과가 여러 형태로 올 수 있음을 고려
        if isinstance(raw_results, str):
            # 단순 문자열인 경우
            normalized.append({
                'id': 0,
                'text': raw_results,
                'confidence': 1.0,
                'bbox': [0, 0, 0, 0],
                'source_image': image_path,
                'extracted_at': datetime.now().isoformat()
            })
            return normalized

        if isinstance(raw_results, list):
            for i, item in enumerate(raw_results):
                text_region = None

                if isinstance(item, dict):
                    # 딕셔너리 형태의 상세 결과
                    text = ''
                    confidence = 1.0
                    bbox = [0, 0, 0, 0]

                    # 다양한 키 형태 지원
                    if 'description' in item:
                        text = item['description']
                    elif 'text' in item:
                        text = item['text']
                    elif 'word' in item:
                        text = item['word']

                    if 'confidence' in item:
                        confidence = float(item['confidence'])
                    elif 'score' in item:
                        confidence = float(item['score'])

                    if 'bbox' in item:
                        bbox = item['bbox']
                    elif 'bounding_box' in item:
                        bbox = item['bounding_box']
                    elif 'boundingPoly' in item:
                        # Google Vision API 스타일
                        vertices = item['boundingPoly'].get('vertices', [])
                        if len(vertices) >= 2:
                            x_coords = [v.get('x', 0) for v in vertices]
                            y_coords = [v.get('y', 0) for v in vertices]
                            bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

                    text_region = {
                        'id': i,
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox,
                        'source_image': image_path,
                        'extracted_at': datetime.now().isoformat()
                    }

                elif isinstance(item, str):
                    # 단순 문자열인 경우
                    text_region = {
                        'id': i,
                        'text': item,
                        'confidence': 1.0,
                        'bbox': [0, 0, 0, 0],
                        'source_image': image_path,
                        'extracted_at': datetime.now().isoformat()
                    }

                # 빈 텍스트가 아닌 경우만 추가
                if text_region and text_region['text'].strip():
                    normalized.append(text_region)

        return normalized

    def extract_text_simple(self, image_path: str) -> List[str]:
        """
        간단한 텍스트 추출 (문자열만 반환)

        Args:
            image_path: 이미지 파일 경로

        Returns:
            추출된 텍스트 문자열 리스트
        """
        results = self.extract_text(image_path, detail=False)
        return [result['text'] for result in results if result['text'].strip()]

    def batch_extract(self, image_paths: List[str], progress_callback: Optional[callable] = None) -> Dict[
        str, List[Dict[str, Any]]]:
        """
        여러 이미지에서 배치 텍스트 추출

        Args:
            image_paths: 이미지 파일 경로 리스트
            progress_callback: 진행률 콜백 함수

        Returns:
            이미지별 추출 결과 딕셔너리
        """
        results = {}
        total = len(image_paths)

        for i, image_path in enumerate(image_paths):
            try:
                results[image_path] = self.extract_text(image_path)

                if progress_callback:
                    progress_callback(i + 1, total, image_path)

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {str(e)}")
                results[image_path] = []

        return results

    def get_supported_formats(self) -> List[str]:
        """지원되는 이미지 형식 반환"""
        return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']

    def validate_image(self, image_path: str) -> bool:
        """
        이미지 파일 유효성 검사

        Args:
            image_path: 이미지 파일 경로

        Returns:
            유효성 여부
        """
        if not os.path.exists(image_path):
            return False

        ext = os.path.splitext(image_path)[1].lower()
        return ext in self.get_supported_formats()

    def get_engine_info(self) -> Dict[str, Any]:
        """OCR 엔진 정보 반환"""
        return {
            'model': self.model,
            'language': self.language,
            'supported_formats': self.get_supported_formats(),
            'initialized': self.ocr is not None,
            'engine_type': 'Pororo OCR'
        }


class OCRResult:
    """OCR 결과를 담는 데이터 클래스"""

    def __init__(self, text_regions: List[Dict[str, Any]], source_image: str):
        self.text_regions = text_regions
        self.source_image = source_image
        self.extracted_at = datetime.now()

    @property
    def text_count(self) -> int:
        """추출된 텍스트 영역 수"""
        return len(self.text_regions)

    @property
    def combined_text(self) -> str:
        """모든 텍스트를 하나로 합친 결과"""
        return '\n'.join(region['text'] for region in self.text_regions)

    @property
    def confidence_scores(self) -> List[float]:
        """신뢰도 점수 리스트"""
        return [region['confidence'] for region in self.text_regions]

    @property
    def average_confidence(self) -> float:
        """평균 신뢰도"""
        scores = self.confidence_scores
        return sum(scores) / len(scores) if scores else 0.0

    def get_high_confidence_text(self, threshold: float = 0.8) -> List[str]:
        """
        높은 신뢰도의 텍스트만 반환

        Args:
            threshold: 신뢰도 임계값

        Returns:
            높은 신뢰도 텍스트 리스트
        """
        return [
            region['text']
            for region in self.text_regions
            if region['confidence'] >= threshold
        ]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            'source_image': self.source_image,
            'extracted_at': self.extracted_at.isoformat(),
            'text_count': self.text_count,
            'combined_text': self.combined_text,
            'average_confidence': self.average_confidence,
            'text_regions': self.text_regions
        }

    def save_to_file(self, output_path: str, format: str = 'json'):
        """
        결과를 파일로 저장

        Args:
            output_path: 출력 파일 경로
            format: 저장 형식 (json, txt)
        """
        import json

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"OCR Result - {self.source_image}\n")
                f.write(f"Extracted at: {self.extracted_at}\n")
                f.write(f"Text regions: {self.text_count}\n")
                f.write("=" * 50 + "\n\n")
                f.write(self.combined_text)
        else:
            raise ValueError(f"Unsupported format: {format}")


# 사용 예제
if __name__ == "__main__":
    # OCR 엔진 초기화
    ocr_engine = OCREngine()

    # 단일 이미지 처리
    image_path = "sample.png"
    if ocr_engine.validate_image(image_path):
        result = ocr_engine.extract_text(image_path)
        ocr_result = OCRResult(result, image_path)

        print(f"Extracted {ocr_result.text_count} text regions")
        print(f"Average confidence: {ocr_result.average_confidence:.2f}")
        print("Combined text:")
        print(ocr_result.combined_text)
    else:
        print(f"Invalid image: {image_path}")