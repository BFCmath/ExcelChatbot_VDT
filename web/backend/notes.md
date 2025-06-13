# Excel Chatbot Backend System Documentation

## Overview

The Excel Chatbot Backend is a sophisticated FastAPI-based system designed to process multiple Excel files and handle natural language queries across hierarchical data structures. The system maintains isolated conversation sessions with their own state and supports complex multi-file operations with intelligent query routing.

## Recent Updates (2025-06-14)

### Major Features Added:
- **System-Wide Alias Management**: Global alias file system with thread-safe operations and logical file removal
- **Query Enrichment Pipeline**: Automatic query enhancement using LLM and alias dictionaries
- **Enhanced API Endpoints**: New alias management endpoints with comprehensive error handling

### Critical Bug Fixes:
- **File Access Conflict Resolution**: Fixed Windows file locking issues by implementing logical file removal instead of physical deletion
- **Thread-Safe Alias Operations**: Implemented proper locking mechanisms for concurrent alias file access
- **Graceful Error Handling**: Enhanced error handling for file-in-use scenarios and alias processing failures

### System Improvements:
- **Automatic Alias Integration**: Conversations automatically detect and use system alias files
- **Enhanced Query Processing**: Multi-step query processing with alias enrichment as first step
- **Robust File Management**: Better handling of file replacement and orphaned file scenarios

## System Architecture

### Core Components

1. **FastAPI Application Layer** (`app.py`)
2. **Conversation Management** (`conversation.py`, `managers.py`)
3. **Alias Management System** (`alias_manager.py`)
4. **Security & Validation** (`middleware.py`)
5. **Core Processing Engine** (`core/` directory)
6. **Configuration Management** (`core/config.py`)

---

## File-by-File Analysis

### 1. `app.py` - Main Application Entry Point

**Purpose**: FastAPI application setup and API endpoint definitions

**Recent Updates (2025-06-14)**:
- **Added Alias Management Endpoints**: System-wide alias file management
- **Enhanced Query Processing**: Automatic alias enrichment integration
- **Improved Error Handling**: Better exception handling for alias operations

**Key Features**:
- **Application Lifecycle Management**: Startup/shutdown handlers with proper resource initialization
- **CORS Configuration**: Configurable allowed origins for security
- **Request Size Limiting**: Middleware to prevent large uploads (16MB default)
- **Exception Handling**: Comprehensive error handling with proper HTTP status codes
- **Async Processing**: All file operations use async/await for better performance

**Main Endpoints**:
- `GET /health` - Health check with active conversation count
- `GET /alias/status` - Check system alias file status
- `POST /alias/upload` - Upload system-wide alias file
- `DELETE /alias` - Remove current alias file (logical removal)
- `POST /conversations` - Create new conversation session
- `POST /upload` - Simple upload endpoint (frontend compatibility)
- `POST /conversations/{id}/upload` - Upload files to specific conversation
- `POST /conversations/{id}/query` - Process natural language queries with alias enrichment
- `GET /conversations/{id}/files` - List processed files
- `GET /conversations/{id}/validate` - Validate conversation existence

**Key Functions**:
- `save_file_async()` - Asynchronous file saving
- `process_file_async()` - Asynchronous file processing
- `process_query_async()` - Asynchronous query processing

### 2. `conversation.py` - Conversation Session Management

**Purpose**: Individual conversation session handling

**Recent Updates (2025-06-14)**:
- **Automatic Alias Integration**: Conversations automatically detect and use system alias files
- **Enhanced Query Processing**: Queries are enriched with alias context when available

**Key Features**:
- **Isolated State**: Each conversation has its own processor instance
- **UUID-based Identification**: Unique conversation IDs
- **Timestamp Tracking**: Creation time for cleanup purposes
- **Error Handling**: Comprehensive exception handling with logging
- **Alias Integration**: Automatic system alias file detection and usage

**Main Class**: `Conversation`
- `__init__()` - Initialize with unique ID and processor
- `get_processed_files()` - Return list of processed filenames
- `process_file()` - Process uploaded file and extract metadata
- `get_response()` - Process query with automatic alias enrichment and return results

### 3. `alias_manager.py` - Global Alias Management System

**Purpose**: System-wide alias file management with thread-safe operations

**Recent Bug Fixes (2025-06-14)**:
- **Fixed File Access Conflicts**: Logical removal instead of physical deletion
- **Enhanced Upload Process**: Better handling of file replacement scenarios
- **Improved Error Handling**: Graceful handling of file-in-use scenarios

**Key Features**:
- **Thread-Safe Operations**: Uses threading.RLock for concurrent access
- **Singleton Pattern**: Global instance shared across the application
- **Logical File Removal**: Avoids file access conflicts by clearing references
- **Automatic File Discovery**: Loads existing alias files on startup
- **File Conflict Resolution**: Handles files in use by other processes

