// Configuration
console.log('🚀 Script.js is loading...');
const API_BASE_URL = 'http://localhost:5001';

// Global state
let currentConversationId = null;
let conversations = {};
let uploadStates = {}; // Track per-file upload states
let isSending = false;

// DOM elements
const elementsCache = {};

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    setupEventListeners();
    loadConversations();
    initializeConversationState();
});

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
        elementsCache[id] = document.getElementById(id);
    });
}

// Setup all event listeners
function setupEventListeners() {
    // Navigation events
    elementsCache['new-conversation-btn'].addEventListener('click', createNewConversation);
    elementsCache['upload-file-btn'].addEventListener('click', openUploadModal);
    
    // Input events
    elementsCache['message-input'].addEventListener('input', handleInputChange);
    elementsCache['message-input'].addEventListener('keydown', handleKeyDown);
    elementsCache['send-btn'].addEventListener('click', sendMessage);
    
    // Modal events
    setupUploadModal();
    
    // Auto-resize textarea
    elementsCache['message-input'].addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // Scroll to bottom button events
    elementsCache['scroll-to-bottom-btn'].addEventListener('click', scrollToBottom);
    elementsCache['messages-container'].addEventListener('scroll', handleScroll);
}

// Handle input changes
function handleInputChange() {
    const input = elementsCache['message-input'];
    const sendBtn = elementsCache['send-btn'];
    
    // Auto-resize textarea
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
    
    // Enable/disable send button
    const hasText = input.value.trim().length > 0;
    const hasFiles = currentConversationId && conversations[currentConversationId]?.files?.length > 0;
    sendBtn.disabled = !hasText || isSending || !hasFiles;
}

// Handle keyboard shortcuts
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!elementsCache['send-btn'].disabled) {
            sendMessage();
        }
    }
}

// Upload modal setup
function setupUploadModal() {
    const modal = elementsCache['upload-modal'];
    const uploadArea = elementsCache['upload-area'];
    const closeBtn = modal.querySelector('.close');
    
    // Close modal events
    closeBtn.addEventListener('click', closeUploadModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeUploadModal();
    });
    
    // File input event
    elementsCache['file-input'].addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    uploadArea.addEventListener('click', () => elementsCache['file-input'].click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    elementsCache['upload-area'].classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    elementsCache['upload-area'].classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    elementsCache['upload-area'].classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files } });
    }
}

