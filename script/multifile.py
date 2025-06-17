"""
Multi-File Excel Chatbot System

This module handles multiple Excel files, including:
- Metadata extraction and caching
- File summarization via LLM
- Query separation and routing to individual files
- Coordinated processing across multiple data sources
"""

import os
import json
import pickle
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import dotenv

# Import existing modules
from preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans
from utils import get_feature_name_content, format_row_dict_for_llm, format_col_dict_for_llm
from metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from llm import get_feature_names, splitter
from extract_df import render_filtered_dataframe

dotenv.load_dotenv()


class FileMetadata:
    """Container for file metadata and processed structures."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.filename = Path(file_path).name
        self.file_hash = self._calculate_file_hash()
        self.feature_names = None
        self.feature_name_result = None
        self.number_of_row_header = None
        self.df = None
        self.row_dict = None
        self.col_dict = None
        self.row_structure = None
        self.col_structure = None
        self.summary = None
        self.processed_at = None
    
    def _calculate_file_hash(self):
        """Calculate MD5 hash of file for caching purposes."""
        hash_md5 = hashlib.md5()
        with open(self.file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def to_dict(self):
        """Convert metadata to dictionary for caching (excluding DataFrame)."""
        return {
            'file_path': self.file_path,
            'filename': self.filename,
            'file_hash': self.file_hash,
            'feature_names': self.feature_names,
            'feature_name_result': self.feature_name_result,
            'number_of_row_header': self.number_of_row_header,
            'row_dict': self.row_dict,
            'col_dict': self.col_dict,
            'row_structure': self.row_structure,
            'col_structure': self.col_structure,
            'summary': self.summary,
            'processed_at': self.processed_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create FileMetadata from dictionary."""
        metadata = cls(data['file_path'])
        for key, value in data.items():
            if key != 'file_path':  # file_path is set in __init__
                setattr(metadata, key, value)
        return metadata