**Main Class**: `AliasFileManager`
- `__init__()` - Initialize with storage directory and load existing files
- `has_alias_file()` - Check if system alias file is available
- `get_alias_file_path()` - Get path to current alias file
- `get_alias_file_info()` - Get metadata about current alias file
- `upload_alias_file()` - Upload new alias file (replaces existing)
- `remove_alias_file()` - Logically remove current alias file
- `get_system_status()` - Get complete system status information

**Global Functions**:
- `get_alias_manager()` - Get singleton instance (thread-safe)
- `has_system_alias_file()` - Quick availability check
- `get_system_alias_file_path()` - Get current alias file path

**File Management Strategy**:
- **Single Active File**: Only one alias file active at a time
- **Physical File Persistence**: Files kept on disk to avoid process conflicts
- **Logical State Management**: System references control file availability
- **Graceful Degradation**: System works with or without alias files

### 4. `managers.py` - Conversation Manager

**Purpose**: Global conversation management and lifecycle

**Key Features**:
- **Thread-Safe Operations**: Uses threading.RLock for concurrent access
- **Automatic Cleanup**: Removes old conversations (7 days default)
- **Memory Management**: In-memory conversation storage
- **Configurable Timeouts**: Environment variable for cleanup intervals

**Main Class**: `ConversationManager`
- `create_conversation()` - Create and store new conversation
- `get_conversation()` - Retrieve conversation by ID with auto-cleanup
- `get_conversation_count()` - Get active conversation statistics
- `cleanup_conversation()` - Manual conversation removal
- `_cleanup_old_conversations()` - Automatic cleanup of expired sessions

### 5. `middleware.py` - Security and Validation

**Purpose**: Request validation and file security

**Key Classes**:

**`FileValidator`**:
- `validate_file()` - Check file type, size, and format
- `sanitize_filename()` - Prevent path traversal attacks with timestamp hashing
- `validate_multiple_files()` - Batch file validation (max 10 files)

**`RequestValidator`**:
- `validate_conversation_id()` - UUID format validation
- `validate_query()` - Query length and content validation

**Security Features**:
- Path traversal prevention
- File type whitelisting (.xlsx, .xls only)
- Size limits (16MB per file)
- Unicode normalization for filenames
- Timestamp-based unique naming

### 6. `core/config.py` - Configuration Management

**Purpose**: Environment configuration and logging setup

**Key Features**:
- **Environment Variables**: Loads from `.env` file
- **LLM Configuration**: Google API key management and model selection
- **Logging Configuration**: UTF-8 safe logging with file and console output
- **Path Management**: Absolute path handling for uploads
- **CORS Settings**: Configurable allowed origins

**Main Functions**:
- `setup_logging()` - Configure logging with Unicode support
- `safe_log_message()` - Unicode-safe logging wrapper
- `is_allowed_file()` - File extension validation

**Configuration Variables**:
- `LLM_MODEL` - Gemini model version
- `UPLOAD_FOLDER` - File upload directory
- `MAX_CONTENT_LENGTH` - File size limit
- `ALLOWED_EXTENSIONS` - Valid file types
- `LOG_LEVEL` - Logging verbosity

---

## Core Processing Engine (`core/` directory)

### 7. `core/processor.py` - Main Processing Engine

**Purpose**: Multi-file Excel processing and query coordination

**Recent Updates (2025-06-14)**:
- **Alias Enrichment Integration**: Automatic query enrichment using system alias files
- **Enhanced Query Flow**: Added alias enrichment as first step in query processing
- **Graceful Fallback**: System works normally when no alias file is available

**Key Classes**:

**`FileMetadata`**: Stores processed file information
- File paths and display names
- DataFrame and preprocessing results
- Feature analysis results
- LLM-generated summaries
- Hierarchical structures

**`MultiFileProcessor`**: Main processing coordinator
- `extract_file_metadata()` - Complete file analysis pipeline
- `generate_file_summary()` - LLM-based file summarization
- `process_multiple_files()` - Batch file processing
- `separate_query()` - Query routing across files
- `process_multi_file_query()` - Coordinate multi-file queries with alias enrichment
- `process_single_file_query()` - Handle individual file queries

**Enhanced Processing Pipeline** (with alias support):
1. **Alias Enrichment** - Enrich query with alias context (if available)
2. Header analysis and row detection
3. Feature name extraction using LLM
4. DataFrame preprocessing and cleaning
5. Hierarchical structure creation
6. LLM summarization
7. Metadata storage

**Alias Integration Features**:
- **Automatic Detection**: Checks for system alias file before processing
- **Query Enrichment**: Enhances user queries with alias context
- **Error Handling**: Graceful fallback when alias processing fails
- **Logging**: Comprehensive logging of alias enrichment process

