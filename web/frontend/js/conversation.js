// Conversation Management Module
console.log('🚀 Loading conversation.js...');

// Create new conversation
function createNewConversation() {
    console.log('🔄 [API] Creating new conversation...');
    window.DOMManager.showLoading('Creating new conversation...');
    
    console.log('🌐 [API] Sending POST request to:', `${window.AppConfig.API_BASE_URL}/conversations`);
    fetch(`${window.AppConfig.API_BASE_URL}/conversations`, {
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
        
        window.AppConfig.setCurrentConversationId(data.conversation_id);
        window.AppConfig.conversations[data.conversation_id] = {
            id: data.conversation_id,
            title: 'New Conversation',
            messages: [],
            files: [],
            createdAt: new Date()
        };
        
        // Defer UI list refresh until after we successfully switch
        switchToConversation(data.conversation_id);
        
        window.MessageManager.showWelcomeMessage();
        
        window.DOMManager.hideLoading();
        window.DOMManager.showSuccess('New conversation created!');
        console.log('✅ [API] Conversation created successfully');
    })
    .catch(error => {
        console.error('❌ [API] Error creating conversation:', error);
        window.DOMManager.hideLoading();
        window.DOMManager.showError('Failed to create conversation: ' + error.message);
    });
}

// Switch to conversation
function switchToConversation(conversationId) {
    const conversation = window.AppConfig.conversations[conversationId];
    
    if (!conversation) {
        window.DOMManager.showError(`Conversation ${conversationId} not found`);
        // Try to create a new conversation as fallback
        createNewConversation();
        return;
    }
    
    // Validate conversation with backend before switching
    console.log('🔍 [API] Validating conversation with backend:', conversationId);
    console.log('🌐 [API] Sending GET request to:', `${window.AppConfig.API_BASE_URL}/conversations/${conversationId}/validate`);
    
    fetch(`${window.AppConfig.API_BASE_URL}/conversations/${conversationId}/validate`)
        .then(response => {
            console.log('📥 [API] Validate conversation response received:', response);
            console.log('📊 [API] Response status:', response.status, response.statusText);
            console.log('✅ [API] Response ok:', response.ok);
            
            if (!response.ok) {
                throw new Error(`Conversation not found in backend`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📋 [API] Validate conversation data:', data);
            
            // Set current conversation
            window.AppConfig.setCurrentConversationId(conversationId);
            
            // Update UI
            updateConversationTitle(conversation.title);
            window.MessageManager.clearMessages();
            
            // Load conversation messages
            loadConversationMessages(conversation);
            
            // Refresh conversations list so active highlighting follows the selected conversation
            updateConversationsList();
            
            // Immediately refresh uploaded-files UI for the selected conversation
            if (window.UploadManager && window.UploadManager.updateUploadedFiles) {
                window.UploadManager.updateUploadedFiles();
            }
            
            // Then sync with backend (may modify the list later)
            window.UploadManager.syncFilesWithBackend();
            
            // Update input state
            window.DOMManager.updateInputState();
            
            console.log('✅ [API] Switched to conversation successfully');
        })
        .catch(error => {
            console.error('❌ [API] Error validating conversation:', error);
            window.DOMManager.showError('Conversation validation failed: ' + error.message);
            
            // Remove invalid conversation from local storage
            delete window.AppConfig.conversations[conversationId];
            updateConversationsList();
            
            // Try to create a new conversation as fallback
            createNewConversation();
        });
}

// Update conversations list in sidebar
function updateConversationsList() {
    const container = window.AppConfig.elementsCache['conversations-container'];
    const currentId = window.AppConfig.getCurrentConversationId();
    
    // Remove active class from all items
    container.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to current conversation
    const currentItem = container.querySelector(`[data-conversation-id="${currentId}"]`);
    if (currentItem) {
        currentItem.classList.add('active');
        return; // Don't rebuild if just updating active state
    }
    
    // Only rebuild if conversation doesn't exist
    container.innerHTML = '';
    
    const sortedConversations = Object.values(window.AppConfig.conversations)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
    sortedConversations.forEach(conversation => {
        const item = document.createElement('div');
        item.className = `conversation-item ${conversation.id === currentId ? 'active' : ''}`;
        item.setAttribute('data-conversation-id', conversation.id);
        item.onclick = () => switchToConversation(conversation.id);
        
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        const preview = lastMessage 
            ? (lastMessage.type === 'user' ? lastMessage.content : 'Bot response')
            : 'No messages yet';
        
        item.innerHTML = `
            <h4>${conversation.title}</h4>
            <p>${window.Utils.truncateText(preview, 50)}</p>
        `;
        
        container.appendChild(item);
    });
}

// Update conversation title
function updateConversationTitle(title) {
    const titleElement = window.AppConfig.elementsCache['current-conversation-title'];
    const idElement = window.AppConfig.elementsCache['current-conversation-id'];
    
    if (titleElement) {
        titleElement.textContent = title;
    }
    
    if (idElement) {
        idElement.textContent = window.AppConfig.getCurrentConversationId() || '';
    }
}

// Load conversation messages
function loadConversationMessages(conversation) {
    if (!conversation.messages || conversation.messages.length === 0) {
        window.MessageManager.showWelcomeMessage();
        return;
    }
    
    conversation.messages.forEach(message => {
        window.MessageManager.addMessageToUI(message.content, message.type, false);
    });
    
    // Scroll to bottom after loading messages
    setTimeout(() => {
        window.DOMManager.scrollToBottom();
    }, 100);
}

// Load conversations from localStorage
function loadConversations() {
    console.log('🔄 Loading conversations from localStorage...');
    try {
        const saved = localStorage.getItem('excel-chatbot-conversations');
        if (saved) {
            const parsed = JSON.parse(saved);
            window.AppConfig.conversations = parsed.conversations || {};
            window.AppConfig.setCurrentConversationId(parsed.currentConversationId || null);
            
            console.log('✅ Loaded conversations from localStorage:', Object.keys(window.AppConfig.conversations).length);
        }
    } catch (error) {
        console.error('❌ Error loading conversations from localStorage:', error);
        window.AppConfig.conversations = {};
        window.AppConfig.setCurrentConversationId(null);
    }
    
    updateConversationsList();
}

// Save conversations to localStorage
function saveConversations() {
    try {
        const data = {
            conversations: window.AppConfig.conversations,
            currentConversationId: window.AppConfig.getCurrentConversationId(),
            lastSaved: new Date().toISOString()
        };
        const dataStr = JSON.stringify(data);
        try {
            if (dataStr.length > 5_000_000) { // ~5 MB
                console.warn('Conversation data too large, cleaning up old conversations');
                cleanupOldConversations();
            }
            localStorage.setItem('excel-chatbot-conversations', dataStr);
            console.log('✅ Conversations saved to localStorage');
        } catch (error) {
            console.error('❌ Error saving conversations to localStorage:', error);
            if (error.name === 'QuotaExceededError') {
                cleanupOldConversations();
            }
        }
    } catch (error) {
        console.error('❌ Error saving conversations to localStorage:', error);
    }
}

// Initialize conversation state
function initializeConversationState() {
    console.log('🔄 Initializing conversation state...');
    
    const currentId = window.AppConfig.getCurrentConversationId();
    
    if (currentId && window.AppConfig.conversations[currentId]) {
        // Validate and switch to current conversation
        switchToConversation(currentId);
    } else if (Object.keys(window.AppConfig.conversations).length > 0) {
        // Switch to most recent conversation
        const mostRecent = Object.values(window.AppConfig.conversations)
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];
        switchToConversation(mostRecent.id);
    } else {
        // Create first conversation
        createNewConversation();
    }
    
    // Validate all conversations with backend
    validateConversationsWithBackend();
    
    // Clean up old conversations periodically
    cleanupOldConversations();
    
    console.log('✅ Conversation state initialized');
}

// Validate conversations with backend
async function validateConversationsWithBackend() {
    console.log('🔄 [API] Validating conversations one-by-one (GET) …');

    const conversationIds = Object.keys(window.AppConfig.conversations);
    if (conversationIds.length === 0) return;

    for (const id of conversationIds) {
        try {
            console.log('🌐 [API] Validating', id, 'via GET');
            const resp = await fetch(`${window.AppConfig.API_BASE_URL}/conversations/${id}/validate`);
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
        } catch (err) {
            console.warn('🗑️ Removing invalid conversation:', id, err);
            delete window.AppConfig.conversations[id];
        }
    }

    updateConversationsList();
    saveConversations();
    console.log('✅ [API] Validation loop complete');
}

// Clean up old conversations (keep only last 5)
function cleanupOldConversations() {
    const conversations = Object.values(window.AppConfig.conversations);
    const maxConversations = 5;
    
    if (conversations.length > maxConversations) {
        console.log(`🧹 Cleaning up old conversations (keeping ${maxConversations} most recent)`);
        
        // Sort by creation date and keep only the most recent ones
        const sortedConversations = conversations
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            .slice(0, maxConversations);
        
        // Rebuild conversations object with only recent ones
        const newConversations = {};
        sortedConversations.forEach(conv => {
            newConversations[conv.id] = conv;
        });
        
        window.AppConfig.conversations = newConversations;
        saveConversations();
        updateConversationsList();
        
        console.log(`✅ Cleanup complete. Conversations: ${Object.keys(newConversations).length}`);
    }
}

// Auto-save conversations periodically
setInterval(() => {
    saveConversations();
}, 5000); // Save every 5 seconds

// Save conversations before page unload
window.addEventListener('beforeunload', () => {
    saveConversations();
});

// Export conversation functions
window.ConversationManager = {
    createNewConversation,
    switchToConversation,
    updateConversationsList,
    updateConversationTitle,
    loadConversationMessages,
    loadConversations,
    saveConversations,
    initializeConversationState,
    validateConversationsWithBackend,
    cleanupOldConversations
};

console.log('✅ Conversation.js loaded'); 