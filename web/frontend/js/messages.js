// Message Handling Module
console.log('🚀 Loading messages.js...');

// Add message to UI with optional animation
function addMessageToUI(content, type, animate = true) {
    const container = window.AppConfig.elementsCache['messages-container'];
    
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
    if (typeof content === 'string') {
        if (content.includes('<div class="query-results">')) {
            // This is formatted query results HTML
            messageContent.innerHTML = content;
            // Setup table events after inserting the HTML
            setTimeout(() => {
                window.TableManager.setupTableToggleEvents(messageContent);
                window.TableManager.setupTablePlottingEvents(messageContent);
            }, 100);
        } else {
            // Regular text content
            messageContent.innerHTML = window.Utils.formatCodeBlocks(content);
        }
    } else {
        // Handle non-string content
        messageContent.textContent = String(content);
    }
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    
    container.appendChild(messageElement);
    
    // Auto-scroll to bottom if user was at bottom, or for user messages
    if (wasAtBottom || type === 'user') {
        setTimeout(() => {
            window.DOMManager.scrollToBottom();
        }, 100); // Small delay to allow DOM update
    } else {
        // Show scroll-to-bottom button if user wasn't at bottom
        const scrollBtn = window.AppConfig.elementsCache['scroll-to-bottom-btn'];
        if (scrollBtn) {
            scrollBtn.classList.add('show');
        }
    }
}

// Add message to conversation history
function addMessageToConversation(content, type) {
    const currentId = window.AppConfig.getCurrentConversationId();
    if (!currentId) return;
    
    window.AppConfig.conversations[currentId].messages.push({
        content,
        type,
        timestamp: new Date()
    });
    
    window.ConversationManager.updateConversationsList();
}

// Add typing indicator
function addTypingIndicator() {
    const container = window.AppConfig.elementsCache['messages-container'];
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
    window.DOMManager.scrollToBottom();
    return indicator;
}

// Remove typing indicator
function removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

// Clear all messages
function clearMessages() {
    window.AppConfig.elementsCache['messages-container'].innerHTML = '';
}

// Show welcome message
function showWelcomeMessage() {
    window.AppConfig.elementsCache['messages-container'].innerHTML = `
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

// Format different types of responses
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
                return window.TableManager.formatTableData(result.data);
            }
            return JSON.stringify(result.data, null, 2);
        }
        
        // Fallback to JSON display for debugging
        console.log('⚠️ [API] Falling back to JSON display for unrecognized format');
        return `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }
    
    return String(result);
}

