#!/usr/bin/env python3
"""
OCR 디버깅 및 진단 도구
Pororo OCR의 원본 결과를 자세히 분석하고 문제를 진단
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OCRDebugger:
    """OCR 디버깅 클래스"""
    
    def __init__(self):
        self.pororo_ocr = None
        self.debug_results = []
    
    def initialize_pororo(self):
        """Pororo OCR 초기화"""
        try:
            from pororo import Pororo
            
            print("🚀 Pororo OCR 초기화 중...")
            self.pororo_ocr = Pororo(task="ocr", lang="ko", model="brainocr")
            print("✅ Pororo OCR 초기화 성공")
            return True
            
        except ImportError as e:
            print(f"❌ Pororo 라이브러리 import 실패: {e}")
            print("해결방법: pip install pororo")
            return False
        except Exception as e:
            print(f"❌ Pororo OCR 초기화 실패: {e}")
            print(traceback.format_exc())
            return False
    
    def analyze_image(self, image_path: str, save_debug: bool = True):
        """이미지 분석 및 디버깅"""
        if not os.path.exists(image_path):
            print(f"❌ 이미지 파일 없음: {image_path}")
            return None
        
        if not self.pororo_ocr:
            if not self.initialize_pororo():
                return None
        
        print(f"\n🔍 이미지 분석 시작: {image_path}")
        print("=" * 60)
        
        debug_info = {
            'image_path': image_path,
            'timestamp': datetime.now().isoformat(),
            'file_size': os.path.getsize(image_path),
            'results': {}
        }
        
        # 1. detail=False로 테스트
        print("📋 Test 1: detail=False")
        try:
            result_simple = self.pororo_ocr(image_path, detail=False)
            debug_info['results']['detail_false'] = {
                'type': str(type(result_simple)),
                'content': result_simple,
                'length': len(result_simple) if hasattr(result_simple, '__len__') else 'N/A'
            }
            print(f"   타입: {type(result_simple)}")
            print(f"   내용: {result_simple}")
            print(f"   길이: {len(result_simple) if hasattr(result_simple, '__len__') else 'N/A'}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            debug_info['results']['detail_false'] = {'error': str(e)}
        
        # 2. detail=True로 테스트
        print("\n📋 Test 2: detail=True")
        try:
            result_detail = self.pororo_ocr(image_path, detail=True)
            debug_info['results']['detail_true'] = {
                'type': str(type(result_detail)),
                'content': result_detail,
            }
            print(f"   타입: {type(result_detail)}")
            
            if isinstance(result_detail, dict):
                print(f"   딕셔너리 키: {list(result_detail.keys())}")
                for key, value in result_detail.items():
                    print(f"     {key}: {type(value)} - {len(value) if hasattr(value, '__len__') else 'N/A'}")
                    if key == 'description' and isinstance(value, list):
                        print(f"       샘플 텍스트: {value[:3]}")
                    elif key == 'bounding_poly' and isinstance(value, list):
                        print(f"       샘플 박스: {value[:1]}")
            
            elif isinstance(result_detail, list):
                print(f"   리스트 길이: {len(result_detail)}")
                for i, item in enumerate(result_detail[:3]):
                    print(f"     항목 {i}: {type(item)} - {item}")
            
            else:
                print(f"   내용: {result_detail}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            debug_info['results']['detail_true'] = {'error': str(e)}
        
        # 3. 다양한 옵션으로 테스트
        print("\n📋 Test 3: 다양한 옵션 테스트")
        options_to_test = [
            {'paragraph': True},
            {'paragraph': False},
            {'skip_details': True},
            {'skip_details': False},
        ]
        
        for i, options in enumerate(options_to_test):
            try:
                print(f"   옵션 {i+1}: {options}")
                result = self.pororo_ocr(image_path, **options)
                print(f"     결과 타입: {type(result)}")
                print(f"     결과 길이: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                if isinstance(result, list) and result:
                    print(f"     첫 번째 항목: {result[0]}")
                debug_info['results'][f'option_{i+1}'] = {
                    'options': options,
                    'type': str(type(result)),
                    'content': result
                }
            except Exception as e:
                print(f"     ❌ 오류: {e}")
                debug_info['results'][f'option_{i+1}'] = {
                    'options': options,
                    'error': str(e)
                }
        
        # 4. OCR 엔진 내부 상세 분석
        print("\n📋 Test 4: OCR 엔진 내부 분석")
        try:
            # Pororo OCR의 실제 처리 과정 분석
            from pororo.models.brainOCR.brainocr import Reader
            
            print("   📊 OCR 모델 정보:")
            print(f"     모델: {self.pororo_ocr._model}")
            print(f"     언어: {self.pororo_ocr.config.lang}")
            
            # 실제 OCR 처리 단계별 분석
            print("   🔧 단계별 처리 분석:")
            
            # 이미지 로드 테스트
            import cv2
            img = cv2.imread(image_path)
            if img is not None:
                print(f"     이미지 로드 성공: {img.shape}")
                debug_info['image_info'] = {
                    'shape': img.shape,
                    'dtype': str(img.dtype)
                }
            else:
                print("     ❌ 이미지 로드 실패")
                debug_info['image_info'] = {'error': 'Failed to load image'}
                
        except Exception as e:
            print(f"   ❌ 내부 분석 오류: {e}")
            debug_info['internal_analysis'] = {'error': str(e)}
        
        # 5. 결과 저장
        if save_debug:
            debug_file = f"debug_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(debug_info, f, ensure_ascii=False, indent=2, default=str)
                print(f"\n💾 디버그 정보 저장: {debug_file}")
            except Exception as e:
                print(f"\n❌ 디버그 정보 저장 실패: {e}")
        
        self.debug_results.append(debug_info)
        return debug_info
    
    def test_batch_processing(self, image_dir: str):
        """배치 처리 테스트"""
        if not os.path.exists(image_dir):
            print(f"❌ 디렉토리 없음: {image_dir}")
            return
        
        print(f"\n🚀 배치 처리 테스트: {image_dir}")
        print("=" * 60)
        
        # 이미지 파일 찾기
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            image_files.extend(Path(image_dir).glob(f"*{ext}"))
            image_files.extend(Path(image_dir).glob(f"*{ext.upper()}"))
        
        print(f"📁 발견된 이미지: {len(image_files)}개")
        
        if not image_files:
            print("⚠️ 이미지 파일이 없습니다.")
            return
        
        # 최대 5개 파일로 제한
        test_files = image_files[:5]
        
        for i, image_file in enumerate(test_files):
            print(f"\n📝 {i+1}/{len(test_files)}: {image_file.name}")
            self.analyze_image(str(image_file), save_debug=False)
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        if not self.debug_results:
            print("📋 분석할 결과가 없습니다.")
            return
        
        print("\n📊 OCR 디버깅 요약 보고서")
        print("=" * 60)
        
        total_images = len(self.debug_results)
        successful_results = 0
        
        for result in self.debug_results:
            has_text = False
            
            # detail=True 결과 확인
            detail_true = result['results'].get('detail_true', {})
            if 'content' in detail_true:
                content = detail_true['content']
                if isinstance(content, dict) and 'description' in content:
                    descriptions = content['description']
                    if descriptions and any(desc.strip() for desc in descriptions):
                        has_text = True
                elif isinstance(content, list) and content:
                    has_text = True
                elif isinstance(content, str) and content.strip():
                    has_text = True
            
            if has_text:
                successful_results += 1
        
        success_rate = (successful_results / total_images * 100) if total_images > 0 else 0
        
        print(f"📈 총 분석 이미지: {total_images}개")
        print(f"✅ 텍스트 추출 성공: {successful_results}개")
        print(f"❌ 텍스트 추출 실패: {total_images - successful_results}개")
        print(f"📊 성공률: {success_rate:.1f}%")
        
        # 오류 패턴 분석
        error_patterns = {}
        for result in self.debug_results:
            for test_name, test_result in result['results'].items():
                if 'error' in test_result:
                    error = test_result['error']
                    error_patterns[error] = error_patterns.get(error, 0) + 1
        
        if error_patterns:
            print(f"\n🔍 발견된 오류 패턴:")
            for error, count in error_patterns.items():
                print(f"  - {error}: {count}회")
        
        # 권장사항
        print(f"\n💡 권장사항:")
        if success_rate < 50:
            print("  - Pororo 라이브러리 재설치 필요")
            print("  - 이미지 품질 확인 필요")
            print("  - DPI 설정 조정 (200-400 범위)")
        elif success_rate < 80:
            print("  - 이미지 전처리 활성화")
            print("  - 텍스트 품질 개선")
        else:
            print("  - OCR 성능이 양호합니다")
            print("  - 현재 설정을 유지하세요")


def main():
    """메인 함수"""
    print("🔍 Pororo OCR 디버깅 도구")
    print("=" * 60)
    
    debugger = OCRDebugger()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
        if os.path.isfile(target):
            # 단일 파일 분석
            debugger.analyze_image(target)
        elif os.path.isdir(target):
            # 디렉토리 배치 분석
            debugger.test_batch_processing(target)
        else:
            print(f"❌ 파일 또는 디렉토리를 찾을 수 없습니다: {target}")
            return 1
    else:
        # 현재 디렉토리에서 이미지 찾기
        current_dir = "."
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
            image_files.extend(Path(current_dir).glob(f"*{ext}"))
        
        if image_files:
            print(f"📁 현재 디렉토리에서 {len(image_files)}개 이미지 발견")
            choice = input("분석하시겠습니까? (y/n): ")
            if choice.lower() == 'y':
                debugger.test_batch_processing(current_dir)
            else:
                print("분석을 취소했습니다.")
        else:
            print("❌ 분석할 이미지가 없습니다.")
            print("\n사용법:")
            print("  python debug_ocr.py image.png        # 단일 이미지 분석")
            print("  python debug_ocr.py image_folder/    # 폴더 배치 분석")
            return 1
    
    # 요약 보고서 생성
    debugger.generate_summary_report()
    
    print(f"\n✅ 디버깅 완료!")
    return 0

if __name__ == "__main__":
    exit(main())