### 8. `core/postprocess.py` - Table Structure Processing

**Purpose**: Convert DataFrames to frontend-ready hierarchical tables

**Key Class**: `TablePostProcessor`

**Main Functions**:
- `extract_hierarchical_table_info()` - Main table extraction
- `build_header_matrix()` - Create header structure with rowspan/colspan
- `create_flattened_headers()` - Generate flat column names
- `calculate_rowspan()` - Vertical cell merging logic
- `calculate_intelligent_colspan()` - Horizontal cell merging logic
- `create_acronym()` - Smart acronym generation for headers

**Features**:
- **MultiIndex Support**: Handles complex Excel header structures
- **Cell Merging**: Intelligent rowspan/colspan calculation
- **Flattened Views**: Alternative flat table representation
- **Acronym Generation**: Preserves case and numbers in abbreviations
- **JSON Serialization**: Frontend-ready data format

### 9. `core/llm.py` - Language Model Processing

**Purpose**: LLM integration for query analysis and feature extraction

**Key Functions**:
- `get_feature_names()` - Extract feature rows/columns from Excel
- `get_feature_names_from_headers()` - Header-only feature analysis
- `splitter()` - Multi-agent query decomposition
- `parse_llm_feature_name_output()` - Parse LLM feature analysis
- `get_schema()` - Schema analysis using LLM

**Multi-Agent System**:
1. **Decomposer Agent**: Split queries into row/column keywords
2. **Row Handler Agent**: Process row-related keywords
3. **Column Handler Agent**: Process column-related keywords

**Parsing Functions**:
- `parse_decomposer_output()` - Extract keywords from decomposer
- `parse_row_handler_output()` - Parse row selection logic
- `parse_col_handler_output()` - Parse column selection logic

### 10. `core/utils.py` - Utility Functions

**Purpose**: Common utilities for data processing

**Key Functions**:
- `read_file()` - Excel to CSV conversion
- `get_feature_name_content()` - Feature matching with fuzzy logic
- `format_row_dict_for_llm()` - Format hierarchical row structure
- `format_col_dict_for_llm()` - Format hierarchical column structure
- `format_nested_dict_for_llm()` - Generic nested structure formatting

**Features**:
- **Fuzzy Matching**: Uses thefuzz library for column name matching
- **MultiIndex Support**: Handles complex column structures
- **Hierarchical Formatting**: LLM-friendly structure representation
- **Mismatch Logging**: Tracks column matching issues

### 11. `core/extract_df.py` - DataFrame Extraction

**Purpose**: Extract data based on hierarchical selections

**Key Functions**:
- `search_column_in_multiindex()` - Find columns in MultiIndex
- `parse_row_paths()` - Parse hierarchical row selections
- `parse_col_paths()` - Parse hierarchical column selections
- `create_row_condition()` - Build pandas filtering conditions
- `create_column_tuples()` - Generate column selection tuples
- `render_filtered_dataframe()` - Main extraction coordinator
- `get_extraction_stats()` - Extraction statistics

**Features**:
- **Hierarchical Path Parsing**: Handle nested row/column structures
- **Pandas Integration**: Efficient DataFrame filtering
- **Condition Building**: Complex boolean condition creation
- **Statistics Tracking**: Monitor extraction performance

### 12. `core/metadata.py` - Metadata Extraction

**Purpose**: Extract structural metadata from Excel files

**Key Functions**:
- `get_number_of_row_header()` - Determine header row count
- `convert_df_headers_to_nested_dict()` - Build column hierarchy
- `convert_df_rows_to_nested_dict()` - Build row hierarchy

**Features**:
- **Header Detection**: Automatic row header counting
- **Hierarchical Conversion**: Multi-level structure creation
- **Recursive Processing**: Handle arbitrary nesting levels
- **Undefined Handling**: Smart handling of undefined values

### 13. `core/preprocess.py` - Data Preprocessing

**Purpose**: Clean and prepare Excel data

**Key Functions**:
- `extract_headers_only()` - Extract headers for LLM analysis
- `clean_unnamed_header()` - Fix unnamed column headers
- `fill_undefined_sequentially()` - Fill NaN values in hierarchy
- `forward_fill_column_nans()` - Forward-fill missing values

**Features**:
- **Header Cleaning**: Handle Excel's unnamed columns
- **Sequential Filling**: Intelligent NaN replacement
- **Forward Filling**: Preserve hierarchical structure
- **Header-Only Extraction**: Efficient header analysis

### 14. `core/prompt.py` - LLM Prompt Templates

**Purpose**: Structured prompts for LLM operations

