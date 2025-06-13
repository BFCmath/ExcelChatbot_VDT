// API Communication Module
console.log('🚀 Loading api.js...');

// Send message to backend
function sendMessage() {
    const input = window.AppConfig.elementsCache['message-input'];
    const message = input.value.trim();
    const currentId = window.AppConfig.getCurrentConversationId();
    
    if (!message || window.AppConfig.getIsSending() || !currentId) {
        return;
    }
    
    // Check if conversation has files
    const conversation = window.AppConfig.conversations[currentId];
    if (!conversation?.files?.length) {
        window.DOMManager.showError('Please upload an Excel file first');
        return;
    }
    
    // Update UI state
    window.AppConfig.setIsSending(true);
    window.DOMManager.updateInputState();
    
    // Add user message to UI immediately
    window.MessageManager.addMessageToUI(message, 'user');
    window.MessageManager.addMessageToConversation(message, 'user');
    
    // Clear input and reset height
    input.value = '';
    input.style.height = 'auto';
    
    // Add typing indicator
    const typingIndicator = window.MessageManager.addTypingIndicator();
    
    // Prepare API request
    const requestData = {
        query: message
    };
    
    console.log('🔄 [API] Sending message...');
    console.log('📤 [API] Request data:', requestData);
    console.log('🌐 [API] Sending POST request to:', `${window.AppConfig.API_BASE_URL}/conversations/${currentId}/query`);
    
    fetch(`${window.AppConfig.API_BASE_URL}/conversations/${currentId}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('📥 [API] Chat response received:', response);
        console.log('📊 [API] Response status:', response.status, response.statusText);
        console.log('✅ [API] Response ok:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📋 [API] Query response data:', data);
        
        // Remove typing indicator
        window.MessageManager.removeTypingIndicator(typingIndicator);
        
        // Handle response using original complex logic
        let responseText = '';
        if (data.results) {
            // Check if data.results is a single object with table data
            if (typeof data.results === 'object' && !Array.isArray(data.results)) {
                // The backend sends: {results: {success: true, results: [actual_table_data]}}
                console.log('🔄 [API] Converting single result object to array format');
                const innerData = data.results;
                if (innerData.results && Array.isArray(innerData.results)) {
                    // Use the inner results array directly
                    const convertedData = {
                        success: innerData.success,
                        results: innerData.results
                    };
                    responseText = window.MessageManager.formatResponse(convertedData);
                } else {
                    // Fallback to original logic if structure is different
                    const convertedData = {
                        success: data.success || data.results.success,
                        results: [data.results]
                    };
                    responseText = window.MessageManager.formatResponse(convertedData);
                }
            } else {
                // Handle array format or pass through as-is
                responseText = window.MessageManager.formatResponse(data);
            }
        } else if (data.message) {
            responseText = data.message;
        } else {
            responseText = 'I received your query but couldn\'t generate a response.';
        }
        
        window.MessageManager.addMessageToUI(responseText, 'bot');
        window.MessageManager.addMessageToConversation(responseText, 'bot');
        
        // Update conversation title if this is the first message
        if (conversation.messages.length <= 2) { // User message + bot response
            updateConversationTitleFromMessage(message, currentId);
        }
        
        console.log('✅ [API] Message sent successfully');
    })
    .catch(error => {
        console.error('❌ [API] Query processing error:', error);
        console.error('❌ [API] Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        
        // Remove typing indicator
        window.MessageManager.removeTypingIndicator(typingIndicator);
        
        // Show error message
        const errorMessage = `I apologize, but I encountered an error while processing your request: ${error.message}`;
        window.MessageManager.addMessageToUI(errorMessage, 'bot');
        window.MessageManager.addMessageToConversation(errorMessage, 'bot');
    })
    .finally(() => {
        console.log('🏁 [API] Query processing completed');
        // Reset UI state
        window.AppConfig.setIsSending(false);
        window.DOMManager.updateInputState();
        
        // Save conversations after each message
        window.ConversationManager.saveConversations();
    });
}

// Update conversation title based on first message
function updateConversationTitleFromMessage(message, conversationId) {
    // Create a meaningful title from the user's first message
    let title = message.length > 30 ? message.substring(0, 30) + '...' : message;
    
    // Clean up the title
    title = title.replace(/[^\w\s]/g, '').trim();
    if (!title) {
        title = 'New Conversation';
    }
    
    // Update conversation
    if (window.AppConfig.conversations[conversationId]) {
        window.AppConfig.conversations[conversationId].title = title;
        window.ConversationManager.updateConversationsList();
        window.ConversationManager.updateConversationTitle(title);
    }
}

// Handle input events
function handleInputChange() {
    const input = window.AppConfig.elementsCache['message-input'];
    
    // Auto-resize textarea
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
    
    // Update button state
    window.DOMManager.updateInputState();
}

// Handle keyboard shortcuts
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!window.AppConfig.elementsCache['send-btn'].disabled) {
            sendMessage();
        }
    }
}

// Export API functions
window.APIManager = {
    sendMessage,
    updateConversationTitleFromMessage,
    handleInputChange,
    handleKeyDown
};

console.log('✅ API.js loaded'); 