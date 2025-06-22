# Excel Chatbot Backend API

A production-ready FastAPI backend for a stateful, conversation-based Excel Chatbot. It handles file uploads, natural language queries, data analysis, and dynamic chart generation.

## ✨ Features

- **Stateful Conversation Management**: Manages multiple, isolated user conversations with persistent context for each session.
- **Secure File Handling**: Robust validation for file uploads (type, size, count), sanitization of filenames, and proper error handling.
- **Asynchronous Processing**: Built with FastAPI and `async` operations for high-performance, non-blocking I/O.
- **Interactive Data Visualization**:
    - Dual-input plotting system supporting both flat and hierarchical data.
    - Generates interactive **Bar charts** and **Sunburst charts**.
    - Intelligent filtering to automatically remove summary/total columns.
    - Outputs self-contained HTML for easy embedding in web frontends.
- **Structured Logging**: Comprehensive logging for easy debugging and monitoring.
- **Health Check Endpoint**: A `/health` endpoint to monitor the API's status and activity.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+

### Installation

1.  Navigate to the `web/backend` directory.
2.  Install the required Python packages:
    ```bash
    pip install -r ../../requirements.txt
    ```

### Running the Server

To start the development server with live reloading:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 5001
```

The API will be available at `http://localhost:5001`.

## 🏛️ Architecture

The backend is designed for modularity and scalability:

- **State Management**: A `ConversationManager` creates and tracks `Conversation` objects. Each `Conversation` has a unique ID and its own `MultiFileProcessor` instance, ensuring that file metadata and context are isolated between conversations.
- **In-Memory State**: All conversation state is currently stored in memory and will be reset if the server restarts.
- **Async Processing**: File uploads and query processing use `async` operations to prevent blocking the server's event loop.
- **Logging**: Comprehensive logging with both file and console output for debugging and monitoring.

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
- **Response Body (Success)**:
  ```json
  {
    "message": "Successfully uploaded 2 files.",
    "uploaded_files": ["sales_data.xlsx", "customer_data.xlsx"],
    "all_processed_files_in_conversation": ["sales_data.xlsx", "customer_data.xlsx"]
  }
  ```

### 4. Query within a Conversation

- **Endpoint**: `POST /conversations/<conversation_id>/query`
- **Description**: Sends a natural language query to be executed against the files within the specified conversation.
- **Request Body**:
  ```json
  {
    "query": "What is the total revenue from all sales?"
  }
  ```
- **Response Body (Success)**: A JSON object where keys are the sub-query and filename, and values are the extracted data in JSON format.
  ```json
  {
    "sales_data.xlsx - total revenue": "[{\"total_revenue\": 500000}]"
  }
  ```

### 5. List Processed Files in a Conversation

- **Endpoint**: `GET /conversations/<conversation_id>/files`
- **Description**: Retrieves a list of the filenames that have been successfully uploaded and processed for the specified conversation.
- **Response Body**:
  ```json
  {
    "processed_files": ["sales_data.xlsx"]
  }
  ```

### 6. Generate Interactive Charts

- **Endpoint**: `POST /plot/generate`
- **Description**: Generates interactive charts from structured JSON data. Automatically selects chart type based on data structure and filters out summary columns.
- **Request Body**: (See original document for detailed structure)
- **Response Body (Success)**:
  ```json
  {
    "success": true,
    "plot_types": ["bar", "sunburst"],
    "plots": {
      "bar_chart": {
        "title": "Bar Chart: example.xlsx",
        "html_content": "<html>...</html>"
      },
      "column_first": {
        "title": "example.xlsx (Column-first Hierarchy)",
        "html_content": "<html>...</html>"
      },
      "row_first": {
        "title": "example.xlsx (Row-first Hierarchy)", 
        "html_content": "<html>...</html>"
      }
    },
    "message": "Successfully created charts.",
    "error": null
  }
  ```
