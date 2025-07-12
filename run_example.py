#!/usr/bin/env python3
"""
Pororo OCR PDF Parser 실행 예제
Import 오류 해결 및 기본 사용법 데모
"""

import os
import sys

def check_imports():
    """필수 모듈 import 확인"""
    print("🔍 모듈 import 확인 중...")
    
    try:
        # Core 모듈 import 테스트
        from core.ocr_engine import OCREngine
        print("✅ OCREngine import 성공")
        
        from core.pdf_handler import PDFHandler
        print("✅ PDFHandler import 성공")
        
        from core.image_processor import ImageProcessor
        print("✅ ImageProcessor import 성공")
        
        from core.text_postprocessor import TextPostProcessor
        print("✅ TextPostProcessor import 성공")
        
        # Batch 모듈 import 테스트
        from batch.batch_processor import BatchProcessor
        print("✅ BatchProcessor import 성공")
        
        # Config 모듈 import 테스트
        from config.config_manager import ConfigManager
        print("✅ ConfigManager import 성공")
        
        # Web 모듈 import 테스트
        from web.app import app
        print("✅ Web app import 성공")
        
        print("\n🎉 모든 모듈이 성공적으로 import되었습니다!")
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("\n해결 방법:")
        print("1. 현재 디렉토리가 프로젝트 루트인지 확인")
        print("2. 모든 __init__.py 파일이 존재하는지 확인")
        print("3. requirements.txt의 의존성이 설치되었는지 확인")
        return False

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🧪 기본 기능 테스트 중...")
    
    try:
        from config.config_manager import ConfigManager
        
        # ConfigManager 테스트
        config = ConfigManager()
        print("✅ ConfigManager 초기화 성공")
        
        # 설정 검증 테스트
        errors = config.validate_config()
        if not errors:
            print("✅ 기본 설정 검증 성공")
        else:
            print(f"⚠️ 설정 검증 경고: {errors}")
        
        print("\n🎉 기본 기능 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 기능 테스트 오류: {e}")
        return False

def show_usage_examples():
    """사용법 예시 출력"""
    print("\n📚 사용법 예시:")
    print("=" * 50)
    
    print("\n1. 단일 PDF 처리:")
    print("   python pororo_ocr_cli.py single document.pdf")
    
    print("\n2. 웹 인터페이스:")
    print("   python pororo_ocr_cli.py web")
    print("   브라우저에서 http://localhost:5000 접속")
    
    print("\n3. 배치 처리:")
    print("   python pororo_ocr_cli.py batch pdf_folder/")
    
    print("\n4. 설정 파일 생성:")
    print("   python pororo_ocr_cli.py config create")
    
    print("\n5. 시스템 정보:")
    print("   python pororo_ocr_cli.py info")

def main():
    """메인 함수"""
    print("🚀 Pororo OCR PDF Parser - Import 테스트 및 예제")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📂 현재 디렉토리: {current_dir}")
    
    # Python 경로 확인
    print(f"🐍 Python 경로: {sys.executable}")
    print(f"📋 Python 버전: {sys.version}")
    
    # Import 테스트
    if not check_imports():
        print("\n❌ Import 오류로 인해 실행을 중단합니다.")
        return 1
    
    # 기본 기능 테스트
    if not test_basic_functionality():
        print("\n⚠️ 일부 기능에 문제가 있을 수 있습니다.")
    
    # 사용법 예시 출력
    show_usage_examples()
    
    print("\n✨ 테스트 완료! 이제 pororo_ocr_cli.py를 사용할 수 있습니다.")
    return 0

if __name__ == "__main__":
    exit(main())
