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


def format_nested_dict_for_llm(nested_input_dict, feature_names=None, dict_type="row"):
    """
    Formats nested dictionary for LLM with specific formatting based on type.
    
    Args:
        nested_input_dict (dict): The nested dictionary to format.
        feature_names (list): List of feature names for proper labeling.
        dict_type (str): "row" for row hierarchy, "col" for column hierarchy.
    
    Returns:
        str: A formatted string representation.
    """
    if dict_type == "row":
        return format_row_dict_for_llm(nested_input_dict, feature_names)
    else:
        return format_col_dict_for_llm(nested_input_dict)


def format_row_dict_for_llm(row_dict, feature_names):
    """
    Formats row dictionary in hierarchical format with feature name labels.
    
    Example output:
    sản phẩm: cà phê
        loại: cà phê đen
            nguồn gốc: việt nam, brazil
    """
    if not row_dict or not feature_names:
        return ""
    
    def format_level(data, feature_level, current_path="", indent_level=0):
        lines = []
        indent = "    " * indent_level
        
        if feature_level >= len(feature_names):
            return lines
            
        feature_name = feature_names[feature_level]
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Format the current level
                lines.append(f"{indent}{feature_name}: {key}")
                
                # Recursively format next level
                if isinstance(value, dict):
                    sub_lines = format_level(value, feature_level + 1, 
                                           current_path + f"/{key}", indent_level + 1)
                    lines.extend(sub_lines)
                elif isinstance(value, list):
                    # This is the leaf level - format as comma-separated values
                    if value and feature_level + 1 < len(feature_names):
                        next_feature_name = feature_names[feature_level + 1]
                        formatted_values = ", ".join([v for v in value])
                        lines.append(f"{indent}    {next_feature_name}: {formatted_values}")
        
        return lines
    
    formatted_lines = format_level(row_dict, 0)
    return "\n".join(formatted_lines)


def format_col_dict_for_llm(col_dict):
    """
    Formats column dictionary in level-based format supporting unlimited hierarchical levels.
    
    Example output:
    level_1: thời gian
        level_2: năm 2024
            level_3: quý 1
                level_4: tháng 1, tháng 2, tháng 3
            level_3: quý 2
                level_4: tháng 4, tháng 5, tháng 6
    level_1: đơn giá
    """
    if not col_dict:
        return ""
    
    def format_level(data, level=1, indent_level=0):
        """
        Recursively format hierarchical column structure.
        
        Args:
            data: Dictionary or other data structure to format
            level: Current hierarchical level (1-based)
            indent_level: Current indentation level for display
            
        Returns:
            List of formatted lines
        """
        lines = []
        indent = "    " * indent_level
        level_name = f"level_{level}"
        
        if isinstance(data, dict):
            if not data:
                # Empty dict - this is a leaf node, don't add anything
                return lines
                
            # Group items by whether they have sub-structure or are leaves
            items_with_dict_subs = []
            items_with_list_subs = []
            leaf_items = []
            
            for key, value in data.items():
                if isinstance(value, dict) and value:
                    # Has dictionary sub-structure
                    items_with_dict_subs.append((key, value))
                elif isinstance(value, list) and value:
                    # Has list sub-structure
                    items_with_list_subs.append((key, value))
                else:
                    # Is a leaf (empty dict, empty list, None, or simple value)
                    leaf_items.append(key)
            
            # Format leaf items first (if any) as comma-separated list
            if leaf_items:
                formatted_leaves = ", ".join([item for item in leaf_items])
                lines.append(f"{indent}{level_name}: {formatted_leaves}")
            
            # Format items with dictionary sub-structure
            for key, value in items_with_dict_subs:
                lines.append(f"{indent}{level_name}: {key}")
                sub_lines = format_level(value, level + 1, indent_level + 1)
                lines.extend(sub_lines)
            
            # Format items with list sub-structure
            for key, value in items_with_list_subs:
                lines.append(f"{indent}{level_name}: {key}")
                # Format list items as the next level
                next_level_name = f"level_{level + 1}"
                next_indent = "    " * (indent_level + 1)
                formatted_list_items = ", ".join([item for item in value])
                lines.append(f"{next_indent}{next_level_name}: {formatted_list_items}")
        
        return lines
    
    # Process top-level items
    all_lines = []
    for main_col, sub_structure in col_dict.items():
        if isinstance(sub_structure, dict) and sub_structure:
            # Has sub-structure - format hierarchically
            all_lines.append(f"level_1: {main_col}")
            sub_lines = format_level(sub_structure, level=2, indent_level=1)
            all_lines.extend(sub_lines)
        else:
            # No sub-structure - just the main column
            all_lines.append(f"level_1: {main_col}")
    
    return "\n".join(all_lines)

