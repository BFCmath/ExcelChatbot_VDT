"""
Multi-File Excel Chatbot System

This module handles multiple Excel files, including:
- Metadata extraction
- File summarization via LLM
- Query separation and routing to individual files
- Coordinated processing across multiple data sources
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import dotenv

from .preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans
from .llm import splitter, get_feature_names
from .extract_df import render_filtered_dataframe
from .postprocess import TablePostProcessor
from .utils import get_feature_name_content, format_row_dict_for_llm, format_col_dict_for_llm
from .metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from .prompt import FILE_SUMMARY_PROMPT, QUERY_SEPARATOR_PROMPT

# Set up logging
logger = logging.getLogger(__name__)

# Construct the path to the .env file within the same directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path=dotenv_path)


class FileMetadata:
    """Stores metadata for a processed file."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.filename = Path(file_path).name
        self.df = None
        self.feature_name_result = None
        self.row_structure = None
        self.col_structure = None
        self.summary = None
        self.feature_names = None
        self.number_of_row_header = None
        self.row_dict = None
        self.col_dict = None


class MultiFileProcessor:
    """Handles processing of multiple Excel files and queries."""
    
    def __init__(self):
        self.file_metadata = {}
        self.llm = None
        self.post_processor = TablePostProcessor()
    
    def initialize_llm(self):
        """Initialize LLM if not already done."""
        if self.llm is None:
            api_key = os.getenv('GOOGLE_API_KEY_1')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.0
            )
    
    def extract_file_metadata(self, file_path):
        """Extract and store metadata for a single file."""
        # Initialize LLM if needed
        self.initialize_llm()
        
        metadata = FileMetadata(file_path)
        
        try:
            logger.info(f"Extracting metadata for: {file_path}")
            
            # Extract feature names
            logger.info(f"Step 1: Extracting feature names for {file_path}")
            metadata.feature_names = get_feature_names(file_path, self.llm)
            logger.info(f"Feature names extracted: {metadata.feature_names}")
            
            # Get feature name content
            logger.info(f"Step 2: Getting feature name content for {file_path}")
            _, metadata.feature_name_result = get_feature_name_content(file_path, metadata.feature_names)
            logger.info(f"Feature name result: {metadata.feature_name_result}")
            
            # Get row header info
            logger.info(f"Step 3: Getting row header info for {file_path}")
            metadata.number_of_row_header = get_number_of_row_header(file_path)
            logger.info(f"Number of row headers: {metadata.number_of_row_header}")
            
            # Load and preprocess DataFrame
            logger.info(f"Step 4: Loading DataFrame for {file_path}")
            metadata.df = pd.read_excel(
                file_path, 
                header=list(range(0, metadata.number_of_row_header)),
                engine='openpyxl'
            )
            logger.info(f"DataFrame loaded successfully. Shape: {metadata.df.shape}")
            
            logger.info(f"Step 5: Preprocessing DataFrame for {file_path}")
            metadata.df = clean_unnamed_header(metadata.df, metadata.number_of_row_header)
            metadata.df = fill_undefined_sequentially(metadata.df, metadata.feature_name_result["feature_rows"])
            metadata.df = forward_fill_column_nans(metadata.df, metadata.feature_name_result["feature_rows"])
            
            # Create nested dictionaries
            logger.info(f"Step 6: Creating nested dictionaries for {file_path}")
            metadata.row_dict = convert_df_rows_to_nested_dict(df_input=metadata.df, hierarchy_columns_list=metadata.feature_name_result["feature_rows"])
            metadata.col_dict = convert_df_headers_to_nested_dict(df=metadata.df, column_names_list=metadata.feature_name_result["feature_cols"])
            
            # Generate structures for LLM
            metadata.row_structure = format_row_dict_for_llm(metadata.row_dict, metadata.feature_name_result["feature_rows"])
            metadata.col_structure = format_col_dict_for_llm(metadata.col_dict)
            
            # Generate summary
            metadata.summary = self.generate_file_summary(metadata)
            
            # Store metadata
            self.file_metadata[file_path] = metadata
            logger.info(f"Successfully processed {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            raise

    def generate_file_summary(self, metadata):
        """Generate LLM summary for a file's metadata."""
        summary_prompt = FILE_SUMMARY_PROMPT.format(
            filename=metadata.filename,
            feature_rows=metadata.feature_name_result['feature_rows'],
            feature_cols=metadata.feature_name_result['feature_cols'],
            row_structure=metadata.row_structure,
            col_structure=metadata.col_structure
        )
        
        message = HumanMessage(content=summary_prompt)
        response = self.llm.invoke([message])
        summary = response.content.strip()
        return summary
    
    def process_multiple_files(self, file_paths):
        """Process multiple files and extract metadata."""
        logger.info("Starting multi-file metadata extraction")
        
        for file_path in file_paths:
            # Always extract metadata, no caching
            self.extract_file_metadata(file_path)
        
        logger.info("Multi-file metadata extraction complete")

    def get_all_file_summaries(self):
        """Returns a formatted string of all file summaries."""
        return "\n\n".join(
            f"Filename: {Path(fp).name}\nContent:\n{md.summary}"
            for fp, md in self.file_metadata.items() if md.summary
        )

    def separate_query(self, query):
        """Use LLM to separate a query based on file summaries."""
        self.initialize_llm()
        files_context = self.get_all_file_summaries()

        separator_prompt = QUERY_SEPARATOR_PROMPT.format(
            files_context=files_context,
            query=query
        )
        
        message = HumanMessage(content=separator_prompt)
        response = self.llm.invoke([message])
        return self.parse_separator_response(response.content)

    def parse_separator_response(self, response):
        """Parse the response from the query separator agent."""
        assignments = []
        # Find the "Separated Query" section
        separated_query_section = response.split("### Separated Query")[-1]
        
        lines = separated_query_section.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Format is "filename.xlsx - query_segment"
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                filename, query_segment = parts
                
                # Find the full path for the filename
                full_path = None
                for fp in self.file_metadata.keys():
                    if Path(fp).name == filename:
                        full_path = fp
                        break
                
                if full_path:
                    assignments.append({
                        'file_path': full_path,
                        'query': query_segment
                    })
                else:
                    logger.warning(f"WARNING: Filename '{filename}' from separator not found in processed files.")
            else:
                logger.warning(f"WARNING: Could not parse separator line: '{line}'")

        return assignments
    
    def process_multi_file_query(self, query):
        """
        Process a query that may involve multiple files.
        1. Separate query.
        2. Process each sub-query.
        3. Combine and return results.
        """
        assignments = self.separate_query(query)
        if not assignments:
            return {
                "success": False,
                "error": "Could not determine which file to query.",
                "results": []
            }
        
        results = []
        for assignment in assignments:
            file_path = assignment['file_path']
            sub_query = assignment['query']
            
            logger.info(f"Processing query for {Path(file_path).name}: {sub_query}")
            
            # Process this specific query against the specific file
            df_result = self.process_single_file_query(assignment)
            # Return the DataFrame as-is to preserve hierarchical structure
            if df_result is not None and not df_result.empty:
                # Use post-processor to preserve hierarchical structure for frontend rendering
                table_info = self.post_processor.extract_hierarchical_table_info(df_result)
                
                result_entry = {
                    "filename": Path(file_path).name,
                    "query": sub_query,
                    "success": True,
                    "table_info": table_info
                }
            else:
                result_entry = {
                    "filename": Path(file_path).name,
                    "query": sub_query,
                    "success": False,
                    "message": "No matching data found.",
                    "data": []
                }
            
            results.append(result_entry)

        return {
            "success": True,
            "query": query,
            "total_files_processed": len(results),
            "results": results
        }

    def process_single_file_query(self, assignment):
        """
        Processes a single file query assignment from the separator.
        
        Args:
            assignment (dict): A dictionary with 'file_path' and 'query'.
            
        Returns:
            DataFrame: The filtered DataFrame result, or None.
        """
        file_path = assignment['file_path']
        query = assignment['query']
        
        metadata = self.file_metadata.get(file_path)
        if not metadata:
            logger.error(f"No metadata found for {file_path}")
            return None
            
        # Ensure LLM is initialized
        self.initialize_llm()
        
        logger.info("Using splitter agent to process query")
        # Use the splitter agent to process the query
        result = splitter(
            query=query,
            feature_rows=metadata.feature_name_result['feature_rows'],
            feature_cols=metadata.feature_name_result['feature_cols'],
            row_structure=metadata.row_structure,
            col_structure=metadata.col_structure,
            llm=self.llm
        )
        
        # Render the filtered DataFrame
        if result and isinstance(result, dict) and 'row_selection' in result and 'col_selection' in result:
            filtered_df = render_filtered_dataframe(
                df=metadata.df,
                row_selection=result['row_selection'],
                col_selection=result['col_selection'],
                feature_rows=metadata.feature_name_result['feature_rows']
            )
            print(filtered_df) # do not delete this
            return filtered_df
        else:
            logger.warning("WARNING: Splitter did not return a valid result.")
            return None
        
