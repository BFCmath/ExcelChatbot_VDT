"""
Interactive Test for Alias Enrichment Feature

This script tests the complete flow: enrich -> separator -> splitter
allowing manual input of file paths for testing.
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.processor import MultiFileProcessor
from core.config import setup_logging

# Setup logging
logger = setup_logging()


def test_alias_enrichment():
    """Interactive test for alias enrichment feature."""
    print("=" * 80)
    print("🧪 ALIAS ENRICHMENT INTERACTIVE TEST")
    print("=" * 80)
    
    # Initialize processor
    processor = MultiFileProcessor()
    
    try:
        print("\n📁 STEP 1: Load Excel files for processing")
        print("-" * 50)
        
        # Get Excel files to process
        excel_files = []
        while True:
            file_path = input("Enter path to Excel file (or 'done' to finish): ").strip()
            if file_path.lower() == 'done':
                break
            if file_path and os.path.exists(file_path):
                excel_files.append(file_path)
                print(f"✅ Added: {file_path}")
            else:
                print(f"❌ File not found: {file_path}")
        
        if not excel_files:
            print("❌ No Excel files provided. Exiting.")
            return
        
        # Process Excel files
        print(f"\n🔄 Processing {len(excel_files)} Excel files...")
        processor.process_multiple_files(excel_files)
        print("✅ Excel files processed successfully!")
        
        # Display file summaries
        print("\n📊 File Summaries:")
        print("-" * 50)
        summaries = processor.get_all_file_summaries()
        print(summaries)
        
        print("\n🔍 STEP 2: Test alias enrichment")
        print("-" * 50)
        
        # Get alias file path
        alias_file_path = None
        use_alias = input("Do you want to use alias enrichment? (y/n): ").strip().lower()
        
        if use_alias == 'y':
            alias_path = input("Enter path to alias Excel file: ").strip()
            if alias_path and os.path.exists(alias_path):
                alias_file_path = alias_path
                print(f"✅ Alias file: {alias_file_path}")
                
                # Test alias dictionary loading
                try:
                    processor.initialize_llm()
                    alias_dict = processor.alias_enricher.load_alias_dictionary(alias_file_path)
                    print("\n📋 Alias Dictionary Preview:")
                    print("-" * 30)
                    # Show first 500 characters of alias dictionary
                    preview = alias_dict[:500] + "..." if len(alias_dict) > 500 else alias_dict
                    print(preview)
                except Exception as e:
                    print(f"❌ Error loading alias dictionary: {e}")
                    alias_file_path = None
            else:
                print(f"❌ Alias file not found: {alias_path}")
        
        print("\n💬 STEP 3: Query processing")
        print("-" * 50)
        
        # Interactive query testing
        while True:
            print("\n" + "=" * 60)
            user_query = input("Enter your query (or 'quit' to exit): ").strip()
            
            if user_query.lower() == 'quit':
                break
            
            if not user_query:
                print("❌ Empty query. Please try again.")
                continue
            
            print(f"\n🔄 Processing query: {user_query}")
            print("-" * 40)
            
            try:
                # Process the query with alias enrichment
                result = processor.process_multi_file_query(user_query, alias_file_path)
                
                if result["success"]:
                    print("✅ Query processed successfully!")
                    print(f"\n📝 Original Query: {result['original_query']}")
                    print(f"✨ Enriched Query: {result['enriched_query']}")
                    print(f"📊 Files Processed: {result['total_files_processed']}")
                    
                    print("\n📋 Results:")
                    print("-" * 30)
                    for i, res in enumerate(result["results"], 1):
                        print(f"\n{i}. File: {res['filename']}")
                        print(f"   Query: {res['query']}")
                        print(f"   Success: {res['success']}")
                        
                        if res['success'] and 'table_info' in res:
                            table_info = res['table_info']
                            print(f"   Rows: {table_info.get('row_count', 'N/A')}")
                            print(f"   Columns: {table_info.get('col_count', 'N/A')}")
                            print(f"   Has MultiIndex: {table_info.get('has_multiindex', 'N/A')}")
                            
                            # Show flattened table info if available
                            if 'flattened_table_info' in res:
                                flattened = res['flattened_table_info']
                                print(f"   Flattened Columns: {len(flattened.get('final_columns', []))}")
                                print(f"   Flattened Column Names: {flattened.get('final_columns', [])[:5]}...")  # Show first 5
                        else:
                            print(f"   Message: {res.get('message', 'No additional info')}")
                else:
                    print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                print(f"❌ Error processing query: {e}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 Test completed!")
    print("=" * 80)


def test_alias_only():
    """Test only the alias enrichment functionality."""
    print("=" * 80)
    print("🧪 ALIAS ENRICHMENT ONLY TEST")
    print("=" * 80)
    
    processor = MultiFileProcessor()
    
    try:
        # Get alias file path
        alias_path = input("Enter path to alias Excel file: ").strip()
        if not alias_path or not os.path.exists(alias_path):
            print(f"❌ Alias file not found: {alias_path}")
            return
        
        # Initialize LLM
        processor.initialize_llm()
        
        # Load alias dictionary
        print(f"\n📋 Loading alias dictionary from: {alias_path}")
        alias_dict = processor.alias_enricher.load_alias_dictionary(alias_path)
        print("✅ Alias dictionary loaded!")
        
        # Show alias dictionary preview
        print("\n📋 Alias Dictionary Preview:")
        print("-" * 40)
        preview = alias_dict[:800] + "..." if len(alias_dict) > 800 else alias_dict
        print(preview)
        
        # Interactive query testing
        while True:
            print("\n" + "=" * 60)
            user_query = input("Enter query to enrich (or 'quit' to exit): ").strip()
            
            if user_query.lower() == 'quit':
                break
            
            if not user_query:
                print("❌ Empty query. Please try again.")
                continue
            
            print(f"\n🔄 Enriching query: {user_query}")
            print("-" * 40)
            
            try:
                enriched = processor.alias_enricher.enrich_query(user_query, alias_path)
                print(f"📝 Original: {user_query}")
                print(f"✨ Enriched: {enriched}")
                
                # Check if enrichment occurred
                if enriched != user_query:
                    print("✅ Query was enriched with aliases!")
                else:
                    print("ℹ️ No aliases found in query.")
                    
            except Exception as e:
                logger.error(f"Error enriching query: {e}", exc_info=True)
                print(f"❌ Error enriching query: {e}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 Alias test completed!")
    print("=" * 80)


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full flow test (alias + separator + splitter)")
    print("2. Alias enrichment only")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_alias_enrichment()
    elif choice == "2":
        test_alias_only()
    else:
        print("❌ Invalid choice. Exiting.") 