#!/usr/bin/env python3
"""
빠른 OCR 테스트 스크립트
현재 문제를 즉시 확인합니다.
"""

import os
import sys

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pororo_direct():
    """Pororo를 직접 테스트"""
    print("🔍 Pororo OCR 직접 테스트")
    
    try:
        from pororo import Pororo
        ocr = Pororo(task="ocr", lang="ko", model="brainocr")
        
        # 최근 생성된 이미지 파일 찾기
        image_dirs = [
            "output/images",
            "static/results"
        ]
        
        test_image = None
        for img_dir in image_dirs:
            if os.path.exists(img_dir):
                for root, dirs, files in os.walk(img_dir):
                    for file in files:
                        if file.endswith('.png'):
                            test_image = os.path.join(root, file)
                            break
                    if test_image:
                        break
        
        if not test_image:
            print("❌ 테스트할 이미지를 찾을 수 없습니다.")
            return
        
        print(f"📸 테스트 이미지: {test_image}")
        
        # detail=False 테스트
        print("\n--- Simple OCR (detail=False) ---")
        result_simple = ocr(test_image, detail=False)
        print(f"타입: {type(result_simple)}")
        print(f"결과: {result_simple}")
        
        # detail=True 테스트
        print("\n--- Detailed OCR (detail=True) ---")
        result_detailed = ocr(test_image, detail=True)
        print(f"타입: {type(result_detailed)}")
        
        if isinstance(result_detailed, list):
            print(f"리스트 길이: {len(result_detailed)}")
            for i, item in enumerate(result_detailed):
                print(f"  항목 {i}: {type(item)} = {item}")
        else:
            print(f"결과: {result_detailed}")
        
        # 우리가 찾는 실제 텍스트 확인
        print("\n--- 텍스트 추출 테스트 ---")
        extracted_texts = []
        
        if isinstance(result_detailed, list):
            for item in result_detailed:
                if isinstance(item, str):
                    extracted_texts.append(item)
                elif isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str) and value.strip():
                            print(f"  {key}: '{value}'")
                            if key in ['text', 'description', 'word'] and value not in ['description', 'bounding_poly']:
                                extracted_texts.append(value)
        
        print(f"\n최종 추출된 텍스트: {extracted_texts}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def test_current_results():
    """현재 저장된 결과 확인"""
    print("\n📊 현재 결과 파일 확인")
    
    results_dir = "static/results"
    if not os.path.exists(results_dir):
        print("❌ 결과 디렉토리가 없습니다.")
        return
    
    # 가장 최근 job 폴더 찾기
    job_dirs = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
    
    if not job_dirs:
        print("❌ 처리된 작업이 없습니다.")
        return
    
    latest_job = sorted(job_dirs)[-1]
    job_path = os.path.join(results_dir, latest_job)
    
    print(f"📁 최근 작업: {latest_job}")
    
    # results.json 확인
    json_file = os.path.join(job_path, "results.json")
    if os.path.exists(json_file):
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"📄 JSON 결과 파일 존재")
        print(f"총 페이지: {len(results.get('pages', []))}")
        
        for i, page in enumerate(results.get('pages', [])):
            print(f"\n--- 페이지 {i+1} ---")
            print(f"text_regions: {page.get('text_regions', [])}")
            print(f"combined_text: '{page.get('combined_text', '')}'")
            print(f"text_count: {page.get('text_count', 0)}")
            
            if 'debug_raw_texts' in page:
                print(f"Raw OCR data: {page['debug_raw_texts'][:2]}...")
    else:
        print("❌ results.json 파일이 없습니다.")

if __name__ == "__main__":
    print("🚀 빠른 OCR 문제 진단")
    print("=" * 40)
    
    test_pororo_direct()
    test_current_results()
    
    print("\n💡 다음 단계:")
    print("1. 위 결과를 확인하여 OCR이 실제로 무엇을 반환하는지 파악")
    print("2. 웹 서버 재시작 후 새 PDF 업로드 테스트")
    print("3. 브라우저 개발자 도구에서 네트워크 탭 확인")
