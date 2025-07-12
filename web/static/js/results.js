// Pororo OCR PDF Parser - Results Page JavaScript

class ResultsPage {
    constructor() {
        this.initializeEventListeners();
        this.initializeTooltips();
        this.setupCopyButtons();
    }
    
    initializeEventListeners() {
        // 탭 전환 이벤트
        document.querySelectorAll('#resultTabs button[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                this.handleTabChange(e.target.getAttribute('data-bs-target'));
            });
        });
        
        // 검색 기능
        this.setupSearchFunctionality();
        
        // 키보드 단축키
        this.setupKeyboardShortcuts();
    }
    
    handleTabChange(targetTab) {
        switch(targetTab) {
            case '#pages':
                this.highlightTextRegions();
                break;
            case '#summary':
                this.animateCharts();
                break;
            case '#entities':
                this.highlightEntities();
                break;
            case '#raw':
                this.formatRawData();
                break;
        }
    }
    
    setupSearchFunctionality() {
        // 검색 입력 필드 생성
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container mb-3';
        searchContainer.innerHTML = `
            <div class="input-group">
                <span class="input-group-text">
                    <i class="fas fa-search"></i>
                </span>
                <input type="text" class="form-control" id="searchInput" 
                       placeholder="텍스트 검색..." autocomplete="off">
                <button class="btn btn-outline-secondary" type="button" id="clearSearch">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="searchResults" class="search-results mt-2"></div>
        `;
        
        // 페이지 탭에 검색 기능 추가
        const pagesTab = document.getElementById('pages');
        if (pagesTab) {
            pagesTab.insertBefore(searchContainer, pagesTab.firstChild);
            
            const searchInput = document.getElementById('searchInput');
            const clearButton = document.getElementById('clearSearch');
            
            searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
            clearButton.addEventListener('click', () => this.clearSearch());
        }
    }
    
    performSearch(query) {
        const searchResults = document.getElementById('searchResults');
        
        if (!query.trim()) {
            this.clearSearch();
            return;
        }
        
        const textRegions = document.querySelectorAll('.text-region, .combined-text');
        const results = [];
        
        textRegions.forEach((region, index) => {
            const text = region.textContent.toLowerCase();
            const searchTerm = query.toLowerCase();
            
            if (text.includes(searchTerm)) {
                const pageCard = region.closest('.page-content-card');
                const pageNumber = pageCard ? pageCard.querySelector('h4').textContent.match(/\d+/)[0] : 'Unknown';
                
                // 텍스트 하이라이트
                const highlighted = this.highlightText(region.textContent, query);
                
                results.push({
                    pageNumber,
                    element: region,
                    highlighted,
                    text: text.substring(text.indexOf(searchTerm) - 20, text.indexOf(searchTerm) + 80)
                });
                
                region.innerHTML = highlighted;
            }
        });
        
        this.displaySearchResults(results, query);
    }
    
    highlightText(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark class="search-highlight">$1</mark>');
    }
    
    displaySearchResults(results, query) {
        const searchResults = document.getElementById('searchResults');
        
        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    "${query}"에 대한 검색 결과가 없습니다.
                </div>
            `;
            return;
        }
        
        const resultHtml = `
            <div class="search-summary mb-2">
                <small class="text-muted">
                    <i class="fas fa-search me-1"></i>
                    "${query}" 검색 결과: <strong>${results.length}개</strong> 발견
                </small>
            </div>
            <div class="search-items">
                ${results.map((result, index) => `
                    <div class="search-item" onclick="scrollToResult(${index})">
                        <div class="search-item-header">
                            <small class="text-muted">페이지 ${result.pageNumber}</small>
                        </div>
                        <div class="search-item-content">
                            ${result.text}...
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        searchResults.innerHTML = resultHtml;
    }
    
    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        if (searchInput) searchInput.value = '';
        if (searchResults) searchResults.innerHTML = '';
        
        // 하이라이트 제거
        document.querySelectorAll('.search-highlight').forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+F: 검색 포커스
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape: 검색 초기화
            if (e.key === 'Escape') {
                this.clearSearch();
            }
            
            // Ctrl+C: 현재 탭 내용 복사
            if ((e.ctrlKey || e.metaKey) && e.key === 'c' && !window.getSelection().toString()) {
                e.preventDefault();
                this.copyCurrentTabContent();
            }
        });
    }
    
    copyCurrentTabContent() {
        const activeTab = document.querySelector('.tab-pane.active');
        if (!activeTab) return;
        
        let content = '';
        
        switch(activeTab.id) {
            case 'pages':
                content = this.extractPagesContent();
                break;
            case 'summary':
                content = this.extractSummaryContent();
                break;
            case 'entities':
                content = this.extractEntitiesContent();
                break;
            case 'raw':
                content = document.getElementById('jsonData').textContent;
                break;
        }
        
        if (content) {
            this.copyToClipboard(content);
        }
    }
    
    extractPagesContent() {
        const pages = document.querySelectorAll('.page-content-card');
        let content = 'OCR 추출 결과\n=================\n\n';
        
        pages.forEach(page => {
            const pageNumber = page.querySelector('h4').textContent;
            const combinedText = page.querySelector('.combined-text pre');
            
            if (combinedText) {
                content += `${pageNumber}\n`;
                content += '-'.repeat(pageNumber.length) + '\n';
                content += combinedText.textContent + '\n\n';
            }
        });
        
        return content;
    }
    
    extractSummaryContent() {
        const summaryCards = document.querySelectorAll('.summary-card');
        let content = '문서 요약\n=========\n\n';
        
        summaryCards.forEach(card => {
            const title = card.querySelector('.card-title').textContent;
            content += `${title}\n`;
            content += '-'.repeat(title.length) + '\n';
            
            const table = card.querySelector('table');
            if (table) {
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length === 2) {
                        content += `${cells[0].textContent}: ${cells[1].textContent}\n`;
                    }
                });
            }
            content += '\n';
        });
        
        return content;
    }
    
    extractEntitiesContent() {
        const entityCards = document.querySelectorAll('.entity-card');
        let content = '추출된 정보\n===========\n\n';
        
        entityCards.forEach(card => {
            const title = card.querySelector('.entity-title').textContent;
            const badges = card.querySelectorAll('.entity-badge');
            
            content += `${title}\n`;
            content += '-'.repeat(title.length) + '\n';
            
            badges.forEach(badge => {
                content += `- ${badge.textContent}\n`;
            });
            content += '\n';
        });
        
        return content;
    }
    
    highlightTextRegions() {
        const textRegions = document.querySelectorAll('.text-region');
        textRegions.forEach((region, index) => {
            setTimeout(() => {
                region.style.transform = 'scale(1.02)';
                setTimeout(() => {
                    region.style.transform = 'scale(1)';
                }, 200);
            }, index * 50);
        });
    }
    
    animateCharts() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width;
            }, 100);
        });
    }
    
    highlightEntities() {
        const entityBadges = document.querySelectorAll('.entity-badge');
        entityBadges.forEach((badge, index) => {
            setTimeout(() => {
                badge.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    badge.style.transform = 'scale(1)';
                }, 200);
            }, index * 30);
        });
    }
    
    formatRawData() {
        const codeElement = document.getElementById('jsonData');
        if (codeElement && window.Prism) {
            Prism.highlightElement(codeElement);
        }
    }
    
    initializeTooltips() {
        // Bootstrap 툴팁 초기화
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    setupCopyButtons() {
        // 복사 버튼에 이벤트 리스너 추가
        document.querySelectorAll('[onclick*="copy"]').forEach(button => {
            button.addEventListener('click', (e) => {
                setTimeout(() => {
                    this.showCopySuccess(e.target);
                }, 100);
            });
        });
    }
    
    showCopySuccess(element) {
        const originalText = element.textContent;
        const originalClass = element.className;
        
        element.innerHTML = '<i class="fas fa-check me-1"></i>복사됨!';
        element.className = originalClass.replace('btn-outline-secondary', 'btn-success');
        
        setTimeout(() => {
            element.innerHTML = '<i class="fas fa-copy me-1"></i>복사';
            element.className = originalClass;
        }, 2000);
    }
    
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
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
                document.execCommand('copy');
                textArea.remove();
            }
            
            this.showNotification('클립보드에 복사되었습니다.', 'success');
        } catch (err) {
            console.error('복사 실패:', err);
            this.showNotification('복사에 실패했습니다.', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} me-2"></i>
                ${message}
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
        `;
        
        document.body.appendChild(notification);
        
        // 애니메이션
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // 자동 제거
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

// 전역 함수들
function copyPageText(pageNumber) {
    const pageText = document.getElementById(`pageText${pageNumber}`);
    if (pageText) {
        const text = pageText.textContent;
        resultsPage.copyToClipboard(text);
    }
}

function scrollToResult(index) {
    const searchItems = document.querySelectorAll('.search-item');
    if (searchItems[index]) {
        searchItems[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // 일시적으로 하이라이트
        searchItems[index].style.backgroundColor = '#fff3cd';
        setTimeout(() => {
            searchItems[index].style.backgroundColor = '';
        }, 2000);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    window.resultsPage = new ResultsPage();
    
    // 페이드인 애니메이션
    const cards = document.querySelectorAll('.stats-card, .page-content-card, .summary-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.6s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, index * 100);
    });
    
    // 스크롤 이벤트 - 무한 스크롤이나 지연 로딩에 사용
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        // 패럴랙스 효과 (헤더에 적용)
        const header = document.querySelector('header');
        if (header) {
            header.style.transform = `translateY(${rate}px)`;
        }
    });
});

// CSS 추가 (검색 관련 스타일)
const additionalStyles = `
.search-container {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.search-item {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.search-item:hover {
    background: #f8f9fa;
    border-color: #007bff;
    transform: translateX(5px);
}

.search-item-header {
    font-size: 0.8rem;
    color: #6c757d;
    margin-bottom: 0.25rem;
}

.search-item-content {
    font-size: 0.9rem;
    line-height: 1.4;
}

.search-highlight {
    background: #fff3cd;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 600;
}

.notification {
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(400px); }
    to { transform: translateX(0); }
}
`;

// 스타일 추가
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);