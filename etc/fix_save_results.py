#!/usr/bin/env python3
"""
web/app.py의 _save_results 함수 수정
KeyError: 'extraction_success' 문제 해결
"""

def _save_results(self, results: Dict[str, Any], output_dir: Path):
    """결과 파일 저장 - 수정된 버전"""
    try:
        # JSON 결과 저장
        json_path = output_dir / 'results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 텍스트 결과 저장
        txt_path = output_dir / 'extracted_text.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"OCR 처리 결과\n")
            f.write(f"처리 시간: {results['processed_at']}\n")
            f.write("=" * 50 + "\n\n")

            for page in results['pages']:
                f.write(f"페이지 {page['page_number']}\n")
                f.write("-" * 20 + "\n")
                
                # 🔥 수정된 부분: has_text 키 사용 (extraction_success 대신)
                if page.get('has_text', False) or page.get('combined_text', '').strip():
                    f.write(page.get('combined_text', '텍스트 없음'))
                else:
                    f.write("이 페이지에서는 텍스트를 찾을 수 없습니다.")
                f.write("\n\n")

        logger.info(f"✅ 결과 저장 완료: {json_path}, {txt_path}")

    except Exception as e:
        logger.error(f"❌ 결과 저장 실패: {str(e)}")
        raise


# 완전한 수정된 _save_results 함수 (web/app.py 교체용)
def _save_results_complete(self, results: Dict[str, Any], output_dir: Path):
    """결과 파일 저장 - 완전 수정 버전"""
    try:
        # 1. JSON 결과 저장
        json_path = output_dir / 'results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON 결과 저장: {json_path}")

        # 2. 텍스트 결과 저장
        txt_path = output_dir / 'extracted_text.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"OCR 처리 결과\n")
            f.write(f"처리 시간: {results.get('processed_at', 'Unknown')}\n")
            f.write(f"성공률: {results.get('processing_summary', {}).get('success_rate', 0):.1f}%\n")
            f.write("=" * 50 + "\n\n")

            for page in results.get('pages', []):
                page_number = page.get('page_number', 'Unknown')
                f.write(f"페이지 {page_number}\n")
                f.write("-" * 20 + "\n")
                
                # 안전한 텍스트 추출
                combined_text = page.get('combined_text', '')
                has_text = page.get('has_text', False)
                text_count = page.get('text_count', 0)
                
                if has_text or combined_text.strip():
                    f.write(f"텍스트 영역 수: {text_count}\n")
                    f.write(f"글자 수: {page.get('character_count', len(combined_text))}\n\n")
                    f.write(combined_text if combined_text.strip() else "텍스트 없음")
                else:
                    f.write("이 페이지에서는 텍스트를 찾을 수 없습니다.")
                
                f.write("\n\n")

        logger.info(f"텍스트 결과 저장: {txt_path}")

        # 3. CSV 요약 저장 (처리 요약이 있는 경우)
        if 'processing_summary' in results:
            csv_path = output_dir / 'summary.csv'
            try:
                import csv
                with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    
                    # 헤더
                    writer.writerow([
                        '페이지', '텍스트_영역_수', '글자_수', '텍스트_있음', '텍스트_미리보기'
                    ])
                    
                    # 데이터
                    for page in results.get('pages', []):
                        preview = page.get('combined_text', '')[:100].replace('\n', ' ')
                        if len(preview) > 97:
                            preview += '...'
                        
                        writer.writerow([
                            page.get('page_number', 0),
                            page.get('text_count', 0),
                            page.get('character_count', 0),
                            'Y' if page.get('has_text', False) else 'N',
                            preview
                        ])
                
                logger.info(f"CSV 요약 저장: {csv_path}")
                
            except Exception as e:
                logger.warning(f"CSV 저장 실패: {str(e)}")

        logger.info(f"✅ 모든 결과 저장 완료: {output_dir}")

    except Exception as e:
        logger.error(f"❌ 결과 저장 실패: {str(e)}")
        logger.error(traceback.format_exc())
        raise


# 빠른 수정을 위한 패치 스크립트
def patch_web_app():
    """web/app.py 파일의 _save_results 함수만 빠르게 수정"""
    import re
    
    web_app_file = "web/app.py"
    
    try:
        # 파일 읽기
        with open(web_app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # _save_results 함수 찾아서 교체
        # 기존 함수 패턴 찾기
        old_pattern = r"def _save_results\(self, results: Dict\[str, Any\], output_dir: Path\):.*?(?=\n    def|\nclass|\Z)"
        
        new_function = '''def _save_results(self, results: Dict[str, Any], output_dir: Path):
        """결과 파일 저장 - 수정된 버전"""
        try:
            # JSON 결과 저장
            json_path = output_dir / 'results.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            # 텍스트 결과 저장
            txt_path = output_dir / 'extracted_text.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"OCR 처리 결과\\n")
                f.write(f"처리 시간: {results.get('processed_at', 'Unknown')}\\n")
                f.write("=" * 50 + "\\n\\n")

                for page in results.get('pages', []):
                    f.write(f"페이지 {page.get('page_number', 'Unknown')}\\n")
                    f.write("-" * 20 + "\\n")
                    
                    # 안전한 텍스트 추출 - has_text 키 사용
                    combined_text = page.get('combined_text', '')
                    has_text = page.get('has_text', False)
                    
                    if has_text or combined_text.strip():
                        f.write(combined_text if combined_text.strip() else "텍스트 없음")
                    else:
                        f.write("이 페이지에서는 텍스트를 찾을 수 없습니다.")
                    f.write("\\n\\n")

            logger.info(f"✅ 결과 저장 완료: {json_path}, {txt_path}")

        except Exception as e:
            logger.error(f"❌ 결과 저장 실패: {str(e)}")
            raise'''
        
        # 정규식으로 교체
        new_content = re.sub(old_pattern, new_function, content, flags=re.DOTALL)
        
        if new_content != content:
            # 백업 생성
            backup_file = f"{web_app_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 수정된 내용 저장
            with open(web_app_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ {web_app_file} _save_results 함수 수정 완료")
            print(f"📁 백업 파일: {backup_file}")
            return True
        else:
            print(f"⚠️ {web_app_file}에서 _save_results 함수를 찾지 못했습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 파일 수정 실패: {str(e)}")
        return False


if __name__ == "__main__":
    import traceback
    from datetime import datetime
    
    print("🔧 _save_results 함수 KeyError 수정")
    print("=" * 50)
    
    success = patch_web_app()
    
    if success:
        print("\n✅ 수정 완료! 웹 서버를 재시작하세요.")
        print("\n재시작 방법:")
        print("  1. Ctrl+C로 현재 서버 중지")
        print("  2. python pororo_ocr_cli.py web --debug")
    else:
        print("\n❌ 자동 수정 실패. 수동으로 수정하세요.")
        print("\nweb/app.py 파일에서 _save_results 함수의")
        print("'extraction_success' 부분을 'has_text'로 변경하세요.")
