# Excel Chatbot Core System Flow

This document describes the complete flow of the multi-file Excel chatbot system located in `web/backend/core/`. The system is designed to handle complex Excel files with hierarchical structures and process natural language queries against them.

## Overview

The core system is a multi-agent Excel chatbot that can:
1. Process multiple Excel files simultaneously
2. Extract hierarchical metadata from complex Excel structures
3. Handle natural language queries and route them to appropriate files
4. Use LLM agents to decompose queries and extract relevant data
5. Return properly formatted hierarchical table results

## System Architecture

### Main Components

1. **MultiFileProcessor** (`processor.py`) - Main orchestrator
2. **LLM Agents** (`llm.py`) - Multi-agent query processing
3. **Metadata Extraction** (`metadata.py`) - Excel structure analysis
4. **Data Preprocessing** (`preprocess.py`) - DataFrame cleaning
5. **DataFrame Filtering** (`extract_df.py`) - Data extraction
6. **Post-processing** (`postprocess.py`) - Result formatting
7. **Utility Functions** (`utils.py`) - Helper functions
8. **Configuration** (`config.py`) - System settings
9. **Prompts** (`prompt.py`) - LLM prompt templates

## Detailed Flow

### Phase 1: System Initialization

#### 1.1 Configuration Loading (`config.py`)
```
Environment Variables Loading:
├── Load .env file from core directory
├── Set LLM model (default: gemini-2.5-flash-preview-04-17)
├── Configure Google API keys
├── Set upload folder paths
├── Configure logging with Unicode support
└── Set CORS and file validation rules
```

#### 1.2 MultiFileProcessor Initialization (`processor.py`)
```
MultiFileProcessor.__init__():
├── Initialize empty file_metadata dictionary
├── Initialize LLM as None (lazy loading)
└── Initialize TablePostProcessor instance
```

### Phase 2: File Processing Pipeline

#### 2.1 File Upload and Initial Processing
```
process_multiple_files():
├── For each uploaded file:
│   ├── Call extract_file_metadata()
│   └── Store metadata in file_metadata dictionary
└── Log completion of multi-file processing
```

#### 2.2 Individual File Metadata Extraction
```
extract_file_metadata() - The Core Processing Pipeline:

Step 1: LLM Initialization
├── Check if LLM is initialized
├── If not, create ChatGoogleGenerativeAI instance
└── Set temperature to 0.0 for consistent results

Step 2: Feature Name Analysis (llm.py)
├── read_file() - Convert Excel to CSV format
├── get_feature_names() - LLM analysis using FEATURE_ANALYSIS_PROMPT
├── parse_llm_feature_name_output() - Extract:
│   ├── is_matrix_table (boolean)
│   ├── feature_rows (list of row hierarchy columns)
│   └── feature_cols (list of column hierarchy columns)
└── Log feature names extracted

Step 3: Feature Content Extraction (utils.py)
├── get_feature_name_content() - Fuzzy matching of feature names to actual columns
├── Use thefuzz library for similarity matching (threshold: 80%)
├── Handle MultiIndex columns appropriately
├── Return feature content and matched column mappings
└── Log mismatches for review

Step 4: Row Header Detection (metadata.py)
├── get_number_of_row_header() - Analyze Excel structure
├── Read DataFrame and examine first column
├── Count consecutive NaN values to determine header rows
├── Default to 1 header row, increment for each NaN
└── Log determined number of headers

Step 5: DataFrame Loading and Preprocessing
├── Load Excel with pd.read_excel() using determined header rows
├── Apply preprocessing pipeline (preprocess.py):
│   ├── clean_unnamed_header() - Replace "Unnamed:" with "Header"
│   ├── fill_undefined_sequentially() - Fill gaps with "Undefined"
│   └── forward_fill_column_nans() - Forward fill NaN values
└── Log DataFrame shape and preprocessing completion

Step 6: Hierarchical Structure Creation (metadata.py)
├── convert_df_rows_to_nested_dict() - Create row hierarchy
│   ├── Build nested dictionary from hierarchy columns
│   ├── Handle undefined values appropriately
│   └── Prune redundant "Undefined" branches
├── convert_df_headers_to_nested_dict() - Create column hierarchy
│   ├── Process MultiIndex columns into nested structure
│   ├── Stop at "Header" components (cleaned unnamed columns)
│   └── Create leaf node lists for final levels
└── Log structure creation completion

Step 7: LLM Structure Formatting (utils.py)
├── format_row_dict_for_llm() - Format row hierarchy for LLM consumption
│   ├── Create indented hierarchical text representation
│   ├── Use feature names as level labels
│   └── Format leaf values as comma-separated lists
├── format_col_dict_for_llm() - Format column hierarchy
│   ├── Use level_1, level_2, level_N notation
│   ├── Handle unlimited hierarchical depth
│   └── Separate items with and without sub-structure
└── Store formatted structures in metadata

Step 8: File Summary Generation
├── generate_file_summary() - Create LLM summary using FILE_SUMMARY_PROMPT
├── Include filename, feature rows/cols, and hierarchical structures
├── Get comprehensive description of file content and structure
└── Store summary in metadata
```

### Phase 3: Query Processing Pipeline

#### 3.1 Multi-File Query Routing
```
process_multi_file_query():

Step 1: Query Separation
├── separate_query() - Use QUERY_SEPARATOR_PROMPT
├── get_all_file_summaries() - Compile all file summaries
├── LLM determines which files are relevant to query
├── parse_separator_response() - Extract file assignments
└── Return list of (file_path, sub_query) assignments

Step 2: Individual File Processing
├── For each assignment:
│   ├── Call process_single_file_query()
│   ├── Apply TablePostProcessor for hierarchical formatting
│   └── Compile results with filename and success status
└── Return combined results structure
```

