from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np 
import re
from utils import read_file

def get_schema(excel_content, feature_name_content, llm):
    # Create the prompt for Gemini
    prompt = f"""
        Read the file, think step by step, identify the feature rows and feature cols in the Excel file
        Reponse in the following format:
        ### Thinking
        ### Feature Cols
        ### Feature Rows
        
        Requirements: 
        + This is an hierachical Excel file with complex header rows and columns.
        + Explecitly analyze the merge cells in Thinking (avoid mentioning in Feature Cols and Feature Rows)
        + Follow format like in Example
        + Rely on the `Name of Feature Rows` to avoid hallucination when analyzing the `Feature Rows` (happen when the `Feature Rows` are too complex with many levels)

        
        Example 1:
        ### Content
        'Thành Phố,Phân loại,Quận,Phường,Giới tính,Unnamed: 5\r\n,,,,Nam,Nữ\r\nHồ Chí Minh,,,,,\r\n,Lớn,,,,\r\n,,Quận 1,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,Trung Bình,,,,\r\n,,Quận 2,,,\r\n,,,Phường 1,,\r\n,,Quận 4,,,\r\n,,,Phường 14,,\r\n,,,Phường 3,,\r\nHà Nội,,,,,\r\n,,Cầu Giấy,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,,Đống Đa,,,\r\n,,,Phường 1,,\r\n'
        
        ### Name of Feature Rows
        "Feature: Thành Phố\n['Hồ Chí Minh' 'Hà Nội']\nFeature: Phân loại\n['Lớn' 'Trung Bình']\nFeature: Quận\n['Quận 1' 'Quận 2' 'Quận 4' 'Cầu Giấy' 'Đống Đa']\nFeature: Phường\n['Phường 1' 'Phường 2' 'Phường 14' 'Phường 3']\n"
        
        ### Thinking
        The provided data represents a hierarchical structure typical of Excel files with complex headers and row labels.
        The header spans two rows. The first row contains top-level categories like "Thành Phố", "Phân loại", "Quận", "Phường", and "Giới tính". The second row provides sub-categories for "Giới tính", namely "Nam" and "Nữ". In an actual Excel file, "Giới tính" in the first row would likely be a merged cell spanning the columns above "Nam" and "Nữ". The other headers in the first row ("Thành Phố", "Phân loại", "Quận", "Phường") would likely be merged downwards to the second row.
        The rows also exhibit a hierarchical structure. The first column contains the highest level of row labels ("Thành Phố"). Subsequent columns contain nested labels ("Phân loại", "Quận", "Phường"). In an actual Excel file, these row labels would typically be represented by merged cells spanning multiple rows corresponding to their sub-categories. For example, "Hồ Chí Minh" would be a merged cell spanning all rows related to Hồ Chí Minh, "Lớn" would be merged across rows related to the "Lớn" category within Hồ Chí Minh, and so on. The structure indicates that "Phường" is the lowest level of row hierarchy before the data values would appear.
        Feature columns have many levels of hierarchy, merged cells, and nested values. We need to effectively cover these in the output.
        
        ### Feature Cols
        - Row 1, 2 | Col 1: Thành Phố
        - Row 1, 2 | Col 2: Phân loại
        - Row 1, 2 | Col 3: Quận
        - Row 1, 2 | Col 4: Phường
        - Row 1 | Col 5, 6: Giới tính
            - Row 2 | Col 5: Nam
            - Row 2 | Col 6: Nữ

        ### Feature Rows
        - Row 3 | Col 1 (Thành Phố): Hồ Chí Minh
            - Row 4 | Col 2 (Phân loại): Lớn
                - Row 5 | Col 3 (Quận): Quận 1
                    - Row 6 | Col 4 (Phường): Phường 1
                    - Row 7 | Col 4 (Phường): Phường 2
            - Row 8 | Col 2 (Phân loại): Trung Bình
                - Row 9 | Col 3 (Quận): Quận 2
                    - Row 10 | Col 4 (Phường): Phường 1
                - Row 11 | Col 3 (Quận): Quận 4
                    - Row 12 | Col 4 (Phường): Phường 14
                    - Row 13 | Col 4 (Phường): Phường 3
        - Row 14 | Col 1 (Thành Phố): Hà Nội
            - None (Phân loại)
                - Row 15 | Col 3 (Quận): Cầu Giấy
                    - Row 16 | Col 4 (Phường): Phường 1
                    - Row 17 | Col 4 (Phường): Phường 2
                - Row 18 | Col 3 (Quận): Đống Đa
                    - Row 19 | Col 4 (Phường): Phường 1

        Example 2:
        ### Content
        'Thứ tự,Cà phê,Loại,Nhập Khẩu ,Thời gian,Unnamed: 5,Thu nhập,Unnamed: 7,Unnamed: 8\r\n,,,,Hè,Đông,Thấp,Trung Bình,Cao\r\n1,Cà phê thường,,,,,,,\r\n1.1,,Loại 1,,,,,,\r\n1.1.1,,,Việt Nam,,,,,\r\n1.1.2,,,Brazil,,,,,\r\n1.1.3,,,Mỹ,,,,,\r\n1.2,,Loại 2,,,,,,\r\n1.2.1,,,Việt Nam,,,,,\r\n1.2.2,,,Mỹ,,,,,\r\n2,Cà phê Đen,,,,,,,\r\n2.1,,Loại 2,,,,,,\r\n2.1.1,,,Việt Nam,,,,,\r\n'
        
        ### Name of Feature Rows
        "Feature: Cà phê\n['Cà phê thường' 'Cà phê Đen']\nFeature: Loại\n['Loại 1' 'Loại 2']\nFeature: Nhập Khẩu\n['Việt Nam' 'Brazil' 'Mỹ']\n"
        
        ### Thinking
        The provided data simulates an Excel file with a complex header spanning two rows and hierarchical row labels.
        The header in the first row includes "Thứ tự", "Cà phê", "Loại", "Nhập Khẩu", "Thời gian", "Unnamed: 5", "Thu nhập", "Unnamed: 7", and "Unnamed: 8". The second row provides sub-categories for "Thời gian" ("Hè", "Đông") and "Thu nhập" ("Thấp", "Trung Bình", "Cao"). In a real Excel file, "Thời gian" in the first row would likely be a merged cell spanning the columns above "Hè" and "Đông". Similarly, "Thu nhập" would be merged above "Thấp", "Trung Bình", and "Cao". The labels "Thứ tự", "Cà phê", "Loại", and "Nhập Khẩu" in the first row would likely be merged downwards to the second row.
        The rows below the header exhibit a clear hierarchy, indicated by the placement of values in different columns. Column 1 ("Thứ tự") appears to be an index. Column 2 ("Cà phê") contains the highest level of row labels ("Cà phê thường", "Cà phê Đen"). Column 3 ("Loại") contains the next level ("Loại 1", "Loại 2"), and Column 4 ("Nhập Khẩu") contains the lowest level ("Việt Nam", "Brazil", "Mỹ"). In an actual Excel file, these row labels would typically be represented by merged cells spanning multiple rows corresponding to their sub-categories. For example, "Cà phê thường" would be merged across all rows related to "Cà phê thường", "Loại 1" would be merged across rows related to "Loại 1" within "Cà phê thường", and so on. The structure indicates that "Nhập Khẩu" is the lowest level of row hierarchy before the data values would appear in the columns under "Thời gian" and "Thu nhập".

        ### Feature Cols
        - Row 1, 2 | Col 1: Thứ tự
        - Row 1, 2 | Col 2: Cà phê
        - Row 1, 2 | Col 3: Loại
        - Row 1, 2 | Col 4: Nhập Khẩu
        - Row 1 | Col 5, 6: Thời gian
            - Row 2 | Col 5: Hè
            - Row 2 | Col 6: Đông
        - Row 1 | Col 7, 8, 9: Thu nhập
            - Row 2 | Col 7: Thấp
            - Row 2 | Col 8: Trung Bình
            - Row 2 | Col 9: Cao

        ### Feature Rows
        - Row 3 | Col 2 (Cà phê): Cà phê thường
            - Row 4 | Col 3 (Loại): Loại 1
                - Row 5 | Col 4 (Nhập Khẩu): Việt Nam
                - Row 6 | Col 4 (Nhập Khẩu): Brazil
                - Row 7 | Col 4 (Nhập Khẩu): Mỹ
            - Row 8 | Col 3 (Loại): Loại 2
                - Row 9 | Col 4 (Nhập Khẩu): Việt Nam
                - Row 10 | Col 4 (Nhập Khẩu): Mỹ
        - Row 11 | Col 2 (Cà phê): Cà phê Đen
            - Row 12 | Col 3 (Loại): Loại 2
                - Row 13 | Col 4 (Nhập Khẩu): Việt Nam
        
        Now solve
        ### Content
        {excel_content}
        ### Name of Feature Rows
        {feature_name_content}
    """
    # Create the message
    message = HumanMessage(content=prompt)

    # Invoke the model
    try:
        response = llm.invoke([message])
        print(response.content)
    except Exception as e:
        print(f"Error invoking the model: {e}")
    return response.content


