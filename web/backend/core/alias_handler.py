"""
Alias Handler Module for Excel Chatbot

This module handles alias enrichment for user queries by reading alias dictionaries
from Excel files and using LLM to enrich queries with context.
"""

import pandas as pd
import logging
import os
from langchain_core.messages import HumanMessage
from .prompt import ALIAS_HANDLE_PROMPT

logger = logging.getLogger(__name__)


def format_excel_sheets(file_path):
    """
    Format Excel sheets into a structured string representation.
    
    Args:
        file_path (str): Path to the Excel file containing alias dictionary
        
    Returns:
        dict: Dictionary with sheet names as keys and formatted content as values
    """
    excel_file = pd.ExcelFile(file_path)
    output = {}
    
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        sheet_output = []
        col_names = df.columns
        
        for index, row in df.iterrows():
            row_strings = []
            for col_name, value in zip(col_names, row):
                if pd.notna(value):
                    value_str = str(value)
                    row_strings.append(f"{col_name}: {value_str}")
            sheet_output.append(", ".join(row_strings))
        
        output[sheet_name] = sheet_output
    
    return output


def get_alias_dictionary(file_path):
    """
    Load and format alias dictionary from Excel file.
    
    Args:
        file_path (str): Path to the alias Excel file
        
    Returns:
        str: Formatted string representation of the alias dictionary
        
    Raises:
        FileNotFoundError: If alias file is not found
        Exception: For other file reading errors
    """
    try:
        formatted_sheets = format_excel_sheets(file_path)
        
        return_string = ""
        for sheet_name, rows in formatted_sheets.items():
            return_string += f"Sheet: {sheet_name}\n"
            for row in rows:
                return_string += f"{row}\n"
            return_string += "\n"  # Empty line between sheets
        
        logger.info(f"Successfully loaded alias dictionary from {file_path}")
        return return_string
    
    except FileNotFoundError:
        logger.error(f"Alias file not found: {file_path}")
        raise FileNotFoundError(f"Alias file '{file_path}' not found.")
    except Exception as e:
        logger.error(f"Error reading alias file {file_path}: {str(e)}")
        raise Exception(f"Error reading alias file: {str(e)}")


def parse_enriched_query(llm_response):
    """
    Parse the LLM response to extract the enriched query.
    
    Args:
        llm_response (str): Raw response from LLM containing enriched query
        
    Returns:
        str: The enriched query string
    """
    # The LLM response should contain the enriched query
    # We need to extract it from the response
    response_content = llm_response.strip()
    
    # Look for "### Enriched Query" section
    if "### Enriched Query" in response_content:
        enriched_part = response_content.split("### Enriched Query")[-1].strip()
        # Remove any trailing markdown or extra text
        lines = enriched_part.split('\n')
        # Take the first non-empty line after the header
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                return line
        return enriched_part
    
    # Look for common patterns in the response
    lines = response_content.split('\n')
    for line in lines:
        line = line.strip()
        # Skip empty lines and headers
        if line and not line.startswith('#') and not line.startswith('**'):
            # This is likely the enriched query
            return line
    
    # If no clear pattern found, return the whole response
    return response_content


class AliasEnricher:
    """
    Handles alias enrichment for user queries using LLM.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the alias enricher.
        
        Args:
            llm: Language model instance for query enrichment
        """
        self.llm = llm
        self.alias_dictionary_cache = {}
        
    def load_alias_dictionary(self, file_path):
        """
        Load alias dictionary from file with caching.
        
        Args:
            file_path (str): Path to alias Excel file
            
        Returns:
            str: Formatted alias dictionary
        """
        # Use absolute path as cache key
        abs_path = os.path.abspath(file_path)
        
        if abs_path not in self.alias_dictionary_cache:
            self.alias_dictionary_cache[abs_path] = get_alias_dictionary(file_path)
            logger.info(f"Cached alias dictionary from {file_path}")
        else:
            logger.debug(f"Using cached alias dictionary for {file_path}")
            
        return self.alias_dictionary_cache[abs_path]
    
    def enrich_query(self, user_query, alias_file_path):
        """
        Enrich user query with alias information using LLM.
        
        Args:
            user_query (str): Original user query
            alias_file_path (str): Path to alias Excel file
            
        Returns:
            str: Enriched query with alias context
            
        Raises:
            ValueError: If LLM is not initialized or query enrichment fails
        """
        if not self.llm:
            raise ValueError("LLM not initialized for alias enrichment")
        
        try:
            logger.info(f"Enriching query: {user_query}")
            
            # Load alias dictionary
            alias_dictionary = self.load_alias_dictionary(alias_file_path)
            
            # Create prompt
            prompt = ALIAS_HANDLE_PROMPT.format(
                alias_dictionary=alias_dictionary,
                user_query=user_query
            )
            
            # Get LLM response
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Parse enriched query
            enriched_query = parse_enriched_query(response.content)
            
            logger.info(f"Original query: {user_query}")
            logger.info(f"Enriched query: {enriched_query}")
            
            return enriched_query
            
        except Exception as e:
            logger.error(f"Failed to enrich query '{user_query}': {str(e)}")
            # Return original query if enrichment fails
            logger.warning("Returning original query due to enrichment failure")
            return user_query
    
    def clear_cache(self):
        """Clear the alias dictionary cache."""
        self.alias_dictionary_cache.clear()
        logger.info("Alias dictionary cache cleared")


# Default global instance
default_alias_enricher = AliasEnricher()


def enrich_query_with_aliases(user_query, alias_file_path, llm=None):
    """
    Convenience function to enrich a query with aliases.
    
    Args:
        user_query (str): Original user query
        alias_file_path (str): Path to alias Excel file
        llm: Language model instance (optional, uses default if None)
        
    Returns:
        str: Enriched query
    """
    if llm:
        enricher = AliasEnricher(llm)
    else:
        if not default_alias_enricher.llm:
            raise ValueError("No LLM provided and default enricher not initialized")
        enricher = default_alias_enricher
    
    return enricher.enrich_query(user_query, alias_file_path) 