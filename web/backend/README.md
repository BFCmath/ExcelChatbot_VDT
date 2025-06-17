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

### 6. Generate Interactive Charts

- **Endpoint**: `POST /plot/generate`
- **Description**: Generates interactive charts from dual JSON inputs. Accepts both completely flattened data (for bar charts) and normal hierarchical data (for sunburst charts). Automatically applies filtering to remove total/summary columns.
- **Request Body**:
  ```json
  {
    "completely_flattened_data": {
      "filename": "example.xlsx",
      "has_multiindex": false,
      "final_columns": ["Category", "Jan", "Feb", "Mar", "Total"],
      "data_rows": [
        ["Product A", 100, 120, 110, 330],
        ["Product B", 80, 90, 85, 255]
      ],
      "feature_rows": ["Category"],
      "feature_cols": [],
      "row_count": 2,
      "col_count": 5
    },
    "normal_data": {
      "filename": "example.xlsx",
      "has_multiindex": true,
      "header_matrix": [
        [
          {"text": "Category", "colspan": 1, "rowspan": 2, "position": 0, "level": 0},
          {"text": "2024 Q1", "colspan": 3, "rowspan": 1, "position": 1, "level": 0}
        ],
        [
          {"text": "Jan", "colspan": 1, "rowspan": 1, "position": 1, "level": 1},
          {"text": "Feb", "colspan": 1, "rowspan": 1, "position": 2, "level": 1},
          {"text": "Mar", "colspan": 1, "rowspan": 1, "position": 3, "level": 1}
        ]
      ],
      "final_columns": ["Category", "Jan", "Feb", "Mar"],
      "data_rows": [
        ["Product A", 100, 120, 110],
        ["Product B", 80, 90, 85]
      ],
      "feature_rows": ["Category"],
      "feature_cols": ["2024 Q1"],
      "row_count": 2,
      "col_count": 4
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
    "data_points_bar": 12,
    "data_points_sunburst": 8,
    "plots": {
      "bar_chart": {
        "title": "Bar Chart: example.xlsx",
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "categorical_column": "Category",
        "metrics_plotted": ["Jan", "Feb", "Mar"],
        "filtered_columns": ["Total"]
      },
      "column_first": {
        "title": "example.xlsx (Column-first Hierarchy)",
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "hierarchy": ["Col_Level_0", "Col_Level_1", "Category"],
        "priority": "column"
      },
      "row_first": {
        "title": "example.xlsx (Row-first Hierarchy)", 
        "html_content": "<html>...complete interactive chart HTML...</html>",
        "hierarchy": ["Category", "Col_Level_0", "Col_Level_1"],
        "priority": "row"
      }
    },
    "analysis": {
      "bar": {
        "categorical_column": "Category",
        "metrics_count": 3,
        "total_value": 915.0,
        "unique_categories": 2,
        "filtered_out_count": 1
      },
      "sunburst": {
        "categorical_columns": ["Category"],
        "hierarchy_levels": 2,
        "total_value": 915.0,
        "unique_categories": {"Category": 2},
        "numeric_positions_original": 4,
        "numeric_positions_filtered": 3,
        "filtered_out_count": 1
      }
    },
    "message": "Bar chart: Successfully created bar chart with 3 metrics and 2 categories; Sunburst chart: Successfully created both column-first and row-first sunburst charts with 8 data points (filtered out 1 total columns)",
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

- **Example Data Formats**:
  - **Simple Data (like 4.json)**: Use for bar charts
    ```json
    {
      "has_multiindex": false,
      "feature_rows": ["Loại hình"],
      "final_columns": ["Loại hình", "Tháng 01", "Tháng 02", "Cộng"],
      "data_rows": [["Sản xuất", 100, 120, 220]]
    }
    ```
  - **Hierarchical Data (like 2.json)**: Use for sunburst charts
    ```json
    {
      "has_multiindex": true,
      "feature_rows": ["Phân loại", "Loại hình"],
      "header_matrix": [...],
      "final_columns": ["Phân loại", "Loại hình", "Tháng 01", "Tháng 02"]
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

## 🎨 Dual-Input Plotting System ✅ COMPLETE

The plotting system generates interactive charts from Excel data using an intelligent dual-input approach that automatically selects optimal chart types.

### System Overview

The plotting system accepts **two JSON inputs** from the frontend and intelligently generates the most appropriate visualizations:

1. **`completely_flattened_data`**: Maximally flattened table data for bar chart generation
2. **`normal_data`**: Current hierarchical table data for sunburst chart generation

### Intelligent Chart Selection

The backend automatically:
- ✅ **Validates both inputs** for structural compatibility
- ✅ **Generates bar chart** if flattened data has simple structure (single categorical column)
- ✅ **Always generates sunburst charts** from hierarchical data
- ✅ **Applies smart filtering** to remove Vietnamese total/summary columns ("Tổng", "Cộng")
- ✅ **Returns user-friendly error messages** when bar chart criteria aren't met

### Chart Types Generated

#### 📊 **Bar Chart** (Conditional)
- **When**: Simple flat structure with single categorical column
- **Purpose**: Clean comparison of metrics across categories
- **Features**: 
  - Grouped bar chart with automatic metric labeling
  - Intelligent column name simplification
  - Horizontal legend layout
  - Consistent styling with sunburst charts

#### 🌅 **Column-first Sunburst** (Always)
- **Purpose**: Time/Period hierarchy first, then categories
- **Optimal for**: Time-series analysis and temporal patterns
- **Features**: Radial layout showing chronological flow

#### 📋 **Row-first Sunburst** (Always)  
- **Purpose**: Categories first, then time/period hierarchy
- **Optimal for**: Category comparison and relationship analysis
- **Features**: Radial layout emphasizing categorical structure

## Frontend Integration Guide

### Using the Plotting Endpoint

The plotting endpoint is designed to work seamlessly with frontend table data exports. Here's how to integrate it:

#### 1. Prepare Your Data

Extract data from your frontend table in two formats:

**For Bar Charts (Simple Data)**:
```javascript
// Example: Completely flattened table data
const flattenedData = {
  filename: "user_table.xlsx",
  has_multiindex: false,
  final_columns: ["Category", "Jan", "Feb", "Mar", "Total"],
  data_rows: [
    ["Product A", 100, 120, 110, 330],
    ["Product B", 80, 90, 85, 255]
  ],
  feature_rows: ["Category"],
  feature_cols: [],
  row_count: 2,
  col_count: 5
};
```

**For Sunburst Charts (Hierarchical Data)**:
```javascript
// Example: Multi-level hierarchical data
const hierarchicalData = {
  filename: "user_table.xlsx", 
  has_multiindex: true,
  header_matrix: [
    // Multi-level header structure
    [
      {text: "Category", colspan: 1, rowspan: 2, position: 0, level: 0},
      {text: "2024 Q1", colspan: 3, rowspan: 1, position: 1, level: 0}
    ],
    [
      {text: "Jan", colspan: 1, rowspan: 1, position: 1, level: 1},
      {text: "Feb", colspan: 1, rowspan: 1, position: 2, level: 1},
      {text: "Mar", colspan: 1, rowspan: 1, position: 3, level: 1}
    ]
  ],
  final_columns: ["Category", "Jan", "Feb", "Mar"],
  data_rows: [
    ["Product A", 100, 120, 110],
    ["Product B", 80, 90, 85]
  ],
  feature_rows: ["Category"],
  feature_cols: ["2024 Q1"]
};
```

#### 2. Make the API Call

```javascript
async function generateCharts(flattenedData, hierarchicalData) {
  try {
    const response = await fetch('/plot/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        completely_flattened_data: flattenedData,
        normal_data: hierarchicalData
      })
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('Generated charts:', result.plot_types);
      return result;
    } else {
      console.error('Chart generation failed:', result.error);
    }
  } catch (error) {
    console.error('API call failed:', error);
  }
}
```

#### 3. Display the Charts

```javascript
function displayCharts(plotResult) {
  const plots = plotResult.plots;
  
  // Display bar chart
  if (plots.bar_chart) {
    const barChartContainer = document.getElementById('bar-chart-container');
    barChartContainer.innerHTML = plots.bar_chart.html_content;
  }
  
  // Display sunburst charts
  if (plots.column_first) {
    const sunburstContainer = document.getElementById('sunburst-container');
    sunburstContainer.innerHTML = plots.column_first.html_content;
  }
  
  // Show analysis information
  if (plotResult.analysis) {
    console.log('Bar chart analysis:', plotResult.analysis.bar);
    console.log('Sunburst analysis:', plotResult.analysis.sunburst);
  }
}
```

#### 4. Handle Different Scenarios

```javascript
// Example: Only one data type available
async function generateChartsFlexible(tableData) {
  const request = {
    completely_flattened_data: tableData.isFlat ? tableData : null,
    normal_data: tableData.isHierarchical ? tableData : null
  };
  
  // The backend will validate and generate appropriate charts
  const result = await generateCharts(request.completely_flattened_data, request.normal_data);
  
  // Handle partial success
  if (result.plot_types.includes('bar')) {
    console.log('Bar chart generated successfully');
  }
  if (result.plot_types.includes('sunburst')) {
    console.log('Sunburst chart generated successfully');
  }
}
```

### Data Format Notes

- **Filtering**: The system automatically removes columns containing "Tổng" or "Cộng" (Vietnamese total keywords)
- **HTML Output**: All charts return complete HTML that can be directly inserted into DOM
- **Responsive**: Charts are responsive and work on different screen sizes
- **Interactive**: Charts include hover effects, zoom, and drill-down capabilities

### Error Handling

```javascript
// Handle various error scenarios
if (!result.success) {
  if (result.error.includes('Missing required fields')) {
    console.error('Data format error:', result.error);
    // Show user-friendly message about data format
  } else if (result.error.includes('No valid')) {
    console.error('Validation error:', result.error);
    // Show message about data requirements
  } else {
    console.error('Server error:', result.error);
    // Show generic error message
  }
}
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
