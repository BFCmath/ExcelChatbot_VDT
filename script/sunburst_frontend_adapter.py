import json
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any

def _analyze_header_matrix_structure(header_matrix: List[List[Dict[str, Any]]], final_columns: List[str], data_rows: List[List]) -> Dict:
    """
    Analyze the header_matrix to understand the true hierarchical structure.
    """
    print(f"🔍 Analyzing header_matrix structure:")
    
    # Build position to header mapping for each level
    level_structures = {}
    for level_idx, level in enumerate(header_matrix):
        level_structures[level_idx] = {}
        for header in level:
            for pos in range(header['position'], header['position'] + header['colspan']):
                level_structures[level_idx][pos] = header['text']
        print(f"   Level {level_idx}: {level_structures[level_idx]}")
    
    # Determine the actual data structure
    data_length = len(data_rows[0]) if data_rows else 0
    columns_length = len(final_columns)
    
    print(f"   data_rows length: {data_length}")
    print(f"   final_columns length: {columns_length}")
    print(f"   final_columns: {final_columns}")
    print(f"   data_rows sample: {data_rows[0] if data_rows else []}")
    
    # Find categorical vs numeric columns based on data analysis
    categorical_positions = []
    numeric_positions = []
    
    if data_rows:
        first_row = data_rows[0]
        for i, value in enumerate(first_row):
            try:
                float(value)
                numeric_positions.append(i)
            except (ValueError, TypeError):
                categorical_positions.append(i)
    
    print(f"   Categorical positions in data_rows: {categorical_positions}")
    print(f"   Numeric positions in data_rows: {numeric_positions}")
    
    # Map data positions to header_matrix positions
    data_to_header_position = {}
    for i in range(data_length):
        data_to_header_position[i] = i
    
    print(f"   Data to header position mapping: {data_to_header_position}")
    
    return {
        "level_structures": level_structures,
        "categorical_positions": categorical_positions,
        "numeric_positions": numeric_positions,
        "data_to_header_position": data_to_header_position,
        "data_length": data_length,
        "columns_length": columns_length
    }

def _build_column_hierarchy_paths(header_matrix: List[List[Dict[str, Any]]], position: int) -> List[str]:
    """
    Build the complete hierarchy path for a specific column position.
    """
    hierarchy_path = []
    
    # Go through each level and find the header that covers this position
    for level_idx, level in enumerate(header_matrix):
        for header in level:
            if header['position'] <= position < header['position'] + header['colspan']:
                hierarchy_path.append(header['text'])
                break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_path = []
    for item in hierarchy_path:
        if item not in seen:
            seen.add(item)
            unique_path.append(item)
    
    return unique_path

