# Excel Chatbot Backend API

This document outlines the improved, production-ready API for the stateful, conversation-based Excel Chatbot backend.

## Recent Improvements

### Security & Validation
- ✅ File upload validation and sanitization
- ✅ Request size limits and proper CORS configuration
- ✅ Input validation for all endpoints
- ✅ Comprehensive error handling with proper HTTP status codes

### Performance & Reliability  
- ✅ Async processing for file operations
- ✅ Proper FastAPI deployment with uvicorn
- ✅ Structured logging framework
- ✅ Health check endpoints
- ✅ Request/response validation middleware

### Testing & Monitoring
- ✅ Unit tests with proper mocking
- ✅ Integration tests with test fixtures
- ✅ Performance monitoring capabilities
- ✅ Comprehensive error tracking with WARNING prefixes

## Architecture

The backend is designed to handle multiple, isolated user conversations. Each conversation maintains its own state, including the set of Excel files that have been uploaded and processed within that session.

- **State Management**: A `ConversationManager` creates and tracks `Conversation` objects. Each `Conversation` object has a unique ID and its own instance of the `MultiFileProcessor`, ensuring that file metadata and context are not shared between conversations.
- **In-Memory**: All conversation state is currently stored in memory and will be reset if the server restarts.
- **Async Processing**: File uploads and query processing use async operations for better performance.
- **Logging**: Comprehensive logging with file and console output for debugging and monitoring.

---

## API Endpoints

### 1. Health Check

- **Endpoint**: `GET /health`
- **Description**: Returns API health status and metrics.
- **Response Body**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "active_conversations": 5
  }
  ```

### 2. Create a New Conversation

- **Endpoint**: `POST /conversations`
- **Description**: Initializes a new, empty conversation session.
- **Response Body**:
  ```json
  {
    "conversation_id": "a-unique-uuid-string"
  }
  ```

### 3. Upload Files to a Conversation

- **Endpoint**: `POST /conversations/<conversation_id>/upload`
- **Description**: Uploads one or more Excel (`.xlsx`, `.xls`) files to the specified conversation. Files are validated and processed immediately to extract their metadata and structure.
- **Request**: `multipart/form-data` with one or more files under the `files` key.
- **Validation**: 
  - File type validation (only Excel files)
  - File size limits (16MB max)
  - Maximum 10 files per request
  - Filename sanitization for security
- **Response Body (Success)**:
  ```json
  {
    "message": "Successfully uploaded 2 files.",
    "uploaded_files": ["sales_data_abc123.xlsx", "customer_data_def456.xlsx"],
    "all_processed_files_in_conversation": ["sales_data_abc123.xlsx", "customer_data_def456.xlsx"]
  }
  ```

### 4. Query within a Conversation

- **Endpoint**: `POST /conversations/<conversation_id>/query`
- **Description**: Sends a natural language query to be executed against the files within the specified conversation. The system will first route the query to the most relevant file(s) and then extract the data.
- **Request Body**:
  ```json
  {
    "query": "your natural language question here (max 1000 chars)"
  }
  ```
- **Validation**:
  - Query length validation (1-1000 characters)
  - Non-empty query requirement
- **Response Body (Success)**: A JSON object where keys are the sub-query and filename, and values are the extracted data in JSON format or a "not found" message.
  ```json
  {
    "sales_data.xlsx - price of coffee": "[{\"Column1\": \"Value1\", ...}]",
    "customer_data.xlsx - sales in 2023": "No matching data found."
  }
  ```

### 5. List Processed Files in a Conversation

- **Endpoint**: `GET /conversations/<conversation_id>/files`
- **Description**: Retrieves a list of the filenames that have been successfully uploaded and processed for the specified conversation.
- **Response Body**:
  ```json
  {
    "processed_files": ["sales_data_abc123.xlsx", "customer_data_def456.xlsx"]
  }
  ```

---

## Error Handling

The API now includes comprehensive error handling with proper HTTP status codes:

- **400 Bad Request**: Invalid input, file validation failures, empty queries
- **404 Not Found**: Conversation not found
- **413 Request Entity Too Large**: File or request too large
- **500 Internal Server Error**: Server processing errors

All errors include descriptive messages and are properly logged.

---

## Environment Configuration

Create a `.env` file in the `core/` directory with:

```env
GOOGLE_API_KEY_1=your_google_api_key_here
GOOGLE_API_KEY_2=your_backup_google_api_key_here
LLM_MODEL=gemini-2.5-flash-preview-04-17
LOG_LEVEL=INFO
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## How to Run

### Development Setup

1. **Navigate to the project's root directory**
2. **Install dependencies**: 
   ```bash
   pip install -r web/backend/requirements.txt
   ```
3. **Set environment variables**: Create `.env` file as shown above
4. **Run the application**: 
   ```bash
   python -m web.backend.app
   ```
   Or with uvicorn directly:
   ```bash
   uvicorn web.backend.app:app --host 127.0.0.1 --port 5001 --reload
   ```
5. **The server will start on**: `http://127.0.0.1:5001`

### Production Deployment

For production, use a proper ASGI server:
```bash
cd web/backend
uvicorn app:app --host 0.0.0.0 --port 5001 --workers 4
```

---

## Testing

### Unit Tests
```bash
python -m pytest web/backend/test_units.py -v
```

### Integration Tests
```bash
python -m pytest web/backend/test_integration.py -v
```

### All Tests
```bash
python -m pytest web/backend/ -v
```

---

## Logging

Logs are written to both console and `logs/app.log`. Log levels can be configured via the `LOG_LEVEL` environment variable.

WARNING messages are prefixed with "WARNING: " for easy tracking of fallback scenarios.

---

## API Documentation

Once running, interactive API documentation is available at:
- Swagger UI: `http://127.0.0.1:5001/docs`
- ReDoc: `http://127.0.0.1:5001/redoc`

---

## Security Features

- **CORS**: Configurable allowed origins (no more wildcard)
- **File Validation**: Strict file type and size checking
- **Input Sanitization**: All inputs are validated and sanitized
- **Filename Security**: Path traversal protection
- **Request Limits**: Size and rate limiting
- **Error Handling**: No sensitive information exposure

---

## Future Improvements

Items noted for later implementation:
- Persistent conversation storage
- Authentication and authorization
- Rate limiting and request throttling
- Conversation cleanup and expiration
- Enhanced caching strategies
- Database integration for metadata storage
