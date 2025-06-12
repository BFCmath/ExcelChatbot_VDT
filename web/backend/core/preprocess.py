import pandas as pd
import numpy as np

def extract_headers_only(excel_file_path, number_of_row_header):
    """
    Extract only the header rows from an Excel file for LLM processing.
    
    Args:
        excel_file_path (str): Path to the Excel file
        number_of_row_header (int): Number of header rows to extract
        
    Returns:
        str: CSV format of only the header rows
    """
    try:
        # Read Excel file with specified number of header rows
        df_headers = pd.read_excel(
            excel_file_path, 
            header=list(range(0, number_of_row_header)),
            nrows=0,  # Only read headers, no data rows
            engine='openpyxl'
        )
        
        # Convert headers to CSV format (empty data, just column structure)
        headers_content = df_headers.to_csv(index=False)
        return headers_content
        
    except Exception as e:
        print(f"Error reading Excel headers: {e}")
        raise

def clean_unnamed_header(df, number_of_row_header):
    def sua_ten_tieu_de_phu(ten_tieu_de_phu):
        if isinstance(ten_tieu_de_phu, str) and ten_tieu_de_phu.startswith("Unnamed:"):
            return "Header"
        return ten_tieu_de_phu
    for i in range(number_of_row_header)[1:]:
        df.rename(columns=sua_ten_tieu_de_phu, level=i, inplace=True)

    return df


def fill_undefined_sequentially(df_input, column_names_list, fill_value="Undefined"):
    """
    Sequentially fills NaNs in specified columns.

    For each pair of columns (col_A, col_B) from column_names_list,
    fills df[col_B][i] with `fill_value` if:
    1. df[col_A][i] is not NaN
    2. df[col_B][i] is NaN
    3. df[col_B][i+1] (value in col_B of the next row) is also NaN.
    """
    df = df_input.copy()
    
    for i in range(len(column_names_list) - 1):
        col_current_id = column_names_list[i]
        col_next_id = column_names_list[i+1]
        
        current_col_series = df[col_current_id]
        next_col_series = df[col_next_id]

        # values_in_col_next_at_next_row = next_col_series.shift(-1, fill_value=np.nan)
        
        condition_to_fill = (
            current_col_series.notna().values &
            next_col_series.isna().values
        )
        df.loc[condition_to_fill[:,0], col_next_id] = fill_value 
    return df

def forward_fill_column_nans(input_df, columns_to_process_list):
    """
    Fills NaN values in specified DataFrame columns using the last valid
    observation in that column (forward-fill).
    """
    df = input_df.copy()
    processing_list = []

    if isinstance(columns_to_process_list, str):
        processing_list = [columns_to_process_list]
    elif isinstance(columns_to_process_list, list):
        processing_list = columns_to_process_list
    else:
        processing_list = list(columns_to_process_list)

    for column_name in processing_list:
        df[column_name] = df[column_name].ffill()            
    return df