def plot_sunburst_from_frontend_json(
    json_path: str,
    priority: str = 'column',
    use_actual_data: bool = True,
    exclude_summaries: bool = True
):
    """
    Generates a sunburst plot from frontend JSON format.
    """
    if priority not in ['column', 'row']:
        raise ValueError("Priority must be either 'column' or 'row'.")

    print(f"\n--- Running Frontend Sunburst Plot for '{json_path}' ---")
    print(f"Mode: Priority='{priority}', Use_Data={use_actual_data}, Exclude_Summaries={exclude_summaries}")

    # 1. Read and Parse Frontend JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    print(f"📊 Loaded JSON with {len(schema.get('data_rows', []))} rows and {len(schema.get('final_columns', []))} columns")
    print(f"🎯 Feature rows: {schema.get('feature_rows', [])}")
    print(f"📈 Feature cols: {schema.get('feature_cols', [])}")
    print(f"🔄 Flatten level applied: {schema.get('flatten_level_applied', 'unknown')}")

    # 2. Extract data from frontend format
    final_columns = schema.get('final_columns', [])
    data_rows = schema.get('data_rows', [])
    feature_rows = schema.get('feature_rows', [])
    feature_cols = schema.get('feature_cols', [])
    header_matrix = schema.get('header_matrix', [])
    has_multiindex = schema.get('has_multiindex', False)
    
    if not final_columns or not data_rows:
        print("❌ No data found in JSON. Required: final_columns and data_rows")
        return

    # 3. Analyze the header_matrix structure properly
    structure_info = _analyze_header_matrix_structure(header_matrix, final_columns, data_rows)
    
    # 4. Get categorical and numeric column information
    categorical_positions = structure_info["categorical_positions"]
    numeric_positions = structure_info["numeric_positions"]
    data_to_header_position = structure_info["data_to_header_position"]
    level_structures = structure_info["level_structures"]
    
    # Get categorical column names from the header_matrix
    categorical_names = []
    for cat_pos in categorical_positions:
        header_pos = data_to_header_position[cat_pos]
        # Get the name from level 0 of header_matrix
        if 0 in level_structures and header_pos in level_structures[0]:
            categorical_names.append(level_structures[0][header_pos])
        else:
            categorical_names.append(f"Category_{cat_pos}")
    
    print(f"📋 Categorical columns: {categorical_names}")
    print(f"📊 Numeric column positions: {numeric_positions}")
    
    # 5. Prepare data for plotting
    plot_data = []
    
    for row_idx, data_row in enumerate(data_rows):
        # Extract categorical values
        row_categories = {}
        for i, cat_pos in enumerate(categorical_positions):
            if cat_pos < len(data_row) and i < len(categorical_names):
                row_categories[categorical_names[i]] = str(data_row[cat_pos])
        
        # Process each numeric column
        for num_pos in numeric_positions:
            if num_pos >= len(data_row):
                continue
            
            # Get the header position for this data position
            header_pos = data_to_header_position[num_pos]
            
            # Build the complete hierarchy path for this column
            hierarchy_path = _build_column_hierarchy_paths(header_matrix, header_pos)
            
            # Skip summary columns if requested
            if exclude_summaries and any(summary in str(hierarchy_path) for summary in ['Cộng', 'Tổng', 'Total', 'Sum']):
                continue
            
            record = {}
            
            # Add categorical data
            for cat_name, cat_value in row_categories.items():
                record[cat_name] = cat_value
            
            # Add column hierarchy levels
            for level_idx, level_name in enumerate(hierarchy_path):
                record[f'Col_Level_{level_idx}'] = level_name
            
            # Add data value
            try:
                actual_value = pd.to_numeric(data_row[num_pos], errors='coerce')
                record['value'] = actual_value if pd.notna(actual_value) else 0
            except (ValueError, TypeError, IndexError):
                record['value'] = 0 if use_actual_data else 1
            
            plot_data.append(record)
    
    if not plot_data:
        print("❌ No data to plot after filtering. Exiting.")
        return
        
    df = pd.DataFrame(plot_data)
    print(f"📊 Created DataFrame with {len(df)} records and columns: {list(df.columns)}")
    
    # Debug: Check the hierarchical structure in detail
    print("\n🔍 DEBUGGING HIERARCHICAL STRUCTURE:")
    col_level_cols = [col for col in df.columns if col.startswith('Col_Level_')]
    for level_col in col_level_cols:
        unique_values = df[level_col].unique()
        print(f"   {level_col}: {list(unique_values)}")
    
    # Check how data is distributed across hierarchy levels
    print("\n🔍 HIERARCHICAL DISTRIBUTION:")
    if 'Col_Level_0' in df.columns and 'Col_Level_3' in df.columns:
        hierarchy_check = df.groupby(['Col_Level_0', 'Col_Level_1', 'Col_Level_2', 'Col_Level_3'])['value'].sum().reset_index()
        print("   Grouped by full hierarchy:")
        for _, row in hierarchy_check.iterrows():
            print(f"     {row['Col_Level_0']} → {row['Col_Level_1']} → {row['Col_Level_2']} → {row['Col_Level_3']}: {row['value']}")
    
    # Debug: Show first few records
    print("\n🔍 First 5 records:")
    for i, record in enumerate(plot_data[:5]):
        print(f"   Record {i}: {record}")

    # 6. Build plot path based on priority
    col_level_cols = [col for col in df.columns if col.startswith('Col_Level_')]
    col_level_cols.sort()  # Ensure proper order
    
    if priority == 'column':
        plot_path = col_level_cols + categorical_names
    else:  # priority == 'row'
        plot_path = categorical_names + col_level_cols
        
    print(f"\n🎯 Plotting with hierarchy: {plot_path}")
    
    # Remove any columns from plot_path that don't exist in the DataFrame
    valid_plot_path = [col for col in plot_path if col in df.columns]
    if len(valid_plot_path) != len(plot_path):
        print(f"⚠️  Adjusted plot path to: {valid_plot_path}")
        plot_path = valid_plot_path

    # 7. Generate the Sunburst Plot
    filename = schema.get('filename', 'table')
    title = f"'{filename}' ({priority.capitalize()}-first Hierarchy, Level {schema.get('flatten_level_applied', '?')})"
    
    # Check for any None values in the path columns
    for col in plot_path:
        if col in df.columns:
            none_count = df[col].isna().sum()
            if none_count > 0:
                print(f"⚠️  Column '{col}' has {none_count} None values - filling with 'Unknown'")
                df[col] = df[col].fillna('Unknown')
    
    # Debug: Check the final DataFrame structure
    print(f"\n🔍 FINAL DATAFRAME ANALYSIS:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Value sum: {df['value'].sum()}")
    print(f"   Plot path: {plot_path}")
    
    try:
        fig = px.sunburst(
            df,
            path=plot_path,
            values='value',
            title=title,
            hover_data={'value': use_actual_data}
        )

        # Enhanced sunburst configuration for better hierarchical display
        fig.update_layout(
            margin=dict(t=80, l=25, r=25, b=25), 
            font=dict(size=11),
            title_font_size=14,
            showlegend=False
        )
        
        # Update traces for better hierarchical visualization
        fig.update_traces(
            insidetextorientation='radial',
            textinfo="label+percent parent",  # Show both label and percentage
            maxdepth=6,  # Allow deeper hierarchies
            branchvalues="total"  # Use total values for hierarchy
        )
        
        # Add hover template for better information display
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: %{value}<br>' +
                         'Percentage of parent: %{percentParent}<br>' +
                         'Path: %{currentPath}<br>' +
                         '<extra></extra>'
        )
        
        # Save with descriptive filename
        output_filename = f'sunburst_{priority}_level{schema.get("flatten_level_applied", "unknown")}_enhanced.html'
        fig.write_html(output_filename)
        print(f"✅ Enhanced Sunburst plot saved to: {output_filename}")
        
        return fig
        
    except Exception as e:
        print(f"❌ Error creating sunburst plot: {e}")
        print(f"🔍 DataFrame info:")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Plot path: {plot_path}")
        print(f"   Data types: {df.dtypes.to_dict()}")
        raise

if __name__ == '__main__':
    file_name = input("Enter the file name: ") # D:\project\vdt\xlsx_chatbot\sucess_2.json
    plot_sunburst_from_frontend_json(file_name, priority='row', use_actual_data=True)
    plot_sunburst_from_frontend_json(file_name, priority='column', use_actual_data=True)
  