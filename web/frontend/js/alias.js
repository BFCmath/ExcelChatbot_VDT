// Alias Manager Module
console.log('🚀 Loading alias.js...');

// Global alias state
let aliasStatus = {
    hasAliasFile: false,
    aliasFileInfo: null,
    isUploading: false
};

// Open alias manager modal
function openAliasModal() {
    window.AppConfig.elementsCache['alias-modal'].style.display = 'block';
    loadAliasStatus();
}

// Close alias manager modal
function closeAliasModal() {
    window.AppConfig.elementsCache['alias-modal'].style.display = 'none';
    resetAliasModal();
}

// Reset alias modal state
function resetAliasModal() {
    const sections = ['alias-status', 'alias-no-file', 'alias-has-file', 'alias-upload-area', 'alias-upload-progress'];
    sections.forEach(id => {
        const element = window.AppConfig.elementsCache[id];
        if (element) element.style.display = 'none';
    });
    
    // Reset file input
    const fileInput = window.AppConfig.elementsCache['alias-file-input'];
    if (fileInput) fileInput.value = '';
    
    // Reset upload progress
    updateAliasProgress(0);
}

// Load alias status from backend
async function loadAliasStatus() {
    console.log('🔄 [ALIAS] Loading alias status...');
    
    // Show loading state
    showAliasSection('alias-status');
    
    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/alias/status`);
        
        if (!response.ok) {
            // Get error details from response body if available
            let errorDetail;
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || response.statusText;
            } catch (e) {
                errorDetail = response.statusText;
            }
            throw new Error(`HTTP ${response.status}: ${errorDetail}`);
        }
        
        const data = await response.json();
        console.log('📊 [ALIAS] Status response:', data);
        
        aliasStatus.hasAliasFile = data.has_alias_file;
        aliasStatus.aliasFileInfo = data.alias_file_info;
        
        // Update UI based on status
        if (data.has_alias_file) {
            showAliasFileInfo(data.alias_file_info);
        } else {
            showNoAliasFile();
        }
        
    } catch (error) {
        console.error('❌ [ALIAS] Failed to load status:', error);
        
        // Check if it's a network error vs server error
        if (error.message.includes('fetch')) {
            window.DOMManager.showError('Could not connect to server. Please check if the backend is running.');
        } else if (error.message.includes('500')) {
            window.DOMManager.showError('Server error when checking alias status. Check backend logs for details.');
        } else {
            window.DOMManager.showError('Failed to load alias status: ' + error.message);
        }
        
        showNoAliasFile(); // Fallback to no file state
    }
}

// Show alias file information
function showAliasFileInfo(fileInfo) {
    console.log('📋 [ALIAS] Showing alias file info:', fileInfo);
    
    // Update file details
    const filenameEl = window.AppConfig.elementsCache['alias-filename'];
    const uploadDateEl = window.AppConfig.elementsCache['alias-upload-date'];
    const fileSizeEl = window.AppConfig.elementsCache['alias-file-size'];
    
    if (filenameEl) filenameEl.textContent = fileInfo.filename || 'Unknown file';
    if (uploadDateEl) {
        const uploadDate = new Date(fileInfo.uploaded_at).toLocaleString();
        uploadDateEl.textContent = `Uploaded: ${uploadDate}`;
    }
    if (fileSizeEl) {
        const sizeKB = Math.round(fileInfo.size / 1024);
        fileSizeEl.textContent = `Size: ${sizeKB} KB`;
    }
    
    showAliasSection('alias-has-file');
}

// Show no alias file state
function showNoAliasFile() {
    console.log('📋 [ALIAS] Showing no alias file state');
    showAliasSection('alias-no-file');
}

// Show specific alias section
function showAliasSection(sectionId) {
    const sections = ['alias-status', 'alias-no-file', 'alias-has-file', 'alias-upload-area', 'alias-upload-progress'];
    
    sections.forEach(id => {
        const element = window.AppConfig.elementsCache[id];
        if (element) {
            element.style.display = id === sectionId ? 'block' : 'none';
        }
    });
}

// Show alias upload area
function showAliasUploadArea() {
    showAliasSection('alias-upload-area');
}

// Handle alias file selection
function handleAliasFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadAliasFile(files[0]);
    }
}

// Upload alias file to server
async function uploadAliasFile(file) {
    console.log('📤 [ALIAS] Starting alias file upload:', file.name);
    
    // Validate file type and size
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        console.error('❌ [ALIAS] Invalid file type:', file.name);
        window.DOMManager.showError('Please upload only Excel files (.xlsx or .xls)');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        console.error('❌ [ALIAS] File too large:', file.size, 'bytes');
        window.DOMManager.showError('File size too large. Maximum size is 50MB.');
        return;
    }
    
    if (aliasStatus.isUploading) {
        console.warn('⏳ [ALIAS] Upload already in progress');
        return;
    }
    
    aliasStatus.isUploading = true;
    
    // Show upload progress
    showAliasSection('alias-upload-progress');
    updateAliasProgress(0);
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file, file.name);
    
    console.log('📦 [ALIAS] FormData created');
    console.log('🌐 [ALIAS] Sending POST request to:', `${window.AppConfig.API_BASE_URL}/alias/upload`);
    
    // Simulate progress for better UX
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        updateAliasProgress(progress);
    }, 200);
    
    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/alias/upload`, {
            method: 'POST',
            body: formData
        });
        
        console.log('📥 [ALIAS] Upload response received:', response);
        clearInterval(progressInterval);
        updateAliasProgress(100);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('📋 [ALIAS] Upload success data:', data);
        
        // Update alias status
        aliasStatus.hasAliasFile = true;
        aliasStatus.aliasFileInfo = data.alias_file_info;
        
        // Show success message
        window.DOMManager.showSuccess(data.message || `Alias file "${file.name}" uploaded successfully!`);
        
        // Update UI
        setTimeout(() => {
            showAliasFileInfo(data.alias_file_info);
        }, 1000);
        
        console.log('✅ [ALIAS] File upload completed successfully');
        
    } catch (error) {
        console.error('❌ [ALIAS] File upload error:', error);
        clearInterval(progressInterval);
        window.DOMManager.showError('Failed to upload alias file: ' + error.message);
        
        // Show appropriate section based on current state
        if (aliasStatus.hasAliasFile) {
            showAliasFileInfo(aliasStatus.aliasFileInfo);
        } else {
            showNoAliasFile();
        }
    } finally {
        aliasStatus.isUploading = false;
    }
}