**Key Prompts**:
- `DECOMPOSER_PROMPT` - Query decomposition into row/column keywords
- `ROW_HANDLER_PROMPT` - Row hierarchy navigation
- `COL_HANDLER_PROMPT` - Column hierarchy navigation
- `FEATURE_ANALYSIS_PROMPT` - Feature extraction from headers
- `SCHEMA_ANALYSIS_PROMPT` - Schema understanding
- `FILE_SUMMARY_PROMPT` - File content summarization
- `QUERY_SEPARATOR_PROMPT` - Multi-file query routing

**Features**:
- **Multi-language Support**: Vietnamese and English examples
- **Hierarchical Examples**: Complex nested structure examples
- **Step-by-step Reasoning**: Detailed thinking processes
- **Flexible Templates**: Configurable prompt parameters

### 15. `core/alias_handler.py` - Alias Processing Engine

**Purpose**: LLM-based query enrichment using alias dictionaries

**Key Features**:
- **Excel-based Alias Dictionaries**: Supports complex alias mappings in Excel format
- **LLM Integration**: Uses language models for intelligent query enrichment
- **Caching System**: Caches loaded alias dictionaries for performance
- **Multi-sheet Support**: Handles multiple sheets in alias Excel files
- **Error Handling**: Graceful handling of missing or invalid alias files

**Key Functions**:
- `format_excel_sheets()` - Convert Excel sheets to structured string format
- `get_alias_dictionary()` - Load and format alias dictionary from Excel
- `parse_enriched_query()` - Extract enriched query from LLM response

**Main Class**: `AliasEnricher`
- `__init__()` - Initialize with optional LLM instance
- `load_alias_dictionary()` - Load alias dictionary with caching
- `enrich_query()` - Main enrichment function using LLM
- `clear_cache()` - Clear alias dictionary cache

**Enrichment Process**:
1. Load alias dictionary from Excel file
2. Format dictionary for LLM consumption
3. Create enrichment prompt with user query and aliases
4. Use LLM to generate enriched query
5. Parse and return enhanced query

**Global Function**:
- `enrich_query_with_aliases()` - Standalone enrichment function

---

## Key System Features

### 1. **Multi-File Processing**
- Independent file metadata extraction
- Cross-file query routing
- Isolated conversation contexts
- Parallel processing capabilities

### 2. **Hierarchical Data Handling**
- MultiIndex column support
- Nested row/column structures
- Intelligent cell merging
- Hierarchical path navigation

### 3. **Natural Language Processing**
- Multi-agent query decomposition
- Keyword extraction and routing
- Context-aware query understanding
- Multi-language support (Vietnamese/English)

### 4. **Alias Management System** *(New in 2025-06-14)*
- **System-wide alias files**: Single alias file shared across all conversations
- **LLM-based enrichment**: Intelligent query enhancement using alias context
- **Excel-based dictionaries**: Support for complex alias mappings in Excel format
- **Automatic integration**: Seamless integration into query processing pipeline
- **File conflict resolution**: Logical file removal to avoid process conflicts
- **Thread-safe operations**: Concurrent access support with proper locking

### 5. **Security & Validation**
- File type and size validation
- Path traversal prevention
- Input sanitization
- Request size limiting
- CORS configuration

### 6. **Performance Optimization**
- Async/await operations
- Memory-efficient processing
- Intelligent caching strategies
- Cleanup automation

### 7. **Frontend Integration**
- JSON-serializable responses
- Hierarchical table structures
- Rowspan/colspan calculations
- Flattened view alternatives

---

## Configuration Requirements

### Environment Variables (.env)
```env
GOOGLE_API_KEY_1=your_google_api_key_here
LLM_MODEL=gemini-2.5-flash-preview-04-17
LOG_LEVEL=INFO
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CONVERSATION_CLEANUP_HOURS=168
```

### Dependencies
- FastAPI & Uvicorn (Web framework)
- Pandas & OpenPyXL (Excel processing)
- LangChain & Google Generative AI (LLM integration)
- TheFuzz (Fuzzy matching)
- Python-dotenv (Environment management)

---

## Deployment Considerations

### Development
```bash
uvicorn web.backend.app:app --host 127.0.0.1 --port 5001 --reload
```

### Production
```bash
uvicorn web.backend.app:app --host 0.0.0.0 --port 5001 --workers 4
```

### Key Production Settings
- Worker processes for scalability
- Proper logging configuration
- Environment-specific CORS settings
- Resource cleanup intervals
- Memory monitoring

---

## Future Improvements

1. **Persistence**: Database integration for conversation storage
2. **Authentication**: User authentication and authorization
3. **Caching**: Redis integration for metadata caching
4. **Monitoring**: Detailed performance metrics
5. **Rate Limiting**: Request throttling mechanisms
6. **Background Processing**: Celery integration for heavy operations

---

This documentation covers the complete backend system architecture, providing detailed insights into each component's functionality and role in the overall Excel chatbot system. 