#!/usr/bin/env python3
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
            print(f"\n🔍 테스트 이미지: {test_image}")
            
            result = ocr_engine.extract_text(test_image)
            print(f"📊 결과: {len(result)}개 텍스트 영역")
            
            for i, region in enumerate(result[:3]):
                print(f"  영역 {i+1}: {region['text'][:100]}...")
                
        else:
            print("⚠️ 테스트할 이미지 파일이 없습니다.")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_engine()
