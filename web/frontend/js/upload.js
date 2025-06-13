// File Upload Module
console.log('🚀 Loading upload.js...');

// Open upload modal
function openUploadModal() {
    const currentId = window.AppConfig.getCurrentConversationId();
    if (!currentId) {
        window.DOMManager.showError('Please create a conversation first');
        return;
    }
    
    window.AppConfig.elementsCache['upload-modal'].style.display = 'block';
    resetUploadModal();
}

// Close upload modal
function closeUploadModal() {
    window.AppConfig.elementsCache['upload-modal'].style.display = 'none';
    resetUploadModal();
}

// Reset upload modal state
function resetUploadModal() {
    window.AppConfig.elementsCache['file-input'].value = '';
    window.AppConfig.elementsCache['upload-progress'].style.display = 'none';
    window.AppConfig.elementsCache['upload-area'].style.display = 'block';
    window.AppConfig.elementsCache['upload-area'].classList.remove('dragover');
    updateProgress(0);
}

// Handle file selection
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

// Upload file to server
function uploadFile(file) {
    const currentId = window.AppConfig.getCurrentConversationId();
    if (!currentId) {
        window.DOMManager.showError('No active conversation');
        return;
    }

    // Validate file type and size before upload
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        console.error('❌ [API] Invalid file type:', file.name);
        window.DOMManager.showError('Please upload only Excel files (.xlsx or .xls)');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        console.error('❌ [API] File too large:', file.size, 'bytes');
        window.DOMManager.showError('File size too large. Maximum size is 50MB.');
        return;
    }

    console.log('📤 [API] Starting file upload:', file.name);
    console.log('📊 [API] File details:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
    });
    console.log('🆔 [API] Upload conversation ID:', currentId);
    
    // Prevent duplicate uploads of the same file (by name + timestamp)
    const fileId = file.name + '_' + file.lastModified;
    if (window.AppConfig.uploadStates[fileId]) {
        console.warn('⏳ Upload already in progress for', file.name);
        return; // Skip duplicate upload
    }

    // Track upload state
    window.AppConfig.uploadStates[fileId] = true;
    
    // Show progress and hide upload area
    window.AppConfig.elementsCache['upload-area'].style.display = 'none';
    window.AppConfig.elementsCache['upload-progress'].style.display = 'block';

    // Create FormData with proper handling for Excel files
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('conversation_id', currentId);

    console.log('📦 [API] FormData created with file and conversation_id');
    console.log('🌐 [API] Sending POST request to:', `${window.AppConfig.API_BASE_URL}/upload`);

    // Simulate progress for better UX
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        updateProgress(progress);
    }, 200);

    fetch(`${window.AppConfig.API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
        // Don't set Content-Type header - let browser set it automatically for FormData
    })
    .then(response => {
        console.log('📥 [API] Upload response received:', response);
        console.log('📊 [API] Response status:', response.status, response.statusText);
        console.log('✅ [API] Response ok:', response.ok);
        
        clearInterval(progressInterval);
        updateProgress(100);
        
        if (!response.ok) {
            return response.text().then(text => {
                console.error('❌ [API] Upload error response text:', text);
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('📋 [API] Upload success data:', data);
        
        // Build file list from whichever field the backend provides
        let backendFiles = [];
        if (Array.isArray(data.files)) {
            // New structure: array of objects
            backendFiles = data.files.map(file => ({
                name: file.filename || file.name,
                size: file.size || 0,
                uploadedAt: new Date(file.uploaded_at || Date.now()),
                conversionId: file.conversion_id || file.file_id
            }));
        } else if (Array.isArray(data.processed_files)) {
            // Legacy structure: simple array of filenames
            backendFiles = data.processed_files.map(fname => ({
                name: fname,
                size: 0,
                uploadedAt: new Date(),
                conversionId: null
            }));
        }

        if (backendFiles.length) {
            window.AppConfig.conversations[currentId].files = backendFiles;
            updateUploadedFiles();
            window.DOMManager.updateInputState();
        }
        
        // Fallback: if backend did not return a file list, keep the manually added file
        if (backendFiles.length === 0) {
            if (!window.AppConfig.conversations[currentId].files) {
                window.AppConfig.conversations[currentId].files = [];
            }
            window.AppConfig.conversations[currentId].files.push({
                name: file.name,
                size: file.size,
                uploadedAt: new Date()
            });
            updateUploadedFiles();
            window.DOMManager.updateInputState();
        }
        
        // Update UI
        closeUploadModal();
        window.DOMManager.showSuccess(`File "${file.name}" uploaded successfully!`);
        console.log('✅ [API] File upload completed successfully');
        
        // Update conversation title if it's still "New Conversation"
        if (window.AppConfig.conversations[currentId].title === 'New Conversation') {
            window.AppConfig.conversations[currentId].title = `Chat with ${file.name}`;
            updateConversationsList();
            const titleElement = window.AppConfig.elementsCache['current-conversation-title'];
            if (titleElement) {
                titleElement.textContent = window.AppConfig.conversations[currentId].title;
            }
            console.log('🏷️ [API] Updated conversation title to:', window.AppConfig.conversations[currentId].title);
        }
    })
    .catch(error => {
        console.error('❌ [API] File upload error:', error);
        clearInterval(progressInterval);
        window.DOMManager.showError('Failed to upload file: ' + error.message);
    })
    .finally(() => {
        delete window.AppConfig.uploadStates[fileId];
        setTimeout(resetUploadModal, 1000);
    });
}

// Update progress bar
function updateProgress(percent) {
    const progressFill = window.AppConfig.elementsCache['upload-progress'].querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
}

// Update uploaded files display
function updateUploadedFiles() {
    const container = window.AppConfig.elementsCache['uploaded-files'];
    const messagesContainer = window.AppConfig.elementsCache['messages-container'];
    const currentId = window.AppConfig.getCurrentConversationId();
    
    // Clear container first
    container.innerHTML = '';
    
    if (!currentId || !window.AppConfig.conversations[currentId]?.files) {
        // Remove has-files class when no files
        if (messagesContainer) {
            messagesContainer.classList.remove('has-files');
        }
        return;
    }
    
    const files = window.AppConfig.conversations[currentId].files;
    
    // Add or remove has-files class based on file presence
    if (messagesContainer) {
        if (files.length > 0) {
            messagesContainer.classList.add('has-files');
        } else {
            messagesContainer.classList.remove('has-files');
        }
    }
    
    // Create uploaded file elements using the original structure
    files.forEach((file, index) => {
        const fileElement = document.createElement('div');
        fileElement.className = 'uploaded-file';
        fileElement.innerHTML = `
            <i class="fas fa-file-excel"></i>
            <span>${window.Utils.escapeHtml(file.name)}</span>
            <i class="fas fa-times remove-file" onclick="window.UploadManager.removeFile(${index})"></i>
        `;
        container.appendChild(fileElement);
    });
}

// Sync files with backend
function syncFilesWithBackend() {
    const currentId = window.AppConfig.getCurrentConversationId();
    if (!currentId) return;
    
    console.log('🔄 [API] Syncing files with backend for conversation:', currentId);
    console.log('🌐 [API] Sending GET request to:', `${window.AppConfig.API_BASE_URL}/conversations/${currentId}/files`);
    
    fetch(`${window.AppConfig.API_BASE_URL}/conversations/${currentId}/files`)
        .then(response => {
            console.log('📥 [API] Files sync response received:', response);
            console.log('📊 [API] Response status:', response.status, response.statusText);
            console.log('✅ [API] Response ok:', response.ok);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📋 [API] Files sync data:', data);
            
            // Build file list from whichever field the backend provides
            let backendFiles = [];
            if (Array.isArray(data.files)) {
                // New structure: array of objects
                backendFiles = data.files.map(file => ({
                    name: file.filename || file.name,
                    size: file.size || 0,
                    uploadedAt: new Date(file.uploaded_at || Date.now()),
                    conversionId: file.conversion_id || file.file_id
                }));
            } else if (Array.isArray(data.processed_files)) {
                // Legacy structure: simple array of filenames
                backendFiles = data.processed_files.map(fname => ({
                    name: fname,
                    size: 0,
                    uploadedAt: new Date(),
                    conversionId: null
                }));
            }

            if (backendFiles.length) {
                window.AppConfig.conversations[currentId].files = backendFiles;
                updateUploadedFiles();
                window.DOMManager.updateInputState();
            }
            
            console.log('✅ [API] Files synced successfully');
        })
        .catch(error => {
            console.error('❌ [API] Error syncing files:', error);
        });
}

// Remove uploaded file
function removeFile(index) {
    const currentId = window.AppConfig.getCurrentConversationId();
    if (!currentId || !window.AppConfig.conversations[currentId]?.files) return;
    
    // Remove from local storage
    window.AppConfig.conversations[currentId].files.splice(index, 1);
    updateUploadedFiles();
    window.DOMManager.updateInputState();
    
    // TODO: Add backend API call to remove file from server
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    window.AppConfig.elementsCache['upload-area'].classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    window.AppConfig.elementsCache['upload-area'].classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    window.AppConfig.elementsCache['upload-area'].classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files } });
    }
}

// Export upload functions
window.UploadManager = {
    openUploadModal,
    closeUploadModal,
    resetUploadModal,
    handleFileSelect,
    uploadFile,
    updateProgress,
    updateUploadedFiles,
    syncFilesWithBackend,
    removeFile,
    handleDragOver,
    handleDragLeave,
    handleDrop
};

console.log('✅ Upload.js loaded'); 