// Format query results with table data
function formatQueryResults(response) {
    console.log('formatQueryResults called with:', response);
    
    if (!response.success) {
        return `<div class="error-message">Error: ${response.error || 'Unknown error'}</div>`;
    }

    let html = '<div class="query-results">';
    
    if (response.results && Array.isArray(response.results) && response.results.length > 0) {
        console.log('📋 [API] Processing results array with length:', response.results.length);
        response.results.forEach((result, localIndex) => {
            // 🔧 FIX: Use globally unique resultIndex instead of local index
            const globalResultIndex = window.AppConfig.globalTableData.length;
            console.log(`🆔 [TABLE] Assigning global resultIndex ${globalResultIndex} for local index ${localIndex}`);
            const resultIndex = globalResultIndex;
            html += `<div class="result-section">`;
            html += `<h4>File: ${result.filename}</h4>`;
            html += `<p><strong>Query:</strong> ${result.query}</p>`;
            
            // Store table data for flattening functionality
            if (result.table_info) {
                window.FlattenManager.storeTableData(
                    resultIndex, 
                    result.table_info, 
                    result.filename,
                    result.feature_rows || [],
                    result.feature_cols || []
                );
                
                // ALSO store the backend's flattened version and metadata for plotting
                window.FlattenManager.storeBackendMetadata(
                    resultIndex,
                    {
                        original_query: response.original_query,
                        enriched_query: response.enriched_query,
                        flattened_table_info: result.flattened_table_info,
                        backend_feature_rows: result.feature_rows || [],
                        backend_feature_cols: result.feature_cols || []
                    }
                );
            }
            
            if (result.success && result.table_info) {
                // Create container with dynamic flattening controls for hierarchical tables
                const isHierarchical = result.table_info.has_multiindex && 
                                     result.table_info.header_matrix && 
                                     result.table_info.header_matrix.length > 1;
                                     
                if (isHierarchical) {
                    const maxLv = (result.table_info.header_matrix ? result.table_info.header_matrix.length - 1 : 1);
                    html += `<div class="table-flatten-container" data-result-index="${resultIndex}" data-max-levels="${maxLv}">`;
                    html += `<div class="table-controls">`;
                    html += `<div class="view-mode-controls">`;
                    html += `<button class="view-mode-btn flatten-up" title="More flattened view" data-direction="up">`;
                    html += `<svg width="10" height="6" viewBox="0 0 12 8" fill="currentColor">`;
                    html += `<path d="M6 0L0 8h12L6 0z"/>`;
                    html += `</svg>`;
                    html += `</button>`;
                    html += `<button class="view-mode-btn flatten-down" title="More hierarchical view" data-direction="down">`;
                    html += `<svg width="10" height="6" viewBox="0 0 12 8" fill="currentColor">`;
                    html += `<path d="M6 8L0 0h12L6 8z"/>`;
                    html += `</svg>`;
                    html += `</button>`;
                    // Calculate initial flatten level (same logic as setupTableToggleEvents)
                    const initialFlattenLevel = Math.max(maxLv - 1, 0);
                    html += `<span class="flatten-level-display" data-current-level="${initialFlattenLevel}" style="display: none;"></span>`;
                    html += `</div>`;
                    html += `<div class="table-filter-controls">`;
                    html += `<div class="table-download-controls">`;
                    html += `<button class="table-download-btn" data-result-index="${resultIndex}" title="Download Table">`;
                    html += `<i class="fas fa-download"></i>`;
                    html += `<span class="download-label">Download</span>`;
                    html += `</button>`;
                    html += `<button class="plot-table-btn" data-result-index="${resultIndex}" title="Generate Charts">`;
                    html += `<i class="fas fa-chart-pie"></i>`;
                    html += `<span class="plot-label">Plot</span>`;
                    html += `</button>`;
                    html += `</div>`;
                    html += `<div class="nan-row-controls">`;
                    html += `<label class="nan-row-toggle">`;
                    html += `<input type="checkbox" class="nan-row-checkbox" data-result-index="${resultIndex}">`;
                    html += `<span class="nan-row-label">Show NaN Rows</span>`;
                    html += `</label>`;
                    html += `</div>`;
                    html += `<div class="feature-col-controls">`;
                    html += `<label class="feature-col-toggle">`;
                    html += `<input type="checkbox" class="feature-col-checkbox" data-result-index="${resultIndex}">`;
                    html += `<span class="feature-col-label">Show All Feature Rows</span>`;
                    html += `</label>`;
                    html += `</div>`;
                    html += `</div>`;
                    html += `</div>`;
                    
                    // Table container for dynamic content
                    html += `<div class="dynamic-table-view">`;
                    html += window.TableManager.createHierarchicalHtmlTable(result.table_info, result.filename);
                    html += `</div>`;
                    
                    html += `</div>`;
                } else {
                    // Regular table without hierarchy - still add NaN row controls
                    // For simple tables, max levels is 1 (only the current level, no flattening needed)
                    html += `<div class="table-simple-container" data-result-index="${resultIndex}" data-max-levels="1">`;
                    html += `<div class="table-controls">`;
                    html += `<div class="table-filter-controls">`;
                    html += `<div class="table-download-controls">`;
                    html += `<button class="table-download-btn" data-result-index="${resultIndex}" title="Download Table">`;
                    html += `<i class="fas fa-download"></i>`;
                    html += `<span class="download-label">Download</span>`;
                    html += `</button>`;
                    html += `<button class="plot-table-btn" data-result-index="${resultIndex}" title="Generate Charts">`;
                    html += `<i class="fas fa-chart-pie"></i>`;
                    html += `<span class="plot-label">Plot</span>`;
                    html += `</button>`;
                    html += `</div>`;
                    html += `<div class="nan-row-controls">`;
                    html += `<label class="nan-row-toggle">`;
                    html += `<input type="checkbox" class="nan-row-checkbox" data-result-index="${resultIndex}">`;
                    html += `<span class="nan-row-label">Show NaN Rows</span>`;
                    html += `</label>`;
                    html += `</div>`;
                    html += `<div class="feature-col-controls">`;
                    html += `<label class="feature-col-toggle">`;
                    html += `<input type="checkbox" class="feature-col-checkbox" data-result-index="${resultIndex}">`;
                    html += `<span class="feature-col-label">Show All Feature Rows</span>`;
                    html += `</label>`;
                    html += `</div>`;
                    html += `</div>`;
                    html += `</div>`;
                    html += `<div class="dynamic-table-view">`;
                    html += window.TableManager.createHierarchicalHtmlTable(result.table_info, result.filename);
                    html += `</div>`;
                    html += `</div>`;
                }
            } else {
                html += `<p class="no-data">${result.message || 'No data found'}</p>`;
            }
            
            html += `</div>`;
        });
    } else {
        console.log('⚠️ [API] No valid results found in response');
        html += `<div class="no-data">No results found in the response.</div>`;
    }
    
    html += '</div>';
    return html;
}

// Export message functions
window.MessageManager = {
    addMessageToUI,
    addMessageToConversation,
    addTypingIndicator,
    removeTypingIndicator,
    clearMessages,
    showWelcomeMessage,
    formatResponse,
    formatQueryResults
};

console.log('✅ Messages.js loaded'); 