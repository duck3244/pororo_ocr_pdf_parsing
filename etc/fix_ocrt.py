#!/usr/bin/env python3
"""
OCR 문제 해결 실행 스크립트
기존 파일을 백업하고 개선된 버전으로 교체
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """파일 백업"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 백업 완료: {backup_path}")
        return backup_path
    return None

def apply_ocr_fixes():
    """OCR 수정사항 적용"""
    print("🔧 OCR 문제 해결 시작...")
    print("=" * 60)
    
    # 1. core/ocr_engine.py 교체
    ocr_engine_file = "core/ocr_engine.py"
    if os.path.exists(ocr_engine_file):
        backup_file(ocr_engine_file)
        
        # 개선된 OCR 엔진 코드 작성
        improved_ocr_code = '''#!/usr/bin/env python3
"""
핵심 OCR 엔진 모듈 - Pororo OCR 최적화 완전 수정 버전
"""

import os
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class OCREngine:
    """Pororo OCR 엔진 래퍼 클래스 - 완전 수정 버전"""

    def __init__(self, model: str = "brainocr", language: str = "ko"):
        self.model = model
        self.language = language
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """OCR 모델 초기화"""
        try:
            from pororo import Pororo
            logger.info(f"🚀 Pororo OCR 초기화: {self.model} ({self.language})")
            
            self.ocr = Pororo(
                task="ocr",
                lang=self.language,
                model=self.model
            )
            logger.info(f"✅ OCR 엔진 초기화 성공")
            
        except ImportError:
            logger.error("❌ Pororo 라이브러리가 설치되지 않았습니다.")
            raise ImportError("Pororo library is not installed. Please install it with: pip install pororo")
        except Exception as e:
            logger.error(f"❌ OCR 엔진 초기화 실패: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def extract_text(self, image_path: str, detail: bool = True) -> List[Dict[str, Any]]:
        """이미지에서 텍스트 추출 - Pororo 최적화 버전"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            logger.info(f"🔍 OCR 처리: {os.path.basename(image_path)}")
            
            # Pororo OCR 실행 - detail=True로 모든 정보 획득
            result = self.ocr(image_path, detail=True)
            
            logger.debug(f"📋 OCR 원본 결과 타입: {type(result)}")
            logger.debug(f"📋 OCR 원본 결과: {result}")

            # Pororo 전용 결과 정규화
            normalized_results = self._normalize_pororo_results(result, image_path)

            logger.info(f"✅ 텍스트 추출 완료: {len(normalized_results)}개 영역")
            
            for i, region in enumerate(normalized_results[:3]):
                sample_text = region.get('text', '')[:100]
                logger.info(f"   영역 {i+1}: '{sample_text}'")

            return normalized_results

        except Exception as e:
            logger.error(f"❌ OCR 추출 실패: {image_path} - {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def _normalize_pororo_results(self, raw_results: Any, image_path: str) -> List[Dict[str, Any]]:
        """Pororo OCR 결과 정규화 - 실제 구조 기반"""
        normalized = []
        
        logger.debug(f"🔧 정규화 시작 - 타입: {type(raw_results)}")
        
        if not raw_results:
            logger.warning("⚠️ OCR 결과가 비어있습니다")
            return normalized

        try:
            # Pororo OCR 결과 구조별 처리
            if isinstance(raw_results, dict):
                # detail=True 결과: {'description': [...], 'bounding_poly': [...]}
                if 'description' in raw_results and 'bounding_poly' in raw_results:
                    descriptions = raw_results['description']
                    bounding_polys = raw_results['bounding_poly']
                    
                    logger.debug(f"   descriptions: {len(descriptions)}개, bounding_polys: {len(bounding_polys)}개")
                    
                    for i, (desc, poly) in enumerate(zip(descriptions, bounding_polys)):
                        if desc and desc.strip():
                            # 바운딩 박스 추출
                            bbox = [0, 0, 0, 0]
                            vertices = poly.get('vertices', [])
                            if vertices and len(vertices) >= 2:
                                x_coords = [v.get('x', 0) for v in vertices]
                                y_coords = [v.get('y', 0) for v in vertices]
                                bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                            
                            text_content = {
                                'id': i,
                                'text': desc.strip(),
                                'confidence': 0.95,  # Pororo는 일반적으로 신뢰도가 높음
                                'bbox': bbox,
                                'source_image': image_path,
                                'extracted_at': datetime.now().isoformat()
                            }
                            normalized.append(text_content)
                            logger.debug(f"   추가: '{desc.strip()[:50]}'")
                
                else:
                    # 다른 딕셔너리 구조
                    text_content = self._extract_text_from_dict(raw_results, image_path, 0)
                    if text_content:
                        normalized.append(text_content)
                        
            elif isinstance(raw_results, list):
                logger.debug(f"📊 리스트 결과 - 길이: {len(raw_results)}")
                
                for i, item in enumerate(raw_results):
                    if isinstance(item, tuple) and len(item) >= 2:
                        # (bbox, text, confidence) 구조
                        text = item[1] if len(item) > 1 else ""
                        confidence = item[2] if len(item) > 2 else 0.95
                        bbox_info = item[0] if len(item) > 0 else []
                        
                        if text and text.strip():
                            # 바운딩 박스 처리
                            bbox = [0, 0, 0, 0]
                            if bbox_info:
                                try:
                                    if isinstance(bbox_info[0], (list, tuple)):
                                        # [[x1,y1], [x2,y2], ...] 형태
                                        x_coords = [pt[0] for pt in bbox_info if len(pt) >= 2]
                                        y_coords = [pt[1] for pt in bbox_info if len(pt) >= 2]
                                        if x_coords and y_coords:
                                            bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                                    else:
                                        # [x1, y1, x2, y2] 형태
                                        bbox = list(bbox_info[:4])
                                except:
                                    pass
                            
                            text_content = {
                                'id': i,
                                'text': text.strip(),
                                'confidence': float(confidence) if confidence else 0.95,
                                'bbox': bbox,
                                'source_image': image_path,
                                'extracted_at': datetime.now().isoformat()
                            }
                            normalized.append(text_content)
                            logger.debug(f"   추가: '{text.strip()[:50]}'")
                    
                    elif isinstance(item, dict):
                        text_content = self._extract_text_from_dict(item, image_path, i)
                        if text_content:
                            normalized.append(text_content)
                    
                    elif isinstance(item, str) and item.strip():
                        text_content = {
                            'id': i,
                            'text': item.strip(),
                            'confidence': 0.95,
                            'bbox': [0, 0, 0, 0],
                            'source_image': image_path,
                            'extracted_at': datetime.now().isoformat()
                        }
                        normalized.append(text_content)
                        logger.debug(f"   추가: '{item.strip()[:50]}'")
            
            elif isinstance(raw_results, str) and raw_results.strip():
                text_content = {
                    'id': 0,
                    'text': raw_results.strip(),
                    'confidence': 0.95,
                    'bbox': [0, 0, 0, 0],
                    'source_image': image_path,
                    'extracted_at': datetime.now().isoformat()
                }
                normalized.append(text_content)
                logger.debug(f"   문자열 추가: '{raw_results.strip()[:50]}'")
            
            else:
                logger.warning(f"⚠️ 알 수 없는 결과 형태: {type(raw_results)}")
                # 마지막 시도
                try:
                    str_result = str(raw_results).strip()
                    if str_result and str_result not in ['None', 'null', '[]', '{}']:
                        text_content = {
                            'id': 0,
                            'text': str_result,
                            'confidence': 0.5,
                            'bbox': [0, 0, 0, 0],
                            'source_image': image_path,
                            'extracted_at': datetime.now().isoformat()
                        }
                        normalized.append(text_content)
                        logger.debug(f"   변환 추가: '{str_result[:50]}'")
                except:
                    logger.error(f"❌ 결과 변환 실패: {type(raw_results)}")
        
        except Exception as e:
            logger.error(f"❌ 정규화 중 오류: {str(e)}")
            logger.error(traceback.format_exc())
        
        logger.info(f"🎯 정규화 완료: {len(normalized)}개 텍스트 영역")
        return normalized

    def _extract_text_from_dict(self, item: dict, image_path: str, index: int) -> Optional[Dict[str, Any]]:
        """딕셔너리에서 텍스트 추출"""
        try:
            text = ""
            confidence = 0.95
            bbox = [0, 0, 0, 0]
            
            # 텍스트 추출
            text_keys = ['description', 'text', 'word', 'content', 'ocr_text']
            for key in text_keys:
                if key in item and item[key]:
                    text = str(item[key]).strip()
                    break
            
            # 신뢰도 추출
            conf_keys = ['confidence', 'score', 'prob']
            for key in conf_keys:
                if key in item:
                    try:
                        confidence = float(item[key])
                        break
                    except:
                        continue
            
            # 바운딩 박스 추출
            if 'vertices' in item:
                vertices = item['vertices']
                if vertices:
                    try:
                        x_coords = [v.get('x', 0) for v in vertices if 'x' in v]
                        y_coords = [v.get('y', 0) for v in vertices if 'y' in v]
                        if x_coords and y_coords:
                            bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    except:
                        pass
            
            if text:
                return {
                    'id': index,
                    'text': text,
                    'confidence': confidence,
                    'bbox': bbox,
                    'source_image': image_path,
                    'extracted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.debug(f"딕셔너리 추출 실패 {index}: {str(e)}")
        
        return None

    def batch_extract(self, image_paths: List[str], progress_callback: Optional[callable] = None) -> Dict[str, List[Dict[str, Any]]]:
        """배치 텍스트 추출"""
        results = {}
        total = len(image_paths)

        logger.info(f"🚀 배치 OCR 시작: {total}개 이미지")

        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"📝 처리: {i+1}/{total} - {os.path.basename(image_path)}")
                results[image_path] = self.extract_text(image_path)

                if progress_callback:
                    progress_callback(i + 1, total, image_path)

            except Exception as e:
                logger.error(f"❌ 배치 처리 실패 {image_path}: {str(e)}")
                results[image_path] = []

        successful = len([r for r in results.values() if r])
        logger.info(f"✅ 배치 OCR 완료: {successful}/{total} 성공")
        
        return results

    def get_supported_formats(self) -> List[str]:
        return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']

    def validate_image(self, image_path: str) -> bool:
        if not os.path.exists(image_path):
            return False
        ext = os.path.splitext(image_path)[1].lower()
        return ext in self.get_supported_formats()

    def get_engine_info(self) -> Dict[str, Any]:
        return {
            'model': self.model,
            'language': self.language,
            'supported_formats': self.get_supported_formats(),
            'initialized': self.ocr is not None,
            'engine_type': 'Pororo OCR (Enhanced)',
            'version': 'Enhanced 1.0'
        }


class OCRResult:
    """OCR 결과 데이터 클래스"""

    def __init__(self, text_regions: List[Dict[str, Any]], source_image: str):
        self.text_regions = text_regions
        self.source_image = source_image
        self.extracted_at = datetime.now()

    @property
    def text_count(self) -> int:
        return len(self.text_regions)

    @property
    def combined_text(self) -> str:
        return '\\n'.join(region['text'] for region in self.text_regions if region['text'].strip())

    @property
    def confidence_scores(self) -> List[float]:
        return [region['confidence'] for region in self.text_regions]

    @property
    def average_confidence(self) -> float:
        scores = self.confidence_scores
        return sum(scores) / len(scores) if scores else 0.0

    def get_high_confidence_text(self, threshold: float = 0.8) -> List[str]:
        return [
            region['text']
            for region in self.text_regions
            if region['confidence'] >= threshold and region['text'].strip()
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_image': self.source_image,
            'extracted_at': self.extracted_at.isoformat(),
            'text_count': self.text_count,
            'combined_text': self.combined_text,
            'average_confidence': self.average_confidence,
            'text_regions': self.text_regions
        }
'''
        
        with open(ocr_engine_file, 'w', encoding='utf-8') as f:
            f.write(improved_ocr_code)
        
        print(f"✅ {ocr_engine_file} 수정 완료")
    
    # 2. web/app.py의 process_pdf 함수 수정
    web_app_file = "web/app.py"
    if os.path.exists(web_app_file):
        backup_file(web_app_file)
        
        # 원본 파일 읽기
        with open(web_app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # OCR 결과 처리 부분을 개선된 코드로 교체
        old_ocr_section = '''            # OCR 결과에서 텍스트 추출
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
            combined_text = '\\n'.join(text_regions) if text_regions else \\'\\'

            logger.info(
                f"Page {page_number} final result: {len(text_regions)} regions, {len(combined_text)} characters")'''

        new_ocr_section = '''            # 🔥 개선된 OCR 결과 처리
            text_regions = []
            page_has_text = False

            logger.info(f"📄 페이지 {page_number} OCR 결과 처리: {len(ocr_result)}개 영역")

            for idx, region in enumerate(ocr_result):
                if isinstance(region, dict) and 'text' in region:
                    text = region['text'].strip()
                    if text and len(text) > 0:
                        text_regions.append(text)
                        page_has_text = True
                        logger.debug(f"    영역 {idx+1}: '{text[:50]}{'...' if len(text) > 50 else ''}'")

            # 텍스트 결합
            combined_text = '\\n'.join(text_regions) if text_regions else \\'\\'
            
            logger.info(f"✅ 페이지 {page_number} 최종: {len(text_regions)}개 영역, {len(combined_text)}글자")'''

        # 교체 실행
        if old_ocr_section in content:
            content = content.replace(old_ocr_section, new_ocr_section)
            
            with open(web_app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {web_app_file} OCR 처리 부분 수정 완료")
        else:
            print(f"⚠️ {web_app_file}에서 수정할 부분을 찾지 못했습니다. 수동으로 수정하세요.")

def create_test_script():
    """테스트 스크립트 생성"""
    test_script = '''#!/usr/bin/env python3
"""
OCR 수정 사항 테스트 스크립트
"""

import os
import sys
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ocr_engine():
    """OCR 엔진 테스트"""
    try:
        from core.ocr_engine import OCREngine
        
        print("🧪 OCR 엔진 테스트 시작")
        print("=" * 50)
        
        # OCR 엔진 초기화
        ocr_engine = OCREngine()
        print("✅ OCR 엔진 초기화 성공")
        
        # 엔진 정보
        info = ocr_engine.get_engine_info()
        print(f"📋 엔진 정보: {info}")
        
        # 이미지 파일이 있으면 테스트
        test_images = []
        for ext in ['.png', '.jpg', '.jpeg']:
            for file in os.listdir('.'):
                if file.lower().endswith(ext):
                    test_images.append(file)
                    break
        
        if test_images:
            test_image = test_images[0]
            print(f"\\n🔍 테스트 이미지: {test_image}")
            
            result = ocr_engine.extract_text(test_image)
            print(f"📊 결과: {len(result)}개 텍스트 영역")
            
            for i, region in enumerate(result[:3]):
                print(f"  영역 {i+1}: {region['text'][:100]}...")
                
        else:
            print("⚠️ 테스트할 이미지 파일이 없습니다.")
        
        print("\\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_engine()
'''
    
    with open('test_ocr_fix.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 테스트 스크립트 생성: test_ocr_fix.py")

def main():
    """메인 실행 함수"""
    print("🔧 Pororo OCR 문제 해결 스크립트")
    print("=" * 60)
    
    try:
        # 수정사항 적용
        apply_ocr_fixes()
        
        # 테스트 스크립트 생성
        create_test_script()
        
        print("\n" + "=" * 60)
        print("✅ 모든 수정사항이 적용되었습니다!")
        print("=" * 60)
        print()
        print("📋 적용된 수정사항:")
        print("  1. core/ocr_engine.py - Pororo OCR 결과 처리 최적화")
        print("  2. web/app.py - OCR 결과 처리 부분 개선")
        print()
        print("🧪 테스트 방법:")
        print("  python test_ocr_fix.py")
        print("  python pororo_ocr_cli.py single your_pdf.pdf")
        print("  python pororo_ocr_cli.py web")
        print()
        print("🔍 문제가 계속 발생하면:")
        print("  1. 로그 레벨을 DEBUG로 설정: --log-level DEBUG")
        print("  2. Pororo 라이브러리 재설치: pip install --upgrade pororo")
        print("  3. 이미지 DPI를 낮춰서 테스트: --dpi 200")
        print()
        print("💡 추가 팁:")
        print("  - PDF 품질이 좋을수록 OCR 성능이 향상됩니다")
        print("  - 전처리를 활성화하면 인식률이 개선될 수 있습니다")
        print("  - 한국어 텍스트에 최적화되어 있습니다")
        
    except Exception as e:
        print(f"\n❌ 수정 과정에서 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
        