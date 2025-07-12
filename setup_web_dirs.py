#!/usr/bin/env python3
"""
웹 디렉토리 구조 생성 스크립트
필요한 폴더와 파일을 자동으로 생성합니다.
"""

import os
from pathlib import Path

def create_web_directories():
    """웹 애플리케이션에 필요한 디렉토리 구조 생성"""
    
    directories = [
        'web',
        'web/templates',
        'web/static',
        'web/static/css',
        'web/static/js',
        'web/static/images',
        'uploads',
        'static/results'
    ]
    
    print("🏗️ 웹 디렉토리 구조 생성 중...")
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 생성됨: {directory}/")
    
    # .gitkeep 파일 생성 (빈 디렉토리 유지용)
    gitkeep_dirs = ['uploads', 'static/results', 'web/static/images']
    
    for directory in gitkeep_dirs:
        gitkeep_path = Path(directory) / '.gitkeep'
        gitkeep_path.touch()
        print(f"📝 생성됨: {gitkeep_path}")

def create_missing_files():
    """누락된 필수 파일들 생성"""
    
    print("\n📄 누락된 파일 확인 중...")
    
    required_files = {
        'web/templates/index.html': '메인 페이지 템플릿',
        'web/templates/results.html': '결과 페이지 템플릿', 
        'web/templates/error.html': '에러 페이지 템플릿',
        'web/static/css/style.css': 'CSS 스타일 파일',
        'web/static/js/main.js': '메인 JavaScript 파일',
        'web/static/js/results.js': '결과 페이지 JavaScript'
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        if not Path(file_path).exists():
            missing_files.append((file_path, description))
    
    if missing_files:
        print("❌ 다음 파일들이 누락되었습니다:")
        for file_path, description in missing_files:
            print(f"   - {file_path} ({description})")
        print("\n이 파일들을 수동으로 생성하거나 artifacts에서 복사하세요.")
    else:
        print("✅ 모든 필수 파일이 존재합니다!")

def check_flask_templates():
    """Flask 템플릿 설정 확인"""
    
    print("\n🔍 Flask 설정 확인 중...")
    
    # web/app.py 파일에서 템플릿 폴더 설정 확인
    app_py_path = Path('web/app.py')
    
    if app_py_path.exists():
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'template_folder=' in content:
            print("✅ Flask 템플릿 폴더가 올바르게 설정됨")
        else:
            print("⚠️ Flask 템플릿 폴더 설정을 확인하세요")
            print("   Flask(__name__, template_folder='templates', static_folder='static')")
    else:
        print("❌ web/app.py 파일이 없습니다")

def generate_simple_templates():
    """간단한 기본 템플릿 생성 (누락된 경우)"""
    
    print("\n🛠️ 기본 템플릿 생성 중...")
    
    # 간단한 index.html
    index_path = Path('web/templates/index.html')
    if not index_path.exists():
        index_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pororo OCR PDF Parser</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">Pororo OCR PDF Parser</h1>
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">PDF 파일 업로드</h5>
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <input type="file" class="form-control" id="fileInput" name="file" accept=".pdf">
                            </div>
                            <button type="submit" class="btn btn-primary">업로드</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ 생성됨: {index_path}")
    
    # 간단한 CSS
    css_path = Path('web/static/css/style.css')
    if not css_path.exists():
        css_content = '''/* Pororo OCR PDF Parser Styles */
body {
    background-color: #f8f9fa;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border: none;
    border-radius: 10px;
}

.btn-primary {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    border: none;
    border-radius: 25px;
}
'''
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        print(f"✅ 생성됨: {css_path}")

def main():
    """메인 함수"""
    print("🚀 Pororo OCR PDF Parser - 웹 구조 설정")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📂 현재 디렉토리: {current_dir}")
    
    # 디렉토리 생성
    create_web_directories()
    
    # 파일 확인
    create_missing_files()
    
    # Flask 설정 확인
    check_flask_templates()
    
    # 기본 템플릿 생성 (누락된 경우)
    response = input("\n기본 템플릿을 생성하시겠습니까? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        generate_simple_templates()
    
    print("\n✨ 웹 구조 설정 완료!")
    print("\n다음 단계:")
    print("1. 모든 템플릿 파일이 생성되었는지 확인")
    print("2. python pororo_ocr_cli.py web 실행")
    print("3. http://localhost:5000 접속")
    
    return 0

if __name__ == "__main__":
    exit(main())
