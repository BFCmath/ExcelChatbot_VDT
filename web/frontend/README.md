# Excel Chatbot Frontend

A modern, GPT-like web interface for chatting with Excel files. This frontend connects to the FastAPI backend to provide a seamless chat experience for analyzing Excel data.

## Features

- 🎨 **Modern GPT-like Interface** - Clean, dark theme with smooth animations
- 💬 **Multi-Conversation Support** - Create and manage multiple chat sessions
- 📊 **Excel File Upload** - Drag-and-drop or browse to upload Excel files
- 🔄 **Real-time Chat** - Send queries and get instant responses
- 💾 **Persistent Conversations** - Conversations saved in browser localStorage
- 📱 **Responsive Design** - Works on desktop and mobile devices
- ⚡ **Fast & Lightweight** - Pure HTML/CSS/JavaScript, no frameworks

## Quick Start

1. **Start the Backend Server**
   ```bash
   cd ../backend
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 5001
   ```

2. **Open the Frontend**
   Simply open `index.html` in your web browser, or use a simple HTTP server:
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Using Node.js
   npx serve .
   
   # Using PHP
   php -S localhost:3000
   ```

3. **Start Chatting**
   - Click "New Conversation" to create a chat session
   - Upload an Excel file using the upload button
   - Start asking questions about your data!

## Usage Examples

Once you've uploaded an Excel file, try these example queries:

### Basic Data Exploration
- "What columns are available in this file?"
- "How many rows does this dataset have?"
- "Show me the first 5 rows"
- "What's the summary statistics for this data?"

### Data Analysis
- "What's the total sum of column A?"
- "Find the average value in column B"
- "Show me all rows where sales > 1000"
- "Which product has the highest revenue?"

### Advanced Queries
- "Create a pivot table grouped by category"
- "Find correlations between columns"
- "Show me the top 10 customers by revenue"
- "What are the monthly trends in this data?"

## File Structure

```
web/frontend/
├── index.html          # Main HTML file
├── styles.css          # CSS styles and animations
├── script.js           # JavaScript functionality
└── README.md          # This file
```

## Features Overview

### Conversation Management
- **New Conversations**: Click the "+" button to start fresh
- **Switch Conversations**: Click on any conversation in the sidebar
- **Auto-Save**: Conversations are automatically saved to localStorage
- **Smart Titles**: Conversations are automatically titled based on uploaded files

### File Upload
- **Drag & Drop**: Drag Excel files directly onto the upload area
- **File Validation**: Only .xlsx and .xls files are accepted
- **Size Limits**: Maximum file size of 10MB
- **Progress Tracking**: Visual upload progress with animations
- **Multiple Files**: Each conversation can handle multiple Excel files

### Chat Interface
- **Real-time Messaging**: Instant message sending and receiving
- **Typing Indicators**: Shows when the AI is processing your query
- **Message Formatting**: Supports code blocks and structured data
- **Auto-scroll**: Automatically scrolls to new messages
- **Keyboard Shortcuts**: Press Enter to send, Shift+Enter for new line

### User Experience
- **Loading States**: Clear feedback during API calls
- **Error Handling**: Graceful error messages with helpful context
- **Success Notifications**: Confirmation messages for actions
- **Responsive Layout**: Adapts to different screen sizes
- **Dark Theme**: Modern, eye-friendly dark interface

## API Integration

The frontend communicates with the FastAPI backend using these endpoints:

- `POST /conversations` - Create new conversation
- `POST /upload` - Upload Excel files
- `POST /conversations/{id}/query` - Send chat messages
- `GET /health` - Health check

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Troubleshooting

### Common Issues

1. **"Failed to create conversation"**
   - Make sure the backend server is running on port 5001
   - Check browser console for CORS errors

2. **File upload fails**
   - Ensure file is .xlsx or .xls format
   - Check file size is under 10MB
   - Verify backend server is accessible

3. **Messages not sending**
   - Upload an Excel file first
   - Check internet connection
   - Verify backend server is running

### Development Tips

- Open browser Developer Tools (F12) to see console logs
- Check Network tab for API request/response details
- Use the browser's Application tab to view localStorage data

## Customization

### Changing Colors
Edit the CSS variables in `styles.css`:
```css
:root {
    --primary-color: #10a37f;  /* Main accent color */
    --bg-color: #1a1a1a;       /* Background color */
    --text-color: #ffffff;     /* Text color */
}
```

### Modifying API URL
Change the API base URL in `script.js`:
```javascript
const API_BASE_URL = 'http://your-api-server:8000';
```

## License

This project is part of the Excel Chatbot application. 