def parse_llm_feature_name_output(output):
    """Parse LLM output to determine if content is a matrix table and extract feature rows.
    
    Args:
        output (str): The raw string output from the LLM.
        
    Returns:
        dict: A dictionary containing 'is_matrix_table' (bool) and 'feature_rows' (list or None).
    """
    sections = {}
    # Split output into sections, preserving headers with positive lookahead
    for part in re.split(r'(?=### )', output):
        if part.strip():
            # Separate header and content
            header, content = part.split('\n', 1)
            section_name = header.strip().lstrip('# ').strip()
            sections[section_name] = content.strip()
    
    # Extract and normalize 'Is Matrix Table?' value
    is_matrix_table_str = sections.get('Is Matrix Table?', '').strip().lower()
    is_matrix_table = is_matrix_table_str == "yes"
    
    # Extract and process 'Name of Feature Rows' value
    feature_rows_str = sections.get('Name of Feature Rows', '').strip()
    if feature_rows_str.lower() == "none":
        feature_rows = None
    else:
        feature_rows = [row.strip() for row in feature_rows_str.split(',')]
    
    feature_cols_str = sections.get('Name of Feature Cols', '').strip()
    if feature_cols_str.lower() == "none":
        feature_cols = None
    else:
        feature_cols = [row.strip() for row in feature_cols_str.split(',')]
    
    return {
        'is_matrix_table': is_matrix_table,
        'feature_rows': feature_rows,
        'feature_cols': feature_cols
    }

