// Main Application Module
console.log('🚀 Loading app.js...');

// Initialize the entire application
function initializeApp() {
    console.log('🌟 Initializing Excel Chatbot Application...');
    
    // Cache DOM elements first
    window.DOMManager.initializeElements();
    
    // Setup event listeners
    window.EventManager.setupEventListeners();
    
    // Load conversations from localStorage
    window.ConversationManager.loadConversations();
    
    // Initialize conversation state
    window.ConversationManager.initializeConversationState();
    
    console.log('✅ Application initialized successfully');
}

// Wait for DOM content to load, then initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded');
    
    // Check if all required modules are loaded
    const requiredModules = [
        'AppConfig',
        'Utils', 
        'DOMManager',
        'FlattenManager',
        'TableManager',
        'MessageManager',
        'UploadManager',
        'ConversationManager',
        'APIManager',
        'EventManager'
    ];
    
    const missingModules = requiredModules.filter(module => !window[module]);
    
    if (missingModules.length > 0) {
        console.error('❌ Missing required modules:', missingModules);
        alert('Application failed to load. Missing modules: ' + missingModules.join(', '));
        return;
    }
    
    console.log('✅ All modules loaded successfully');
    
    // Initialize the application
    initializeApp();
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('🚨 Global Error:', e.error);
    console.error('Stack:', e.error?.stack);
    
    // Show user-friendly error message
    if (window.DOMManager) {
        window.DOMManager.showError('An unexpected error occurred. Please refresh the page.');
    }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('🚨 Unhandled Promise Rejection:', e.reason);
    
    // Show user-friendly error message
    if (window.DOMManager) {
        window.DOMManager.showError('A network or processing error occurred.');
    }
    
    // Prevent default browser behavior
    e.preventDefault();
});

// Export main app functions
window.App = {
    initializeApp
};

console.log('✅ App.js loaded'); 