#### 3.2 Single File Query Processing
```
process_single_file_query():

Step 1: Multi-Agent Query Decomposition (llm.py - splitter())
├── Decomposer Agent:
│   ├── Use DECOMPOSER_PROMPT with query and hierarchical structures
│   ├── Analyze query to extract row and column keywords
│   ├── parse_decomposer_output() - Extract row_keywords and col_keywords
│   └── Log decomposer results

├── Row Handler Agent:
│   ├── Use ROW_HANDLER_PROMPT with row keywords and row hierarchy
│   ├── Navigate row hierarchy to find matching paths
│   ├── parse_row_handler_output() - Extract hierarchical row selection
│   └── Use "Undefined" for unspecified intermediate levels

└── Column Handler Agent:
    ├── Use COL_HANDLER_PROMPT with column keywords and column hierarchy
    ├── Navigate column hierarchy to find matching paths
    ├── parse_col_handler_output() - Extract hierarchical column selection
    └── Return level-based column identifiers

Step 2: DataFrame Filtering (extract_df.py)
├── render_filtered_dataframe():
│   ├── parse_row_paths() - Convert hierarchical row selection to paths
│   ├── parse_col_paths() - Convert hierarchical column selection to paths
│   ├── create_row_condition() - Build pandas boolean conditions
│   ├── create_column_tuples() - Identify MultiIndex column tuples
│   ├── Apply filters to DataFrame
│   └── Return filtered result preserving hierarchical structure
└── Handle MultiIndex column searching and matching
```

### Phase 4: Result Processing and Formatting

#### 4.1 Hierarchical Table Post-Processing (`postprocess.py`)
```
TablePostProcessor.extract_hierarchical_table_info():

Step 1: Header Matrix Construction
├── build_header_matrix() - Create matrix representation of MultiIndex headers
├── calculate_rowspan() - Determine vertical spanning for empty placeholders
├── calculate_intelligent_colspan() - Determine horizontal spanning logic
├── Handle "Header" placeholders from preprocessing
└── Create cell information with position, colspan, and rowspan

Step 2: Data Serialization
├── Convert DataFrame data to JSON-serializable format
├── Handle numeric values, NaN values, and string conversion
├── Preserve data types while ensuring frontend compatibility
└── Create final data structure with:
    ├── has_multiindex flag
    ├── header_matrix for table rendering
    ├── final_columns list
    ├── data_rows array
    └── row/column counts
```

### Phase 5: Error Handling and Logging

#### 5.1 Comprehensive Error Handling
```
Error Handling Throughout Pipeline:
├── File reading errors (invalid Excel files)
├── LLM API errors (rate limiting, authentication)
├── Column matching errors (fuzzy matching fallbacks)
├── DataFrame processing errors (empty data, invalid structure)
├── Query parsing errors (invalid LLM responses)
└── Unicode handling errors (safe logging mechanisms)
```

#### 5.2 Logging System
```
Logging Configuration (config.py):
├── UTF-8 encoding support for Unicode content
├── File and console handlers
├── Structured log levels (INFO, WARNING, ERROR)
├── Safe message logging with Unicode fallbacks
└── Separate log files for debugging
```

## Key Design Patterns

### 1. Multi-Agent Architecture
- **Decomposer Agent**: Splits queries into row and column components
- **Row Handler Agent**: Navigates row hierarchies
- **Column Handler Agent**: Navigates column hierarchies
- **Query Separator Agent**: Routes queries to appropriate files

### 2. Hierarchical Data Handling
- **MultiIndex Support**: Full support for complex Excel hierarchies
- **Undefined Handling**: Smart handling of unspecified hierarchy levels
- **Structure Preservation**: Maintains original Excel structure throughout pipeline

### 3. Flexible Column Matching
- **Fuzzy Matching**: Uses similarity scoring for robust column identification
- **MultiIndex Navigation**: Handles complex nested column structures
- **Fallback Mechanisms**: Graceful degradation when matches aren't found

### 4. Lazy Loading and Caching
- **LLM Initialization**: Only when needed
- **Metadata Storage**: Persistent metadata for processed files
- **Resource Management**: Efficient memory usage for large files

## File Dependencies

```
processor.py (Main Entry Point)
├── imports: preprocess, llm, extract_df, postprocess, utils, metadata, prompt
├── coordinates: All file processing and query handling

llm.py (LLM Agents)
├── imports: utils, prompt
├── provides: Feature analysis, query decomposition, and processing agents

metadata.py (Structure Analysis)
├── provides: Row header detection, hierarchical structure creation

extract_df.py (Data Filtering)
├── provides: DataFrame filtering based on hierarchical selections

postprocess.py (Result Formatting)
├── provides: Table formatting with rowspan/colspan for frontend

utils.py (Utilities)
├── provides: File reading, fuzzy matching, structure formatting

preprocess.py (Data Cleaning)
├── provides: DataFrame preprocessing and cleaning functions

config.py (Configuration)
├── provides: Environment setup, logging, validation

prompt.py (LLM Templates)
├── provides: All prompt templates for different agents
```

## System Flow Summary

1. **Initialization**: Load configuration and initialize processor
2. **File Processing**: Extract metadata from uploaded Excel files using multi-step pipeline
3. **Query Reception**: Receive natural language query from user
4. **Query Routing**: Determine which files are relevant using LLM
5. **Query Decomposition**: Split query into row/column components using multi-agent system
6. **Data Extraction**: Filter DataFrames based on hierarchical selections
7. **Result Formatting**: Format results with proper table structure for frontend
8. **Response**: Return formatted results with metadata

This system handles the complete lifecycle of Excel file processing and querying, from upload to structured response, with robust error handling and support for complex hierarchical data structures. 