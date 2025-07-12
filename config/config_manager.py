#!/usr/bin/env python3
"""
설정 관리 모듈
애플리케이션의 다양한 설정을 관리하는 기능 제공
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OCRConfig:
    """OCR 엔진 설정"""
    model: str = "brainocr"
    language: str = "ko"
    confidence_threshold: float = 0.8
    detail_output: bool = True


@dataclass
class PDFConfig:
    """PDF 처리 설정"""
    dpi: int = 300
    image_format: str = "PNG"
    preprocessing: bool = True
    keep_images: bool = False
    optimize_pdf: bool = False


@dataclass
class ImageProcessingConfig:
    """이미지 전처리 설정"""
    convert_grayscale: bool = True
    enhance_contrast: Dict[str, Any] = None
    remove_noise: Dict[str, Any] = None
    apply_threshold: Dict[str, Any] = None
    morphology: Dict[str, Any] = None
    correct_skew: bool = True
    resize: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.enhance_contrast is None:
            self.enhance_contrast = {
                'method': 'clahe',
                'clip_limit': 3.0,
                'tile_grid_size': (8, 8)
            }

        if self.remove_noise is None:
            self.remove_noise = {
                'method': 'bilateral',
                'd': 9,
                'sigma_color': 75,
                'sigma_space': 75
            }

        if self.apply_threshold is None:
            self.apply_threshold = {
                'threshold_type': 'adaptive',
                'max_value': 255,
                'adaptive_method': 'ADAPTIVE_THRESH_GAUSSIAN_C',
                'threshold_type_cv': 'THRESH_BINARY',
                'block_size': 11,
                'c_constant': 2
            }

        if self.morphology is None:
            self.morphology = {
                'operation': 'opening',
                'kernel_size': (2, 2)
            }


@dataclass
class TextProcessingConfig:
    """텍스트 후처리 설정"""
    enable_postprocessing: bool = True
    clean_text: bool = True
    correct_errors: bool = True
    extract_entities: bool = True
    detect_structure: bool = True
    merge_threshold: float = 0.8


@dataclass
class OutputConfig:
    """출력 설정"""
    directory: str = "output"
    formats: list = None
    filename_format: str = "{pdf_name}_{timestamp}"
    json_indent: int = 2
    ensure_ascii: bool = False
    include_metadata: bool = True

    def __post_init__(self):
        if self.formats is None:
            self.formats = ["json", "txt"]


@dataclass
class BatchConfig:
    """배치 처리 설정"""
    max_workers: int = 4
    chunk_size: int = 10
    progress_bar: bool = True
    save_individual_results: bool = True
    generate_summary: bool = True
    cleanup_temp_files: bool = True


@dataclass
class PerformanceConfig:
    """성능 설정"""
    use_gpu: bool = False
    batch_size: int = 8
    memory_limit: str = "8GB"
    timeout_seconds: int = 300
    retry_attempts: int = 3


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True
    max_file_size: str = "10MB"
    backup_count: int = 5


@dataclass
class WebConfig:
    """웹 애플리케이션 설정"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    upload_folder: str = "uploads"
    result_folder: str = "static/results"
    session_timeout: int = 1800  # 30분


