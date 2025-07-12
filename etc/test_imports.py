#!/usr/bin/env python3
"""
Import 테스트 스크립트
모든 모듈의 import 상태를 확인합니다.
"""

import sys
import traceback

def test_import(module_name, import_statement):
    """개별 모듈 import 테스트"""
    try:
        exec(import_statement)
        print(f"✅ {module_name}: 성공")
        return True
    except Exception as e:
        print(f"❌ {module_name}: {e}")
        print(f"   Import statement: {import_statement}")
        return False

def test_all_imports():
    """모든 모듈 import 테스트"""
    print("🔍 모듈 Import 테스트")
    print("=" * 50)
    
    imports_to_test = [
        # 기본 라이브러리
        ("yaml", "import yaml"),
        ("torch", "import torch"),
        ("cv2", "import cv2"),
        ("numpy", "import numpy"),
        ("PIL", "from PIL import Image"),
        ("flask", "import flask"),
        ("tqdm", "from tqdm import tqdm"),
        
        # 프로젝트 모듈
        ("config_manager", "from config.config_manager import ConfigManager"),
        ("ocr_engine", "from core.ocr_engine import OCREngine"),
        ("pdf_handler", "from core.pdf_handler import PDFHandler"),
        ("image_processor", "from core.image_processor import ImageProcessor"),
        ("text_postprocessor", "from core.text_postprocessor import TextPostProcessor"),
        ("batch_processor", "from batch.batch_processor import BatchProcessor"),
        ("web_app", "from web.app import app"),
    ]
    
    failed_imports = []
    
    for module_name, import_statement in imports_to_test:
        if not test_import(module_name, import_statement):
            failed_imports.append(module_name)
    
    print("\n" + "=" * 50)
    if failed_imports:
        print(f"❌ 실패한 모듈: {len(failed_imports)}개")
        print(f"   {', '.join(failed_imports)}")
        return False
    else:
        print("🎉 모든 모듈 import 성공!")
        return True

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🧪 기본 기능 테스트")
    print("=" * 30)
    
    try:
        from config.config_manager import ConfigManager
        
        # ConfigManager 초기화 테스트
        config = ConfigManager()
        print("✅ ConfigManager 초기화 성공")
        
        # 설정 검증 테스트
        errors = config.validate_config()
        if not errors:
            print("✅ 기본 설정 검증 성공")
        else:
            print(f"⚠️ 설정 검증 경고: {list(errors.keys())}")
        
        # 설정을 딕셔너리로 변환 테스트
        config_dict = config.to_dict()
        print(f"✅ 설정 변환 성공 ({len(config_dict)}개 섹션)")
        
        return True
        
    except Exception as e:
        print(f"❌ 기능 테스트 실패: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("🚀 Pororo OCR PDF Parser - Import 및 기능 테스트")
    print(f"🐍 Python 버전: {sys.version}")
    print(f"📂 작업 디렉토리: {sys.path[0]}")
    print()
    
    # Import 테스트
    import_success = test_all_imports()
    
    if import_success:
        # 기본 기능 테스트
        func_success = test_basic_functionality()
        
        if func_success:
            print("\n🎉 모든 테스트 통과!")
            print("\n다음 단계:")
            print("  python pororo_ocr_cli.py --help")
            return 0
        else:
            print("\n⚠️ 기능 테스트 실패")
            return 1
    else:
        print("\n❌ Import 테스트 실패")
        print("\n해결 방법:")
        print("1. pip install -r requirements.txt")
        print("2. python install.py")
        return 1

if __name__ == "__main__":
    exit(main())
