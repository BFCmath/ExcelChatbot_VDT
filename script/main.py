import os
import getpass
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import openpyxl
from preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans
from utils import read_file, get_feature_name_content, format_nested_dict_for_llm
from metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from llm import get_schema, get_feature_names, process_natural_language_query
import dotenv
dotenv.load_dotenv()

print("Preprocessing...")
# Initialize the Gemini 2.5 Flash model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
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

print("=" * 50)
print("Excel Chatbot Ready!")
print("=" * 50)
print("Commands:")
print("- Enter your query in natural language")
print("- Type 'sanity check' to see data structure")
print("- Type 'exit' or 'quit' to stop")
print("=" * 50)

while True:
    try:
        # Get user input
        query = input("\nEnter your query: ").strip()
        
        # Check for exit commands
        if query.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
            
        # Check for sanity check command
        if query.lower() == 'sanity check':
            print("\n" + "="*50)
            print("SANITY CHECK - Data Structure")
            print("="*50)
            
            print(f"\nFeature Rows: {feature_rows}")
            print(f"\nFeature Cols: {feature_cols}")
            
            print("\nRow Dictionary:")
            import json
            print(json.dumps(row_dict, ensure_ascii=False, indent=2))
            
            print("\nColumn Dictionary:")
            print(json.dumps(col_dict, ensure_ascii=False, indent=2))
            
            print("\n" + "="*50)
            continue
            
        # Skip empty queries
        if not query:
            print("Please enter a query.")
            continue
            
        # Process the query
        print(f"\nProcessing query: '{query}'")
        print("-" * 30)
        
        result = process_natural_language_query(query, feature_rows, feature_cols, row_dict, col_dict, llm)
        
        print("\nResult:")
        print(result)
        print("-" * 30)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"\nError processing query: {e}")
        print("Please try again.")