#!/usr/bin/env python3
"""
텍스트 후처리 모듈
OCR 결과의 텍스트를 정제하고 구조화하는 기능 제공
"""

import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntity:
    """추출된 엔티티 정보"""
    text: str
    entity_type: str
    confidence: float
    position: Tuple[int, int]  # 시작, 끝 위치
    page_number: int

@dataclass
class TextStructure:
    """텍스트 구조 정보"""
    titles: List[str]
    paragraphs: List[str]
    lists: List[str]
    tables: List[List[str]]
    entities: List[ExtractedEntity]

class TextPostProcessor:
    """텍스트 후처리 클래스"""
    
    def __init__(self):
        """텍스트 후처리기 초기화"""
        self._initialize_patterns()
        self._initialize_corrections()
    
    def _initialize_patterns(self):
        """정규표현식 패턴 초기화"""
        # 언어 감지 패턴
        self.korean_pattern = re.compile(r'[가-힣]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        self.number_pattern = re.compile(r'\d+')
        
        # 엔티티 추출 패턴
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\d{2,3}[-\s]?)?\d{3,4}[-\s]?\d{4}'),
            'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'),
            'date_korean': re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일'),
            'date_numeric': re.compile(r'\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}'),
            'time': re.compile(r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?'),
            'currency': re.compile(r'[₩$¥€][\d,]+(?:\.\d{2})?|\d{1,3}(?:,\d{3})*원'),
            'postcode': re.compile(r'\d{5}(?:-\d{4})?'),
            'id_number': re.compile(r'\d{6}-[1-4]\d{6}'),
            'business_number': re.compile(r'\d{3}-\d{2}-\d{5}')
        }
        
        # 제목 감지 패턴
        self.title_patterns = [
            re.compile(r'^[A-Z\s]{3,30}$'),  # 모두 대문자
            re.compile(r'^제\s*\d+\s*[장절조항]'),  # 제1장, 제2절 등
            re.compile(r'^[가-힣\s]{2,20}$'),  # 한글 제목
            re.compile(r'^\d+\.\s*[가-힣A-Za-z]'),  # 번호가 있는 제목
        ]
        
        # 목록 패턴
        self.list_patterns = [
            re.compile(r'^[\-\*\•]\s+'),  # 불릿 포인트
            re.compile(r'^\d+[\.\)]\s+'),  # 번호 목록
            re.compile(r'^[가-힣]\.\s+'),  # 한글 목록 (가. 나. 다.)
            re.compile(r'^\([가-힣]\)\s+'),  # 괄호 한글 목록
        ]
    
    def _initialize_corrections(self):
        """OCR 오류 교정 규칙 초기화"""
        # 한글 자모와 영문자 혼동 교정
        self.char_corrections = {
            'ㅇ': 'o', 'ㅁ': 'm', 'ㅂ': 'b', 'ㅍ': 'p',
            'ㅌ': 't', 'ㅋ': 'k', 'ㅈ': 'j', 'ㅎ': 'h',
            'ㅗ': 'o', 'ㅏ': 'a', 'ㅓ': 'e', 'ㅜ': 'u', 'ㅣ': 'i',
            'O': '0', 'l': '1', 'I': '1', 'S': '5'
        }
        
        # 일반적인 단어 교정
        self.word_corrections = {
            '휴대폰': '휴대전화',
            '핸드폰': '휴대전화',
            'E-mail': '이메일',
            'e-mail': '이메일',
            'Tel': '전화',
            'Fax': '팩스',
        }
        
        # 불필요한 문자 패턴
        self.noise_patterns = [
            re.compile(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]'),  # 특수문자
            re.compile(r'(.)\1{4,}'),  # 연속된 같은 문자 (5개 이상)
            re.compile(r'[ㄱ-ㅎㅏ-ㅣ]'),  # 불완전한 한글 자모
        ]
    
    def clean_text(self, text: str) -> str:
        """
        기본 텍스트 정리
        
        Args:
            text: 입력 텍스트
            
        Returns:
            정리된 텍스트
        """
        if not text:
            return ""
        
        cleaned = text
        
        # 1. 불필요한 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # 2. 줄바꿈 정리
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        
        # 3. 노이즈 문자 제거
        for pattern in self.noise_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # 4. 문자 교정
        for wrong, correct in self.char_corrections.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # 5. 단어 교정
        for wrong, correct in self.word_corrections.items():
            cleaned = cleaned.replace(wrong, correct)
        
        return cleaned.strip()
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        텍스트 언어 감지
        
        Args:
            text: 입력 텍스트
            
        Returns:
            언어 감지 결과
        """
        if not text:
            return {'primary_language': 'unknown', 'confidence': 0.0}
        
        # 각 언어 문자 수 계산
        korean_chars = len(self.korean_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        number_chars = len(self.number_pattern.findall(text))
        
        total_chars = len(re.sub(r'\s', '', text))
        
        if total_chars == 0:
            return {'primary_language': 'unknown', 'confidence': 0.0}
        
        # 비율 계산
        korean_ratio = korean_chars / total_chars
        english_ratio = english_chars / total_chars
        number_ratio = number_chars / total_chars
        
        # 주 언어 결정
        if korean_ratio > 0.3:
            primary_lang = 'korean'
            confidence = korean_ratio
        elif english_ratio > 0.3:
            primary_lang = 'english'
            confidence = english_ratio
        else:
            primary_lang = 'mixed'
            confidence = max(korean_ratio, english_ratio)
        
        return {
            'primary_language': primary_lang,
            'confidence': confidence,
            'korean_ratio': korean_ratio,
            'english_ratio': english_ratio,
            'number_ratio': number_ratio
        }
    
    def extract_entities(self, text: str, page_number: int = 1) -> List[ExtractedEntity]:
        """
        텍스트에서 엔티티 추출
        
        Args:
            text: 입력 텍스트
            page_number: 페이지 번호
            
        Returns:
            추출된 엔티티 리스트
        """
        entities = []
        
        for entity_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entity = ExtractedEntity(
                    text=match.group(),
                    entity_type=entity_type,
                    confidence=1.0,  # 정규식 매칭은 신뢰도 1.0
                    position=(match.start(), match.end()),
                    page_number=page_number
                )
                entities.append(entity)
        
        return entities
    
    def detect_text_structure(self, text: str) -> TextStructure:
        """
        텍스트 구조 감지
        
        Args:
            text: 입력 텍스트
            
        Returns:
            감지된 텍스트 구조
        """
        lines = text.split('\n')
        
        titles = []
        paragraphs = []
        lists = []
        tables = []
        
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # 빈 줄 - 문단 구분
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                continue
            
            # 제목 감지
            is_title = False
            for title_pattern in self.title_patterns:
                if title_pattern.match(line):
                    titles.append(line)
                    is_title = True
                    break
            
            if is_title:
                continue
            
            # 목록 감지
            is_list = False
            for list_pattern in self.list_patterns:
                if list_pattern.match(line):
                    lists.append(line)
                    is_list = True
                    break
            
            if is_list:
                continue
            
            # 표 구조 감지 (탭이나 여러 공백으로 구분)
            if '\t' in line or re.search(r'\s{3,}', line):
                if '\t' in line:
                    columns = line.split('\t')
                else:
                    columns = re.split(r'\s{3,}', line)
                
                columns = [col.strip() for col in columns if col.strip()]
                if len(columns) > 1:
                    tables.append(columns)
                    continue
            
            # 일반 문단
            current_paragraph.append(line)
        
        # 마지막 문단 처리
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return TextStructure(
            titles=titles,
            paragraphs=paragraphs,
            lists=lists,
            tables=tables,
            entities=[]
        )
    
    def calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        텍스트 통계 계산
        
        Args:
            text: 입력 텍스트
            
        Returns:
            텍스트 통계 딕셔너리
        """
        if not text:
            return {
                'character_count': 0,
                'word_count': 0,
                'line_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0
            }
        
        # 기본 통계
        character_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # 문장 수 (한국어와 영어 문장 구분자 고려)
        sentence_endings = re.findall(r'[.!?።]', text)
        sentence_count = len(sentence_endings)
        
        # 문단 수 (빈 줄로 구분)
        paragraphs = re.split(r'\n\s*\n', text.strip())
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # 언어별 문자 수
        korean_chars = len(self.korean_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        number_chars = len(self.number_pattern.findall(text))
        
        # 평균 계산
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
        avg_chars_per_word = character_count / word_count if word_count > 0 else 0
        
        return {
            'character_count': character_count,
            'word_count': word_count,
            'line_count': line_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'korean_characters': korean_chars,
            'english_characters': english_chars,
            'number_characters': number_chars,
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_chars_per_word': round(avg_chars_per_word, 2)
        }
    
    def correct_common_errors(self, text: str) -> str:
        """
        일반적인 OCR 오류 교정
        
        Args:
            text: 입력 텍스트
            
        Returns:
            교정된 텍스트
        """
        corrected = text
        
        # 1. 연속된 같은 문자 제거 (OCR 오인식으로 인한)
        corrected = re.sub(r'(.)\1{3,}', r'\1', corrected)
        
        # 2. 불완전한 한글 자모 제거
        corrected = re.sub(r'[ㄱ-ㅎㅏ-ㅣ]', '', corrected)
        
        # 3. 잘못된 공백 교정
        corrected = re.sub(r'\s+([,.!?;:])', r'\1', corrected)  # 문장부호 앞 공백 제거
        corrected = re.sub(r'([,.!?;:])\s*([가-힣A-Za-z])', r'\1 \2', corrected)  # 문장부호 뒤 공백 추가
        
        # 4. 숫자와 단위 사이 공백 정리
        corrected = re.sub(r'(\d)\s+(원|달러|킬로|미터|센티|그램)', r'\1\2', corrected)
        
        # 5. 일반적인 오타 교정
        corrections = {
            '휴대폰': '휴대전화',
            '핸드폰': '휴대전화',
            'E-mail': '이메일',
            'e-mail': '이메일',
            'Tel': '전화',
            'Fax': '팩스',
            '웹사이트': '웹사이트',
            '홈페이지': '홈페이지'
        }
        
        for wrong, correct in corrections.items():
            corrected = corrected.replace(wrong, correct)
        
        return corrected
    
    def merge_text_regions(self, text_regions: List[str], merge_threshold: float = 0.8) -> List[str]:
        """
        유사한 텍스트 영역 병합
        
        Args:
            text_regions: 텍스트 영역 리스트
            merge_threshold: 병합 임계값
            
        Returns:
            병합된 텍스트 영역 리스트
        """
        if not text_regions:
            return []
        
        def similarity(text1: str, text2: str) -> float:
            """두 텍스트 간 유사도 계산"""
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 and not words2:
                return 1.0
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return intersection / union if union > 0 else 0.0
        
        merged = []
        used_indices = set()
        
        for i, region in enumerate(text_regions):
            if i in used_indices:
                continue
            
            current_group = [region]
            used_indices.add(i)
            
            for j, other_region in enumerate(text_regions[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if similarity(region, other_region) >= merge_threshold:
                    current_group.append(other_region)
                    used_indices.add(j)
            
            # 그룹 병합
            if len(current_group) == 1:
                merged.append(current_group[0])
            else:
                merged_text = ' '.join(current_group)
                merged.append(merged_text)
        
        return merged
    
    def process_page_text(self, page_text: str, page_number: int = 1) -> Dict[str, Any]:
        """
        페이지 텍스트 종합 처리
        
        Args:
            page_text: 페이지 텍스트
            page_number: 페이지 번호
            
        Returns:
            처리된 텍스트 정보
        """
        # 1. 기본 텍스트 정리
        cleaned_text = self.clean_text(page_text)
        
        # 2. OCR 오류 교정
        corrected_text = self.correct_common_errors(cleaned_text)
        
        # 3. 언어 감지
        language_info = self.detect_language(corrected_text)
        
        # 4. 텍스트 구조 감지
        structure = self.detect_text_structure(corrected_text)
        
        # 5. 엔티티 추출
        entities = self.extract_entities(corrected_text, page_number)
        structure.entities = entities
        
        # 6. 텍스트 통계 계산
        statistics = self.calculate_text_statistics(corrected_text)
        
        return {
            'page_number': page_number,
            'original_text': page_text,
            'cleaned_text': cleaned_text,
            'corrected_text': corrected_text,
            'language_info': language_info,
            'structure': asdict(structure),
            'statistics': statistics,
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0'
            }
        }
    
    def generate_document_summary(self, processed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        전체 문서 요약 생성
        
        Args:
            processed_pages: 처리된 페이지 리스트
            
        Returns:
            문서 요약 정보
        """
        if not processed_pages:
            return {}
        
        total_pages = len(processed_pages)
        
        # 전체 통계 합계
        total_stats = {
            'character_count': sum(page['statistics']['character_count'] for page in processed_pages),
            'word_count': sum(page['statistics']['word_count'] for page in processed_pages),
            'sentence_count': sum(page['statistics']['sentence_count'] for page in processed_pages),
            'paragraph_count': sum(page['statistics']['paragraph_count'] for page in processed_pages)
        }
        
        # 언어 분포
        languages = [page['language_info']['primary_language'] for page in processed_pages]
        language_distribution = dict(Counter(languages))
        
        # 모든 엔티티 수집
        all_entities = []
        for page in processed_pages:
            all_entities.extend(page['structure']['entities'])
        
        # 엔티티 유형별 통계
        entity_stats = {}
        for entity in all_entities:
            entity_type = entity['entity_type']
            if entity_type not in entity_stats:
                entity_stats[entity_type] = []
            entity_stats[entity_type].append(entity['text'])
        
        # 중복 제거
        unique_entities = {}
        for entity_type, entities in entity_stats.items():
            unique_entities[entity_type] = list(set(entities))
        
        # 모든 제목, 목록 수집
        all_titles = []
        all_lists = []
        all_tables = []
        
        for page in processed_pages:
            all_titles.extend(page['structure']['titles'])
            all_lists.extend(page['structure']['lists'])
            all_tables.extend(page['structure']['tables'])
        
        return {
            'document_summary': {
                'total_pages': total_pages,
                'total_characters': total_stats['character_count'],
                'total_words': total_stats['word_count'],
                'total_sentences': total_stats['sentence_count'],
                'total_paragraphs': total_stats['paragraph_count'],
                'average_chars_per_page': total_stats['character_count'] / total_pages,
                'average_words_per_page': total_stats['word_count'] / total_pages,
                'language_distribution': language_distribution,
                'generated_at': datetime.now().isoformat()
            },
            'content_overview': {
                'title_count': len(all_titles),
                'list_count': len(all_lists),
                'table_count': len(all_tables),
                'unique_titles': list(set(all_titles)),
                'entity_summary': {entity_type: len(entities) for entity_type, entities in unique_entities.items()}
            },
            'extracted_entities': unique_entities
        }
    
    def export_structured_data(self, processed_pages: List[Dict[str, Any]], format: str = 'json') -> str:
        """
        구조화된 데이터 내보내기
        
        Args:
            processed_pages: 처리된 페이지 리스트
            format: 출력 형식 (json, csv, txt)
            
        Returns:
            내보낸 데이터 문자열
        """
        if format == 'json':
            return json.dumps(processed_pages, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 헤더
            writer.writerow([
                'Page', 'Character Count', 'Word Count', 'Language',
                'Title Count', 'List Count', 'Entity Count', 'Text Preview'
            ])
            
            # 데이터
            for page in processed_pages:
                stats = page['statistics']
                structure = page['structure']
                preview = page['corrected_text'][:100] + '...' if len(page['corrected_text']) > 100 else page['corrected_text']
                
                writer.writerow([
                    page['page_number'],
                    stats['character_count'],
                    stats['word_count'],
                    page['language_info']['primary_language'],
                    len(structure['titles']),
                    len(structure['lists']),
                    len(structure['entities']),
                    preview.replace('\n', ' ')
                ])
            
            return output.getvalue()
        
        elif format == 'txt':
            lines = []
            lines.append("문서 처리 결과 요약")
            lines.append("=" * 50)
            lines.append(f"총 페이지 수: {len(processed_pages)}")
            lines.append("")
            
            for page in processed_pages:
                lines.append(f"페이지 {page['page_number']}")
                lines.append("-" * 20)
                lines.append(f"언어: {page['language_info']['primary_language']}")
                lines.append(f"글자 수: {page['statistics']['character_count']:,}")
                lines.append(f"단어 수: {page['statistics']['word_count']:,}")
                lines.append("")
                lines.append("텍스트:")
                lines.append(page['corrected_text'])
                lines.append("")
                lines.append("=" * 50)
                lines.append("")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# 사용 예제
if __name__ == "__main__":
    # 텍스트 후처리기 초기화
    processor = TextPostProcessor()
    
    # 샘플 텍스트
    sample_text = """
    회사 소개서
    
    ABC 주식회사는 2020년에 설립된 혁신적인 기술 회사입니다.
    
    연락처 정보:
    - 전화: 02-1234-5678
    - 이메일: info@abc.com
    - 웹사이트: https://www.abc.com
    
    설립일: 2020년 1월 15일
    주소: 서울시 강남구 테헤란로 123
    
    주요 사업 영역:
    1. 소프트웨어 개발
    2. 데이터 분석
    3. 컨설팅 서비스
    """
    
    # 페이지 텍스트 처리
    result = processor.process_page_text(sample_text, 1)
    
    # 결과 출력
    print("=== 처리 결과 ===")
    print(f"언어: {result['language_info']['primary_language']}")
    print(f"글자 수: {result['statistics']['character_count']}")
    print(f"단어 수: {result['statistics']['word_count']}")
    print(f"제목 수: {len(result['structure']['titles'])}")
    print(f"목록 수: {len(result['structure']['lists'])}")
    print(f"엔티티 수: {len(result['structure']['entities'])}")
    
    print("\n=== 추출된 엔티티 ===")
    for entity in result['structure']['entities']:
        print(f"{entity['entity_type']}: {entity['text']}")
    
    print("\n=== 정리된 텍스트 ===")
    print(result['corrected_text'])
