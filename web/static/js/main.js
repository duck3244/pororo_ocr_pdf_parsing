// Pororo OCR PDF Parser - Main JavaScript

class OCRUploader {
    constructor() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.uploadForm = document.getElementById('uploadForm');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.statusMessage = document.getElementById('statusMessage');
        this.processingTimeElement = document.getElementById('processingTime');
        
        this.currentJobId = null;
        this.startTime = null;
        this.statusInterval = null;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // 드래그 앤 드롭 이벤트
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // 파일 선택 이벤트
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // 폼 제출 이벤트
        this.uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        if (e.target.files.length > 0) {
            this.selectFile(e.target.files[0]);
        }
    }
    
    selectFile(file) {
        // 파일 유효성 검사
        if (!this.validateFile(file)) {
            return;
        }
        
        // 파일 정보 표시
        this.displayFileInfo(file);
        
        // 업로드 버튼 활성화
        this.uploadBtn.disabled = false;
        
        // 파일 입력에 설정
        const dt = new DataTransfer();
        dt.items.add(file);
        this.fileInput.files = dt.files;
    }
    
    validateFile(file) {
        // 파일 형식 확인
        if (file.type !== 'application/pdf') {
            this.showAlert('PDF 파일만 업로드 가능합니다.', 'danger');
            return false;
        }
        
        // 파일 크기 확인 (16MB)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showAlert('파일 크기는 16MB를 초과할 수 없습니다.', 'danger');
            return false;
        }
        
        return true;
    }
    
    displayFileInfo(file) {
        const fileSize = this.formatFileSize(file.size);
        const fileName = file.name;
        
        this.uploadArea.innerHTML = `
            <div class="upload-content">
                <i class="fas fa-file-pdf upload-icon text-success"></i>
                <h4 class="upload-title text-success">파일 선택됨</h4>
                <p class="upload-subtitle"><strong>${fileName}</strong></p>
                <div class="upload-info">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        크기: ${fileSize}
                    </small>
                </div>
            </div>
        `;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (!this.fileInput.files[0]) {
            this.showAlert('파일을 선택해주세요.', 'warning');
            return;
        }
        
        // 폼 데이터 준비
        const formData = new FormData();
        formData.append('file', this.fileInput.files[0]);
        formData.append('dpi', document.getElementById('dpi').value);
        formData.append('preprocess', document.getElementById('preprocess').checked);
        formData.append('postprocess', document.getElementById('postprocessing').checked);
        
        try {
            // 진행률 표시 시작
            this.startProcessing();
            
            // 업로드 요청
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.currentJobId = result.job_id;
                this.startStatusPolling();
            } else {
                this.showAlert(result.error || '업로드 중 오류가 발생했습니다.', 'danger');
                this.resetForm();
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('업로드 중 오류가 발생했습니다.', 'danger');
            this.resetForm();
        }
    }
    
    startProcessing() {
        this.startTime = Date.now();
        this.progressContainer.style.display = 'block';
        this.uploadBtn.disabled = true;
        this.uploadForm.style.display = 'none';
        
        // 처리 시간 업데이트 시작
        this.timeInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            this.processingTimeElement.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    startStatusPolling() {
        this.statusInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentJobId}`);
                const status = await response.json();
                
                if (response.ok) {
                    this.updateProgress(status);
                    
                    if (status.status === 'completed') {
                        this.handleSuccess();
                    } else if (status.status === 'error') {
                        this.handleError(status.message);
                    }
                } else {
                    this.handleError('상태 확인 중 오류가 발생했습니다.');
                }
            } catch (error) {
                console.error('Status polling error:', error);
                this.handleError('상태 확인 중 오류가 발생했습니다.');
            }
        }, 2000);
    }
    
    updateProgress(status) {
        const progress = Math.min(status.progress || 0, 100);
        
        this.progressBar.style.width = `${progress}%`;
        this.progressText.textContent = `${Math.round(progress)}%`;
        this.statusMessage.textContent = status.message || '처리 중...';
        
        // 진행률에 따른 색상 변경
        if (progress < 30) {
            this.progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
        } else if (progress < 70) {
            this.progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
        } else {
            this.progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
        }
    }
    
    handleSuccess() {
        this.stopPolling();
        
        // 성공 애니메이션
        this.progressBar.className = 'progress-bar bg-success';
        this.progressBar.style.width = '100%';
        this.progressText.textContent = '100%';
        this.statusMessage.innerHTML = '<i class="fas fa-check-circle me-2"></i>처리 완료!';
        
        // 결과 페이지로 이동
        setTimeout(() => {
            window.location.href = `/results/${this.currentJobId}`;
        }, 1500);
    }
    
    handleError(message) {
        this.stopPolling();
        
        this.progressBar.className = 'progress-bar bg-danger';
        this.statusMessage.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
        
        this.showAlert(message, 'danger');
        this.resetForm();
    }
    
    stopPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        
        if (this.timeInterval) {
            clearInterval(this.timeInterval);
            this.timeInterval = null;
        }
    }
    
    resetForm() {
        setTimeout(() => {
            this.progressContainer.style.display = 'none';
            this.uploadForm.style.display = 'block';
            this.uploadBtn.disabled = true;
            
            // 업로드 영역 초기화
            this.uploadArea.innerHTML = `
                <div class="upload-content">
                    <i class="fas fa-cloud-upload-alt upload-icon"></i>
                    <h4 class="upload-title">PDF 파일을 여기에 드롭하세요</h4>
                    <p class="upload-subtitle text-muted">또는 클릭하여 파일 선택</p>
                    <div class="upload-info">
                        <small class="text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            지원 형식: PDF | 최대 크기: 16MB
                        </small>
                    </div>
                </div>
            `;
            
            // 폼 초기화
            this.fileInput.value = '';
            this.currentJobId = null;
        }, 3000);
    }
    
    showAlert(message, type = 'info') {
        // 기존 알림 제거
        const existingAlert = document.querySelector('.alert-notification');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // 새 알림 생성
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-notification position-fixed fade-in`;
        alert.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        `;
        
        const iconMap = {
            'success': 'fas fa-check-circle',
            'danger': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle'
        };
        
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${iconMap[type]} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(alert);
        
        // 자동 제거
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

// 유틸리티 함수들
class OCRUtils {
    static copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        } else {
            // 폴백 방법
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            return new Promise((resolve, reject) => {
                try {
                    document.execCommand('copy');
                    textArea.remove();
                    resolve();
                } catch (err) {
                    textArea.remove();
                    reject(err);
                }
            });
        }
    }
    
    static showCopySuccess(element) {
        const originalText = element.textContent;
        const originalClass = element.className;
        
        element.textContent = '복사됨!';
        element.className = originalClass + ' copy-success';
        
        setTimeout(() => {
            element.textContent = originalText;
            element.className = originalClass;
        }, 2000);
    }
    
    static formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    }
    
    static formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
}

// 모달 관련 함수들
function showHelp() {
    const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
    helpModal.show();
}

function showSettings() {
    const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
    settingsModal.show();
}

// 전역 함수들
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    OCRUtils.copyToClipboard(text)
        .then(() => {
            OCRUtils.showCopySuccess(event.target);
        })
        .catch(err => {
            console.error('복사 실패:', err);
            alert('복사에 실패했습니다.');
        });
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // OCR 업로더 초기화
    const uploader = new OCRUploader();
    
    // 툴팁 초기화
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 페이드인 애니메이션
    const elements = document.querySelectorAll('.card, .feature-card');
    elements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('fade-in');
        }, index * 100);
    });
    
    // 스크롤 이벤트 (부드러운 스크롤)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 키보드 단축키
    document.addEventListener('keydown', function(e) {
        // Ctrl+U 또는 Cmd+U: 파일 업로드
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            document.getElementById('fileInput').click();
        }
        
        // ESC: 모달 닫기
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
    
    // 성능 모니터링
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(function() {
                const perfData = performance.getEntriesByType('navigation')[0];
                console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
            }, 0);
        });
    }
    
    // 오프라인/온라인 상태 감지
    window.addEventListener('online', function() {
        console.log('Network connection restored');
    });
    
    window.addEventListener('offline', function() {
        console.log('Network connection lost');
        uploader.showAlert('인터넷 연결이 끊어졌습니다. 연결을 확인해주세요.', 'warning');
    });
});

// 서비스 워커 등록 (PWA 지원)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}

// 에러 핸들링
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OCRUploader, OCRUtils };
}