from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np 
from thefuzz import fuzz, process

def read_file(excel_file_path, show=False):
    try:
        df = pd.read_excel(excel_file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        exit(1)
    excel_content = df.to_csv(index=False)
    if show:
        # beautiful print for the context (in table format)
        print("Excel Content:")
        print(df.to_string(index=False))
    return excel_content


def get_feature_name_content(excel_file_path, feature_names, similarity_threshold=80):
    """
    Get the content of feature names from the Excel file, using fuzzy matching for loose column name matching.
    Prints mismatch cases separately for review.
    
    Parameters:
    - excel_file_path (str): Path to the Excel file.
    - feature_names (dict): Dictionary containing 'feature_rows' and/or 'feature_cols' with expected feature names.
    - similarity_threshold (int): Minimum similarity score (0-100) to consider a match. Default is 80.
    
    Returns:
    - tuple: (str, dict)
        - str: Formatted content of matched features and their unique values.
        - dict: A dictionary with 'feature_rows' and 'feature_cols' keys containing matched columns.
    """
    # Read the Excel file
    df = pd.read_excel(excel_file_path)
    feature_name_content = ""
    result = {'feature_rows': [], 'feature_cols': []}  # Dictionary to store results for both types
    
    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        # Get the first level of MultiIndex for matching
        excel_columns_for_matching = [col[0] for col in df.columns]
        excel_columns_full = df.columns.tolist()  # Keep full column names for actual access
    else:
        excel_columns_for_matching = df.columns.tolist()
        excel_columns_full = df.columns.tolist()
    
    mismatch_log = []  # To store mismatch cases
    
    # Process feature_rows if they exist
    if 'feature_rows' in feature_names and feature_names['feature_rows']:
        for feature in feature_names['feature_rows']:
            # Use fuzzy matching to find the closest column name (using first level for MultiIndex)
            best_match_first_level, similarity_score = process.extractOne(feature, excel_columns_for_matching, scorer=fuzz.token_sort_ratio)
            
            # Check if the match meets the similarity threshold
            if similarity_score >= similarity_threshold:
                # Find the full column name that corresponds to the matched first level
                if isinstance(df.columns, pd.MultiIndex):
                    # Find the first column that matches the first level
                    matched_full_column = None
                    for full_col in excel_columns_full:
                        if full_col[0] == best_match_first_level:
                            matched_full_column = full_col
                            break
                    actual_column_to_use = matched_full_column
                else:
                    actual_column_to_use = best_match_first_level
                
                # Get unique values, convert to list for JSON compatibility
                unique_values = df[actual_column_to_use].dropna().unique().tolist()
                # Build the string output
                feature_name_content += f"Feature: {feature}\n"
                feature_name_content += f"{unique_values}\n"
                # Store in dictionary
                result['feature_rows'].append(actual_column_to_use)
                # Log potential mismatches (even if above threshold, for review)
                if similarity_score < 100:  # Not a perfect match
                    mismatch_log.append(f"Feature Row Mismatch - Expected: '{feature}', Matched to: '{best_match_first_level}', Similarity: {similarity_score}%")
            else:
                # No good match, still include in output but with no values
                feature_name_content += f"Feature: {feature}\n"
                feature_name_content += "[]\n"
                # Store in dictionary
                result['feature_rows'].append(None)
                mismatch_log.append(f"Feature Row No Match - Expected: '{feature}', Best was: '{best_match_first_level}', Similarity: {similarity_score}%")
    
    # Process feature_cols if they exist
    if 'feature_cols' in feature_names and feature_names['feature_cols']:
        for feature in feature_names['feature_cols']:
            # Use fuzzy matching to find the closest column name (using first level for MultiIndex)
            best_match_first_level, similarity_score = process.extractOne(feature, excel_columns_for_matching, scorer=fuzz.token_sort_ratio)
            
            # Check if the match meets the similarity threshold
            if similarity_score >= similarity_threshold:
                # Find the first column that matches the first level (same as feature_rows)
                if isinstance(df.columns, pd.MultiIndex):
                    # Find the first column that matches the first level
                    matched_full_column = None
                    for full_col in excel_columns_full:
                        if full_col[0] == best_match_first_level:
                            matched_full_column = full_col
                            break
                    actual_column_to_use = matched_full_column
                else:
                    actual_column_to_use = best_match_first_level
                
                # Get unique values, convert to list for JSON compatibility
                unique_values = df[actual_column_to_use].dropna().unique().tolist()
                
                # Build the string output
                feature_name_content += f"Feature: {feature}\n"
                feature_name_content += f"{unique_values}\n"
                # Store in dictionary
                result['feature_cols'].append(actual_column_to_use)
                # Log potential mismatches (even if above threshold, for review)
                if similarity_score < 100:  # Not a perfect match
                    mismatch_log.append(f"Feature Col Mismatch - Expected: '{feature}', Matched to: '{best_match_first_level}', Similarity: {similarity_score}%")
            else:
                # No good match, still include in output but with no values
                feature_name_content += f"Feature: {feature}\n"
                feature_name_content += "[]\n"
                # Store in dictionary
                result['feature_cols'].append(None)
                mismatch_log.append(f"Feature Col No Match - Expected: '{feature}', Best was: '{best_match_first_level}', Similarity: {similarity_score}%")

    # Print mismatch cases separately
    if mismatch_log:
        print("Mismatch Cases:")
        for log in mismatch_log:
            print(log)
    
    return feature_name_content, result


def format_nested_dict_for_llm(nested_input_dict, initial_indent_level=0, indent_char="  "):
    """
    Converts a nested dictionary (which may contain lists as leaf collections)
    into an indented string representation suitable for LLMs.

    Args:
        nested_input_dict (dict): The nested dictionary to format.
        initial_indent_level (int): The starting indentation level.
        indent_char (str): The string to use for each indentation level.

    Returns:
        str: A multi-line string representing the nested structure.
    """

    # --- Recursive helper function ---
    def _recursive_format_to_lines(current_item, current_level):
        lines_output = []
        current_indent_str = indent_char * current_level

        if isinstance(current_item, dict):
            if not current_item:
                return [] 

            for key in current_item.keys():
                value = current_item[key]
                
                if isinstance(value, dict) and not value:
                    lines_output.append(f"{current_indent_str}{key}")
                else:
                    lines_output.append(f"{current_indent_str}{key}:")
                
                sub_lines = _recursive_format_to_lines(value, current_level + 1)
                lines_output.extend(sub_lines)
                
        elif isinstance(current_item, list):
            for sub_item_in_list in current_item: 
                lines_output.append(f"{current_indent_str}- {sub_item_in_list}")

        return lines_output

    if not isinstance(nested_input_dict, dict):
        return str(nested_input_dict) 

    all_formatted_lines = _recursive_format_to_lines(nested_input_dict, initial_indent_level)
    
    return "\n".join(all_formatted_lines)

