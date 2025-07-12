#!/usr/bin/env python3
"""
Pororo OCR PDF Parser 설치 스크립트
"""

from setuptools import setup, find_packages
import os

# README 파일 읽기
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Pororo OCR PDF Parser - 한국어 PDF OCR 솔루션"

# requirements.txt 읽기
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="pororo-ocr-pdf-parser",
    version="1.0.0",
    description="한국어 최적화 PDF OCR 솔루션",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/pororo-ocr-pdf-parser",
    packages=find_packages(),
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.12.0',
            'black>=21.0.0',
            'flake8>=3.9.0',
        ],
        'web': [
            'gunicorn>=20.0.0',
            'redis>=4.0.0',
        ],
        'monitoring': [
            'psutil>=5.8.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'pororo-ocr=pororo_ocr_cli:main',
            'pororo-ocr-web=web.app:main',
            'pororo-ocr-batch=batch.batch_processor:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        'web': ['templates/*.html', 'static/*'],
        'config': ['*.yaml', '*.json'],
    },
    zip_safe=False,
)
