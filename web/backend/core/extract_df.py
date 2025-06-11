"""
DataFrame Extraction and Filtering Module

This module handles the extraction and filtering of DataFrames based on 
hierarchical row and column selections from the multi-agent query system.
"""

import pandas as pd


def search_column_in_multiindex(df, column_name):
    """
    Search for a column name in MultiIndex columns and return the full tuple.
    
    Args:
        df: DataFrame with MultiIndex columns
        column_name: Name to search for
        
    Returns:
        tuple: Full MultiIndex tuple for the column, or None if not found
    """
    if not isinstance(df.columns, pd.MultiIndex):
        # If it's not a MultiIndex, search in the regular index
        if column_name in df.columns:
            return column_name
        return None

    for col_tuple in df.columns:
        if column_name in col_tuple:
            return col_tuple
    
    return None


def parse_row_paths(row_selection):
    """
    Parse hierarchical row selection into individual paths.
    
    Args:
        row_selection: String with hierarchical row structure
        
    Returns:
        list: List of dictionaries, each representing a path
    """
    if not row_selection.strip():
        return []
    
    lines = row_selection.strip().split('\n')
    paths = []
    current_path = {}
    
    for line in lines:
        if not line.strip():
            continue
            
        # Count indentation level
        indent_level = (len(line) - len(line.lstrip())) // 4
        
        # Parse feature: value
        if ':' in line:
            feature, value = line.strip().split(':', 1)
            feature = feature.strip()
            value = value.strip()
            
            # If this is a top-level feature (indent 0), start a new path
            if indent_level == 0:
                if current_path:  # Save previous path
                    paths.append(current_path.copy())
                current_path = {feature: value}
            else:
                # Add to current path
                current_path[feature] = value
    
    # Don't forget the last path
    if current_path:
        paths.append(current_path)
    
    return paths


def parse_col_paths(col_selection):
    """
    Parse hierarchical column selection into individual paths.
    
    Args:
        col_selection: String with hierarchical column structure
        
    Returns:
        list: List of dictionaries, each representing a path
    """
    if not col_selection.strip():
        return []
    
    lines = col_selection.strip().split('\n')
    paths = []
    current_path = {}
    max_level = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        # Count indentation level
        indent_level = (len(line) - len(line.lstrip())) // 4
        
        # Parse level_X: value
        if ':' in line:
            level_part, value = line.strip().split(':', 1)
            level_part = level_part.strip()
            value = value.strip()
            
            # Extract level number
            if level_part.startswith('level_'):
                level_num = int(level_part.split('_')[1])
                max_level = max(max_level, level_num)
                
                # If this is level_1, start a new path
                if level_num == 1:
                    if current_path:  # Save previous path
                        paths.append(current_path.copy())
                    current_path = {level_num: value}
                else:
                    # Add to current path
                    current_path[level_num] = value
    
    # Don't forget the last path
    if current_path:
        paths.append(current_path)
    
    return paths


def create_row_condition(df, row_paths):
    """
    Create pandas condition for row filtering based on row paths.
    
    Args:
        df: DataFrame to filter
        row_paths: List of path dictionaries from parse_row_paths
        
    Returns:
        pandas condition: Boolean condition for filtering
    """
    if not row_paths:
        return pd.Series([True] * len(df), index=df.index)
    
    path_conditions = []
    
    for path in row_paths:
        conditions_for_path = []
        
        for feature, value in path.items():
            if str(value).lower() == 'undefined':
                continue  # Skip undefined conditions
                
            # Search for the column in MultiIndex
            col_tuple = search_column_in_multiindex(df, feature)
            if col_tuple is not None:
                # Create condition for this feature-value pair
                if ',' in value:
                    # Multiple values
                    values = [v.strip() for v in value.split(',')]
                    condition = df[col_tuple].isin(values)
                else:
                    # Single value
                    condition = df[col_tuple].isin([value])
                
                conditions_for_path.append(condition)
        
        # Combine conditions for this path with AND
        if conditions_for_path:
            path_condition = conditions_for_path[0]
            for cond in conditions_for_path[1:]:
                path_condition = path_condition & cond
            path_conditions.append(path_condition)
    
    # Combine all path conditions with OR
    if path_conditions:
        final_condition = path_conditions[0]
        for cond in path_conditions[1:]:
            final_condition = final_condition | cond
        return final_condition
    else:
        return pd.Series([True] * len(df), index=df.index)


