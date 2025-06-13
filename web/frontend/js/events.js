// Event Handling Module
console.log('🚀 Loading events.js...');

// Setup all event listeners
function setupEventListeners() {
    console.log('🔄 Setting up event listeners...');
    
    // Navigation events
    window.AppConfig.elementsCache['new-conversation-btn'].addEventListener('click', window.ConversationManager.createNewConversation);
    window.AppConfig.elementsCache['upload-file-btn'].addEventListener('click', window.UploadManager.openUploadModal);
    window.AppConfig.elementsCache['alias-manager-btn'].addEventListener('click', window.AliasManager.openAliasModal);
    
    // Input events
    window.AppConfig.elementsCache['message-input'].addEventListener('input', window.APIManager.handleInputChange);
    window.AppConfig.elementsCache['message-input'].addEventListener('keydown', window.APIManager.handleKeyDown);
    window.AppConfig.elementsCache['send-btn'].addEventListener('click', window.APIManager.sendMessage);
    
    // Auto-resize textarea
    window.AppConfig.elementsCache['message-input'].addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // Scroll events
    window.AppConfig.elementsCache['scroll-to-bottom-btn'].addEventListener('click', window.DOMManager.scrollToBottom);
    window.AppConfig.elementsCache['messages-container'].addEventListener('scroll', window.DOMManager.handleScroll);
    
    // Upload modal events
    setupUploadModalEvents();
    
    // Alias modal events  
    setupAliasModalEvents();
    
    console.log('✅ Event listeners setup complete');
}

// Setup upload modal specific events
function setupUploadModalEvents() {
    const modal = window.AppConfig.elementsCache['upload-modal'];
    const uploadArea = window.AppConfig.elementsCache['upload-area'];
    const closeBtn = modal.querySelector('.close');
    
    // Close modal events
    closeBtn.addEventListener('click', window.UploadManager.closeUploadModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) window.UploadManager.closeUploadModal();
    });
    
    // File input event
    window.AppConfig.elementsCache['file-input'].addEventListener('change', window.UploadManager.handleFileSelect);
    
    // Choose file button
    const chooseFileBtn = modal.querySelector('#choose-file-btn');
    if (chooseFileBtn) {
        chooseFileBtn.addEventListener('click', () => window.AppConfig.elementsCache['file-input'].click());
    }
    
    // Drag and drop events
    uploadArea.addEventListener('click', () => window.AppConfig.elementsCache['file-input'].click());
    uploadArea.addEventListener('dragover', window.UploadManager.handleDragOver);
    uploadArea.addEventListener('dragleave', window.UploadManager.handleDragLeave);
    uploadArea.addEventListener('drop', window.UploadManager.handleDrop);
    
    // ESC key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            window.UploadManager.closeUploadModal();
        }
    });
}

// Setup alias modal specific events
function setupAliasModalEvents() {
    const modal = window.AppConfig.elementsCache['alias-modal'];
    const uploadArea = window.AppConfig.elementsCache['alias-upload-area'];
    const closeBtn = modal.querySelector('.alias-close');
    
    // Close modal events
    closeBtn.addEventListener('click', window.AliasManager.closeAliasModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) window.AliasManager.closeAliasModal();
    });
    
    // File input event
    window.AppConfig.elementsCache['alias-file-input'].addEventListener('change', window.AliasManager.handleAliasFileSelect);
    
    // Action buttons
    const uploadBtn = window.AppConfig.elementsCache['upload-alias-btn'];
    const replaceBtn = window.AppConfig.elementsCache['replace-alias-btn'];
    const removeBtn = window.AppConfig.elementsCache['remove-alias-btn'];
    const chooseBtn = window.AppConfig.elementsCache['choose-alias-file-btn'];
    
    if (uploadBtn) uploadBtn.addEventListener('click', window.AliasManager.showAliasUploadArea);
    if (replaceBtn) replaceBtn.addEventListener('click', window.AliasManager.showAliasUploadArea);
    if (removeBtn) removeBtn.addEventListener('click', window.AliasManager.removeAliasFile);
    if (chooseBtn) chooseBtn.addEventListener('click', () => window.AppConfig.elementsCache['alias-file-input'].click());
    
    // Drag and drop events for upload area
    if (uploadArea) {
        uploadArea.addEventListener('click', () => window.AppConfig.elementsCache['alias-file-input'].click());
        uploadArea.addEventListener('dragover', window.AliasManager.handleAliasDragOver);
        uploadArea.addEventListener('dragleave', window.AliasManager.handleAliasDragLeave);
        uploadArea.addEventListener('drop', window.AliasManager.handleAliasDrop);
    }
    
    // ESC key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            window.AliasManager.closeAliasModal();
        }
    });
}

// Export event functions
window.EventManager = {
    setupEventListeners,
    setupUploadModalEvents,
    setupAliasModalEvents
};

console.log('✅ Events.js loaded'); 