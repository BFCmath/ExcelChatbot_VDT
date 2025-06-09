import os
import getpass
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import openpyxl
from preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans
from utils import get_feature_name_content
from metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from llm import get_feature_names, single_agent, splitter
from utils import format_row_dict_for_llm, format_col_dict_for_llm
from extract_df import render_filtered_dataframe
import json
import dotenv
dotenv.load_dotenv()

print("Preprocessing...")
# Initialize the Gemini 2.5 Flash model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    google_api_key=os.getenv("GOOGLE_API_KEY_1"),
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

file_path = '../data/example2.xlsx'

feature_names = get_feature_names(file_path, llm)
_, feature_name_result = get_feature_name_content(file_path, feature_names)
number_of_row_header = get_number_of_row_header(file_path)
df = pd.read_excel(file_path, header=list(range(0,number_of_row_header)))
df = clean_unnamed_header(df, number_of_row_header)
df = fill_undefined_sequentially(df,feature_name_result["feature_rows"])
df = forward_fill_column_nans(df,feature_name_result["feature_rows"])

row_dict = convert_df_rows_to_nested_dict(df, feature_name_result["feature_rows"])
col_dict = convert_df_headers_to_nested_dict(df, feature_name_result["feature_cols"])

feature_cols = feature_name_result["feature_cols"]
feature_rows = feature_name_result["feature_rows"]
    # Format dictionaries using the new formatting functions
row_structure = format_row_dict_for_llm(row_dict, feature_rows)
col_structure = format_col_dict_for_llm(col_dict)
print(col_structure)
print("=" * 50)
print("Excel Chatbot Ready!")
print("=" * 50)
print("Commands:")
print("- Enter your query in natural language")
print("- Type 'single' to use single agent mode")
print("- Type 'splitter' to use multi-agent splitter mode")
print("- Type 'sanity check' to see data structure")
print("- Type 'reports' to see recent query reports")
print("- Type 'exit' or 'quit' to stop")
print("=" * 50)

# Default mode
current_mode = "splitter"
print(f"Current mode: {current_mode}")

while True:
    try:
        # Get user input
        query = input(f"\n[{current_mode}] Enter your query: ").strip()
        
        # Check for exit commands
        if query.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
            
        # Check for mode switch commands
        if query.lower() == 'single':
            current_mode = "single"
            print(f"Switched to {current_mode} agent mode")
            continue
        elif query.lower() == 'splitter':
            current_mode = "splitter"
            print(f"Switched to {current_mode} multi-agent mode")
            continue
            
        # Check for sanity check command
        if query.lower() == 'sanity check':
            print("\n" + "="*50)
            print("SANITY CHECK - Data Structure")
            print("="*50)
            
            print(f"\nFeature Rows: {feature_rows}")
            print(f"\nFeature Cols: {feature_cols}")
            
            print("\nRow Dictionary:")
            print(row_structure)
            print("\nColumn Dictionary:")
            print(col_structure)
            
            print("\n" + "="*50)
            continue
            
        # Check for reports command
        if query.lower() == 'reports':
            print("\n" + "="*50)
            print("RECENT QUERY REPORTS")
            print("="*50)
            
            from reporter import reporter
            reporter.display_recent_reports_summary(limit=10)
            
            print("\n" + "="*50)
            continue
            
        # Skip empty queries
        if not query:
            print("Please enter a query.")
            continue
            
        # Process the query based on current mode
        print(f"\nProcessing query: '{query}' using {current_mode} mode")
        print("-" * 30)
        
        if current_mode == "single":
            result = single_agent(query, feature_rows, feature_cols, row_dict, col_dict, llm)
            print("Note: Single agent mode - manual result interpretation needed")
            
            # Save report for single mode
            from reporter import reporter
            file_info = {
                'filename': os.path.basename(file_path),
                'feature_rows': feature_rows,
                'feature_cols': feature_cols
            }
            report_id = reporter.save_single_query_report(query, result, file_info, "single")
            
        else:  # splitter mode
            result = splitter(query, feature_rows, feature_cols, row_structure, col_structure, llm)
            
            # Render the filtered DataFrame if we have valid results
            if result and isinstance(result, dict) and 'row_selection' in result and 'col_selection' in result:
                try:
                    filtered_df = render_filtered_dataframe(df, result['row_selection'], result['col_selection'], feature_rows)
                    print("\n" + "="*50)
                    print("FILTERED RESULT TABLE")
                    print("="*50)
                    if not filtered_df.empty:
                        print(filtered_df.to_string())
                    else:
                        print("No matching data found for the query.")
                    print("="*50)
                    
                    # Save report for splitter mode with DataFrame results
                    from reporter import reporter
                    file_info = {
                        'filename': os.path.basename(file_path),
                        'feature_rows': feature_rows,
                        'feature_cols': feature_cols
                    }
                    # Add DataFrame info to result
                    result_with_df = result.copy()
                    result_with_df['dataframe'] = filtered_df
                    report_id = reporter.save_single_query_report(query, result_with_df, file_info, "splitter")
                    
                except Exception as e:
                    print(f"\nError rendering table: {e}")
                    print("Raw result:")
                    print(f"Row Selection:\n{result['row_selection']}")
                    print(f"Col Selection:\n{result['col_selection']}")
                    
                    # Save report even if table rendering failed
                    from reporter import reporter
                    file_info = {
                        'filename': os.path.basename(file_path),
                        'feature_rows': feature_rows,
                        'feature_cols': feature_cols
                    }
                    result_with_error = result.copy()
                    result_with_error['error'] = str(e)
                    report_id = reporter.save_single_query_report(query, result_with_error, file_info, "splitter")
        
        print("-" * 30)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"\nError processing query: {e}")
        print("Please try again.")