def create_column_tuples(df, col_paths):
    """
    Create MultiIndex column tuples for column selection based on col paths.
    
    Args:
        df: DataFrame with MultiIndex columns
        col_paths: List of path dictionaries from parse_col_paths
        
    Returns:
        list: List of column tuples
    """
    if not col_paths:
        return []
    
    column_tuples = []
    
    # Determine max levels in MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        max_levels = df.columns.nlevels
    else:
        max_levels = 1
    
    for path in col_paths:
        # Find ALL matching columns for this path (not just the first one)
        if isinstance(df.columns, pd.MultiIndex):
            for col_tuple in df.columns:
                # Check if this column matches our pattern
                matches = True
                for level_num, value in path.items():
                    if level_num <= max_levels:
                        level_index = level_num - 1  # Convert to 0-based index
                        if level_index < len(col_tuple):
                            actual_val = col_tuple[level_index]
                            if value != actual_val:
                                matches = False
                                break
                        else:
                            matches = False
                            break
                
                if matches:
                    column_tuples.append(col_tuple)
        else:
            # Handle simple (non-MultiIndex) columns
            if 1 in path:  # level_1 is the only level for simple columns
                target_value = path[1]
                for col in df.columns:
                    if str(col) == target_value:
                        column_tuples.append(col)
    
    return column_tuples


def render_filtered_dataframe(df, row_selection, col_selection, feature_rows=None):
    """
    Filter DataFrame based on hierarchical row and column selections.
    
    Args:
        df: Input DataFrame with MultiIndex columns
        row_selection: Hierarchical row selection string
        col_selection: Hierarchical column selection string
        feature_rows: List of feature row column names to include in output
        
    Returns:
        DataFrame: Filtered DataFrame
    """
    print("=== RENDERING FILTERED DATAFRAME ===")
    
    # Parse row and column selections
    row_paths = parse_row_paths(row_selection)
    col_paths = parse_col_paths(col_selection)
    
    print(f"Parsed {len(row_paths)} row paths")
    print(f"Parsed {len(col_paths)} column paths")
    
    # Create row filtering condition
    row_condition = create_row_condition(df, row_paths)
    print(f"Row condition filters {row_condition.sum()} out of {len(df)} rows")
    
    # Filter rows first
    row_filtered_df = df[row_condition]
    
    # Create column selection
    column_tuples = create_column_tuples(df, col_paths)
    print(f"Selected {len(column_tuples)} columns")
    
    # Include feature rows columns for clearer output
    feature_row_tuples = []
    if feature_rows:
        for feature_row in feature_rows:
            feature_tuple = search_column_in_multiindex(df, feature_row)
            if feature_tuple:
                feature_row_tuples.append(feature_tuple)
        print(f"Added {len(feature_row_tuples)} feature row columns")
    
    # Combine feature rows and selected columns
    all_columns = feature_row_tuples + column_tuples
    
    if all_columns:
        # Filter columns (feature rows + selected columns)
        final_df = row_filtered_df[all_columns]
    else:
        # No specific column selection, use all columns
        final_df = row_filtered_df
    
    print("Filtering completed successfully")
    return final_df


def get_extraction_stats(df, row_selection, col_selection):
    """
    Get statistics about what would be extracted without actually extracting.
    
    Args:
        df: Input DataFrame
        row_selection: Hierarchical row selection string
        col_selection: Hierarchical column selection string
        
    Returns:
        dict: Statistics about the extraction
    """
    row_paths = parse_row_paths(row_selection)
    col_paths = parse_col_paths(col_selection)
    
    row_condition = create_row_condition(df, row_paths)
    column_tuples = create_column_tuples(df, col_paths)
    
    stats = {
        'total_rows': len(df),
        'filtered_rows': row_condition.sum(),
        'total_columns': len(df.columns),
        'selected_columns': len(column_tuples),
        'row_paths_count': len(row_paths),
        'col_paths_count': len(col_paths),
        'extraction_percentage': (row_condition.sum() / len(df)) * 100 if len(df) > 0 else 0
    }
    
    return stats 