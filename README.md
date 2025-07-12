# Pororo OCR PDF Parser

🚀 **한국어 최적화 PDF OCR 솔루션**

Pororo OCR을 기반으로 한 고성능 PDF 문서 텍스트 추출 도구입니다. 한국어 문서에 특화된 OCR 엔진과 고급 이미지 전처리 기능을 제공하여 높은 정확도의 텍스트 추출을 실현합니다.

## ✨ 주요 특징

### 🎯 **핵심 기능**
- **한국어 최적화**: Pororo 엔진 기반 고정확도 한국어 텍스트 인식
- **이미지 전처리**: 노이즈 제거, 대비 향상, 기울기 보정으로 인식률 개선
- **텍스트 후처리**: 오타 교정, 엔티티 추출, 문서 구조 분석
- **배치 처리**: 대량의 PDF 파일 병렬 처리 지원
- **웹 인터페이스**: 직관적인 웹 UI로 쉬운 사용

### 📊 **지원 형식**
- **입력**: PDF 파일 (최대 16MB)
- **출력**: JSON, TXT, CSV 형식
- **이미지**: PNG, JPEG, TIFF 변환 지원

### 🔧 **고급 기능**
- 실시간 처리 상태 모니터링
- 엔티티 자동 추출 (이메일, 전화번호, 날짜, URL 등)
- 언어 분포 분석
- 문서 구조 감지 (제목, 문단, 목록, 표)
- 디버그 정보 제공

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/pororo-ocr-pdf-parser.git
cd pororo-ocr-pdf-parser

# 의존성 설치
pip install -r requirements.txt

# Pororo OCR 엔진 설치
pip install pororo
```

### 2. 사용법

#### 🖥️ **CLI 사용법**

```bash
# 단일 PDF 처리
python pororo_ocr_cli.py single document.pdf

# 고급 옵션으로 처리
python pororo_ocr_cli.py single document.pdf --dpi 400 --output-dir results

# 배치 처리 (여러 PDF 파일)
python pororo_ocr_cli.py batch pdf_folder/ --workers 4

# 웹 서버 실행
python pororo_ocr_cli.py web --port 8080
```

#### 🌐 **웹 인터페이스 사용법**

```bash
# 웹 서버 시작
python pororo_ocr_cli.py web

# 브라우저에서 접속
# http://localhost:5000
```

#### 🐍 **Python API 사용법**

```python
from core.pdf_handler import PDFHandler
from core.ocr_engine import OCREngine
from core.text_postprocessor import TextPostProcessor

# 컴포넌트 초기화
pdf_handler = PDFHandler()
ocr_engine = OCREngine()
text_processor = TextPostProcessor()

# PDF 처리
pdf_info = pdf_handler.extract_pdf_info("document.pdf")
image_paths = pdf_handler.convert_to_images("document.pdf", dpi=300)
ocr_results = ocr_engine.batch_extract(image_paths)

# 결과 후처리
for page_num, (image_path, regions) in enumerate(ocr_results.items(), 1):
    combined_text = '\n'.join([region['text'] for region in regions])
    processed = text_processor.process_page_text(combined_text, page_num)
    print(f"페이지 {page_num}: {len(regions)}개 텍스트 영역 추출")
```

## 📁 프로젝트 구조

```
pororo-ocr-pdf-parser/
├── core/                     # 핵심 처리 모듈
│   ├── pdf_handler.py       # PDF 처리 및 이미지 변환
│   ├── image_processor.py   # 이미지 전처리
│   ├── ocr_engine.py       # OCR 엔진 (Pororo 래퍼)
│   └── text_postprocessor.py # 텍스트 후처리
├── batch/                   # 배치 처리
│   └── batch_processor.py  # 대량 파일 처리
├── config/                  # 설정 관리
│   └── config_manager.py   # 설정 파일 관리
├── web/                     # 웹 인터페이스
│   ├── app.py              # Flask 웹 애플리케이션
│   ├── templates/          # HTML 템플릿
│   └── static/             # CSS, JS, 이미지
├── utils/                   # 유틸리티
│   └── image_util.py       # 이미지 처리 유틸
├── pororo_ocr_cli.py       # 통합 CLI 인터페이스
└── requirements.txt        # 의존성 목록
```

## ⚙️ 설정 옵션

### 📝 **설정 파일 생성**

```bash
# 기본 설정 파일 생성
python pororo_ocr_cli.py config create

# 프리셋 프로필 사용
python pororo_ocr_cli.py config create --profile accurate
```

### 🎛️ **주요 설정 항목**

```yaml
# config.yaml 예시
ocr:
  model: "brainocr"      # OCR 모델
  language: "ko"         # 언어 설정
  confidence_threshold: 0.8

pdf:
  dpi: 300              # 이미지 변환 해상도
  preprocessing: true    # 이미지 전처리 활성화
  keep_images: false    # 변환 이미지 보관 여부

image_processing:
  convert_grayscale: true
  enhance_contrast:
    method: "clahe"
    clip_limit: 3.0
  remove_noise:
    method: "bilateral"
    d: 9

text_processing:
  enable_postprocessing: true
  clean_text: true
  correct_errors: true
  extract_entities: true

batch:
  max_workers: 4        # 병렬 처리 워커 수
  save_individual_results: true
```

## 🔧 CLI 명령어 가이드

### 📄 **단일 파일 처리**
```bash
# 기본 처리
python pororo_ocr_cli.py single document.pdf

# 고해상도 처리
python pororo_ocr_cli.py single document.pdf --dpi 400

# 전처리 비활성화
python pororo_ocr_cli.py single document.pdf --no-preprocess

