"""
Interactive test script for the complete Excel Chatbot pipeline.
Allows user to input file path and query, then shows both normal and flattened table results.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.processor import MultiFileProcessor
from core.config import setup_logging
import logging

def print_separator(title):
    """Print a visual separator with title."""
    print("\n" + "="*80)
    print(f" {title} ")
    print("="*80)

def print_table_info(table_info, table_type="Normal"):
    """Pretty print table information."""
    print(f"\n--- {table_type} Table Info ---")
    print(f"Has MultiIndex: {table_info.get('has_multiindex', False)}")
    print(f"Row Count: {table_info.get('row_count', 0)}")
    print(f"Column Count: {table_info.get('col_count', 0)}")
    
    print(f"\nFinal Columns ({len(table_info.get('final_columns', []))}):")
    for i, col in enumerate(table_info.get('final_columns', [])):
        print(f"  {i+1}. {col}")
    
    if table_info.get('has_multiindex', False):
        print(f"\nHeader Matrix Levels: {len(table_info.get('header_matrix', []))}")
        for level_idx, level in enumerate(table_info.get('header_matrix', [])):
            print(f"  Level {level_idx + 1}: {len(level)} header cells")
    
    print(f"\nData Rows ({len(table_info.get('data_rows', []))}):")
    for i, row in enumerate(table_info.get('data_rows', [])[:3]):  # Show first 3 rows
        print(f"  Row {i+1}: {row}")
    
    if len(table_info.get('data_rows', [])) > 3:
        print(f"  ... and {len(table_info.get('data_rows', [])) - 3} more rows")

def interactive_test():
    """Run the interactive test."""
    print_separator("EXCEL CHATBOT INTERACTIVE TEST")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Initialize processor
    print("\n🔧 Initializing MultiFileProcessor...")
    processor = MultiFileProcessor()
    
    try:
        # Get file path from user
        print_separator("FILE INPUT")
        while True:
            file_path = input("Enter the path to your Excel file: ").strip()
            
            if not file_path:
                print("❌ Please enter a valid file path.")
                continue
                
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
                
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                print("❌ Please provide an Excel file (.xlsx or .xls)")
                continue
                
            break
        
        print(f"✅ File selected: {file_path}")
        
        # Process the file
        print_separator("FILE PROCESSING")
        print("🔄 Processing file metadata...")
        
        original_filename = Path(file_path).name
        processor.extract_file_metadata(file_path, original_filename)
        
        print("✅ File processed successfully!")
        print(f"📊 Processed files: {len(processor.file_metadata)}")
        
        # Show file summary
        summaries = processor.get_all_file_summaries()
        if summaries:
            print("\n📋 File Summary:")
            print(summaries[:500] + "..." if len(summaries) > 500 else summaries)
        
        # Get query from user
        print_separator("QUERY INPUT")
        while True:
            query = input("Enter your natural language query: ").strip()
            
            if not query:
                print("❌ Please enter a valid query.")
                continue
                
            if len(query) > 1000:
                print("❌ Query too long. Maximum 1000 characters.")
                continue
                
            break
        
        print(f"✅ Query: {query}")
        
        # Process the query
        print_separator("QUERY PROCESSING")
        print("🔄 Processing query...")
        
        result = processor.process_multi_file_query(query)
        
        # Display results
        print_separator("QUERY RESULTS")
        
        if result.get('success', False):
            print(f"✅ Query processed successfully!")
            print(f"📊 Total files processed: {result.get('total_files_processed', 0)}")
            
            for i, file_result in enumerate(result.get('results', [])):
                print(f"\n🗂️  File {i+1}: {file_result.get('filename', 'Unknown')}")
                print(f"🔍 Sub-query: {file_result.get('query', 'N/A')}")
                
                if file_result.get('success', False):
                    print("✅ Processing successful")
                    
                    # Show normal table info
                    if 'table_info' in file_result:
                        print_table_info(file_result['table_info'], "Normal Hierarchical")
                    
                    # Show flattened table info
                    if 'flattened_table_info' in file_result:
                        print_table_info(file_result['flattened_table_info'], "Flattened")
                    
                    # Compare headers
                    normal_cols = file_result.get('table_info', {}).get('final_columns', [])
                    flattened_cols = file_result.get('flattened_table_info', {}).get('final_columns', [])
                    
                    if normal_cols and flattened_cols:
                        print("\n🔄 Header Comparison:")
                        print("Normal Headers -> Flattened Headers")
                        for j, (normal, flattened) in enumerate(zip(normal_cols, flattened_cols)):
                            status = "✓" if normal != flattened else "="
                            print(f"  {j+1}. {normal} -> {flattened} {status}")
                
                else:
                    print(f"❌ Processing failed: {file_result.get('message', 'Unknown error')}")
        
        else:
            print(f"❌ Query processing failed: {result.get('error', 'Unknown error')}")
        
        # Ask if user wants to try another query
        print_separator("CONTINUE?")
        while True:
            continue_choice = input("Would you like to try another query with the same file? (y/n): ").strip().lower()
            if continue_choice in ['y', 'yes']:
                return True  # Continue with same file
            elif continue_choice in ['n', 'no']:
                return False  # Exit
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Main function to run the interactive test."""
    print("🚀 Welcome to the Excel Chatbot Interactive Test!")
    print("This tool will walk you through the complete pipeline:")
    print("  1. File processing and metadata extraction")
    print("  2. Query processing with multi-agent system")
    print("  3. DataFrame filtering and table generation")
    print("  4. Both normal and flattened table results")
    
    while True:
        try:
            should_continue = interactive_test()
            if not should_continue:
                break
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
    
    print_separator("TEST COMPLETED")
    print("Thank you for testing the Excel Chatbot system! 🎉")

if __name__ == "__main__":
    main() 