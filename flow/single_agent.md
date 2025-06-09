# Excel Chatbot - Single Agent Flow

## 📋 **Excel Chatbot Flow**

### **1. Initialization & Setup**
```python
# Load environment variables (Google API key)
# Initialize Gemini 2.5 Flash LLM model
# Set file path to Excel file
```

### **2. Feature Discovery & Analysis**
```python
feature_names = get_feature_names(file_path, llm)
```
- **Purpose**: LLM analyzes the Excel file to determine if it's a matrix table
- **Output**: Dictionary with `feature_rows` and `feature_cols` lists
- **Example**: `{'feature_rows': ['Cà phê', 'Loại', 'Nhập Khẩu'], 'feature_cols': ['Thời gian', 'Thu nhập']}`

### **3. Feature Name Mapping**
```python
_, feature_name_result = get_feature_name_content(file_path, feature_names)
```
- **Purpose**: Maps feature names to actual Excel column references using fuzzy matching
- **Handles**: MultiIndex columns (tuples) and regular columns
- **Output**: Dictionary with matched column references

### **4. Excel File Preprocessing**
```python
number_of_row_header = get_number_of_row_header(file_path)
df = pd.read_excel(file_path, header=list(range(0,number_of_row_header)))
df = clean_unnamed_header(df, number_of_row_header)
df = fill_undefined_sequentially(df, feature_name_result["feature_rows"])
df = forward_fill_column_nans(df, feature_name_result["feature_rows"])
```
- **Purpose**: Clean and structure the Excel data
- **Steps**:
  - Detect number of header rows
  - Read with proper multi-level headers
  - Clean unnamed columns
  - Fill missing hierarchical values with "Undefined"
  - Forward-fill NaN values in feature columns

### **5. Metadata Structure Creation**
```python
row_dict = convert_df_rows_to_nested_dict(df, feature_name_result["feature_rows"])
col_dict = convert_df_headers_to_nested_dict(df, feature_name_result["feature_cols"])
```
- **Purpose**: Create hierarchical dictionaries representing data structure
- **Row Dict**: Nested structure of row hierarchies
- **Col Dict**: Nested structure of column hierarchies
- **Example**:
  ```python
  row_dict = {
    "Cà phê thường": {
      "Loại 1": ["Việt Nam", "Brazil", "Mỹ"]
    }
  }
  col_dict = {
    "Thời gian": {"Hè": {}, "Đông": {}}
  }
  ```

### **6. Interactive Query Processing Loop**
```python
while True:
    query = input("\nEnter your query: ")
    # Special commands handling
    # Natural language processing
    result = process_natural_language_query(query, feature_rows, feature_cols, row_dict, col_dict, llm)
```

#### **6a. Special Commands**
- **`sanity check`**: Display all data structures (feature_rows, feature_cols, row_dict, col_dict)
- **`exit/quit/q`**: Terminate the program

#### **6b. Natural Language Query Processing**
```python
process_natural_language_query(query, feature_rows, feature_cols, row_dict, col_dict, llm)
```
- **Purpose**: Convert natural language to structured row/column selections
- **Process**:
  1. Send query + data structure to LLM as JSON
  2. LLM analyzes and maps query terms to exact data values
  3. Returns structured format:
     ```json
     ### Row Choose
     {"Cà phê": ["Cà phê thường"], "Nhập Khẩu": ["Việt Nam"]}
     
     ### Col Choose
     ["Thời gian - Hè", "Thu nhập - Trung Bình"]
     ```

## 🔄 **Complete Workflow Diagram**

```
📁 Excel File
    ↓
🤖 LLM Feature Analysis → feature_rows, feature_cols
    ↓
🔍 Fuzzy Column Matching → matched column references
    ↓
🧹 Data Preprocessing → cleaned DataFrame
    ↓
📊 Structure Creation → row_dict, col_dict
    ↓
💬 Interactive Loop:
    ├── User Query → LLM Processing → Structured Output
    ├── "sanity check" → Display Data Structure
    └── "exit" → Terminate
```

## 🎯 **Key Components**

1. **LLM-Powered Analysis**: Uses Gemini to understand Excel structure and queries
2. **Hierarchical Data Handling**: Manages complex multi-level headers and rows
3. **Fuzzy Matching**: Maps feature names to actual columns even with slight differences
4. **Interactive Testing**: Allows continuous query testing without restart
5. **Error Handling**: Graceful error management and recovery

## 📚 **Module Breakdown**

### Core Modules:
- **`llm.py`**: LLM interaction functions
  - `get_feature_names()`: Analyze Excel structure
  - `process_natural_language_query()`: Query processing
  
- **`utils.py`**: Utility functions
  - `get_feature_name_content()`: Column mapping
  - `read_file()`: Excel file reading
  
- **`metadata.py`**: Data structure creation
  - `convert_df_rows_to_nested_dict()`: Row hierarchy
  - `convert_df_headers_to_nested_dict()`: Column hierarchy
  
- **`preprocess.py`**: Data cleaning
  - `clean_unnamed_header()`: Header cleaning
  - `fill_undefined_sequentially()`: Fill missing values

### Data Flow:
```
Raw Excel → Feature Analysis → Column Mapping → Preprocessing → Structure Creation → Query Processing
```

## 🔧 **Technical Architecture**

### Single Agent Design:
- **One LLM instance** handles both structure analysis and query processing
- **Stateful preprocessing** creates reusable data structures
- **Interactive loop** maintains session state for continuous querying
- **JSON-based communication** between components and LLM

### Benefits:
- **Simplicity**: Single agent handles all LLM tasks
- **Efficiency**: Preprocessing done once, querying is fast
- **Consistency**: Same LLM context for structure understanding and query processing
- **Maintainability**: Clear separation of concerns between modules

This flow enables users to query complex hierarchical Excel files using natural language, with the LLM handling the mapping between human queries and structured data selections. 