// Conversation management
function createNewConversation() {
    console.log('🔄 [API] Creating new conversation...');
    showLoading('Creating new conversation...');
    
    console.log('🌐 [API] Sending POST request to:', `${API_BASE_URL}/conversations`);
    fetch(`${API_BASE_URL}/conversations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('📥 [API] Create conversation response received:', response);
        console.log('📊 [API] Response status:', response.status, response.statusText);
        console.log('✅ [API] Response ok:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📋 [API] Create conversation data:', data);
        console.log('🆔 [API] New conversation ID:', data.conversation_id);
        
        currentConversationId = data.conversation_id;
        conversations[currentConversationId] = {
            id: currentConversationId,
            title: 'New Conversation',
            messages: [],
            files: [],
            createdAt: new Date()
        };
        
        updateConversationsList();
        switchToConversation(currentConversationId);
        showWelcomeMessage();
        
        hideLoading();
        showSuccess('New conversation created!');
        console.log('✅ [API] Conversation created successfully');
    })
    .catch(error => {
        console.error('❌ [API] Error creating conversation:', error);
        hideLoading();
        showError('Failed to create conversation: ' + error.message);
    });
}

function switchToConversation(conversationId) {
    const conversation = conversations[conversationId];
    
    if (!conversation) {
        showError(`Conversation ${conversationId} not found`);
        // Try to create a new conversation as fallback
        createNewConversation();
        return;
    }
    
    // Validate conversation with backend before switching
    console.log('🔍 [API] Validating conversation with backend:', conversationId);
    console.log('🌐 [API] Sending GET request to:', `${API_BASE_URL}/conversations/${conversationId}/validate`);
    
    fetch(`${API_BASE_URL}/conversations/${conversationId}/validate`)
        .then(response => {
            console.log('📥 [API] Validate conversation response received:', response);
            console.log('📊 [API] Response status:', response.status, response.statusText);
            console.log('✅ [API] Response ok:', response.ok);
            
            if (!response.ok) {
                throw new Error(`Conversation not found in backend`);
            }
            return response.json();
        })
        .then(() => {
            console.log('✅ [API] Conversation validation successful for:', conversationId);
            // Conversation is valid, proceed with switch
            currentConversationId = conversationId;
            
            // Update UI
            elementsCache['current-conversation-title'].textContent = conversation.title;
            elementsCache['current-conversation-id'].textContent = `ID: ${conversationId}`;
            
            // Update conversations list
            updateConversationsList();
            
            // Clear and load messages
            clearMessages();
            if (conversation.messages.length === 0) {
                showWelcomeMessage();
            } else {
                conversation.messages.forEach(message => {
                    addMessageToUI(message.content, message.type, false);
                });
            }
            
            // Update uploaded files and sync with backend
            syncFilesWithBackend();
            updateInputState();
        })
        .catch(error => {
            console.error('❌ [API] Error validating conversation:', conversationId, error);
            console.error(`Error switching to conversation ${conversationId}:`, error);
            
            // Remove invalid conversation from frontend
            delete conversations[conversationId];
            saveConversations();
            updateConversationsList();
            
            showError(`Conversation expired or invalid. Creating a new one.`);
            
            // Create new conversation as fallback
            createNewConversation();
        });
}

function updateConversationsList() {
    const container = elementsCache['conversations-container'];
    
    // Remove active class from all items
    container.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to current conversation
    const currentItem = container.querySelector(`[data-conversation-id="${currentConversationId}"]`);
    if (currentItem) {
        currentItem.classList.add('active');
        return; // Don't rebuild if just updating active state
    }
    
    // Only rebuild if conversation doesn't exist
    container.innerHTML = '';
    
    const sortedConversations = Object.values(conversations)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
    sortedConversations.forEach(conversation => {
        const item = document.createElement('div');
        item.className = `conversation-item ${conversation.id === currentConversationId ? 'active' : ''}`;
        item.setAttribute('data-conversation-id', conversation.id);
        item.onclick = () => switchToConversation(conversation.id);
        
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        const preview = lastMessage 
            ? (lastMessage.type === 'user' ? lastMessage.content : 'Bot response')
            : 'No messages yet';
        
        item.innerHTML = `
            <h4>${conversation.title}</h4>
            <p>${truncateText(preview, 50)}</p>
        `;
        
        container.appendChild(item);
    });
}

// File upload handling
function openUploadModal() {
    if (!currentConversationId) {
        showError('Please create a conversation first');
        return;
    }
    elementsCache['upload-modal'].style.display = 'block';
}

function closeUploadModal() {
    elementsCache['upload-modal'].style.display = 'none';
    resetUploadModal();
}

function resetUploadModal() {
    elementsCache['file-input'].value = '';
    elementsCache['upload-progress'].style.display = 'none';
    elementsCache['upload-area'].style.display = 'block';
    elementsCache['upload-area'].classList.remove('dragover');
    updateProgress(0);
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length === 0) return;
    
    const file = files[0];
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        showError('Please select an Excel file (.xlsx or .xls)');
        return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
    }
    
    uploadFile(file);
}

function uploadFile(file) {
    const fileId = file.name + '_' + file.lastModified;
    if (uploadStates[fileId]) return;
    
    console.log('📤 [API] Starting file upload:', file.name);
    console.log('📊 [API] File details:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
    });
    console.log('🆔 [API] Upload conversation ID:', currentConversationId);
    
    // Validate file type and size before upload
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        console.error('❌ [API] Invalid file type:', file.name);
        showError('Please upload only Excel files (.xlsx or .xls)');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        console.error('❌ [API] File too large:', file.size, 'bytes');
        showError('File size too large. Maximum size is 50MB.');
        return;
    }
    
    uploadStates[fileId] = true;
    elementsCache['upload-area'].style.display = 'none';
    elementsCache['upload-progress'].style.display = 'block';
    
    // Create FormData with proper handling for Excel files
    const formData = new FormData();
    
    // Append file as binary data (this preserves Excel structure)
    formData.append('file', file, file.name);
    formData.append('conversation_id', currentConversationId);
    
    console.log('📦 [API] FormData created with file and conversation_id');
    console.log('🌐 [API] Sending POST request to:', `${API_BASE_URL}/upload`);
    
    // Simulate progress for better UX
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        updateProgress(progress);
    }, 200);
    
    // Enhanced fetch with better error handling
    fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it automatically for FormData
        // This ensures proper multipart/form-data boundary is set
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
        
        // Add file to conversation
        if (!conversations[currentConversationId].files) {
            conversations[currentConversationId].files = [];
        }
        conversations[currentConversationId].files.push({
            name: file.name,
            size: file.size,
            uploadedAt: new Date()
        });
        
        updateUploadedFiles();
        updateInputState();
        closeUploadModal();
        showSuccess(`File "${file.name}" uploaded successfully!`);
        console.log('✅ [API] File upload completed successfully');
        
        // Update conversation title if it's still "New Conversation"
        if (conversations[currentConversationId].title === 'New Conversation') {
            conversations[currentConversationId].title = `Chat with ${file.name}`;
            updateConversationsList();
            elementsCache['current-conversation-title'].textContent = conversations[currentConversationId].title;
            console.log('🏷️ [API] Updated conversation title to:', conversations[currentConversationId].title);
        }
    })
    .catch(error => {
        console.error('❌ [API] File upload error:', error);
        clearInterval(progressInterval);
        showError('Failed to upload file: ' + error.message);
    })
    .finally(() => {
        delete uploadStates[fileId];
        setTimeout(resetUploadModal, 1000);
    });
}

function updateProgress(percent) {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
}

function updateUploadedFiles() {
    const container = elementsCache['uploaded-files'];
    const messagesContainer = elementsCache['messages-container'];
    container.innerHTML = '';
    
    if (!currentConversationId || !conversations[currentConversationId]?.files) {
        // Remove has-files class when no files
        messagesContainer.classList.remove('has-files');
        return;
    }
    
    const files = conversations[currentConversationId].files;
    
    // Add or remove has-files class based on file presence
    if (files.length > 0) {
        messagesContainer.classList.add('has-files');
    } else {
        messagesContainer.classList.remove('has-files');
    }
    
    files.forEach((file, index) => {
        const fileElement = document.createElement('div');
        fileElement.className = 'uploaded-file';
        fileElement.innerHTML = `
            <i class="fas fa-file-excel"></i>
            <span>${file.name}</span>
            <i class="fas fa-times remove-file" onclick="removeFile(${index})"></i>
        `;
        container.appendChild(fileElement);
    });
}

function syncFilesWithBackend() {
    if (!currentConversationId) return;
    
    console.log('🔄 [API] Syncing files with backend for conversation:', currentConversationId);
    console.log('🌐 [API] Sending GET request to:', `${API_BASE_URL}/conversations/${currentConversationId}/files`);
    
    fetch(`${API_BASE_URL}/conversations/${currentConversationId}/files`)
    .then(response => {
        console.log('📥 [API] Sync files response received:', response);
        console.log('📊 [API] Response status:', response.status, response.statusText);
        console.log('✅ [API] Response ok:', response.ok);
        return response.json();
    })
    .then(data => {
        console.log('📋 [API] Sync files data:', data);
        console.log('📁 [API] Processed files:', data.processed_files);
        
        if (data.processed_files) {
            // Sync frontend files with backend
            const backendFiles = data.processed_files.map(filename => ({
                name: filename,
                size: 0, // Size not available from backend
                uploadedAt: new Date()
            }));
            
            conversations[currentConversationId].files = backendFiles;
            updateUploadedFiles();
            updateInputState();
            console.log('✅ [API] Files synced successfully');
        }
    })
    .catch(error => {
        console.error('❌ [API] Error syncing files with backend:', error);
    });
}

function removeFile(index) {
    if (!currentConversationId || !conversations[currentConversationId]?.files) return;
    
    conversations[currentConversationId].files.splice(index, 1);
    updateUploadedFiles();
    updateInputState();
}

// Message handling
function sendMessage() {
    const input = elementsCache['message-input'];
    const message = input.value.trim();
    
    console.log('💬 [API] Sending message:', message);
    console.log('🆔 [API] Current conversation ID:', currentConversationId);
    
    if (!message || isSending) return;
    
    if (!currentConversationId) {
        console.error('❌ [API] No conversation ID available');
        showError('Please create a conversation first');
        return;
    }
    
    const hasFiles = conversations[currentConversationId]?.files?.length > 0;
    console.log('📁 [API] Has files:', hasFiles);
    console.log('📊 [API] Files count:', conversations[currentConversationId]?.files?.length || 0);
    
    if (!hasFiles) {
        console.error('❌ [API] No files uploaded');
        showError('Please upload an Excel file first');
        return;
    }
    
    isSending = true;
    updateInputState();
    
    // Add user message to UI
    addMessageToUI(message, 'user');
    addMessageToConversation(message, 'user');
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    console.log('🌐 [API] Sending POST request to:', `${API_BASE_URL}/conversations/${currentConversationId}/query`);
    console.log('📦 [API] Request payload:', { query: message });
    
    // Send to API
    fetch(`${API_BASE_URL}/conversations/${currentConversationId}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: message })
    })
    .then(response => {
        console.log('📥 [API] Query response received:', response);
        console.log('📊 [API] Response status:', response.status, response.statusText);
        console.log('✅ [API] Response ok:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        removeTypingIndicator(typingIndicator);
        
        // Add comprehensive logging of API response
        console.log('=== RAW API RESPONSE ===');
        console.log('Full API response:', data);
        console.log('API response stringified:', JSON.stringify(data, null, 2));
        console.log('data.results exists:', !!data.results);
        console.log('data.results type:', typeof data.results);
        console.log('data.results is array:', Array.isArray(data.results));
        console.log('data.success:', data.success);
        
        if (data.results) {
            if (Array.isArray(data.results) && data.results.length > 0) {
                console.log('📋 [API] Processing results array with length:', data.results.length);
                data.results.forEach((result, resultIndex) => {
                    console.log(`Result ${resultIndex}:`, result);
                    console.log(`Result ${resultIndex} has table_info:`, !!result.table_info);
                    console.log(`Result ${resultIndex} has flattened_table_info:`, !!result.flattened_table_info);
                });
            } else {
                console.error('❌ [API] data.results is not an array:', data.results);
                console.log('❌ [API] data.results constructor:', data.results.constructor.name);
                console.log('❌ [API] data.results keys:', Object.keys(data.results));
            }
        }
        
        let responseText = '';
        if (data.results) {
            // Check if data.results is a single object with table data
            if (typeof data.results === 'object' && !Array.isArray(data.results)) {
                // The backend sends: {results: {success: true, results: [actual_table_data]}}
                // We need to extract the inner structure properly
                console.log('🔄 [API] Converting single result object to array format');
                const innerData = data.results;
                if (innerData.results && Array.isArray(innerData.results)) {
                    // Use the inner results array directly
                    const convertedData = {
                        success: innerData.success,
                        results: innerData.results  // Use the actual results array
                    };
                    responseText = formatResponse(convertedData);
                } else {
                    // Fallback to original logic if structure is different
                    const convertedData = {
                        success: data.success || data.results.success,
                        results: [data.results]
                    };
                    responseText = formatResponse(convertedData);
                }
            } else {
                // Handle array format or pass through as-is
                responseText = formatResponse(data);
            }
        } else if (data.message) {
            responseText = data.message;
        } else {
            responseText = 'I received your query but couldn\'t generate a response.';
        }
        
        addMessageToUI(responseText, 'bot');
        addMessageToConversation(responseText, 'bot');
    })
    .catch(error => {
        console.error('❌ [API] Query processing error:', error);
        console.error('❌ [API] Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        
        removeTypingIndicator(typingIndicator);
        const errorMessage = `I apologize, but I encountered an error while processing your request: ${error.message}`;
        addMessageToUI(errorMessage, 'bot');
        addMessageToConversation(errorMessage, 'bot');
    })
    .finally(() => {
        console.log('🏁 [API] Query processing completed');
        isSending = false;
        updateInputState();
    });
}

function formatResponse(result) {
    console.log('formatResponse called with:', result);
    console.log('formatResponse result type:', typeof result);
    console.log('formatResponse result.success:', result.success);
    console.log('formatResponse result.results:', result.results);
    
    if (typeof result === 'string') {
        return result;
    }
    
    if (typeof result === 'object') {
        // Handle structured query response format (both array and converted single object)
        if (result.success !== undefined && result.results) {
            console.log('🎯 [API] Processing structured response with formatQueryResults');
            return formatQueryResults(result);
        }
        
        // Handle legacy structured data
        if (result.answer) {
            return result.answer;
        }
        
        if (result.data) {
            // Format tabular data
            if (Array.isArray(result.data)) {
                return formatTableData(result.data);
            }
            return JSON.stringify(result.data, null, 2);
        }
        
        // Fallback to JSON display for debugging
        console.log('⚠️ [API] Falling back to JSON display for unrecognized format');
        return `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }
    
    return String(result);
}

function formatQueryResults(response) {
    console.log('formatQueryResults called with:', response);
    
    // Add comprehensive console logging for table data
    console.log('=== FULL RESPONSE STRUCTURE ===');
    console.log('Response:', JSON.stringify(response, null, 2));
    
    // ADDITIONAL DEBUGGING: Let's trace exactly what we receive
    console.log('🔍 [DEBUG] response keys:', Object.keys(response));
    console.log('🔍 [DEBUG] response.results type:', typeof response.results);
    console.log('🔍 [DEBUG] response.results Array.isArray:', Array.isArray(response.results));
    if (response.results && response.results.length > 0) {
        console.log('🔍 [DEBUG] First result keys:', Object.keys(response.results[0]));
        console.log('🔍 [DEBUG] First result flattened_table_info exists:', 'flattened_table_info' in response.results[0]);
        console.log('🔍 [DEBUG] First result flattened_table_info value:', response.results[0].flattened_table_info);
    }
    
    if (!response.success) {
        return `<div class="error-message">Error: ${response.error || 'Unknown error'}</div>`;
    }

    let html = '<div class="query-results">';
    
    if (response.results && Array.isArray(response.results) && response.results.length > 0) {
        console.log('📋 [API] Processing results array with length:', response.results.length);
        response.results.forEach((result, resultIndex) => {
            console.log(`=== RESULT ${resultIndex} ===`);
            console.log('Result object:', result);
            
            // Log normal table info
            if (result.table_info) {
                console.log('=== NORMAL TABLE INFO ===');
                console.log('Normal table_info:', JSON.stringify(result.table_info, null, 2));
                console.log('Normal final_columns:', result.table_info.final_columns);
                console.log('Normal data_rows:', result.table_info.data_rows);
                console.log('Normal header_matrix:', result.table_info.header_matrix);
            }
            
            // Log flattened table info
            if (result.flattened_table_info) {
                console.log('=== FLATTENED TABLE INFO ===');
                console.log('Flattened table_info:', JSON.stringify(result.flattened_table_info, null, 2));
                console.log('Flattened final_columns:', result.flattened_table_info.final_columns);
                console.log('Flattened data_rows:', result.flattened_table_info.data_rows);
                console.log('Flattened header_matrix:', result.flattened_table_info.header_matrix);
            } else {
                console.log('=== NO FLATTENED TABLE INFO ===');
                console.log('flattened_table_info is:', result.flattened_table_info);
            }
            
            html += `<div class="result-section">`;
            html += `<h4>File: ${result.filename}</h4>`;
            html += `<p><strong>Query:</strong> ${result.query}</p>`;
            
            if (result.success && result.table_info) {
                // Check if we have both normal and flattened table data
                const hasFlattened = result.flattened_table_info && 
                                   result.flattened_table_info.final_columns && 
                                   result.flattened_table_info.final_columns.length > 0;
                                   
                console.log('HasFlattened:', hasFlattened);
                
                if (hasFlattened) {
                    // Create container with toggle button for tables that have flattened version
                    html += `<div class="table-toggle-container" data-result-index="${resultIndex}">`;
                    html += `<div class="table-controls">`;
                    html += `<button class="table-toggle-btn" data-mode="hierarchical" title="Switch to flattened headers">`;
                    html += `<i class="fas fa-layer-group"></i> Hierarchical View`;
                    html += `</button>`;
                    html += `</div>`;
                    
                    // Normal table (initially visible)
                    html += `<div class="table-view hierarchical-view active">`;
                    html += createHierarchicalHtmlTable(result.table_info, result.filename);
                    html += `</div>`;
                    
                    // Flattened table (initially hidden)
                    html += `<div class="table-view flattened-view">`;
                    html += createHierarchicalHtmlTable(result.flattened_table_info, result.filename);
                    html += `</div>`;
                    
                    html += `</div>`;
                } else {
                    // Regular table without flattened option
                    html += createHierarchicalHtmlTable(result.table_info, result.filename);
                }
            } else {
                html += `<p class="no-data">${result.message || 'No data found'}</p>`;
            }
            
            html += `</div>`;
        });
    }
    
    // Handle case where results is not an array but still contains data
    else if (response.results && !Array.isArray(response.results)) {
        console.log('⚠️ [API] response.results is not an array, attempting to handle as single result');
        console.log('📋 [API] Single result data:', response.results);
        
        // Try to treat it as a single result object
        const result = response.results;
        html += `<div class="result-section">`;
        html += `<h4>File: ${result.filename || 'Unknown'}</h4>`;
        html += `<p><strong>Query:</strong> ${result.query || 'Unknown'}</p>`;
        
        if (result.success && result.table_info) {
            const hasFlattened = result.flattened_table_info && 
                               result.flattened_table_info.final_columns && 
                               result.flattened_table_info.final_columns.length > 0;
                               
            if (hasFlattened) {
                html += `<div class="table-toggle-container" data-result-index="0">`;
                html += `<div class="table-controls">`;
                html += `<button class="table-toggle-btn" data-mode="hierarchical" title="Switch to flattened headers">`;
                html += `<i class="fas fa-layer-group"></i> Hierarchical View`;
                html += `</button>`;
                html += `</div>`;
                
                html += `<div class="table-view hierarchical-view active">`;
                html += createHierarchicalHtmlTable(result.table_info, result.filename);
                html += `</div>`;
                
                html += `<div class="table-view flattened-view">`;
                html += createHierarchicalHtmlTable(result.flattened_table_info, result.filename);
                html += `</div>`;
                
                html += `</div>`;
            } else {
                html += createHierarchicalHtmlTable(result.table_info, result.filename);
            }
        } else {
            html += `<p class="no-data">${result.message || 'No data found'}</p>`;
        }
        
        html += `</div>`;
    }
    
    // Handle case where no results are found
    else {
        console.log('⚠️ [API] No valid results found in response');
        html += `<div class="no-data">No results found in the response.</div>`;
    }
    
    html += '</div>';
    return html;
}

function createHierarchicalHtmlTable(tableInfo, filename) {
    if (!tableInfo || !tableInfo.data_rows || tableInfo.data_rows.length === 0) {
        return '<p class="no-data">No data to display</p>';
    }

    const { has_multiindex, header_matrix, final_columns, data_rows, row_count, col_count } = tableInfo;
    
    let html = '<div class="table-container">';
    html += `<div class="table-info">Showing ${row_count} rows × ${col_count} columns`;
    if (row_count > 100) {
        html += ` (first 100 rows displayed)`;
    }
    html += '</div>';
    
    // Wrap the table in a table-wrapper for horizontal scrolling
    html += '<div class="table-wrapper">';
    html += '<table class="data-table hierarchical-table">';
    
    // Generate header section with proper rowspan and colspan
    html += '<thead>';
    
    if (has_multiindex && header_matrix && header_matrix.length > 1) {
        // Multi-level headers with merged cells (both rowspan and colspan)
        // Track cells that should be skipped due to rowspan from previous levels
        const skipMatrix = Array(header_matrix.length).fill(null).map(() => Array(col_count).fill(false));
        
        header_matrix.forEach((level, levelIndex) => {
            html += '<tr class="header-level-' + levelIndex + '">';
            
            let currentPosition = 0;
            level.forEach(header => {
                // Skip positions that are covered by rowspan from previous levels
                while (currentPosition < col_count && skipMatrix[levelIndex][currentPosition]) {
                    currentPosition++;
                }
                
                if (currentPosition >= col_count) return;
                
                // Only render cells that should be displayed (not hidden by spanning)
                const colspanAttr = header.colspan > 1 ? ` colspan="${header.colspan}"` : '';
                const rowspanAttr = header.rowspan > 1 ? ` rowspan="${header.rowspan}"` : '';
                const headerText = header.text || '';
                
                // Determine header class based on level and spanning
                let levelClass = 'sub-level-header';
                if (levelIndex === 0) {
                    levelClass = 'top-level-header';
                }
                if (header.rowspan > 1) {
                    levelClass += ' vertical-span';
                }
                if (header.colspan > 1) {
                    levelClass += ' horizontal-span';
                }
                
                html += `<th class="${levelClass}"${colspanAttr}${rowspanAttr}>${escapeHtml(headerText)}</th>`;
                
                // Mark positions as occupied due to this cell's span
                for (let r = levelIndex; r < levelIndex + header.rowspan && r < skipMatrix.length; r++) {
                    for (let c = currentPosition; c < currentPosition + header.colspan && c < col_count; c++) {
                        if (r > levelIndex) { // Don't mark the current cell as skipped
                            skipMatrix[r][c] = true;
                        }
                    }
                }
                
                currentPosition += header.colspan;
            });
            
            html += '</tr>';
        });
    } else {
        // Simple single-level headers
        html += '<tr>';
        final_columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '</tr>';
    }
    
    html += '</thead>';
    
    // Generate body section
    html += '<tbody>';
    const maxRows = Math.min(data_rows.length, 100);
    
    for (let i = 0; i < maxRows; i++) {
        const row = data_rows[i];
        html += '<tr>';
        
        row.forEach((cell, colIndex) => {
            const cellValue = formatCellValue(cell);
            html += `<td>${cellValue}</td>`;
        });
        
        html += '</tr>';
    }
    
    html += '</tbody>';
    html += '</table>';
    html += '</div>'; // Close table-wrapper
    html += '</div>'; // Close table-container
    
    return html;
}

function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '<span class="null-value">—</span>';
    }
    
    if (typeof value === 'number') {
        // Format numbers with proper locale
        if (Number.isInteger(value)) {
            return value.toLocaleString();
        } else {
            return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
    }
    
    if (typeof value === 'string') {
        // Escape HTML and handle long strings
        const escaped = escapeHtml(value);
        if (escaped.length > 50) {
            return `<span title="${escaped}">${escaped.substring(0, 47)}...</span>`;
        }
        return escaped;
    }
    
    return escapeHtml(String(value));
}

function formatTableData(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return 'No data found.';
    }
    
    // Convert simple array data to table format for legacy support
    // This is a fallback for simple data structures
    const tableInfo = {
        has_multiindex: false,
        header_matrix: [[{
            text: 'Data',
            colspan: 1,
            position: 0
        }]],
        final_columns: ['Data'],
        data_rows: data.map(item => [item]),
        row_count: data.length,
        col_count: 1
    };
    
    return createHierarchicalHtmlTable(tableInfo, 'data');
}

function addMessageToUI(content, type, animate = true) {
    const container = elementsCache['messages-container'];
    
    // Check if user was at bottom before adding message
    const wasAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
    
    // Remove welcome message if it exists
    const welcomeMessage = container.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageElement = document.createElement('div');
    messageElement.className = `message ${type} ${animate ? 'fade-in' : ''}`;
    
    const avatar = document.createElement('div');
    avatar.className = `message-avatar ${type}-avatar`;
    avatar.textContent = type === 'user' ? 'U' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Handle different content types
    if (type === 'user') {
        // For user messages, always escape HTML for security
        messageContent.textContent = content;
    } else if (type === 'bot') {
        // For bot messages, check if it's HTML content or plain text
        if (content.includes('<div class="query-results">') || 
            content.includes('<table') || 
            content.includes('<div class="error-message">') ||
            content.includes('<div class="info-message">')) {
            // This is HTML content from our table rendering, render as HTML
            messageContent.innerHTML = content;
            
            // Setup table toggle functionality for this message
            setupTableToggleEvents(messageContent);
        } else if (content.includes('```')) {
            // Handle code blocks
            messageContent.innerHTML = formatCodeBlocks(escapeHtml(content));
        } else {
            // Plain text content, escape HTML
            messageContent.textContent = content;
        }
    } else {
        // Fallback for other types
        messageContent.textContent = content;
    }
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    
    container.appendChild(messageElement);
    
    // Auto-scroll to bottom if user was at bottom, or for user messages
    if (wasAtBottom || type === 'user') {
        setTimeout(() => {
            scrollToBottom();
        }, 100); // Small delay to allow DOM update
    } else {
        // Show scroll-to-bottom button if user wasn't at bottom
        const scrollBtn = elementsCache['scroll-to-bottom-btn'];
        if (scrollBtn) {
            scrollBtn.classList.add('show');
        }
    }
}

