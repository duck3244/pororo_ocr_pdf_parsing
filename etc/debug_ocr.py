#!/usr/bin/env python3
"""
OCR 결과 디버깅 스크립트
실제 OCR 결과를 확인하고 문제점을 파악합니다.
"""

import sys
import os
import json
from pprint import pprint

# 프로젝트 모듈 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.ocr_engine import OCREngine
    from core.pdf_handler import PDFHandler
    from core.image_processor import ImageProcessor
except ImportError as e:
    print(f"Import 오류: {e}")
    print("필요한 모듈을 먼저 설치하고 import 경로를 확인하세요.")
    sys.exit(1)

def test_pororo_ocr_directly():
    """Pororo OCR을 직접 테스트"""
    print("🧪 Pororo OCR 직접 테스트")
    print("=" * 40)
    
    try:
        from pororo import Pororo
        ocr = Pororo(task="ocr", lang="ko", model="brainocr")
        
        # 테스트 이미지 경로 (실제 생성된 이미지 경로 사용)
        test_images = [
            "output/images/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e_sample_page_001.png",
            "static/results/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e/preprocessed/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e_sample_page_001_preprocessed.png"
        ]
        
        for image_path in test_images:
            if os.path.exists(image_path):
                print(f"\n📷 테스트 이미지: {image_path}")
                
                # detail=False로 테스트
                print("\n--- detail=False 결과 ---")
                result_simple = ocr(image_path, detail=False)
                print(f"타입: {type(result_simple)}")
                print(f"결과: {result_simple}")
                
                # detail=True로 테스트
                print("\n--- detail=True 결과 ---")
                result_detailed = ocr(image_path, detail=True)
                print(f"타입: {type(result_detailed)}")
                print("결과 구조:")
                pprint(result_detailed)
                
                print("\n" + "="*50)
            else:
                print(f"❌ 이미지 파일 없음: {image_path}")
                
    except Exception as e:
        print(f"❌ Pororo OCR 테스트 실패: {str(e)}")

def test_ocr_engine():
    """OCREngine 클래스 테스트"""
    print("\n🔧 OCREngine 클래스 테스트")
    print("=" * 40)
    
    try:
        engine = OCREngine()
        
        test_images = [
            "output/images/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e_sample_page_001.png",
            "static/results/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e/preprocessed/8cfe0bb3-b0c3-4690-9b25-31e87ea6038e_sample_page_001_preprocessed.png"
        ]
        
        for image_path in test_images:
            if os.path.exists(image_path):
                print(f"\n📷 테스트 이미지: {image_path}")
                
                result = engine.extract_text(image_path)
                print(f"정규화된 결과 ({len(result)}개 영역):")
                for i, region in enumerate(result):
                    print(f"  {i+1}. {region['text']} (신뢰도: {region['confidence']})")
                
    except Exception as e:
        print(f"❌ OCREngine 테스트 실패: {str(e)}")

def test_sample_pdf():
    """샘플 PDF로 전체 파이프라인 테스트"""
    print("\n📄 샘플 PDF 전체 파이프라인 테스트")
    print("=" * 40)
    
    # 업로드된 샘플 PDF 경로 확인
    sample_pdf = None
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith('.pdf'):
                sample_pdf = os.path.join(uploads_dir, file)
                break
    
    if not sample_pdf:
        print("❌ 샘플 PDF 파일을 찾을 수 없습니다.")
        print("웹 인터페이스에서 PDF를 업로드한 후 다시 시도하세요.")
        return
    
    print(f"📁 샘플 PDF: {sample_pdf}")
    
    try:
        # PDF 핸들러로 이미지 변환
        pdf_handler = PDFHandler("debug_output")
        image_paths = pdf_handler.convert_to_images(sample_pdf, dpi=300)
        print(f"✅ {len(image_paths)}개 페이지를 이미지로 변환")
        
        # OCR 엔진으로 텍스트 추출
        ocr_engine = OCREngine()
        
        for i, image_path in enumerate(image_paths):
            print(f"\n--- 페이지 {i+1} ---")
            result = ocr_engine.extract_text(image_path)
            
            print(f"추출된 텍스트 영역: {len(result)}개")
            for j, region in enumerate(result):
                print(f"  영역 {j+1}: '{region['text']}' (신뢰도: {region['confidence']:.2f})")
        
    except Exception as e:
        print(f"❌ 전체 파이프라인 테스트 실패: {str(e)}")

def analyze_log_output():
    """로그 출력 분석"""
    print("\n📋 로그 분석")
    print("=" * 40)
    
    print("현재 상황 분석:")
    print("1. ✅ 웹 서버가 정상적으로 시작됨")
    print("2. ✅ PDF 업로드 및 이미지 변환 성공")
    print("3. ✅ 이미지 전처리 성공 (기울기 보정 포함)")
    print("4. ⚠️ OCR 결과가 예상과 다름:")
    print("   - 실제 텍스트: 'Pdf 파일 샘플'")
    print("   - OCR 결과: 'description', 'bounding_poly'")
    print("5. ⚠️ 텍스트 후처리가 제대로 적용되지 않음")
    
    print("\n추정 원인:")
    print("- Pororo OCR 결과 형식이 예상과 다름")
    print("- OCR 결과 파싱에서 메타데이터 키를 텍스트로 인식")
    print("- 텍스트 후처리 시 빈 텍스트로 인한 처리 건너뛰기")

def main():
    """메인 함수"""
    print("🐛 Pororo OCR PDF Parser - 디버깅 도구")
    print("=" * 60)
    
    # 현재 환경 확인
    print(f"📂 현재 디렉토리: {os.getcwd()}")
    print(f"🐍 Python 경로: {sys.executable}")
    
    # 로그 분석
    analyze_log_output()
    
    # Pororo OCR 직접 테스트
    test_pororo_ocr_directly()
    
    # OCREngine 테스트
    test_ocr_engine()
    
    # 전체 파이프라인 테스트
    test_sample_pdf()
    
    print("\n💡 권장사항:")
    print("1. OCR 결과 파싱 로직 개선")
    print("2. 텍스트 후처리 오류 처리 강화")
    print("3. 디버그 모드로 더 자세한 로그 확인")

if __name__ == "__main__":
    main()
