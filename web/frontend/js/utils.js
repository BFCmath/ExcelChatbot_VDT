// Utility Functions Module
console.log('🚀 Loading utils.js...');

// HTML escaping function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format code blocks
function formatCodeBlocks(content) {
    return content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
}

// Text truncation
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Cell value formatting for tables
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

// Save JSON data to file with automatic download
function saveJsonToFile(data, filename) {
    try {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create temporary download link
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        
        // Add to DOM, trigger download, then remove
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Clean up the object URL
        URL.revokeObjectURL(url);
        
        console.log(`💾 Debug data saved to ${filename}`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to save file ${filename}:`, error);
        return false;
    }
}

// Save text data to file with automatic download
function saveTextToFile(text, filename) {
    try {
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        // Create temporary download link
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        
        // Add to DOM, trigger download, then remove
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Clean up the object URL
        URL.revokeObjectURL(url);
        
        console.log(`💾 Text data saved to ${filename}`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to save file ${filename}:`, error);
        return false;
    }
}

// Export utility functions
window.Utils = {
    escapeHtml,
    formatCodeBlocks,
    truncateText,
    formatCellValue,
    saveJsonToFile,
    saveTextToFile
};

console.log('✅ Utils.js loaded'); 