function setupTableToggleEvents(container) {
    // Find all table toggle buttons in this container
    const toggleButtons = container.querySelectorAll('.table-toggle-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const toggleContainer = this.closest('.table-toggle-container');
            const hierarchicalView = toggleContainer.querySelector('.hierarchical-view');
            const flattenedView = toggleContainer.querySelector('.flattened-view');
            const currentMode = this.getAttribute('data-mode');
            
            if (currentMode === 'hierarchical') {
                // Switch to flattened view
                hierarchicalView.classList.remove('active');
                flattenedView.classList.add('active');
                this.setAttribute('data-mode', 'flattened');
                this.innerHTML = '<i class="fas fa-list"></i> Flattened View';
                this.setAttribute('title', 'Switch to hierarchical headers');
            } else {
                // Switch to hierarchical view
                flattenedView.classList.remove('active');
                hierarchicalView.classList.add('active');
                this.setAttribute('data-mode', 'hierarchical');
                this.innerHTML = '<i class="fas fa-layer-group"></i> Hierarchical View';
                this.setAttribute('title', 'Switch to flattened headers');
            }
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatCodeBlocks(content) {
    return content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
}

function addMessageToConversation(content, type) {
    if (!currentConversationId) return;
    
    conversations[currentConversationId].messages.push({
        content,
        type,
        timestamp: new Date()
    });
    
    updateConversationsList();
}

function addTypingIndicator() {
    const container = elementsCache['messages-container'];
    const indicator = document.createElement('div');
    indicator.className = 'message bot typing-message';
    indicator.innerHTML = `
        <div class="message-avatar bot-avatar">AI</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span>Thinking...</span>
            </div>
        </div>
    `;
    
    container.appendChild(indicator);
    scrollToBottom();
    return indicator;
}

function removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

function clearMessages() {
    elementsCache['messages-container'].innerHTML = '';
}

function showWelcomeMessage() {
    elementsCache['messages-container'].innerHTML = `
        <div class="welcome-message">
            <div class="welcome-content">
                <i class="fas fa-table welcome-icon"></i>
                <h2>Welcome to Excel Chatbot</h2>
                <p>Upload an Excel file and start asking questions about your data!</p>
                <div class="example-queries">
                    <h4>Try asking:</h4>
                    <ul>
                        <li>"What's the total sum of column A?"</li>
                        <li>"Show me the top 5 rows"</li>
                        <li>"What columns are available?"</li>
                        <li>"Find all rows where column B > 100"</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function scrollToBottom() {
    const container = elementsCache['messages-container'];
    if (!container) return;
    
    // Smooth scroll to bottom
    container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
    });
    
    // Hide the scroll to bottom button
    const scrollBtn = elementsCache['scroll-to-bottom-btn'];
    if (scrollBtn) {
        scrollBtn.classList.remove('show');
    }
}

function handleScroll() {
    const container = elementsCache['messages-container'];
    const scrollBtn = elementsCache['scroll-to-bottom-btn'];
    
    if (!container || !scrollBtn) return;
    
    // Show button if not at bottom (with more tolerance for fixed input)
    const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
    
    if (isAtBottom) {
        scrollBtn.classList.remove('show');
    } else {
        scrollBtn.classList.add('show');
    }
}

// UI state management
function updateInputState() {
    const input = elementsCache['message-input'];
    const sendBtn = elementsCache['send-btn'];
    
    const hasText = input.value.trim().length > 0;
    const hasFiles = currentConversationId && conversations[currentConversationId]?.files?.length > 0;
    
    sendBtn.disabled = !hasText || isSending || !hasFiles;
    
    // Update placeholder
    if (!hasFiles) {
        input.placeholder = 'Please upload an Excel file first...';
        input.disabled = true;
    } else {
        input.placeholder = 'Ask me anything about your Excel data...';
        input.disabled = false;
    }
}

// Utility functions
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

function showLoading(message = 'Loading...') {
    const overlay = elementsCache['loading-overlay'];
    const text = overlay.querySelector('p');
    text.textContent = message;
    overlay.style.display = 'flex';
}

function hideLoading() {
    elementsCache['loading-overlay'].style.display = 'none';
}

function showError(message) {
    showNotification(message, 'error');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `${type}-message`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'check-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to top of messages container
    const container = elementsCache['messages-container'];
    container.insertBefore(notification, container.firstChild);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Load conversations from localStorage (for demo purposes)
function loadConversations() {
    const saved = localStorage.getItem('excel-chatbot-conversations');
    if (saved) {
        try {
            conversations = JSON.parse(saved);
            updateConversationsList();
        } catch (error) {
            console.error('Error loading conversations:', error);
            conversations = {};
        }
    }
}

// Initialize conversation state on app load
function initializeConversationState() {
    const conversationIds = Object.keys(conversations);
    
    if (conversationIds.length === 0) {
        // No conversations exist, create a new one
        createNewConversation();
        return;
    }
    
    // Validate existing conversations with backend
    validateConversationsWithBackend()
        .then(validConversations => {
            if (validConversations.length === 0) {
                // No valid conversations, create a new one
                createNewConversation();
            } else {
                // Switch to the most recent valid conversation
                const mostRecent = validConversations
                    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];
                switchToConversation(mostRecent.id);
            }
        })
        .catch(error => {
            console.error('Error validating conversations:', error);
            // Fallback: create a new conversation
            createNewConversation();
        });
}

// Validate conversations with backend
async function validateConversationsWithBackend() {
    const conversationIds = Object.keys(conversations);
    const validConversations = [];
    
    console.log('🔍 [API] Validating conversations with backend');
    console.log('📋 [API] Conversation IDs to validate:', conversationIds);
    
    for (const id of conversationIds) {
        try {
            console.log(`🔍 [API] Validating conversation: ${id}`);
            console.log('🌐 [API] Sending GET request to:', `${API_BASE_URL}/conversations/${id}/validate`);
            
            const response = await fetch(`${API_BASE_URL}/conversations/${id}/validate`);
            
            console.log(`📥 [API] Validation response for ${id}:`, response);
            console.log(`📊 [API] Response status for ${id}:`, response.status, response.statusText);
            console.log(`✅ [API] Response ok for ${id}:`, response.ok);
            
            if (response.ok) {
                console.log(`✅ [API] Conversation ${id} is valid`);
                validConversations.push(conversations[id]);
            } else {
                // Remove invalid conversation from frontend state
                console.log(`❌ [API] Removing invalid conversation: ${id}`);
                delete conversations[id];
            }
        } catch (error) {
            console.error(`❌ [API] Error validating conversation ${id}:`, error);
            // Remove conversation that can't be validated
            console.log(`🗑️ [API] Removing unvalidatable conversation: ${id}`);
            delete conversations[id];
        }
    }
    
    console.log('📋 [API] Valid conversations found:', validConversations.length);
    console.log('✅ [API] Valid conversation IDs:', validConversations.map(c => c.id));
    
    // Update localStorage with cleaned conversations
    saveConversations();
    updateConversationsList();
    
    return validConversations;
}

// Save conversations to localStorage
function saveConversations() {
    try {
        // Check localStorage quota before saving
        const data = JSON.stringify(conversations);
        if (data.length > 5000000) { // ~5MB limit
            console.warn('Conversation data too large, cleaning up old conversations');
            cleanupOldConversations();
        }
        localStorage.setItem('excel-chatbot-conversations', data);
    } catch (error) {
        console.error('Error saving conversations:', error);
        if (error.name === 'QuotaExceededError') {
            cleanupOldConversations();
        }
    }
}

function cleanupOldConversations() {
    const sorted = Object.values(conversations)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .slice(0, 5); // Keep only 5 most recent
    
    conversations = {};
    sorted.forEach(conv => {
        conversations[conv.id] = conv;
    });
}

// Save conversations periodically
setInterval(saveConversations, 5000);

// Save before page unload
window.addEventListener('beforeunload', saveConversations); 