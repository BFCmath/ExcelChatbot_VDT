from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np 
import re
from .utils import read_file
from .prompt import DECOMPOSER_PROMPT, ROW_HANDLER_PROMPT, COL_HANDLER_PROMPT, FEATURE_ANALYSIS_PROMPT, SCHEMA_ANALYSIS_PROMPT
from .config import get_next_api_key, LLM_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm_instance():
    """Creates and returns an instance of the ChatGoogleGenerativeAI LLM."""
    api_key = get_next_api_key()
    return ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=api_key, temperature=0)

def get_schema(excel_content, feature_name_content):
    llm = get_llm_instance()
    # Create the prompt using the template from prompt.py
    prompt = SCHEMA_ANALYSIS_PROMPT.format(excel_content=excel_content, feature_name_content=feature_name_content)
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

def get_feature_names_from_headers(headers_content):
    """
    Get feature names from header content only (not full file content).
    
    Args:
        headers_content (str): CSV format of only the header rows
        
    Returns:
        dict: Dictionary containing 'is_matrix_table', 'feature_rows', and 'feature_cols'
    """
    llm = get_llm_instance()
    # Create the prompt using the template from prompt.py
    prompt = FEATURE_ANALYSIS_PROMPT.format(excel_content=headers_content)
    # Create the message
    message = HumanMessage(content=prompt)

    # Invoke the model
    try:
        response = llm.invoke([message])
        print(response.content)
    except Exception as e:
        print(f"Error invoking the model: {e}")
        raise
    return parse_llm_feature_name_output(response.content)

def get_feature_names(excel_file_path):
    llm = get_llm_instance()
    excel_content = read_file(excel_file_path)
    # Create the prompt using the template from prompt.py
    prompt = FEATURE_ANALYSIS_PROMPT.format(excel_content=excel_content)
    # Create the message
    message = HumanMessage(content=prompt)

    # Invoke the model
    try:
        response = llm.invoke([message])
        print(response.content)
    except Exception as e:
        print(f"Error invoking the model: {e}")
    return parse_llm_feature_name_output(response.content)


def splitter(query, feature_rows, feature_cols, row_structure, col_structure):
    """
    Advanced multi-agent query processing using decomposer, row handler, and column handler.
    
    Args:
        query (str): Natural language query
        feature_rows (list): List of feature row names
        feature_cols (list): List of feature column names  
        row_dict (dict): Nested dictionary of row hierarchy
        col_dict (dict): Nested dictionary of column hierarchy
        
    Returns:
        dict: Dictionary with 'row_selection' and 'col_selection' keys
    """
    llm = get_llm_instance()
    
    print("=== DECOMPOSER AGENT ===")
    # Step 1: Decomposer Agent - Split query into row and column keywords
    decomposer_prompt = DECOMPOSER_PROMPT.format(
        query=query,
        feature_rows=feature_rows,
        feature_cols=feature_cols,
        row_structure=row_structure,
        col_structure=col_structure
    )
    
    decomposer_message = HumanMessage(content=decomposer_prompt)
    decomposer_response = llm.invoke([decomposer_message])
    print("Decomposer Response:")
    print(decomposer_response.content)
    
    # Parse decomposer output
    decomposer_result = parse_decomposer_output(decomposer_response.content)
    row_keywords = decomposer_result['row_keywords']
    col_keywords = decomposer_result['col_keywords']
    
    print()
    print(f"Extracted Row Keywords: {row_keywords}")
    print(f"Extracted Col Keywords: {col_keywords}")
    
    print()
    print("=== ROW HANDLER AGENT ===")
    # Step 2: Row Handler Agent - Process row keywords
    row_handler_prompt = ROW_HANDLER_PROMPT.format(
        query=query,
        feature_rows=feature_rows,
        row_structure=row_structure,
        row_keywords=row_keywords
    )
    
    row_handler_message = HumanMessage(content=row_handler_prompt)
    row_handler_response = llm.invoke([row_handler_message])
    print("Row Handler Response:")
    print(row_handler_response.content)
    
    # Parse row handler output
    row_selection = parse_row_handler_output(row_handler_response.content)
    
    print()
    print("=== COL HANDLER AGENT ===")
    # Step 3: Column Handler Agent - Process column keywords
    col_handler_prompt = COL_HANDLER_PROMPT.format(
        col_structure=col_structure,
        query=query,
        col_keywords=col_keywords
    )
    
    col_handler_message = HumanMessage(content=col_handler_prompt)
    col_handler_response = llm.invoke([col_handler_message])
    print("Col Handler Response:")
    print(col_handler_response.content)
    
    # Parse column handler output
    col_selection = parse_col_handler_output(col_handler_response.content)
    
    print()
    print("=== FINAL RESULT ===")
    result = {
        'row_selection': row_selection,
        'col_selection': col_selection
    }
    print("Final Result:")
    print("Row Selection:")
    print(result['row_selection'])
    print()
    print("Col Selection:")
    print(result['col_selection'])
    return result


def parse_decomposer_output(output):
    """Parse decomposer agent output to extract row and column keywords."""
    result = {'row_keywords': [], 'col_keywords': []}
    current_section = None
    
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('### Row Keywords'):
            current_section = 'row_keywords'
        elif line.startswith('### Col Keywords'):
            current_section = 'col_keywords'
        elif line.startswith('### Thinking'):
            current_section = None  # Stop parsing when we reach thinking section
        elif line and current_section and line.startswith('-'):
            keyword = line.lstrip('- ').strip()  # Remove "- " prefix more robustly
            if keyword:  # Only add non-empty keywords
                result[current_section].append(keyword)
    
    return result


def parse_row_handler_output(output):
    """Parse row handler agent output to extract row identifier in hierarchical format."""
    lines = output.strip().split('\n')
    row_identifier_lines = []
    capturing = False
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('### Row Identifier'):
            capturing = True
            continue
        elif line_stripped.startswith('###') and capturing:
            # Stop when we hit another section
            break
        elif capturing:
            row_identifier_lines.append(line)
            
    return '\n'.join(row_identifier_lines).strip()


def parse_col_handler_output(output):
    """Parse col handler agent output to extract col identifier in hierarchical format."""
    lines = output.strip().split('\n')
    col_identifier_lines = []
    capturing = False
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('### Col Identifier'):
            capturing = True
            continue
        elif line_stripped.startswith('###') and capturing:
            break
        elif capturing:
            col_identifier_lines.append(line)
            
    return '\n'.join(col_identifier_lines).strip()