class ConfigManager:
    """설정 관리 클래스"""

    def __init__(self, config_path: Optional[str] = None):
        """
        설정 관리자 초기화

        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path
        self.config_data = {}

        # 기본 설정 초기화
        self._initialize_default_configs()

        # 설정 파일 로드
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)

    def _initialize_default_configs(self):
        """기본 설정 초기화"""
        self.ocr_config = OCRConfig()
        self.pdf_config = PDFConfig()
        self.image_config = ImageProcessingConfig()
        self.text_config = TextProcessingConfig()
        self.output_config = OutputConfig()
        self.batch_config = BatchConfig()
        self.performance_config = PerformanceConfig()
        self.logging_config = LoggingConfig()
        self.web_config = WebConfig()

    def load_config(self, config_path: str) -> bool:
        """
        설정 파일 로드

        Args:
            config_path: 설정 파일 경로

        Returns:
            로드 성공 여부
        """
        try:
            file_ext = Path(config_path).suffix.lower()

            with open(config_path, 'r', encoding='utf-8') as f:
                if file_ext in ['.yaml', '.yml']:
                    self.config_data = yaml.safe_load(f)
                elif file_ext == '.json':
                    self.config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {file_ext}")

            # 설정 적용
            self._apply_config()

            logger.info(f"Configuration loaded from {config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {str(e)}")
            return False

    def _apply_config(self):
        """로드된 설정을 적용"""
        # OCR 설정
        if 'ocr' in self.config_data:
            ocr_data = self.config_data['ocr']
            self.ocr_config = OCRConfig(
                model=ocr_data.get('model', self.ocr_config.model),
                language=ocr_data.get('language', self.ocr_config.language),
                confidence_threshold=ocr_data.get('confidence_threshold', self.ocr_config.confidence_threshold),
                detail_output=ocr_data.get('detail_output', self.ocr_config.detail_output)
            )

        # PDF 설정
        if 'pdf' in self.config_data:
            pdf_data = self.config_data['pdf']
            self.pdf_config = PDFConfig(
                dpi=pdf_data.get('dpi', self.pdf_config.dpi),
                image_format=pdf_data.get('image_format', self.pdf_config.image_format),
                preprocessing=pdf_data.get('preprocessing', self.pdf_config.preprocessing),
                keep_images=pdf_data.get('keep_images', self.pdf_config.keep_images),
                optimize_pdf=pdf_data.get('optimize_pdf', self.pdf_config.optimize_pdf)
            )

        # 이미지 처리 설정
        if 'image_processing' in self.config_data:
            img_data = self.config_data['image_processing']
            self.image_config = ImageProcessingConfig(
                convert_grayscale=img_data.get('convert_grayscale', self.image_config.convert_grayscale),
                enhance_contrast=img_data.get('enhance_contrast', self.image_config.enhance_contrast),
                remove_noise=img_data.get('remove_noise', self.image_config.remove_noise),
                apply_threshold=img_data.get('apply_threshold', self.image_config.apply_threshold),
                morphology=img_data.get('morphology', self.image_config.morphology),
                correct_skew=img_data.get('correct_skew', self.image_config.correct_skew),
                resize=img_data.get('resize', self.image_config.resize)
            )

        # 텍스트 처리 설정
        if 'text_processing' in self.config_data:
            text_data = self.config_data['text_processing']
            self.text_config = TextProcessingConfig(
                enable_postprocessing=text_data.get('enable_postprocessing', self.text_config.enable_postprocessing),
                clean_text=text_data.get('clean_text', self.text_config.clean_text),
                correct_errors=text_data.get('correct_errors', self.text_config.correct_errors),
                extract_entities=text_data.get('extract_entities', self.text_config.extract_entities),
                detect_structure=text_data.get('detect_structure', self.text_config.detect_structure),
                merge_threshold=text_data.get('merge_threshold', self.text_config.merge_threshold)
            )

        # 출력 설정
        if 'output' in self.config_data:
            output_data = self.config_data['output']
            self.output_config = OutputConfig(
                directory=output_data.get('directory', self.output_config.directory),
                formats=output_data.get('formats', self.output_config.formats),
                filename_format=output_data.get('filename_format', self.output_config.filename_format),
                json_indent=output_data.get('json_indent', self.output_config.json_indent),
                ensure_ascii=output_data.get('ensure_ascii', self.output_config.ensure_ascii),
                include_metadata=output_data.get('include_metadata', self.output_config.include_metadata)
            )

        # 배치 설정
        if 'batch' in self.config_data:
            batch_data = self.config_data['batch']
            self.batch_config = BatchConfig(
                max_workers=batch_data.get('max_workers', self.batch_config.max_workers),
                chunk_size=batch_data.get('chunk_size', self.batch_config.chunk_size),
                progress_bar=batch_data.get('progress_bar', self.batch_config.progress_bar),
                save_individual_results=batch_data.get('save_individual_results',
                                                       self.batch_config.save_individual_results),
                generate_summary=batch_data.get('generate_summary', self.batch_config.generate_summary),
                cleanup_temp_files=batch_data.get('cleanup_temp_files', self.batch_config.cleanup_temp_files)
            )

        # 성능 설정
        if 'performance' in self.config_data:
            perf_data = self.config_data['performance']
            self.performance_config = PerformanceConfig(
                use_gpu=perf_data.get('use_gpu', self.performance_config.use_gpu),
                batch_size=perf_data.get('batch_size', self.performance_config.batch_size),
                memory_limit=perf_data.get('memory_limit', self.performance_config.memory_limit),
                timeout_seconds=perf_data.get('timeout_seconds', self.performance_config.timeout_seconds),
                retry_attempts=perf_data.get('retry_attempts', self.performance_config.retry_attempts)
            )

        # 로깅 설정
        if 'logging' in self.config_data:
            log_data = self.config_data['logging']
            self.logging_config = LoggingConfig(
                level=log_data.get('level', self.logging_config.level),
                format=log_data.get('format', self.logging_config.format),
                file=log_data.get('file', self.logging_config.file),
                console=log_data.get('console', self.logging_config.console),
                max_file_size=log_data.get('max_file_size', self.logging_config.max_file_size),
                backup_count=log_data.get('backup_count', self.logging_config.backup_count)
            )

        # 웹 설정
        if 'web' in self.config_data:
            web_data = self.config_data['web']
            self.web_config = WebConfig(
                host=web_data.get('host', self.web_config.host),
                port=web_data.get('port', self.web_config.port),
                debug=web_data.get('debug', self.web_config.debug),
                max_content_length=web_data.get('max_content_length', self.web_config.max_content_length),
                upload_folder=web_data.get('upload_folder', self.web_config.upload_folder),
                result_folder=web_data.get('result_folder', self.web_config.result_folder),
                session_timeout=web_data.get('session_timeout', self.web_config.session_timeout)
            )

    def save_config(self, output_path: str, format: str = 'yaml') -> bool:
        """
        현재 설정을 파일로 저장

        Args:
            output_path: 출력 파일 경로
            format: 파일 형식 (yaml, json)

        Returns:
            저장 성공 여부
        """
        try:
            config_dict = self.to_dict()

            # 메타데이터 추가
            config_dict['_metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'description': 'Pororo OCR PDF Parser Configuration'
            }

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif format.lower() == 'json':
                    json.dump(config_dict, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Configuration saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config to {output_path}: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'ocr': asdict(self.ocr_config),
            'pdf': asdict(self.pdf_config),
            'image_processing': asdict(self.image_config),
            'text_processing': asdict(self.text_config),
            'output': asdict(self.output_config),
            'batch': asdict(self.batch_config),
            'performance': asdict(self.performance_config),
            'logging': asdict(self.logging_config),
            'web': asdict(self.web_config)
        }

    def get_processing_config(self) -> Dict[str, Any]:
        """처리용 설정 딕셔너리 반환"""
        return {
            'dpi': self.pdf_config.dpi,
            'preprocess': self.pdf_config.preprocessing,
            'preprocess_config': asdict(self.image_config),
            'postprocess': self.text_config.enable_postprocessing,
            'postprocess_config': asdict(self.text_config),
            'keep_images': self.pdf_config.keep_images,
            'output_formats': self.output_config.formats
        }

    def update_config(self, section: str, **kwargs):
        """
        설정 업데이트

        Args:
            section: 설정 섹션명
            **kwargs: 업데이트할 설정값들
        """
        if section == 'ocr':
            for key, value in kwargs.items():
                if hasattr(self.ocr_config, key):
                    setattr(self.ocr_config, key, value)
        elif section == 'pdf':
            for key, value in kwargs.items():
                if hasattr(self.pdf_config, key):
                    setattr(self.pdf_config, key, value)
        elif section == 'image_processing':
            for key, value in kwargs.items():
                if hasattr(self.image_config, key):
                    setattr(self.image_config, key, value)
        elif section == 'text_processing':
            for key, value in kwargs.items():
                if hasattr(self.text_config, key):
                    setattr(self.text_config, key, value)
        elif section == 'output':
            for key, value in kwargs.items():
                if hasattr(self.output_config, key):
                    setattr(self.output_config, key, value)
        elif section == 'batch':
            for key, value in kwargs.items():
                if hasattr(self.batch_config, key):
                    setattr(self.batch_config, key, value)
        elif section == 'performance':
            for key, value in kwargs.items():
                if hasattr(self.performance_config, key):
                    setattr(self.performance_config, key, value)
        elif section == 'logging':
            for key, value in kwargs.items():
                if hasattr(self.logging_config, key):
                    setattr(self.logging_config, key, value)
        elif section == 'web':
            for key, value in kwargs.items():
                if hasattr(self.web_config, key):
                    setattr(self.web_config, key, value)
        else:
            raise ValueError(f"Unknown config section: {section}")

    def validate_config(self) -> Dict[str, List[str]]:
        """
        설정 유효성 검사

        Returns:
            섹션별 오류 메시지 딕셔너리
        """
        errors = {}

        # OCR 설정 검사
        ocr_errors = []
        if self.ocr_config.confidence_threshold < 0 or self.ocr_config.confidence_threshold > 1:
            ocr_errors.append("confidence_threshold must be between 0 and 1")
        if ocr_errors:
            errors['ocr'] = ocr_errors

        # PDF 설정 검사
        pdf_errors = []
        if self.pdf_config.dpi < 72 or self.pdf_config.dpi > 1200:
            pdf_errors.append("dpi should be between 72 and 1200")
        if self.pdf_config.image_format not in ['PNG', 'JPEG', 'TIFF']:
            pdf_errors.append("image_format must be PNG, JPEG, or TIFF")
        if pdf_errors:
            errors['pdf'] = pdf_errors

        # 이미지 처리 설정 검사
        img_errors = []
        if 'clip_limit' in self.image_config.enhance_contrast:
            if self.image_config.enhance_contrast['clip_limit'] <= 0:
                img_errors.append("enhance_contrast.clip_limit must be positive")
        if img_errors:
            errors['image_processing'] = img_errors

        # 텍스트 처리 설정 검사
        text_errors = []
        if self.text_config.merge_threshold < 0 or self.text_config.merge_threshold > 1:
            text_errors.append("merge_threshold must be between 0 and 1")
        if text_errors:
            errors['text_processing'] = text_errors

        # 배치 설정 검사
        batch_errors = []
        if self.batch_config.max_workers < 1:
            batch_errors.append("max_workers must be at least 1")
        if self.batch_config.chunk_size < 1:
            batch_errors.append("chunk_size must be at least 1")
        if batch_errors:
            errors['batch'] = batch_errors

        # 성능 설정 검사
        perf_errors = []
        if self.performance_config.batch_size < 1:
            perf_errors.append("batch_size must be at least 1")
        if self.performance_config.timeout_seconds < 1:
            perf_errors.append("timeout_seconds must be at least 1")
        if perf_errors:
            errors['performance'] = perf_errors

        # 웹 설정 검사
        web_errors = []
        if self.web_config.port < 1 or self.web_config.port > 65535:
            web_errors.append("port must be between 1 and 65535")
        if self.web_config.max_content_length < 1024:
            web_errors.append("max_content_length should be at least 1024 bytes")
        if web_errors:
            errors['web'] = web_errors

        return errors

    def setup_logging(self):
        """로깅 설정 적용"""
        log_level = getattr(logging, self.logging_config.level.upper())

        # 기본 핸들러 제거
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 포맷터 생성
        formatter = logging.Formatter(self.logging_config.format)

        # 콘솔 핸들러
        if self.logging_config.console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # 파일 핸들러
        if self.logging_config.file:
            try:
                from logging.handlers import RotatingFileHandler

                # 파일 크기를 바이트로 변환
                max_bytes = self._parse_size(self.logging_config.max_file_size)

                file_handler = RotatingFileHandler(
                    self.logging_config.file,
                    maxBytes=max_bytes,
                    backupCount=self.logging_config.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                logger.error(f"Failed to setup file logging: {str(e)}")

        root_logger.setLevel(log_level)

    def _parse_size(self, size_str: str) -> int:
        """크기 문자열을 바이트로 변환"""
        size_str = size_str.upper()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }

        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-len(suffix)]) * multiplier)

        # 숫자만 있는 경우 바이트로 간주
        return int(size_str)

    def create_profile(self, profile_name: str, **overrides) -> 'ConfigManager':
        """
        설정 프로필 생성

        Args:
            profile_name: 프로필 이름
            **overrides: 재정의할 설정값들

        Returns:
            새로운 ConfigManager 인스턴스
        """
        # 현재 설정 복사
        profile_config = ConfigManager()
        profile_config.ocr_config = self.ocr_config
        profile_config.pdf_config = self.pdf_config
        profile_config.image_config = self.image_config
        profile_config.text_config = self.text_config
        profile_config.output_config = self.output_config
        profile_config.batch_config = self.batch_config
        profile_config.performance_config = self.performance_config
        profile_config.logging_config = self.logging_config
        profile_config.web_config = self.web_config

        # 재정의 적용
        for section_key, section_overrides in overrides.items():
            if isinstance(section_overrides, dict):
                profile_config.update_config(section_key, **section_overrides)

        return profile_config

    def get_profile_presets(self) -> Dict[str, Dict[str, Any]]:
        """미리 정의된 프로필 반환"""
        return {
            'fast': {
                'pdf': {'dpi': 200, 'preprocessing': False},
                'text_processing': {'enable_postprocessing': False},
                'performance': {'batch_size': 16}
            },
            'accurate': {
                'pdf': {'dpi': 400, 'preprocessing': True},
                'image_processing': {'enhance_contrast': {'method': 'clahe', 'clip_limit': 2.0}},
                'text_processing': {'enable_postprocessing': True},
                'performance': {'batch_size': 4}
            },
            'balanced': {
                'pdf': {'dpi': 300, 'preprocessing': True},
                'text_processing': {'enable_postprocessing': True},
                'performance': {'batch_size': 8}
            },
            'batch_optimized': {
                'batch': {'max_workers': 8, 'save_individual_results': False},
                'pdf': {'keep_images': False},
                'performance': {'batch_size': 12}
            }
        }


def create_default_config_file(output_path: str = "config.yaml"):
    """기본 설정 파일 생성"""
    config_manager = ConfigManager()

    success = config_manager.save_config(output_path, 'yaml')
    if success:
        print(f"Default configuration file created: {output_path}")
    else:
        print(f"Failed to create configuration file: {output_path}")

    return success


# 사용 예제
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Pororo OCR Configuration Manager')
    parser.add_argument('--create-default', action='store_true', help='Create default config file')
    parser.add_argument('--config', help='Config file path to load and validate')
    parser.add_argument('--output', default='config.yaml', help='Output config file path')
    parser.add_argument('--profile', choices=['fast', 'accurate', 'balanced', 'batch_optimized'],
                        help='Create config with predefined profile')

    args = parser.parse_args()

    if args.create_default:
        create_default_config_file(args.output)

    elif args.config:
        # 설정 파일 로드 및 검증
        config_manager = ConfigManager(args.config)

        # 유효성 검사
        errors = config_manager.validate_config()
        if errors:
            print("Configuration validation errors:")
            for section, error_list in errors.items():
                print(f"  [{section}]:")
                for error in error_list:
                    print(f"    - {error}")
        else:
            print("Configuration is valid!")

        # 설정 요약 출력
        print("\nConfiguration Summary:")
        print(f"  OCR Model: {config_manager.ocr_config.model}")
        print(f"  PDF DPI: {config_manager.pdf_config.dpi}")
        print(f"  Preprocessing: {config_manager.pdf_config.preprocessing}")
        print(f"  Postprocessing: {config_manager.text_config.enable_postprocessing}")
        print(f"  Batch Workers: {config_manager.batch_config.max_workers}")

    elif args.profile:
        # 프로필로 설정 생성
        config_manager = ConfigManager()
        presets = config_manager.get_profile_presets()

        if args.profile in presets:
            profile_config = config_manager.create_profile(args.profile, **presets[args.profile])
            profile_config.save_config(args.output)
            print(f"Created {args.profile} profile configuration: {args.output}")
        else:
            print(f"Unknown profile: {args.profile}")

    else:
        print("Please specify an action. Use --help for more information.")