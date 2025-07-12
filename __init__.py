"""
Pororo OCR PDF Parser - 한국어 최적화 PDF OCR 솔루션

This package provides comprehensive PDF OCR functionality optimized for Korean text,
including web interface, batch processing, and command-line tools.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from core import OCREngine, PDFHandler, ImageProcessor, TextPostProcessor
from config import ConfigManager
from batch import BatchProcessor

__all__ = [
    'OCREngine',
    'PDFHandler', 
    'ImageProcessor',
    'TextPostProcessor',
    'ConfigManager',
    'BatchProcessor'
]