class MultiFileProcessor:
    """Handles processing and caching of multiple Excel files."""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_cache_file = self.cache_dir / "file_metadata.pkl"
        self.file_metadata = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cached metadata."""
        if self.metadata_cache_file.exists():
            try:
                with open(self.metadata_cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    for file_path, data in cached_data.items():
                        self.file_metadata[file_path] = FileMetadata.from_dict(data)
                print(f"Loaded cache for {len(self.file_metadata)} files")
            except Exception as e:
                print(f"Error loading cache: {e}")
    
    def _save_cache(self):
        """Save metadata to cache."""
        try:
            cache_data = {}
            for file_path, metadata in self.file_metadata.items():
                cache_data[file_path] = metadata.to_dict()
            
            with open(self.metadata_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"Saved cache for {len(self.file_metadata)} files")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def is_file_cached_and_valid(self, file_path):
        """Check if file is cached and cache is still valid."""
        if file_path not in self.file_metadata:
            return False
        
        metadata = self.file_metadata[file_path]
        # Check if file hash matches (file hasn't changed)
        current_hash = FileMetadata(file_path)._calculate_file_hash()
        return metadata.file_hash == current_hash
    
    def extract_file_metadata(self, file_path):
        """Extract and cache metadata for a single file."""
        print(f"\n{'='*20} Processing {Path(file_path).name} {'='*20}")
        
        # Check cache first
        if self.is_file_cached_and_valid(file_path):
            print("Using cached metadata")
            return self.file_metadata[file_path]
        
        # Initialize LLM if needed
        self.initialize_llm()
        
        # Create new metadata
        metadata = FileMetadata(file_path)
        
        try:
            # Extract feature names
            print("Extracting feature names...")
            metadata.feature_names = get_feature_names(file_path, self.llm)
            
            # Get feature name content
            print("Processing feature name content...")
            _, metadata.feature_name_result = get_feature_name_content(file_path, metadata.feature_names)
            
            # Get row header info
            metadata.number_of_row_header = get_number_of_row_header(file_path)
            
            # Load and preprocess DataFrame
            print("Loading and preprocessing DataFrame...")
            metadata.df = pd.read_excel(file_path, header=list(range(0, metadata.number_of_row_header)))
            metadata.df = clean_unnamed_header(metadata.df, metadata.number_of_row_header)
            metadata.df = fill_undefined_sequentially(metadata.df, metadata.feature_name_result["feature_rows"])
            metadata.df = forward_fill_column_nans(metadata.df, metadata.feature_name_result["feature_rows"])
            
            # Create nested dictionaries
            print("Creating nested dictionaries...")
            metadata.row_dict = convert_df_rows_to_nested_dict(metadata.df, metadata.feature_name_result["feature_rows"])
            metadata.col_dict = convert_df_headers_to_nested_dict(metadata.df, metadata.feature_name_result["feature_cols"])
            
            # Format structures for LLM
            metadata.row_structure = format_row_dict_for_llm(metadata.row_dict, metadata.feature_name_result["feature_rows"])
            metadata.col_structure = format_col_dict_for_llm(metadata.col_dict)
            
            # Generate summary
            print("Generating file summary...")
            metadata.summary = self.generate_file_summary(metadata)
            
            metadata.processed_at = datetime.now().isoformat()
            
            # Cache the metadata
            self.file_metadata[file_path] = metadata
            self._save_cache()
            
            print(f"Successfully processed {metadata.filename}")
            return metadata
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            raise
    
    def generate_file_summary(self, metadata):
        """Generate LLM summary for a file's metadata."""
        from prompt import FILE_SUMMARY_PROMPT
        from reporter import reporter
        
        summary_prompt = FILE_SUMMARY_PROMPT.format(
            filename=metadata.filename,
            feature_rows=metadata.feature_name_result['feature_rows'],
            feature_cols=metadata.feature_name_result['feature_cols'],
            row_structure=metadata.row_structure,
            col_structure=metadata.col_structure
        )
        
        try:
            message = HumanMessage(content=summary_prompt)
            response = self.llm.invoke([message])
            summary = response.content.strip()
            
            # Save summary report
            report_id = reporter.save_summary_report(
                metadata.filename,
                {
                    'feature_rows': metadata.feature_name_result['feature_rows'],
                    'feature_cols': metadata.feature_name_result['feature_cols'],
                    'df_shape': metadata.df.shape if hasattr(metadata.df, 'shape') else None
                },
                summary
            )
            
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"File contains {len(metadata.feature_name_result['feature_rows'])} row features and {len(metadata.feature_name_result['feature_cols'])} column features."
    
    def process_multiple_files(self, file_paths):
        """Process multiple files and extract metadata."""
        print("="*60)
        print("MULTI-FILE METADATA EXTRACTION")
        print("="*60)
        
        for file_path in file_paths:
            try:
                self.extract_file_metadata(file_path)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
        
        print("\n" + "="*60)
        print("METADATA EXTRACTION COMPLETE")
        print("="*60)
        self.display_file_summaries()
    
    def display_file_summaries(self):
        """Display summaries of all processed files."""
        print("\nFILE SUMMARIES:")
        print("-" * 40)
        
        for file_path, metadata in self.file_metadata.items():
            print(f"\n📄 {metadata.filename}")
            print(f"   {metadata.summary}")
            print(f"   Features: {metadata.feature_name_result['feature_rows']} (rows), {metadata.feature_name_result['feature_cols']} (cols)")
    
    def separate_query(self, query):
        """Separate multi-file query into individual file queries."""
        from prompt import QUERY_SEPARATOR_PROMPT
        print(self._get_files_context())
        separator_prompt = QUERY_SEPARATOR_PROMPT.format(
            files_context=self._get_files_context(),
            query=query
        )
        
        try:
            llm = get_llm_instance()
            message = HumanMessage(content=separator_prompt)
            response = llm.invoke([message])
            return self.parse_separator_response(response.content)
        except Exception as e:
            print(f"Error separating query: {e}")
            return None
    
    def _get_files_context(self):
        """Get context string of all files and their summaries."""
        context = ""
        for file_path, metadata in self.file_metadata.items():
            context += f"\n{metadata.filename}:\n{metadata.summary}\n"
        return context
    
    def parse_separator_response(self, response):
        """Parse the separator response into structured assignments based on the new format."""
        assignments = []
        lines = response.strip().split('\n')
        
        # Look for the ### Separated Query section
        capturing = False
        for line in lines:
            line = line.strip()
            
            if line.startswith('### Separated Query') or line.startswith('###Separated Query'):
                capturing = True
                continue
            elif line.startswith('###') and capturing:
                # Stop when we hit another section
                break
            elif capturing and line and ' - ' in line:
                # Parse format: "filename - query"
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    filename = parts[0].strip()
                    query = parts[1].strip()
                    assignments.append({
                        'file': filename,
                        'query': query,
                        'reasoning': 'From query separator analysis'
                    })
        
        return assignments
    
    def process_multi_file_query(self, query):
        """Process a query that may involve multiple files."""
        print(f"\n{'='*60}")
        print("MULTI-FILE QUERY PROCESSING")
        print("="*60)
        print(f"Query: {query}")
        
        # Separate the query
        print("\n" + "-"*40)
        print("QUERY SEPARATION")
        print("-"*40)
        
        assignments = self.separate_query(query)
        
        if not assignments:
            print("Could not separate query or no matching files found.")
            return
        
        print(f"Query separated into {len(assignments)} file-specific queries:")
        for i, assignment in enumerate(assignments, 1):
            print(f"{i}. {assignment['file']}: {assignment['query']}")
        
        # Process each assignment
        results = {}
        for assignment in assignments:
            file_results = self.process_single_file_query(assignment)
            if file_results:
                results[assignment['file']] = file_results
        
        # Display combined results
        self.display_combined_results(results, query)
        
        # Save report
        from reporter import reporter
        report_id = reporter.save_multi_query_report(query, assignments, results)
        
        return results
    
    def process_single_file_query(self, assignment):
        """Process a query for a single file."""
        filename = assignment['file']
        query = assignment['query']
        
        # Find the metadata for this file
        metadata = None
        for file_path, meta in self.file_metadata.items():
            if Path(file_path).name == filename:
                metadata = meta
                break
        
        if not metadata:
            print(f"Metadata not found for {filename}")
            return None
        
        print(f"\n{'='*40}")
        print(f"PROCESSING: {filename}")
        print("="*40)
        print(f"Query: {query}")
        print(f"Reasoning: {assignment.get('reasoning', 'N/A')}")
        
        try:
            # Use the splitter function from existing system
            self.initialize_llm()
            result = splitter(
                query, 
                metadata.feature_name_result["feature_rows"],
                metadata.feature_name_result["feature_cols"], 
                metadata.row_structure, 
                metadata.col_structure, 
                self.llm
            )
            
            # Render the filtered DataFrame if we have valid results
            if result and isinstance(result, dict) and 'row_selection' in result and 'col_selection' in result:
                try:
                    filtered_df = render_filtered_dataframe(
                        metadata.df, 
                        result['row_selection'], 
                        result['col_selection'], 
                        metadata.feature_name_result["feature_rows"]
                    )
                    
                    print(f"\n📊 RESULTS FOR {filename}:")
                    print("-" * 30)
                    if not filtered_df.empty:
                        print(filtered_df.to_string())
                    else:
                        print("No matching data found.")
                    
                    return {
                        'query': query,
                        'result': result,
                        'dataframe': filtered_df,
                        'reasoning': assignment.get('reasoning', 'N/A')
                    }
                    
                except Exception as e:
                    print(f"Error rendering table for {filename}: {e}")
                    return {
                        'query': query,
                        'result': result,
                        'error': str(e)
                    }
            else:
                print(f"Invalid result format for {filename}")
                return None
                
        except Exception as e:
            print(f"Error processing query for {filename}: {e}")
            return None
    
    def display_combined_results(self, results, original_query):
        """Display combined results from multiple files."""
        print(f"\n{'='*60}")
        print("COMBINED RESULTS SUMMARY")
        print("="*60)
        print(f"Original Query: {original_query}")
        print(f"Files Processed: {len(results)}")
        
        for filename, result in results.items():
            print(f"\n📄 {filename}:")
            print(f"   Query: {result['query']}")
            if 'dataframe' in result and not result['dataframe'].empty:
                print(f"   Results: {len(result['dataframe'])} rows × {len(result['dataframe'].columns)} columns")
            else:
                print("   Results: No data found")


