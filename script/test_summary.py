"""
Test File Summary Generation

This file allows testing the file summary functionality on a single Excel file
to evaluate how well the LLM understands the schema and generates meaningful summaries.
"""

import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Import existing modules
from preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans
from utils import get_feature_name_content, format_row_dict_for_llm, format_col_dict_for_llm
from metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from llm import get_feature_names
from prompt import FILE_SUMMARY_PROMPT
import pandas as pd

dotenv.load_dotenv()


class SummaryTester:
    """Test class for evaluating file summary generation."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=os.getenv("GOOGLE_API_KEY_1"),
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    
    def process_file_for_summary(self, file_path):
        """Process a single file and extract all metadata needed for summary."""
        print(f"📁 Processing file: {file_path}")
        print("=" * 60)
        
        try:
            # Extract feature names
            print("1. Extracting feature names...")
            feature_names = get_feature_names(file_path, self.llm)
            print(f"   ✅ Feature names extracted: {feature_names}")
            
            # Get feature name content
            print("\n2. Processing feature name content...")
            _, feature_name_result = get_feature_name_content(file_path, feature_names)
            print(f"   ✅ Feature rows: {feature_name_result['feature_rows']}")
            print(f"   ✅ Feature cols: {feature_name_result['feature_cols']}")
            
            # Get row header info
            print("\n3. Analyzing row headers...")
            number_of_row_header = get_number_of_row_header(file_path)
            print(f"   ✅ Number of row headers: {number_of_row_header}")
            
            # Load and preprocess DataFrame
            print("\n4. Loading and preprocessing DataFrame...")
            df = pd.read_excel(file_path, header=list(range(0, number_of_row_header)))
            df = clean_unnamed_header(df, number_of_row_header)
            df = fill_undefined_sequentially(df, feature_name_result["feature_rows"])
            df = forward_fill_column_nans(df, feature_name_result["feature_rows"])
            print(f"   ✅ DataFrame shape: {df.shape}")
            
            # Create nested dictionaries
            print("\n5. Creating nested dictionaries...")
            row_dict = convert_df_rows_to_nested_dict(df, feature_name_result["feature_rows"])
            col_dict = convert_df_headers_to_nested_dict(df, feature_name_result["feature_cols"])
            print(f"   ✅ Row dictionary created with {len(row_dict)} top-level items")
            print(f"   ✅ Column dictionary created with {len(col_dict)} top-level items")
            
            # Format structures for LLM
            print("\n6. Formatting structures for LLM...")
            row_structure = format_row_dict_for_llm(row_dict, feature_name_result["feature_rows"])
            col_structure = format_col_dict_for_llm(col_dict)
            
            print("   ✅ Structures formatted successfully")
            
            return {
                'filename': os.path.basename(file_path),
                'feature_name_result': feature_name_result,
                'row_structure': row_structure,
                'col_structure': col_structure,
                'df_shape': df.shape
            }
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            raise
    
    def generate_summary(self, metadata):
        """Generate summary for the processed metadata."""
        print("\n" + "=" * 60)
        print("GENERATING FILE SUMMARY")
        print("=" * 60)
        
        # Create the summary prompt
        summary_prompt = FILE_SUMMARY_PROMPT.format(
            filename=metadata['filename'],
            feature_rows=metadata['feature_name_result']['feature_rows'],
            feature_cols=metadata['feature_name_result']['feature_cols'],
            row_structure=metadata['row_structure'],
            col_structure=metadata['col_structure']
        )
        
        print("📝 Prompt sent to LLM:")
        print("-" * 40)
        print(summary_prompt[:500] + "..." if len(summary_prompt) > 500 else summary_prompt)
        print("-" * 40)
        
        try:
            message = HumanMessage(content=summary_prompt)
            response = self.llm.invoke([message])
            summary = response.content.strip()
            
            print("\n🤖 LLM Response:")
            print("-" * 40)
            print(summary)
            print("-" * 40)
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def test_single_file(self, file_path):
        """Test summary generation for a single file."""
        print("🧪 TESTING FILE SUMMARY GENERATION")
        print("=" * 60)
        print(f"Target file: {file_path}")
        
        try:
            # Process the file
            metadata = self.process_file_for_summary(file_path)
            
            # Generate summary
            summary = self.generate_summary(metadata)
            
            # Save summary report
            from reporter import reporter
            report_id = reporter.save_summary_report(
                metadata['filename'],
                {
                    'feature_rows': metadata['feature_name_result']['feature_rows'],
                    'feature_cols': metadata['feature_name_result']['feature_cols'],
                    'df_shape': metadata['df_shape']
                },
                summary
            )
            
            return {
                'metadata': metadata,
                'summary': summary,
                'report_id': report_id
            }
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            return None


def main():
    """Main function for testing summary generation."""
    tester = SummaryTester()
    
    # Test with example file
    file_path = '../data/example2.xlsx'
    
    print("🚀 Starting Summary Generation Test")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Please make sure the file exists or update the file path.")
        return
    
    # Run the test
    result = tester.test_single_file(file_path)
    
    if result:
        print(f"\n✅ Test completed successfully!")
        
        # Optional: Allow user to test different prompts or analyze further
        while True:
            print("\n" + "=" * 40)
            print("OPTIONS:")
            print("1. Re-generate summary")
            print("2. Show full summary")
            print("3. Exit")
            
            choice = input("\nChoose an option (1-3): ").strip()
            
            if choice == '1':
                print("\n🔄 Re-generating summary...")
                new_summary = tester.generate_summary(result['metadata'])
                
            elif choice == '2':
                print("\n📝 Full Summary:")
                print("-" * 40)
                print(result['summary'])
                print("-" * 40)
                
            elif choice == '3':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
    else:
        print("\n❌ Test failed. Please check the error messages above.")


if __name__ == "__main__":
    main() 