// Remove alias file
async function removeAliasFile() {
    console.log('🗑️ [ALIAS] Removing alias file...');
    
    if (!aliasStatus.hasAliasFile) {
        console.warn('⚠️ [ALIAS] No alias file to remove');
        return;
    }
    
    // Show confirmation
    if (!confirm('Are you sure you want to remove the alias file? This will disable query enrichment for all conversations.')) {
        return;
    }
    
    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/alias`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('📋 [ALIAS] Remove success:', data);
        
        // Update alias status
        aliasStatus.hasAliasFile = false;
        aliasStatus.aliasFileInfo = null;
        
        // Show success message
        window.DOMManager.showSuccess(data.message || 'Alias file removed successfully');
        
        // Update UI
        showNoAliasFile();
        
        console.log('✅ [ALIAS] File removed successfully');
        
    } catch (error) {
        console.error('❌ [ALIAS] Failed to remove file:', error);
        window.DOMManager.showError('Failed to remove alias file: ' + error.message);
    }
}

// Update alias upload progress
function updateAliasProgress(percent) {
    const progressFill = document.querySelector('#alias-upload-progress .progress-fill');
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
}

// Handle drag and drop for alias files
function handleAliasDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    const uploadArea = window.AppConfig.elementsCache['alias-upload-area'];
    if (uploadArea) uploadArea.classList.add('dragover');
}

function handleAliasDragLeave(e) {
    e.preventDefault();
    const uploadArea = window.AppConfig.elementsCache['alias-upload-area'];
    if (uploadArea) uploadArea.classList.remove('dragover');
}

function handleAliasDrop(e) {
    e.preventDefault();
    const uploadArea = window.AppConfig.elementsCache['alias-upload-area'];
    if (uploadArea) uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadAliasFile(files[0]);
    }
}

// Get current alias status
function getAliasStatus() {
    return aliasStatus;
}

// Refresh alias status
async function refreshAliasStatus() {
    await loadAliasStatus();
}

// Export alias functions
window.AliasManager = {
    openAliasModal,
    closeAliasModal,
    resetAliasModal,
    loadAliasStatus,
    showAliasFileInfo,
    showNoAliasFile,
    showAliasUploadArea,
    handleAliasFileSelect,
    uploadAliasFile,
    removeAliasFile,
    updateAliasProgress,
    handleAliasDragOver,
    handleAliasDragLeave,
    handleAliasDrop,
    getAliasStatus,
    refreshAliasStatus
};

console.log('✅ alias.js loaded'); 