def main():
    """Main function for multi-file processing."""
    # Initialize processor
    processor = MultiFileProcessor()
    
    # Example file paths (modify as needed)
    file_paths = [
        '../data/real/Sản lượng 2022.xlsx',
        '../data/real/Sản lượng 2023.xlsx', 
        '../data/real/Sản lượng 2024.xlsx',
        '../data/real/Doanh tác theo đối tác và nguồn 2022.xlsx',
        '../data/real/Doanh tác theo đối tác và nguồn 2023.xlsx',
        '../data/real/Doanh tác theo đối tác và nguồn 2024.xlsx',
        '../data/real/Kết quả kinh doanh chi tiết 2022.xlsx',
        '../data/real/Kết quả kinh doanh chi tiết 2023.xlsx',
        '../data/real/Kết quả kinh doanh chi tiết 2024.xlsx',
        '../data/real/Kết quả kinh doanh và chỉ số tài chính công ty 2022.xlsx',
        '../data/real/Kết quả kinh doanh và chỉ số tài chính công ty 2023.xlsx',
        '../data/real/Kết quả kinh doanh và chỉ số tài chính công ty 2024.xlsx',
        # Add more file paths here
    ]
    
    # Process files
    processor.process_multiple_files(file_paths)
    
    # Interactive query loop
    print("\n" + "="*60)
    print("MULTI-FILE EXCEL CHATBOT READY!")
    print("="*60)
    print("Commands:")
    print("- Enter your query in natural language")
    print("- Type 'files' to see file summaries")
    print("- Type 'reports' to see recent query reports")
    print("- Type 'exit' or 'quit' to stop")
    print("="*60)
    
    while True:
        try:
            query = input("\n🔍 Enter your multi-file query: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            elif query.lower() == 'files':
                processor.display_file_summaries()
                continue
            elif query.lower() == 'reports':
                print("\n" + "="*60)
                print("RECENT QUERY REPORTS")
                print("="*60)
                
                from reporter import reporter
                reporter.display_recent_reports_summary(limit=10)
                
                print("\n" + "="*60)
                continue
            elif not query:
                print("Please enter a query.")
                continue
            
            # Process the multi-file query
            processor.process_multi_file_query(query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