# 이미지 보관
python pororo_ocr_cli.py single document.pdf --keep-images
```

### 📚 **배치 처리**
```bash
# 기본 배치 처리
python pororo_ocr_cli.py batch pdf_folder/

# 멀티프로세싱 사용
python pororo_ocr_cli.py batch pdf_folder/ --multiprocessing

# 워커 수 조정
python pororo_ocr_cli.py batch pdf_folder/ --workers 8

# 드라이런 (실제 처리 없이 파일 목록만 확인)
python pororo_ocr_cli.py batch pdf_folder/ --dry-run
```

### 🌐 **웹 서버**
```bash
# 기본 실행
python pororo_ocr_cli.py web

# 포트 변경
python pororo_ocr_cli.py web --port 8080

# 외부 접속 허용
python pororo_ocr_cli.py web --host 0.0.0.0

# 디버그 모드
python pororo_ocr_cli.py web --debug
```

### ⚙️ **설정 관리**
```bash
# 설정 파일 생성
python pororo_ocr_cli.py config create

# 설정 검증
python pororo_ocr_cli.py config validate config.yaml

# 현재 설정 표시
python pororo_ocr_cli.py config show

# 프리셋 프로필 생성
python pororo_ocr_cli.py config create --profile fast
```

### ℹ️ **시스템 정보**
```bash
# 시스템 정보 확인
python pororo_ocr_cli.py info

# PDF 파일 정보 확인
python pororo_ocr_cli.py info --pdf document.pdf
```

## 📊 성능 최적화

### 🚀 **처리 속도 향상**
```bash
# 빠른 처리 (정확도 다소 감소)
python pororo_ocr_cli.py single document.pdf --dpi 200 --no-preprocess

# 배치 처리 최적화
python pororo_ocr_cli.py batch folder/ --workers 8 --multiprocessing
```

### 🎯 **정확도 향상**
```bash
# 고정확도 처리 (처리 시간 증가)
python pororo_ocr_cli.py single document.pdf --dpi 400 --config accurate_config.yaml
```

### 💾 **메모리 사용량 조절**
```yaml
# config.yaml에서 설정
performance:
  memory_limit: "4GB"
  batch_size: 4
```

## 🐛 문제 해결

### ❗ **일반적인 문제들**

#### 1. **Pororo 설치 실패**
```bash
# conda 환경에서 설치 (권장)
conda create -n pororo-ocr python=3.8
conda activate pororo-ocr
pip install pororo
```

#### 2. **CUDA 지원 문제**
```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 지원 확인
python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. **메모리 부족 오류**
```bash
# 배치 크기 조정
python pororo_ocr_cli.py single document.pdf --config low_memory_config.yaml
```

#### 4. **텍스트 추출 실패**
- DPI 설정을 높여보세요 (400-600)
- 이미지 전처리를 활성화하세요
- 원본 PDF 품질을 확인하세요

### 🔍 **디버그 정보 확인**
```bash
# 디버그 모드로 실행
python pororo_ocr_cli.py single document.pdf --log-level DEBUG

# 시스템 정보 확인
python pororo_ocr_cli.py info
```

## 📈 출력 형식

### 📄 **JSON 출력 예시**
```json
{
  "pdf_info": {
    "file_name": "document.pdf",
    "page_count": 5,
    "file_size": 2048576
  },
  "pages": [
    {
      "page_number": 1,
      "text_regions": ["첫 번째 텍스트", "두 번째 텍스트"],
      "combined_text": "첫 번째 텍스트\n두 번째 텍스트",
      "text_count": 2
    }
  ],
  "processing_summary": {
    "total_pages": 5,
    "successful_pages": 4,
    "success_rate": 80.0,
    "total_characters": 15420
  }
}
```

### 📝 **TXT 출력 예시**
```
OCR 처리 결과
처리 시간: 2024-01-15T10:30:00
성공률: 95.2%
==================================================

페이지 1
--------------------
여기에 추출된 텍스트가 표시됩니다.
첫 번째 문단입니다.

두 번째 문단입니다.

페이지 2
--------------------
두 번째 페이지의 내용입니다.
```

## 🚀 고급 사용법

### 🔄 **배치 처리 워크플로우**
```bash
# 1. 파일 확인
python pororo_ocr_cli.py batch input_folder/ --dry-run

# 2. 실제 처리
python pororo_ocr_cli.py batch input_folder/ --workers 4 --output-dir results/

# 3. 결과 확인
ls results/reports/
```

### 📊 **결과 분석**
```python
import json
import pandas as pd

# JSON 결과 로드
with open('results/reports/batch_summary_20240115_103000.json', 'r') as f:
    results = json.load(f)

# 성공률 분석
success_rate = results['batch_info']['success_rate']
print(f"전체 성공률: {success_rate}%")

# CSV로 상세 분석
df = pd.read_csv('results/reports/batch_details_20240115_103000.csv')
print(df.describe())
```

### 🛠️ **커스텀 전처리 파이프라인**
```python
from core.image_processor import ImageProcessor

processor = ImageProcessor()

# 커스텀 전처리 설정
custom_config = {
    'enhance_contrast': {'method': 'clahe', 'clip_limit': 2.0},
    'remove_noise': {'method': 'bilateral', 'd': 7},
    'apply_threshold': {'threshold_type': 'adaptive', 'block_size': 15},
    'correct_skew': True
}

# 이미지 전처리 적용
processed_path = processor.preprocess_for_ocr('input.png', config=custom_config)
```

## 🙏 감사의 말

- [Pororo](https://github.com/kakaobrain/pororo) - 카카오브레인의 오픈소스 NLP 라이브러리
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF 처리 라이브러리
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리