def get_feature_names(excel_file_path, llm):
    excel_content = read_file(excel_file_path)
    # Create the prompt for Gemini
    prompt = f"""
        Read the file, think step by step, identify if this is a matrix table or a flatten table.
        Reponse in the following format:
        ### Thinking
        ### Is Matrix Table?
        ### Name of Feature Rows
        ### Name of Feature Cols
        
        Instructions:
        If the table is a matrix table, Feature Rows are the columns show hierarchical structure vertically, and usually the very first columns.
        Feature rows should exclude the order column like ID, ...
        Feature cols are the columns that are not feature rows, usually show hierarchical structure horizontally.
        
        Example 1
        ### Content
        'Thành Phố,Phân loại,Quận,Phường,Giới tính,Unnamed: 5\r\n,,,,Nam,Nữ\r\nHồ Chí Minh,,,,,\r\n,Lớn,,,,\r\n,,Quận 1,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,Trung Bình,,,,\r\n,,Quận 2,,,\r\n,,,Phường 1,,\r\n,,Quận 4,,,\r\n,,,Phường 14,,\r\n,,,Phường 3,,\r\nHà Nội,,,,,\r\n,,Cầu Giấy,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,,Đống Đa,,,\r\n,,,Phường 1,,\r\n'
        ### Thinking
        The provided content has multiple header rows. 
        The first row lists potential feature names, and the second row provides specific values (`Nam`, `Nữ`) under the `Giới tính` column. 
        The first few columns show a hierarchical structure in the data rows:
            + Thành Phố: Hồ Chí Minh, Hà Nội
            + Phân loại: Lớn, Trung Bình
            + Quận: Quận 1, Quận 2, Quận 4, Cầu Giấy, Đống Đa
            + Phường: Phường 1, Phường 2, Phường 14, Phường 3
        Giới Tính however is a Feature Column, indicated by the values `Nam` and `Nữ` in the second row.
        ### Is Matrix Table?
        Yes

        ### Name of Feature Rows
        Thành Phố,Phân loại,Quận,Phường
        
        ### Name of Feature Cols
        Giới tính
        
        Example 2
        ### Content
        'Thứ tự,Thành Phố,Phân loại,Quận,Phường,Thu nhập,Unnamed: 6,Unnamed: 7\r\n,,,,,Thấp,Trung Bình,Cao\r\n1,Hồ Chí Minh,,,,,,\r\n1.1,,Lớn,,,,,\r\n1.1.1,,,Quận 1,,,,\r\n1.1.1.1,,,,Phường 1,,,\r\n1.1.1.2,,,,Phường 2,,,\r\n1.2,,Nhỏ,,,,,\r\n1.2.1,,,Quận 4,,,,\r\n1.2.1.1,,,,Phường 1,,,\r\n2,Hà Nội,,,,,,\r\n2.1,,,Cầu Giấy,,,,\r\n2.1.1,,,,Phường 1,,,\r\n'
        ### Thinking
        The provided content has two header rows. The first row lists potential feature names, and the second row provides specific values (`Thấp`, `Trung Bình`, `Cao`) under the `Thu nhập` column and its subsequent unnamed columns. This indicates that `Thu nhập` is a feature column with values listed in the second header row.
        The first few columns (`Thành Phố`, `Phân loại`, `Quận`, `Phường`) show a clear hierarchical structure in the data rows, where values are nested within the preceding columns. This structure defines the rows of the table.
        The combination of multiple header rows defining feature columns and hierarchical structure in the initial columns defining the rows is characteristic of a matrix table.
        We do not include `Thứ tự` as this is not a feature row but rather an index or identifier for the records.
        ### Is Matrix Table?
        Yes

        ### Name of Feature Rows
        Thành Phố,Phân loại,Quận,Phường
        ### Name of Feature Cols
        Thu nhập
        
        Example 3
        ### Content
        'ID,Cà phê,Loại,Nhập Khẩu ,Thời gian,Unnamed: 5,Thu nhập,Unnamed: 7,Unnamed: 8\r\n,,,,Hè,Đông,Thấp,Trung Bình,Cao\r\n1,Cà phê thường,,,,,,,\r\n1.1,,Loại 1,,,,,,\r\n1.1.1,,,Việt Nam,,,,,\r\n1.1.2,,,Brazil,,,,,\r\n1.1.3,,,Mỹ,,,,,\r\n1.2,,Loại 2,,,,,,\r\n1.2.1,,,Việt Nam,,,,,\r\n1.2.2,,,Mỹ,,,,,\r\n2,Cà phê Đen,,,,,,,\r\n2.1,,Loại 2,,,,,,\r\n2.1.1,,,Việt Nam,,,,,\r\n'
        ### Thinking
        The provided content has two header rows. The first row lists potential feature names (`ID`, `Cà phê`, `Loại`, `Nhập Khẩu`, `Thời gian`, `Thu nhập`, etc.). The second row provides specific values (`Hè`, `Đông`, `Thấp`, `Trung Bình`, `Cao`) under columns related to `Thời gian` and `Thu nhập`. This indicates that `Thời gian` and `Thu nhập` are feature columns with values listed in the second header row.
        The initial columns (`Cà phê`, `Loại`, `Nhập Khẩu`) show a clear hierarchical structure in the data rows, where values are nested within the preceding columns (e.g., `Loại 1` is under `Cà phê thường`, `Việt Nam` is under `Loại 1`). This structure defines the rows of the table.
        The combination of multiple header rows defining feature columns and hierarchical structure in the initial columns defining the rows is characteristic of a matrix table. The columns defining the hierarchical structure (`Cà phê`, `Loại`, `Nhập Khẩu`) are the feature rows.
        We do not include `ID` as this is not a feature row but rather an index or identifier for the records.

        ### Is Matrix Table?
        Yes

        ### Name of Feature Rows
        Cà phê,Loại,Nhập Khẩu 
        ### Name of Feature Cols
        Thời gian,Thu nhập
        
        Example 4
        ### Content
        'TT,Quan hệ,Tên \r\n1,Cha ,Đổng\r\n2,Mẹ,Thị\r\n3,Chồng,Nam\r\n4,Vợ,Lan\r\n5,Con trai 1,Tú\r\n6,Con trai 2,Tuấn\r\n'
        ### Thinking
        The provided content has a single header row: `TT,Quan hệ,Tên`. The subsequent rows contain data where each row represents a distinct record with values corresponding to the columns defined in the header. There is no indication of multiple header rows defining feature columns or a hierarchical structure in the data rows where values are nested within preceding columns. This structure is typical of a flatten table.

        ### Is Matrix Table?
        No

        ### Name of Feature Rows
        None
        ### Name of Feature Cols
        None
        
        Now solve
        ### Content
        {excel_content}
    """
    # Create the message
    message = HumanMessage(content=prompt)

    # Invoke the model
    try:
        response = llm.invoke([message])
        print(response.content)
    except Exception as e:
        print(f"Error invoking the model: {e}")
    return parse_llm_feature_name_output(response.content)


