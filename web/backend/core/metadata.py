import pandas as pd
import numpy as np 

def get_number_of_row_header(file_path):
    import logging
    logger = logging.getLogger(__name__)
    
    # Bước 1: Đọc tệp Excel với header đa cấp (2 dòng đầu)
    logger.info(f"Reading Excel file for row header analysis: {file_path}")
    df = pd.read_excel(file_path)
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"DataFrame columns: {df.columns}")
    logger.info(f"DataFrame columns type: {type(df.columns)}")

    number_of_row_header = 1
    
    try:
        first_column = df.columns[0]
        logger.info(f"First column: {first_column}")
        logger.info(f"First column type: {type(first_column)}")
        
        first_column_data = df[first_column]
        logger.info(f"First column data type: {type(first_column_data)}")
        logger.info(f"First column data shape: {first_column_data.shape if hasattr(first_column_data, 'shape') else 'No shape'}")
        
        for i, v in enumerate(first_column_data):
            logger.info(f"Row {i}: {v} (is nan: {pd.isna(v)})")
            if pd.isna(v):
                number_of_row_header += 1
            else:
                break
            if i > 10:  # Prevent infinite loop
                logger.warning("Stopping header analysis after 10 rows")
                break
                
    except Exception as e:
        import traceback
        logger.error(f"Error in get_number_of_row_header: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise
    
    logger.info(f"Number of row headers determined: {number_of_row_header}")
    return number_of_row_header



def convert_df_headers_to_nested_dict(df, column_names_list):
    """
    Converts portions of a DataFrame's MultiIndex columns into a nested dictionary,
    starting from a list of specified top-level column names.
    If all children of a node are leaf nodes (or pruned by 'Header'),
    that node will map to a list of its children's keys.
    The process stops building a branch if a column component named 'Header' is encountered.
    
    Parameters:
    - df (DataFrame): Input DataFrame with MultiIndex columns
    - column_names_list (list): List of top-level column names to process
    
    Returns:
    - dict: Combined nested dictionary representing the hierarchical structure of all specified columns
    """

    def _recursive_build(current_column_structure):
        nested_structure = {}
        
        if current_column_structure.empty or current_column_structure.nlevels == 0:
            return {} # Base case: leaf node or empty structure returns {}

        try:
            unique_values_at_this_level = list(current_column_structure.get_level_values(0).unique())
        except IndexError: 
            return {}

        for value in unique_values_at_this_level:
            if pd.isna(value):
                continue
            if value == 'Header':
                continue 

            mask_for_current_value = current_column_structure.get_level_values(0) == value
            columns_for_this_value_branch = current_column_structure[mask_for_current_value]

            child_result = {} # Default to empty dict if no further levels
            if columns_for_this_value_branch.nlevels > 1:
                next_level_structure = columns_for_this_value_branch.droplevel(0)
                if not next_level_structure.empty and next_level_structure.nlevels > 0 :
                    child_result = _recursive_build(next_level_structure)
                # If next_level_structure is empty or has 0 levels, child_result remains {}
                # which signifies this 'value' is a leaf from its parent's perspective.
            # If columns_for_this_value_branch.nlevels <= 1, it means 'value' is a pre-leaf.
            # The next_level_structure would be empty/0-levels, so _recursive_build on it
            # would return {}, making child_result = {}.

            # Check if child_result (representing children of 'value')
            # consists entirely of leaf nodes (which are represented as empty dicts themselves).
            if isinstance(child_result, dict) and child_result and \
               all(isinstance(v, dict) and not v for v in child_result.values()):
                # If so, 'value' maps to a list of its children's keys.
                nested_structure[value] = sorted(list(child_result.keys())) # Sort for consistent order
            else:
                # Otherwise, 'value' maps to the structured dictionary of its children.
                # This includes cases where child_result is {} (value is a leaf itself),
                # or where children are a mix of lists and dicts, or just one non-leaf child.
                nested_structure[value] = child_result
        
        return nested_structure

    # Validate inputs
    if not isinstance(column_names_list, list):
        raise ValueError("column_names_list must be a list")
    
    if not column_names_list:
        return {}

    if not isinstance(df.columns, pd.MultiIndex):
        # For non-MultiIndex columns, return empty dict for each column name
        return {col_name: {} for col_name in column_names_list}

    combined_result = {}
    
    for start_column_top_level_name in column_names_list:
        try:
            if start_column_top_level_name not in df.columns.get_level_values(0):
                combined_result[start_column_top_level_name] = {}
                continue
            
            top_level_mask = df.columns.get_level_values(0) == start_column_top_level_name
            relevant_columns = df.columns[top_level_mask]
        except Exception: 
            combined_result[start_column_top_level_name] = {}
            continue

        if relevant_columns.empty:
            combined_result[start_column_top_level_name] = {}
            continue

        # If start_column_top_level_name itself has no sub-levels after selection,
        # or if its only sub-level would be pruned by 'Header'.
        if relevant_columns.nlevels <= 1: 
            # Check if the "next level" would consist only of 'Header' or be empty
            sub_structure_check = relevant_columns.droplevel(0)
            if sub_structure_check.empty or \
               (sub_structure_check.nlevels == 1 and \
                list(sub_structure_check.get_level_values(0).unique()) == ['Header']):
                combined_result[start_column_top_level_name] = {}
                continue
            # Fall through if there's actual structure to process below.

        structure_for_recursion = relevant_columns.droplevel(0)
        
        if structure_for_recursion.empty or structure_for_recursion.nlevels == 0:
            combined_result[start_column_top_level_name] = {}
            continue

        combined_result[start_column_top_level_name] = _recursive_build(structure_for_recursion)

    return combined_result

def convert_df_rows_to_nested_dict(df_input, hierarchy_columns_list, undefined_label="Undefined"):
    """
    Converts DataFrame rows into a nested dictionary based on hierarchy columns.
    
    Parameters:
    - df_input (DataFrame): Input DataFrame
    - hierarchy_columns_list (list): List of column references (can be strings for regular columns 
                                   or tuples for MultiIndex columns)
    - undefined_label (str): Label to use for undefined values, defaults to "Undefined"
    
    Returns:
    - dict: Nested dictionary representing the hierarchical structure
    """
    df_copy = df_input.copy()

    # Helper function to determine if a structure is redundant (only Undefined or empty)
    def _is_redundant_undefined_child(child_structure, current_undefined_label):
        if not child_structure: # Handles {} or []
            return True
        
        if isinstance(child_structure, list):
            return all(item == current_undefined_label for item in child_structure)
        
        if isinstance(child_structure, dict):
            for key, deeper_structure in child_structure.items():
                if key != current_undefined_label:
                    return False # Contains a meaningful key
                # If key is undefined_label, check its child structure
                if not _is_redundant_undefined_child(deeper_structure, current_undefined_label):
                    return False # This 'Undefined' child has meaningful content
            return True # All keys were undefined_label and their children were redundant
        
        return False # Should not be reached for dict/list/empty

    def _recursive_build(current_df_slice, level_idx):
        if level_idx >= len(hierarchy_columns_list):
            return {} 

        col_reference = hierarchy_columns_list[level_idx]
        
        # Handle both regular column names (strings) and MultiIndex column tuples
        try:
            selected_data = current_df_slice[col_reference] 
        except KeyError:
            # If direct access fails, try to find the column in available columns
            available_cols = current_df_slice.columns.tolist()
            if col_reference in available_cols:
                selected_data = current_df_slice[col_reference]
            else:
                # Return empty dict if column not found
                return {}

        series_to_process = None
        if isinstance(selected_data, pd.DataFrame):
            import logging
            logger = logging.getLogger(__name__)
            
            if selected_data.empty or len(selected_data.columns) == 0:
                logger.warning(f"Selected DataFrame is empty or has no columns for column {col_reference}")
                return {}
            
            # If selected_data (DataFrame) has no columns, .iloc[:, 0] will raise IndexError.
            # This error will propagate as per "để lỗi tự báo".
            try:
                series_to_process = selected_data.iloc[:, 0]
            except IndexError as e:
                logger.error(f"IndexError accessing first column of DataFrame: {e}")
                logger.error(f"DataFrame shape: {selected_data.shape}")
                logger.error(f"DataFrame columns: {selected_data.columns}")
                raise
        else: # Assumed to be pd.Series if not DataFrame
            series_to_process = selected_data
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Selected data is Series with shape: {series_to_process.shape if hasattr(series_to_process, 'shape') else 'No shape'}")
        
        # .dropna().unique() will raise AttributeError if series_to_process is not Series-like.
        # This error will propagate.
        unique_vals = list(series_to_process.dropna().unique())

        # Build the dictionary for the current level first
        temp_current_level_dict = {}
        for val in unique_vals:
            next_slice = current_df_slice[series_to_process == val]
            child_dict = _recursive_build(next_slice, level_idx + 1)
            temp_current_level_dict[val] = child_dict
        
        # Prune redundant "Undefined" keys
        final_current_level_dict = {}
        for key, sub_structure in temp_current_level_dict.items():
            if key == undefined_label and _is_redundant_undefined_child(sub_structure, undefined_label):
                continue # Skip this redundant "Undefined" key
            final_current_level_dict[key] = sub_structure
        
        # Convert to list of keys if all children are terminal (empty dicts)
        if final_current_level_dict and all(isinstance(v, dict) and not v for v in final_current_level_dict.values()):
            return list(final_current_level_dict.keys()) # No sort, as per user's last snippet
        else:
            return final_current_level_dict

    # Validate inputs
    if not isinstance(hierarchy_columns_list, list):
        raise ValueError("hierarchy_columns_list must be a list")
    
    if not hierarchy_columns_list:
        return {}
    
    # Errors from invalid inputs or structure will propagate.
    return _recursive_build(df_copy, 0)