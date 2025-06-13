// Configuration and Global State
console.log('🚀 Loading config.js...');

// API Configuration
const API_BASE_URL = 'http://localhost:5001';

// Global State
let currentConversationId = null;
let conversations = {};
let uploadStates = {}; // Track per-file upload states
let isSending = false;

// DOM elements cache
const elementsCache = {};

// Store table data globally for access during flattening
let globalTableData = [];

// Export for use in other modules
window.AppConfig = {
    API_BASE_URL,
    currentConversationId,
    conversations,
    uploadStates,
    isSending,
    elementsCache,
    globalTableData,
    
    // Getters and setters for state management
    setCurrentConversationId(id) {
        currentConversationId = id;
        window.AppConfig.currentConversationId = id;
    },
    
    getCurrentConversationId() {
        return currentConversationId;
    },
    
    setIsSending(state) {
        isSending = state;
        window.AppConfig.isSending = state;
    },
    
    getIsSending() {
        return isSending;
    }
};

console.log('✅ Config.js loaded'); 