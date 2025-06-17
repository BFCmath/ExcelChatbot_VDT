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

### Interactive Data Visualization ✨ NEW
- ✅ **Dual-input plotting system** with automatic chart type selection
- ✅ **Bar charts** for simple flat data structures
- ✅ **Sunburst charts** for complex hierarchical data
- ✅ **Intelligent filtering** removes total/summary columns automatically
- ✅ **HTML output** ready for web integration
- ✅ **Vietnamese language support** for filtering keywords
- ✅ **Responsive design** with clean, professional styling

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
    "query": "cho tôi biết chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh"
  }
  ```
- **Validation**:
  - Query length validation (1-1000 characters)
  - Non-empty query requirement
- **Response Body (Success)**: A JSON object where keys are the sub-query and filename, and values are the extracted data in JSON format or a "not found" message.
  ```json
  {
    "chi phi hoc tap.xlsx - chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh": "[{\"Tên\": \"trần bích thu\", \"Môn\": \"tổng cộng\", \"Chi phí cấp 1\": 100, \"Chi phí cấp 2\": 200}, {\"Tên\": \"nguyễn nam\", \"Môn\": \"tổng cộng\", \"Chi phí cấp 1\": 120, \"Chi phí cấp 2\": 220}]"
  }
  ```

### 5. List Processed Files in a Conversation

- **Endpoint**: `GET /conversations/<conversation_id>/files`
- **Description**: Retrieves a list of the filenames that have been successfully uploaded and processed for the specified conversation.
- **Response Body**:
  ```json
  {
    "processed_files": ["chi phi hoc tap.xlsx"]
  }
  ```

### 6. Generate Interactive Charts

- **Endpoint**: `POST /plot/generate`
- **Description**: Generates interactive charts from dual JSON inputs. Accepts both completely flattened data (for bar charts) and normal hierarchical data (for sunburst charts). Automatically applies filtering to remove total/summary columns.
- **Request Body**:
  ```json
  {
    "completely_flattened_data": {
        "has_multiindex": false,
        "feature_rows": ["Loại hình"],
        "final_columns": ["Loại hình", "Tháng 01", "Tháng 02", "Cộng"],
        "data_rows": [["Sản xuất", 100, 120, 220]]
    },
    "normal_data": {
        "has_multiindex": true,
        "feature_rows": ["Phân loại", "Loại hình"],
        "feature_cols": ["Thời gian", "Chỉ số"],
        "header_matrix": [
            [{"text": "Phân loại", "rowspan": 2}, {"text": "Loại hình", "rowspan": 2}, {"text": "Quý 1", "colspan": 2}],
            [{"text": "Tháng 1"}, {"text": "Tháng 2"}]
        ],
        "data_rows": [
            ["Nguyên vật liệu", "Sản xuất", 100, 120],
            ["Thành phẩm", "Tồn kho", 50, 60]
        ]
    }
  }
  ```

- **Input Validation**:
  - `completely_flattened_data`: Must have `has_multiindex: false`, exactly 1 `feature_rows` entry
  - `normal_data`: Must have `header_matrix`, `feature_rows`, and `feature_cols`
  - Both inputs: Must contain `final_columns`, `data_rows`
  - At least one input must be valid for the request to succeed

- **Filtering Logic**: 
  - Automatically removes columns containing Vietnamese total keywords: `'Tổng'`, `'Cộng'`
  - Applied to both bar charts and sunburst charts
  - Provides analysis of filtered columns in response

- **Response Body (Success)**:
  ```json
  {
    "success": true,
    "plot_types": ["bar", "sunburst"],
    "data_points_bar": 2,
    "data_points_sunburst": 4,
    "plots": {
      "bar_chart": {
        "title": "Bar Chart: example.xlsx",
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "categorical_column": "Loại hình",
        "metrics_plotted": ["Tháng 01", "Tháng 02"],
        "filtered_columns": ["Cộng"]
      },
      "column_first": {
        "title": "example.xlsx (Column-first Hierarchy)",
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "hierarchy": ["Thời gian", "Chỉ số", "Phân loại", "Loại hình"],
        "priority": "column"
      },
      "row_first": {
        "title": "example.xlsx (Row-first Hierarchy)", 
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "hierarchy": ["Phân loại", "Loại hình", "Thời gian", "Chỉ số"],
        "priority": "row"
      }
    },
    "analysis": {
      "bar": {
        "categorical_column": "Loại hình",
        "metrics_count": 2,
        "total_value": 220.0,
        "unique_categories": 1,
        "filtered_out_count": 1
      },
      "sunburst": {
        "categorical_columns": ["Phân loại", "Loại hình"],
        "hierarchy_levels": 2,
        "total_value": 330.0,
        "unique_categories": {"Phân loại": 2, "Loại hình": 2},
        "numeric_positions_original": 2,
        "numeric_positions_filtered": 2,
        "filtered_out_count": 0
      }
    },
    "message": "Bar chart: Successfully created bar chart with 2 metrics and 1 categories; Sunburst chart: Successfully created both column-first and row-first sunburst charts with 4 data points",
    "error": null
  }
  ```

- **Chart Types Generated**:
  - **Bar Chart**: Generated if `completely_flattened_data` is valid (simple flat structure)
    - Best for: Simple categorical data with multiple metrics
    - Features: Grouped bars, automatic filtering, simplified column names
  - **Sunburst Chart**: Generated if `normal_data` is valid (hierarchical structure)
    - Two variants: Column-first and Row-first hierarchy
    - Best for: Multi-level hierarchical data exploration
    - Features: Interactive drill-down, hierarchical filtering

- **HTML Output**: 
  - All charts return complete, standalone HTML files
  - Ready to display in browser or embed in web applications
  - Include interactive features (hover, zoom, drill-down)
  - Responsive design with clean, professional styling

---

## File-by-File Analysis and Bug Report

This section provides a detailed analysis of each module in the `web/backend` directory, including its purpose, design, and identified issues.

### 1. `app.py`

- **Purpose**: The main FastAPI application file. It defines all API endpoints, handles request validation, and orchestrates the overall workflow by calling various manager and core modules.
- **Design**:
    - Uses FastAPI's `async` capabilities correctly, running blocking operations in a thread pool to avoid blocking the event loop.
    - Employs Pydantic models for robust request and response validation.
    - Features a modular design, delegating logic to specialized components.
    - Includes comprehensive logging, although it can be overly verbose.
- **Identified Issues**:
    - **[CRITICAL] Race Condition**: The `/alias/upload` endpoint is vulnerable to a race condition. If two users upload an alias file with the same name simultaneously, their operations will conflict, potentially corrupting the temporary file.
        - **Fix**: Use a guaranteed-unique temporary filename, for example by using Python's `uuid` module.
    - **[MEDIUM] Resource Leak**: In the `/conversations/{conversation_id}/upload` endpoint, if processing a file fails, the uploaded file is not deleted from the server. This can lead to an accumulation of orphaned files in the `uploads` directory.
        - **Fix**: Add a `try...except` block around the file processing call and ensure the file is removed in the `except` block.
    - **[MEDIUM] Information Leak**: Some error handlers return detailed internal exception messages to the client. This can expose sensitive information about the application's structure.
        - **Fix**: Return generic error messages for 500-level errors and log the detailed exception server-side only.
    - **[LOW] Verbose Logging**: The `/query` and `/plot` endpoints log extremely detailed information about data structures at the `INFO` level. This is excessive for production and clutters logs.
        - **Fix**: Change these log statements to the `DEBUG` level.

### 2. `managers.py`

- **Purpose**: Manages the lifecycle of user conversations. It is responsible for creating, retrieving, and cleaning up `Conversation` objects.
- **Design**: Uses a dictionary (`active_conversations`) to store conversation instances in memory, keyed by a UUID. It includes a `cleanup_stale_conversations` mechanism to remove inactive sessions.
- **Identified Issues**:
    - **[HIGH] Lack of Persistence**: The entire application state (all user sessions and their processed files) is stored in memory. A server restart will wipe all data. This is not a scalable or robust solution for a production environment.
        - **Fix**: Replace the in-memory dictionary with a persistent storage solution like Redis for caching session data.
    - **[LOW] Inefficient Cleanup**: The `cleanup_stale_conversations` function iterates through all conversations every time `get_conversation` is called. For a large number of active conversations, this could become a performance bottleneck.
        - **Fix**: Run the cleanup task as a periodic background job instead of triggering it on every `get` request.

### 3. `middleware.py`

- **Purpose**: Provides security and validation for incoming API requests before they hit the endpoint logic.
- **Design**: Contains two main classes: `FileValidator` for validating uploaded files (size, type, count) and `RequestValidator` for validating other request parameters like conversation IDs and query strings.
- **Identified Issues**:
    - **[LOW] Hardcoded Limits**: Configuration values like `MAX_FILE_SIZE`, `MAX_FILES`, and `ALLOWED_EXTENSIONS` are hardcoded directly in the middleware file. This makes them difficult to change without modifying the code.
        - **Fix**: Externalize these values into the central `config.py` file.
    - **[LOW] Incomplete Filename Sanitization**: The `sanitize_filename` function is good, but could be more robust. For example, it doesn't handle path traversal attempts using backslashes (`\`). While `os.path.basename` is used later, sanitizing more aggressively at the first step is better practice.
        - **Fix**: Improve the sanitization regex to strip or reject a wider range of malicious characters and sequences.

### 4. `alias_manager.py`

- **Purpose**: Manages the global alias file for the entire application. It ensures that aliases (synonyms for column/row names) can be uploaded, updated, and used across all conversations.
- **Design**: Implements a thread-safe singleton pattern to ensure only one instance of the manager exists. It uses a `ReentrantLock` to handle concurrent access to the alias file, preventing race conditions during read/write operations. It cleverly caches the alias data in memory.
- **Identified Issues**:
    - **[LOW] Minor Resource Leak**: When a new alias file is uploaded, the old file (`system_alias.xlsx`) is overwritten. However, the temporary file used during the upload is not consistently deleted, and if the old file had a different extension, it might not be cleaned up.
        - **Fix**: Ensure old alias files with any valid Excel extension are removed and that temporary files are always cleaned up in a `finally` block.
    - **[LOW] Brittle Startup**: The manager's state depends on a `has_system_alias_file()` function that checks for a specific filename. This is slightly brittle.
        - **Fix**: The logic is mostly sound due to the singleton pattern, but could be made more robust by relying on the manager's internal state rather than filesystem checks after initialization.

### 5. `conversation.py`

- **Purpose**: Defines the `Conversation` class, which represents a single, isolated user session.
- **Design**: Each `Conversation` instance encapsulates a `MultiFileProcessor` from the `core` library. This is an excellent design choice, as it effectively isolates the files, metadata, and state of one user from another. It also tracks the last access time, which is used by `managers.py` for cleanup.
- **Identified Issues**:
    - **[LOW] Generic Error Handling**: The `get_response` method has a broad `except Exception` block that catches any error during query processing and returns a generic failure message. While this prevents crashes, it makes debugging difficult.
        - **Fix**: Add more specific exception handling to differentiate between different failure modes (e.g., file not found, processing error, LLM error) and provide more informative (but still safe) feedback.

For an analysis of the `core` library modules, see the [README in the `core` directory](./core/README.md).
