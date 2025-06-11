import os
import logging
import hashlib
import unicodedata
import re
import uuid
from pathlib import Path
from typing import List
from fastapi import HTTPException, UploadFile
from core.config import is_allowed_file, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

class FileValidator:
    """Validates uploaded files for security and format compliance."""
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        Validate an uploaded file.
        
        Args:
            file: The uploaded file to validate
            
        Raises:
            HTTPException: If validation fails
        """
        # Check if file is provided
        if not file or not file.filename:
            logger.warning("WARNING: Empty file upload attempted")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        if not is_allowed_file(file.filename):
            logger.warning(f"WARNING: Invalid file extension: {file.filename}")
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size (FastAPI handles this automatically, but we can add custom logic)
        if hasattr(file, 'size') and file.size and file.size > MAX_CONTENT_LENGTH:
            logger.warning(f"WARNING: File too large: {file.filename} ({file.size} bytes)")
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {MAX_CONTENT_LENGTH} bytes"
            )
        
        logger.info(f"File validation passed: {file.filename}")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            logger.warning("WARNING: Empty filename provided")
            return "unknown_file"
        
        # Normalize unicode and remove dangerous characters
        safe_filename = unicodedata.normalize('NFKD', filename)
        safe_filename = Path(safe_filename).name
        # Remove any remaining path separators and dangerous chars
        safe_filename = re.sub(r'[^\w\.-]', '_', safe_filename)
        
        # Ensure filename isn't empty after sanitization
        if not safe_filename:
            logger.warning(f"WARNING: Filename became empty after sanitization: {filename}")
            safe_filename = "sanitized_file.xlsx"
        
        # Add timestamp to prevent conflicts
        timestamp = hashlib.md5(filename.encode()).hexdigest()[:8]
        name, ext = os.path.splitext(safe_filename)
        
        # If no extension or invalid extension, default to .xlsx
        if not ext or ext.lower() not in ['.xlsx', '.xls']:
            ext = '.xlsx'
        
        safe_filename = f"{name}_{timestamp}{ext}"
        
        logger.info(f"Filename sanitized: {filename} -> {safe_filename}")
        return safe_filename

    @staticmethod
    def validate_multiple_files(files: List[UploadFile]) -> None:
        """
        Validate multiple uploaded files.
        
        Args:
            files: List of uploaded files
            
        Raises:
            HTTPException: If validation fails
        """
        if not files:
            logger.warning("WARNING: No files provided in upload request")
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit number of files
            logger.warning(f"WARNING: Too many files uploaded: {len(files)}")
            raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files allowed")
        
        for file in files:
            FileValidator.validate_file(file)

class RequestValidator:
    """Validates API requests."""
    
    @staticmethod
    def validate_conversation_id(conversation_id: str) -> None:
        """
        Validate conversation ID format.
        
        Args:
            conversation_id: The conversation ID to validate
            
        Raises:
            HTTPException: If validation fails
        """
        if not conversation_id:
            logger.warning("WARNING: Empty conversation ID provided")
            raise HTTPException(status_code=400, detail="Conversation ID is required")
        
        try:
            uuid.UUID(conversation_id, version=4)
        except (ValueError, TypeError):
            logger.warning(f"WARNING: Invalid conversation ID format: {conversation_id}")
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    @staticmethod
    def validate_query(query: str) -> None:
        """
        Validate query string.
        
        Args:
            query: The query string to validate
            
        Raises:
            HTTPException: If validation fails
        """
        if not query or not query.strip():
            logger.warning("WARNING: Empty query provided")
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(query) > 1000:  # Reasonable query length limit
            logger.warning(f"WARNING: Query too long: {len(query)} characters")
            raise HTTPException(status_code=400, detail="Query too long. Maximum 1000 characters allowed") 