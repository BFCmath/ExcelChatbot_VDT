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
from langchain_core.messages import HumanMessage
import dotenv

from .preprocess import clean_unnamed_header, fill_undefined_sequentially, forward_fill_column_nans, extract_headers_only
from .llm import splitter, get_feature_names, get_feature_names_from_headers, get_llm_instance
from .extract_df import render_filtered_dataframe
from .postprocess import TablePostProcessor
from .utils import get_feature_name_content, format_row_dict_for_llm, format_col_dict_for_llm
from .metadata import get_number_of_row_header, convert_df_headers_to_nested_dict, convert_df_rows_to_nested_dict
from .prompt import FILE_SUMMARY_PROMPT, QUERY_SEPARATOR_PROMPT
from .alias_handler import AliasEnricher

# Set up logging
logger = logging.getLogger(__name__)

# Construct the path to the .env file within the same directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path=dotenv_path)


class FileMetadata:
    """Stores metadata for a processed file."""
    
    def __init__(self, file_path, original_filename=None):
        self.file_path = file_path
        self.filename = Path(file_path).name  # sanitized filename for internal use
        self.original_filename = original_filename or self.filename  # display name
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
        self.post_processor = TablePostProcessor()
        # AliasEnricher will get its LLM instance on-demand
        self.alias_enricher = AliasEnricher()
    
    def extract_file_metadata(self, file_path, original_filename=None):
        """Extract and store metadata for a single file."""
        metadata = FileMetadata(file_path, original_filename)
        
        try:
            logger.info(f"Extracting metadata for: {file_path}")
            
            # Get row header info FIRST
            logger.info(f"Step 1: Getting row header info for {file_path}")
            metadata.number_of_row_header = get_number_of_row_header(file_path)
            logger.info(f"Number of row headers: {metadata.number_of_row_header}")
            
            # Extract only headers for LLM processing
            logger.info(f"Step 2: Extracting headers for LLM analysis for {file_path}")
            headers_content = extract_headers_only(file_path, metadata.number_of_row_header)
            logger.info(f"Headers extracted for LLM processing")
            
            # Extract feature names from headers only
            logger.info(f"Step 3: Extracting feature names from headers for {file_path}")
            metadata.feature_names = get_feature_names_from_headers(headers_content)
            logger.info(f"Feature names extracted: {metadata.feature_names}")
            
            # Get feature name content
            logger.info(f"Step 4: Getting feature name content for {file_path}")
            _, metadata.feature_name_result = get_feature_name_content(file_path, metadata.feature_names)
            logger.info(f"Feature name result: {metadata.feature_name_result}")
            
            # Load and preprocess DataFrame
            logger.info(f"Step 5: Loading DataFrame for {file_path}")
            metadata.df = pd.read_excel(
                file_path, 
                header=list(range(0, metadata.number_of_row_header)),
                engine='openpyxl'
            )
            logger.info(f"DataFrame loaded successfully. Shape: {metadata.df.shape}")
            
            logger.info(f"Step 6: Preprocessing DataFrame for {file_path}")
            metadata.df = clean_unnamed_header(metadata.df, metadata.number_of_row_header)
            metadata.df = fill_undefined_sequentially(metadata.df, metadata.feature_name_result["feature_rows"])
            metadata.df = forward_fill_column_nans(metadata.df, metadata.feature_name_result["feature_rows"])
            
            # Create nested dictionaries
            logger.info(f"Step 7: Creating nested dictionaries for {file_path}")
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
        llm = get_llm_instance()
        summary_prompt = FILE_SUMMARY_PROMPT.format(
            filename=metadata.original_filename,
            feature_rows=metadata.feature_name_result['feature_rows'],
            feature_cols=metadata.feature_name_result['feature_cols'],
            row_structure=metadata.row_structure,
            col_structure=metadata.col_structure
        )
        
        message = HumanMessage(content=summary_prompt)
        response = llm.invoke([message])
        summary = response.content.strip()
        return summary
    
    def process_multiple_files(self, file_paths, original_filenames=None):
        """Process multiple files and extract metadata."""
        logger.info("Starting multi-file metadata extraction")
        
        if original_filenames is None:
            original_filenames = [None] * len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            original_filename = original_filenames[i] if i < len(original_filenames) else None
            # Always extract metadata, no caching
            self.extract_file_metadata(file_path, original_filename)
        
        logger.info("Multi-file metadata extraction complete")

    def get_all_file_summaries(self):
        """Returns a formatted string of all file summaries."""
        return "\n\n".join(
            f"Filename: {md.original_filename}\nContent:\n{md.summary}"
            for fp, md in self.file_metadata.items() if md.summary
        )

    def separate_query(self, query):
        """Use LLM to separate a query based on file summaries."""
        llm = get_llm_instance()
        files_context = self.get_all_file_summaries()

        separator_prompt = QUERY_SEPARATOR_PROMPT.format(
            files_context=files_context,
            query=query
        )
        
        message = HumanMessage(content=separator_prompt)
        response = llm.invoke([message])
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
                for fp, metadata in self.file_metadata.items():
                    if metadata.original_filename == filename:
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
    
    def process_multi_file_query(self, query, alias_file_path=None):
        """
        Process a query that may involve multiple files.
        1. Enrich query with aliases (if alias file provided).
        2. Separate query.
        3. Process each sub-query.
        4. Combine and return results.
        """
        # Step 1: Enrich query with aliases if alias file is provided
        enriched_query = query
        if alias_file_path:
            # The AliasEnricher will now get its own LLM instance internally
            try:
                logger.info(f"🔍 Enriching query with aliases from {alias_file_path}")
                enriched_query = self.alias_enricher.enrich_query(query, alias_file_path)
                logger.info(f"📝 Original query: {query}")
                logger.info(f"✨ Enriched query: {enriched_query}")
            except Exception as e:
                logger.warning(f"⚠️ Alias enrichment failed: {e}, using original query")
                enriched_query = query
        
        # Step 2: Separate query (using enriched query)
        assignments = self.separate_query(enriched_query)
        if not assignments:
            logger.warning("Query separator did not assign the query to any file.")
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
                table_structures = self.post_processor.extract_hierarchical_table_info(df_result)
                # if 'normal_table' in table_structures:
                #     normal_table = table_structures["normal_table"]
                
                # if 'flattened_table' in table_structures:
                #     flattened_table = table_structures["flattened_table"]
                
                result_entry = {
                    "filename": self.file_metadata[file_path].original_filename,
                    "query": sub_query,
                    "success": True,
                    "table_info": table_structures["normal_table"],  # Keep backward compatibility
                    "flattened_table_info": table_structures["flattened_table"],  # Add flattened table
                    "feature_rows": self.file_metadata[file_path].feature_name_result["feature_rows"],  # Add feature rows info
                    "feature_cols": self.file_metadata[file_path].feature_name_result["feature_cols"]   # Add feature cols info
                }

            else:
                result_entry = {
                    "filename": self.file_metadata[file_path].original_filename,
                    "query": sub_query,
                    "success": False,
                    "message": "No matching data found.",
                    "data": []
                }
            
            results.append(result_entry)

        return {
            "success": True,
            "original_query": query,
            "enriched_query": enriched_query,
            "total_files_processed": len(results),
            "results": results
        }

    def process_single_file_query(self, assignment):
        """Process a single sub-query for a specific file."""
        file_path = assignment['file_path']
        query = assignment['query']
        
        metadata = self.file_metadata.get(file_path)
        if not metadata:
            logger.error(f"No metadata found for {file_path}")
            return None
            
        # Ensure LLM is initialized
        
        logger.info("Using splitter agent to process query")
        # Use the splitter agent to process the query
        result = splitter(
            query=query,
            feature_rows=metadata.feature_name_result['feature_rows'],
            feature_cols=metadata.feature_name_result['feature_cols'],
            row_structure=metadata.row_structure,
            col_structure=metadata.col_structure,
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
        
