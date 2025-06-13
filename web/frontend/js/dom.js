// DOM Management Module
console.log('🚀 Loading dom.js...');

// Cache DOM elements for better performance
function initializeElements() {
    const elements = [
        'new-conversation-btn', 'upload-file-btn', 'send-btn', 'message-input',
        'conversations-container', 'messages-container', 'uploaded-files',
        'current-conversation-title', 'current-conversation-id',
        'upload-modal', 'upload-area', 'file-input', 'upload-progress',
        'loading-overlay', 'scroll-to-bottom-btn'
    ];
    
    elements.forEach(id => {
        window.AppConfig.elementsCache[id] = document.getElementById(id);
    });
}

// Show loading overlay
function showLoading(message = 'Loading...') {
    const overlay = window.AppConfig.elementsCache['loading-overlay'];
    const text = overlay.querySelector('p');
    text.textContent = message;
    overlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    window.AppConfig.elementsCache['loading-overlay'].style.display = 'none';
}

// Show error notification
function showError(message) {
    showNotification(message, 'error');
}

// Show success notification
function showSuccess(message) {
    showNotification(message, 'success');
}

// Show notification
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `${type}-message`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'check-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to top of messages container
    const container = window.AppConfig.elementsCache['messages-container'];
    container.insertBefore(notification, container.firstChild);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Update input state based on current conditions
function updateInputState() {
    const input = window.AppConfig.elementsCache['message-input'];
    const sendBtn = window.AppConfig.elementsCache['send-btn'];
    
    const hasText = input.value.trim().length > 0;
    const currentId = window.AppConfig.getCurrentConversationId();
    const hasFiles = currentId && window.AppConfig.conversations[currentId]?.files?.length > 0;
    
    sendBtn.disabled = !hasText || window.AppConfig.getIsSending() || !hasFiles;
    
    // Update placeholder
    if (!hasFiles) {
        input.placeholder = 'Please upload an Excel file first...';
        input.disabled = true;
    } else {
        input.placeholder = 'Ask me anything about your Excel data...';
        input.disabled = false;
    }
}

// Scroll to bottom of messages
function scrollToBottom() {
    const container = window.AppConfig.elementsCache['messages-container'];
    if (!container) return;
    
    // Smooth scroll to bottom
    container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
    });
    
    // Hide the scroll to bottom button
    const scrollBtn = window.AppConfig.elementsCache['scroll-to-bottom-btn'];
    if (scrollBtn) {
        scrollBtn.classList.remove('show');
    }
}

// Handle scroll events
function handleScroll() {
    const container = window.AppConfig.elementsCache['messages-container'];
    const scrollBtn = window.AppConfig.elementsCache['scroll-to-bottom-btn'];
    
    if (!container || !scrollBtn) return;
    
    // Show button if not at bottom (with more tolerance for fixed input)
    const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
    
    if (isAtBottom) {
        scrollBtn.classList.remove('show');
    } else {
        scrollBtn.classList.add('show');
    }
}

// Export DOM functions
window.DOMManager = {
    initializeElements,
    showLoading,
    hideLoading,
    showError,
    showSuccess,
    showNotification,
    updateInputState,
    scrollToBottom,
    handleScroll
};

console.log('✅ DOM.js loaded'); 