def process_natural_language_query(query, feature_rows, feature_cols, row_dict, col_dict, llm):
    """
    Parse a natural language query to extract row and column selections.
    
    Args:
        query (str): Natural language query
        feature_rows (list): List of feature row names
        feature_cols (list): List of feature column names  
        row_dict (dict): Nested dictionary of row hierarchy
        col_dict (dict): Nested dictionary of column hierarchy
        llm: Language model instance
        
    Returns:
        dict: Dictionary with 'row_selection' and 'col_selection' keys
    """
    
    # Convert dictionaries to JSON strings for the prompt
    import json
    
    row_structure = json.dumps(row_dict, ensure_ascii=False, indent=2)
    col_structure = json.dumps(col_dict, ensure_ascii=False, indent=2)
    
    prompt = f"""You are an **expert interpreter of queries for hierarchically structured tabular data**. Your core mission is to deconstruct natural language requests and map them with utmost precision to specific row and column selections. This requires mastery in navigating multi-level vertical headers (`Feature Rows` with `Row Hierarchy`) and multi-level horizontal headers (`Feature Cols` with `Column Hierarchy`) to guarantee the accuracy of retrieved data, irrespective of the data's specific domain (e.g., financial, product, operational).

**Instructions**

1.  **Deep Query Deconstruction:** Meticulously dissect the user's natural language. Isolate all explicit and implicit cues for row selection (tied to `Feature Rows`) and column selection (tied to `Feature Cols`).

2.  **Precision in Row Selection (`Row Choose`):**
    *   Iterate through `Feature Rows` hierarchically.
    *   For each `Feature Row`: Pinpoint user-specified values. If a level in the `Row Hierarchy` is unaddressed by the query (e.g., 'Loại' is skipped when 'Cà phê' and 'Nhập Khẩu' are given) or if an "all-encompassing" term is used for that level, assign `Undefined`. This signals inclusion of all valid sub-options.

3.  **Strategic Column Selection & Formatting (`Col Choose`):**
    *   Identify all targeted `Feature Cols` and their sub-columns. **Crucially, if a sub-column (e.g., "Hè") is named, its parent `Feature Col` (e.g., "Thời gian") MUST be inferred.**
    *   **Strict Output Formatting for `Col Choose`:**
        *   **Specific Sub-column Path:** `'Parent Feature Col - Full Path to Leaf Sub-column'` (e.g., `'Thời gian - Năm 2024 - Hè'`).
        *   **General Parent (with sub-columns):** If a `Feature Col` with sub-columns (like 'Thời gian') is requested generally (e.g., "thời gian thu hoạch"), output **ONLY the parent `Feature Col` name** (e.g., `'Thời gian'`).
        *   **Parent (no sub-columns):** If a `Feature Col` has no sub-columns (e.g., 'Đơn giá'), output its name directly (e.g., `'Đơn giá'`).
    *   Compile these into the `Col Choose` list.

4.  **Transparent Reasoning (`Thinking` - Non-Negotiable):**
    *   Articulate your entire decision path:
        *   **Query Essence:** What is the user's core need?
        *   **Row Logic:** How did query terms map to `Feature Row` values or `Undefined`? Justify every `Undefined`.
        *   **Column Logic:** How were `Feature Cols`/sub-columns identified? How were parents inferred? **Critically, demonstrate the precise application of the `Col Choose` formatting rules (Instruction 3.b).**

5.  **Graceful Handling of Unmatched Terms:**
    *   If the query mentions terms for rows or columns that are absent from the provided `Row Hierarchy` or `Column Hierarchy`, these terms are to be disregarded. Focus solely on mapping existing, valid elements.
    
**Input Format**
The system relies on the following precisely structured inputs:

### Query:
The user's verbatim natural language request, provided as a single string.
*Example:* `"Tôi muốn xem thời gian thu hoạch Hè của cà phê đen từ Việt Nam"`

### Feature Rows:
An ordered list of strings, meticulously defining the sequence of vertical row categorization, from the broadest category to the most granular.
*Example:* `['Cà phê', 'Loại', 'Nhập Khẩu']`

### Row Hierarchy:
**A valid JSON string** is mandatory. This string encapsulates a nested dictionary structure that maps out the complete hierarchical relationships for `Feature Rows`. Keys represent category values, leading to further nested dictionaries or, at the lowest level, a list of specific string identifiers.
*Example*:
{{
  "Cà phê thường": {{
    "Loại 1": ["Việt Nam", "Brazil", "Mỹ"],
    "Loại 2": ["Việt Nam", "Mỹ"]
  }},
  "Cà phê Đen": {{
    "Loại 2": ["Việt Nam"]
  }}
}}

### Feature Cols:
A list of strings, naming all top-level column headers available in the dataset.
*Example:* `['Thời gian', 'Thu nhập', 'Đơn giá', 'Ghi chú đặc biệt']`

### Column Hierarchy:
**A valid JSON string** is mandatory. This string details the sub-column structure for `Feature Cols`.
*   Only `Feature Cols` possessing sub-columns *need* to be included as top-level keys.
*   Sub-columns are represented as nested dictionaries; a leaf sub-column is denoted by an empty dictionary `{{}}`.
*   **Crucially, `Feature Cols` that lack sub-columns (e.g., 'Đơn giá', 'Ghi chú đặc biệt') can either be explicitly defined with an empty dictionary (e.g., `"Đơn giá": {{}}`) or, more commonly, be entirely omitted from this JSON string. The interpreter MUST correctly identify them as direct data columns in both scenarios.**
*Example*:
{{
  "Thời gian": {{
    "Hè": {{}},
    "Đông": {{}}
  }},
  "Thu nhập": {{
    "Thấp": {{}},
    "Trung Bình": {{}},
    "Cao": {{}}
  }},
  "Đơn giá": {{}}
}}

**Output Format**
You MUST strictly adhere to the following output format. Output ONLY the specified sections (`### Thinking:`, `### Row Choose`, `### Col Choose`) and their content as described. Do not include any other text, introductions, or summaries.

### Thinking:
You MUST strictly adhere to the following output format. Output ONLY the specified sections (`### Thinking:`, `### Row Choose`, `### Col Choose`) and their content as described. Do not include any other text, introductions, or summaries.

### Row Choose
A **JSON string** representing a dictionary.
*   Keys are the names of the `Feature Rows` (as provided in the `Feature Rows` input).
*   The value for each `Feature Row` key must be:
    *   A JSON array of strings, representing the specific class(es)/value(s) selected for that `Feature Row`.
    *   The string literal `"Undefined"` (e.g., `"Loại": "Undefined"`) if no specific value was selected for that `Feature Row`.

*Example for Row Choose:*
{{
  "Cà phê": ["Cà phê Đen"],
  "Loại": "Undefined",
  "Nhập Khẩu": ["Việt Nam"]
}}

{{
  "Cà phê": ["Cà phê thường"],
  "Loại": "Undefined",
  "Nhập Khẩu": "Undefined"
}}

### Col Choose
A **JSON string** representing a list of strings. Each string in the list represents a selected column and MUST adhere to the following formats, as determined by Instruction 3:
*   `'Parent Feature Col - Sub-column'` (e.g., `"Thời gian - Hè"`) if a specific sub-column is selected or inferred.
*   `'Parent Feature Col'` (e.g., `"Thời gian"`) if a `Feature Col` with sub-columns is requested generally.
*   `'Parent Feature Col'` (e.g., `"Đơn giá"`) if the `Feature Col` has NO sub-columns.

*Example for Col Choose:*

# Query: "thời gian Hè và thu nhập Trung Bình của cà phê"
["Thời gian - Hè", "Thu nhập - Trung Bình"]

["Thời gian", "Đơn giá"]

**Example 1**
### Query: "Tôi muốn xem thời gian thu hoạch của cà phê đen từ Việt Nam"
### Feature Rows: ['Cà phê', 'Loại', 'Nhập Khẩu']
### Row Hierarchy: 
{{
  "Cà phê thường": {{
    "Loại 1": ["Việt Nam", "Brazil", "Mỹ"],
    "Loại 2": ["Việt Nam", "Mỹ"]
  }},
  "Cà phê Đen": {{
    "Loại 2": ["Việt Nam"]
  }}
}}

### Feature Cols: ['Thời gian', 'Thu nhập']
### Column Hierarchy: 
Thời gian:
{{
  "Thời gian": {{
    "Hè": {{}},
    "Đông": {{}}
  }},
  "Thu nhập": {{
    "Thấp": {{}},
    "Trung Bình": {{}},
    "Cao": {{}}
  }}
}}

### Thinking:
**1. Query Analysis:**
The user's request is: "Tôi muốn xem thời gian thu hoạch của cà phê đen từ Việt Nam."
This translates to: Show harvest time for "cà phê đen" (black coffee) from "Việt Nam" (Vietnam).
- Row-related keywords: "cà phê đen", "Việt Nam".
- Column-related keywords: "thời gian thu hoạch" (harvest time).

**2. Row Tracing (Adhering to Instruction 2):**
The `Feature Rows` are `['Cà phê', 'Loại', 'Nhập Khẩu']`.
- For 'Cà phê': The query specifies "cà phê đen". This maps to 'Cà phê Đen' in the `Row Hierarchy`. So, `'Cà phê': ['Cà phê Đen']`.
- For 'Loại': The query specifies "Cà phê Đen" and "Việt Nam". Tracing `Row Hierarchy`: 'Cà phê Đen' has 'Loại 2', under which 'Việt Nam' exists. However, the query *does not explicitly mention any 'Loại'*. As per Instruction 2, when a level in the hierarchy is unaddressed by the query between specified parent and child levels, it becomes `Undefined`. Thus, `'Loại': "Undefined"`. This correctly implies that if 'Cà phê Đen' from 'Việt Nam' existed under multiple 'Loại' values, all would be included (though in this specific hierarchy, only 'Loại 2' is applicable).
- For 'Nhập Khẩu': The query specifies "từ Việt Nam". This maps to 'Việt Nam' under the selected 'Cà phê Đen' and implicitly covered 'Loại 2'. So, `'Nhập Khẩu': ['Việt Nam']`.

The resulting `Row Choose` selection, before formatting as a JSON string, is:
{{'Cà phê': ['Cà phê Đen'], 'Loại': 'Undefined', 'Nhập Khẩu': ['Việt Nam']}}

**3. Column Tracing & Formatting (Adhering to Instruction 3):**
The `Feature Cols` are `['Thời gian', 'Thu nhập']`.
- The query mentions "thời gian thu hoạch", which clearly refers to the `Feature Col` 'Thời gian'.
- The `Column Hierarchy` shows that 'Thời gian' has sub-columns ('Hè', 'Đông').
- The query *does not* specify a particular sub-column of 'Thời gian' (like 'Hè' or 'Đông'). It's a general request for 'Thời gian'.
- As per **Instruction 3, Format 2 (General Parent with Sub-columns)**, when a `Feature Col` that possesses sub-columns is requested generally, ONLY the parent `Feature Col` name is outputted.
- Therefore, 'Thời gian' is selected. No other columns are requested.

The resulting `Col Choose` selection, before formatting as a JSON string, is: `['Thời gian']`

### Row Choose
{{
  "Cà phê": ["Cà phê Đen"],
  "Loại": "Undefined",
  "Nhập Khẩu": ["Việt Nam"]
}}

### Col Choose
["Thời gian"]


**Example 2**
### Query: "cho tôi biết điểm trung bình 2 kì môn lý của Trần Bích Thu"
### Feature Rows: ['Tên', 'Môn']
### Row Hierarchy: 
{{
  "Trần Bích Thu": ["Lý", "Toán", "Hóa", "Sinh"],
  "Nguyễn Nam": ["Lý", "Toán", "Hóa", "Sinh"]
}}

### Feature Cols: ['Chi Phí']
### Column Hierarchy: 
Thời gian:
{{
  "Chi Phí": {{
    "Cấp 1": ["Học kì 1", "Học kì 2", "Trung Bình"],
    "Cấp 2": ["Học kì 1", "Học kì 2", "Trung Bình"],
    "Tổng cộng": {{}}
  }}
}}

### Thinking:
**1. Query Analysis:**
The user's request is: "cho tôi biết điểm trung bình 2 kì môn lý của Trần Bích Thu".
This translates to: Show the average score over 2 semesters for the subject "Lý" (Physics) for the student "Trần Bích Thu". The term "điểm" (score/points) is contextually linked to "Chi Phí" as it's the only `Feature Col`. "Trung bình 2 kì" implies an average related to semesters.

- Row-related keywords: "Trần Bích Thu", "môn lý".
- Column-related keywords: "điểm trung bình 2 kì". This implies the sub-column "Trung Bình".

**2. Row Tracing (Adhering to Instruction 2):**
The `Feature Rows` are `['Tên', 'Môn']`.
- For 'Tên': The query specifies "Trần Bích Thu". This maps directly. So, `'Tên': ['Trần Bích Thu']`.
- For 'Môn': The query specifies "môn lý". This maps to 'Lý'. 'Lý' is a valid value for 'Môn' under 'Trần Bích Thu' in the `Row Hierarchy`. So, `'Môn': ['Lý']`.

The resulting `Row Choose` selection, before formatting as a JSON string, is:
`{{'Tên': ['Trần Bích Thu'], 'Môn': ['Lý']}}`

**3. Column Tracing & Formatting (Adhering to Instruction 3):**
The `Feature Col` is `['Chi Phí']`.
- The query asks for "điểm trung bình 2 kì". "Điểm" maps to the `Feature Col` 'Chi Phí'.
- The term "trung bình" directly points to the sub-column 'Trung Bình'.
- Looking at the `Column Hierarchy` for 'Chi Phí':
    - 'Chi Phí' has sub-categories 'Cấp 1' and 'Cấp 2'.
    - Both 'Cấp 1' and 'Cấp 2' contain 'Trung Bình' as a leaf sub-column.
- The query does not specify "Cấp 1" or "Cấp 2". It asks for "trung bình 2 kì", which implies the 'Trung Bình' that is associated with semester data. Since 'Trung Bình' appears under both 'Cấp 1' and 'Cấp 2' (which are the levels containing semester data), we should select 'Trung Bình' from both these contexts.
- As per **Instruction 3, Format 1 (Specific Sub-column)**, the format is `'Parent Feature Col - Sub-column'`. In a multi-level scenario, "Sub-column" refers to the full path to the leaf.
    - The path to 'Trung Bình' under 'Cấp 1' is 'Chi Phí - Cấp 1 - Trung Bình'.
    - The path to 'Trung Bình' under 'Cấp 2' is 'Chi Phí - Cấp 2 - Trung Bình'.

The resulting `Col Choose` selection, before formatting as a JSON string, is:
`['Chi Phí - Cấp 1 - Trung Bình', 'Chi Phí - Cấp 2 - Trung Bình']`

### Row Choose
{{
  "Tên": ["Trần Bích Thu"],
  "Môn": ["Lý"]
}}

### Col Choose
["Chi Phí - Cấp 1 - Trung Bình", "Chi Phí - Cấp 2 - Trung Bình"]

Now solve this query
### Query: 
{query}
### Feature Rows: 
{feature_rows}
### Row Hierarchy: 
{row_structure}
### Feature Cols: 
{feature_cols}  
### Column Hierarchy: 
{col_structure}

### Thinking: 
"""

    # Create the message
    message = HumanMessage(content=prompt)

    # Invoke the model
    response = llm.invoke([message])
    print("LLM Response:")
    print(response.content)
    return response.content
