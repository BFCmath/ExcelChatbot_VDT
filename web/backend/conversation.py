import uuid
import logging
from datetime import datetime
from core.processor import MultiFileProcessor

# Set up logging
logger = logging.getLogger(__name__)

class Conversation:
    """
    Represents a single, isolated conversation session.

    Each conversation has a unique ID and its own instance of the
    MultiFileProcessor, ensuring that its state (processed files, metadata)
    is completely separate from other conversations.
    """
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.processor = MultiFileProcessor()
        self.created_at = datetime.now()
        logger.info(f"Created new conversation: {self.id}")

    def get_processed_files(self):
        """Returns the list of filenames processed in this conversation."""
        try:
            return [f.filename for f in self.processor.file_metadata.values()]
        except Exception as e:
            logger.error(f"Error getting processed files for conversation {self.id}: {e}")
            return []

    def process_file(self, file_path: str):
        """
        Process an uploaded file and extract its metadata.
        
        Args:
            file_path (str): Path to the uploaded file
            
        Raises:
            ValueError: If file processing fails
        """
        try:
            logger.info(f"Processing file {file_path} for conversation {self.id}")
            self.processor.extract_file_metadata(file_path)
            logger.info(f"Successfully processed file {file_path} for conversation {self.id}")
        except Exception as e:
            import traceback
            logger.error(f"Failed to process file {file_path} for conversation {self.id}: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise ValueError(f"Failed to process file: {str(e)}")

    def get_response(self, query: str):
        """
        Process a user query and return the response.
        
        Args:
            query (str): User's natural language query
            
        Returns:
            dict: Query results or error information
            
        Raises:
            ValueError: If query processing fails
        """
        try:
            logger.info(f"Processing query for conversation {self.id}: {query}")
            
            if not self.processor.file_metadata:
                logger.warning(f"WARNING: No files processed in conversation {self.id}")
                raise ValueError("No files have been processed in this conversation")
            
            # Use multi-file query processing
            result = self.processor.process_multi_file_query(query)
            logger.info(f"Successfully processed query for conversation {self.id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process query for conversation {self.id}: {e}")
            raise ValueError(f"Failed to process query: {str(e)}") 