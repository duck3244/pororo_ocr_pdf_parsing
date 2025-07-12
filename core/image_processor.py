#!/usr/bin/env python3
"""
이미지 전처리 모듈
OCR 정확도 향상을 위한 이미지 전처리 기능 제공
"""

import cv2
import numpy as np
import os
import logging
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageProcessor:
    """이미지 전처리 클래스"""
    
    def __init__(self):
        """이미지 프로세서 초기화"""
        self.processing_history = []
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        이미지 파일 로드
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            OpenCV 이미지 배열
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            logger.debug(f"Loaded image: {image_path} ({image.shape})")
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {str(e)}")
            raise
    
    def save_image(self, image: np.ndarray, output_path: str) -> str:
        """
        이미지 저장
        
        Args:
            image: OpenCV 이미지 배열
            output_path: 출력 파일 경로
            
        Returns:
            저장된 파일 경로
        """
        try:
            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 이미지 저장
            success = cv2.imwrite(output_path, image)
            if not success:
                raise ValueError(f"Failed to save image to {output_path}")
            
            logger.debug(f"Saved image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        이미지를 그레이스케일로 변환
        
        Args:
            image: 입력 이미지
            
        Returns:
            그레이스케일 이미지
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug("Converted to grayscale")
            return gray
        return image
    
    def apply_gaussian_blur(self, image: np.ndarray, kernel_size: Tuple[int, int] = (5, 5), sigma: float = 0) -> np.ndarray:
        """
        가우시안 블러 적용
        
        Args:
            image: 입력 이미지
            kernel_size: 커널 크기
            sigma: 시그마 값
            
        Returns:
            블러 처리된 이미지
        """
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        logger.debug(f"Applied Gaussian blur: kernel={kernel_size}, sigma={sigma}")
        return blurred
    
    def apply_threshold(self, image: np.ndarray, threshold_type: str = "adaptive", **kwargs) -> np.ndarray:
        """
        임계값 적용
        
        Args:
            image: 입력 이미지 (그레이스케일)
            threshold_type: 임계값 유형 (adaptive, binary, otsu)
            **kwargs: 추가 매개변수
            
        Returns:
            임계값 처리된 이미지
        """
        if threshold_type == "adaptive":
            max_value = kwargs.get('max_value', 255)
            adaptive_method = getattr(cv2, kwargs.get('adaptive_method', 'ADAPTIVE_THRESH_GAUSSIAN_C'))
            threshold_type_cv = getattr(cv2, kwargs.get('threshold_type_cv', 'THRESH_BINARY'))
            block_size = kwargs.get('block_size', 11)
            c_constant = kwargs.get('c_constant', 2)
            
            thresh = cv2.adaptiveThreshold(
                image, max_value, adaptive_method, threshold_type_cv, block_size, c_constant
            )
            
        elif threshold_type == "binary":
            threshold_value = kwargs.get('threshold_value', 127)
            max_value = kwargs.get('max_value', 255)
            _, thresh = cv2.threshold(image, threshold_value, max_value, cv2.THRESH_BINARY)
            
        elif threshold_type == "otsu":
            max_value = kwargs.get('max_value', 255)
            _, thresh = cv2.threshold(image, 0, max_value, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
        else:
            raise ValueError(f"Unsupported threshold type: {threshold_type}")
        
        logger.debug(f"Applied {threshold_type} threshold")
        return thresh
    
    def apply_median_blur(self, image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        미디언 블러 적용 (노이즈 제거)
        
        Args:
            image: 입력 이미지
            kernel_size: 커널 크기
            
        Returns:
            노이즈 제거된 이미지
        """
        denoised = cv2.medianBlur(image, kernel_size)
        logger.debug(f"Applied median blur: kernel_size={kernel_size}")
        return denoised
    
    def apply_morphology(self, image: np.ndarray, operation: str = "opening", kernel_size: Tuple[int, int] = (3, 3)) -> np.ndarray:
        """
        모폴로지 연산 적용
        
        Args:
            image: 입력 이미지
            operation: 연산 유형 (opening, closing, erosion, dilation)
            kernel_size: 커널 크기
            
        Returns:
            모폴로지 처리된 이미지
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        
        if operation == "opening":
            result = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif operation == "closing":
            result = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        elif operation == "erosion":
            result = cv2.erode(image, kernel, iterations=1)
        elif operation == "dilation":
            result = cv2.dilate(image, kernel, iterations=1)
        else:
            raise ValueError(f"Unsupported morphology operation: {operation}")
        
        logger.debug(f"Applied morphology: {operation}, kernel_size={kernel_size}")
        return result
    
    def enhance_contrast(self, image: np.ndarray, method: str = "clahe", **kwargs) -> np.ndarray:
        """
        대비 향상
        
        Args:
            image: 입력 이미지
            method: 대비 향상 방법 (clahe, histogram_eq)
            **kwargs: 추가 매개변수
            
        Returns:
            대비 향상된 이미지
        """
        if method == "clahe":
            clip_limit = kwargs.get('clip_limit', 3.0)
            tile_grid_size = kwargs.get('tile_grid_size', (8, 8))
            
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            enhanced = clahe.apply(image)
            
        elif method == "histogram_eq":
            enhanced = cv2.equalizeHist(image)
            
        else:
            raise ValueError(f"Unsupported contrast enhancement method: {method}")
        
        logger.debug(f"Enhanced contrast using {method}")
        return enhanced
    
    def remove_noise(self, image: np.ndarray, method: str = "bilateral", **kwargs) -> np.ndarray:
        """
        노이즈 제거
        
        Args:
            image: 입력 이미지
            method: 노이즈 제거 방법 (bilateral, gaussian, median)
            **kwargs: 추가 매개변수
            
        Returns:
            노이즈 제거된 이미지
        """
        if method == "bilateral":
            d = kwargs.get('d', 9)
            sigma_color = kwargs.get('sigma_color', 75)
            sigma_space = kwargs.get('sigma_space', 75)
            
            denoised = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            
        elif method == "gaussian":
            kernel_size = kwargs.get('kernel_size', (5, 5))
            sigma = kwargs.get('sigma', 0)
            
            denoised = cv2.GaussianBlur(image, kernel_size, sigma)
            
        elif method == "median":
            kernel_size = kwargs.get('kernel_size', 5)
            denoised = cv2.medianBlur(image, kernel_size)
            
        else:
            raise ValueError(f"Unsupported noise removal method: {method}")
        
        logger.debug(f"Removed noise using {method}")
        return denoised
    
    def correct_skew(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        기울어진 이미지 보정
        
        Args:
            image: 입력 이미지
            
        Returns:
            보정된 이미지와 회전 각도
        """
        try:
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 이진화
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binary = cv2.bitwise_not(binary)
            
            # 허프 변환으로 선 검출
            lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
            
            if lines is not None:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    angles.append(angle)
                
                # 평균 각도 계산
                median_angle = np.median(angles)
                
                # 이미지 회전
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                corrected = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                
                logger.debug(f"Corrected skew: {median_angle:.2f} degrees")
                return corrected, median_angle
            
        except Exception as e:
            logger.warning(f"Failed to correct skew: {str(e)}")
        
        return image, 0.0
    
    def resize_image(self, image: np.ndarray, width: Optional[int] = None, height: Optional[int] = None, scale_factor: Optional[float] = None) -> np.ndarray:
        """
        이미지 크기 조정
        
        Args:
            image: 입력 이미지
            width: 목표 너비
            height: 목표 높이
            scale_factor: 스케일 팩터
            
        Returns:
            크기 조정된 이미지
        """
        original_height, original_width = image.shape[:2]
        
        if scale_factor is not None:
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
        elif width is not None and height is not None:
            new_width, new_height = width, height
        elif width is not None:
            scale = width / original_width
            new_width = width
            new_height = int(original_height * scale)
        elif height is not None:
            scale = height / original_height
            new_width = int(original_width * scale)
            new_height = height
        else:
            return image
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        logger.debug(f"Resized image: {original_width}x{original_height} -> {new_width}x{new_height}")
        return resized
    
    def preprocess_for_ocr(self, image_path: str, output_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> str:
        """
        OCR을 위한 종합 전처리
        
        Args:
            image_path: 입력 이미지 경로
            output_path: 출력 이미지 경로 (None이면 자동 생성)
            config: 전처리 설정
            
        Returns:
            전처리된 이미지 경로
        """
        # 기본 설정
        default_config = {
            'convert_grayscale': True,
            'enhance_contrast': {'method': 'clahe', 'clip_limit': 3.0},
            'remove_noise': {'method': 'bilateral', 'd': 9},
            'apply_threshold': {'threshold_type': 'adaptive', 'block_size': 11, 'c_constant': 2},
            'morphology': {'operation': 'opening', 'kernel_size': (2, 2)},
            'correct_skew': True,
            'resize': None  # {'scale_factor': 1.2}
        }
        
        if config:
            default_config.update(config)
        
        try:
            # 이미지 로드
            image = self.load_image(image_path)
            processed = image.copy()
            
            processing_steps = []
            
            # 1. 그레이스케일 변환
            if default_config['convert_grayscale']:
                processed = self.convert_to_grayscale(processed)
                processing_steps.append("grayscale")
            
            # 2. 대비 향상
            if default_config['enhance_contrast']:
                config_contrast = default_config['enhance_contrast']
                processed = self.enhance_contrast(processed, **config_contrast)
                processing_steps.append("contrast_enhancement")
            
            # 3. 노이즈 제거
            if default_config['remove_noise']:
                config_noise = default_config['remove_noise']
                processed = self.remove_noise(processed, **config_noise)
                processing_steps.append("noise_removal")
            
            # 4. 기울기 보정
            if default_config['correct_skew']:
                processed, skew_angle = self.correct_skew(processed)
                processing_steps.append(f"skew_correction({skew_angle:.2f}°)")
            
            # 5. 임계값 적용
            if default_config['apply_threshold']:
                config_threshold = default_config['apply_threshold']
                processed = self.apply_threshold(processed, **config_threshold)
                processing_steps.append("thresholding")
            
            # 6. 모폴로지 연산
            if default_config['morphology']:
                config_morph = default_config['morphology']
                processed = self.apply_morphology(processed, **config_morph)
                processing_steps.append("morphology")
            
            # 7. 크기 조정
            if default_config['resize']:
                config_resize = default_config['resize']
                processed = self.resize_image(processed, **config_resize)
                processing_steps.append("resize")
            
            # 출력 경로 생성
            if output_path is None:
                input_path = Path(image_path)
                output_path = input_path.parent / f"{input_path.stem}_preprocessed{input_path.suffix}"
            
            # 전처리된 이미지 저장
            final_path = self.save_image(processed, str(output_path))
            
            # 처리 이력 저장
            processing_record = {
                'input_path': image_path,
                'output_path': final_path,
                'processing_steps': processing_steps,
                'config': default_config,
                'processed_at': datetime.now().isoformat()
            }
            self.processing_history.append(processing_record)
            
            logger.info(f"Preprocessed image: {image_path} -> {final_path}")
            logger.info(f"Processing steps: {', '.join(processing_steps)}")
            
            return final_path
            
        except Exception as e:
            logger.error(f"Failed to preprocess image: {str(e)}")
            raise
    
    def batch_preprocess(self, image_paths: List[str], output_dir: str, config: Optional[Dict[str, Any]] = None, progress_callback: Optional[callable] = None) -> List[str]:
        """
        여러 이미지 배치 전처리
        
        Args:
            image_paths: 입력 이미지 경로 리스트
            output_dir: 출력 디렉토리
            config: 전처리 설정
            progress_callback: 진행률 콜백 함수
            
        Returns:
            전처리된 이미지 경로 리스트
        """
        output_path_obj = Path(output_dir)
        output_path_obj.mkdir(parents=True, exist_ok=True)
        
        processed_paths = []
        
        for i, image_path in enumerate(image_paths):
            try:
                # 출력 파일 경로 생성
                input_name = Path(image_path).stem
                output_path = output_path_obj / f"{input_name}_preprocessed.png"
                
                # 전처리 실행
                processed_path = self.preprocess_for_ocr(image_path, str(output_path), config)
                processed_paths.append(processed_path)
                
                # 진행률 콜백 호출
                if progress_callback:
                    progress_callback(i + 1, len(image_paths), processed_path)
                
            except Exception as e:
                logger.error(f"Failed to preprocess {image_path}: {str(e)}")
                processed_paths.append(None)
        
        successful_count = len([p for p in processed_paths if p is not None])
        logger.info(f"Batch preprocessing completed: {successful_count}/{len(image_paths)} successful")
        
        return processed_paths
    
    def get_image_quality_metrics(self, image_path: str) -> Dict[str, float]:
        """
        이미지 품질 메트릭 계산
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            품질 메트릭 딕셔너리
        """
        try:
            image = self.load_image(image_path)
            gray = self.convert_to_grayscale(image)
            
            # 선명도 (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 대비 (표준편차)
            contrast = gray.std()
            
            # 밝기 (평균)
            brightness = gray.mean()
            
            # 노이즈 레벨 (가우시안 블러와의 차이)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_level = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
            
            metrics = {
                'sharpness': float(sharpness),
                'contrast': float(contrast),
                'brightness': float(brightness),
                'noise_level': float(noise_level),
                'resolution': f"{image.shape[1]}x{image.shape[0]}"
            }
            
            logger.debug(f"Image quality metrics for {image_path}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate image quality metrics: {str(e)}")
            return {}
    
    def get_processing_history(self) -> List[Dict[str, Any]]:
        """처리 이력 반환"""
        return self.processing_history
    
    def clear_processing_history(self):
        """처리 이력 초기화"""
        self.processing_history = []


# 사용 예제
if __name__ == "__main__":
    # 이미지 프로세서 초기화
    processor = ImageProcessor()
    
    # 단일 이미지 전처리
    image_path = "sample.png"
    if os.path.exists(image_path):
        # 커스텀 설정
        config = {
            'enhance_contrast': {'method': 'clahe', 'clip_limit': 2.0},
            'remove_noise': {'method': 'bilateral', 'd': 7},
            'correct_skew': True
        }
        
        # 전처리 실행
        processed_path = processor.preprocess_for_ocr(image_path, config=config)
        print(f"Preprocessed: {processed_path}")
        
        # 품질 메트릭 확인
        metrics = processor.get_image_quality_metrics(processed_path)
        print(f"Quality metrics: {metrics}")
        
    else:
        print(f"Sample image not found: {image_path}")
    
    # 처리 이력 확인
    history = processor.get_processing_history()
    for record in history:
        print(f"Processed: {record['input_path']} -> {record['output_path']}")
        print(f"Steps: {', '.join(record['processing_steps'])}")
