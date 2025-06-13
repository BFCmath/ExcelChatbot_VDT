"""
Global Alias File Manager

Manages system-level alias files that are shared across all conversations.
Provides centralized state management for alias files.
"""

import os
import shutil
import logging
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AliasFileManager:
    """
    Manages the global alias file for the entire system.
    Only one alias file can be active at a time, shared across all conversations.
    """
    
    def __init__(self, alias_storage_dir: str = "alias_files"):
        """
        Initialize the alias file manager.
        
        Args:
            alias_storage_dir (str): Directory to store alias files
        """
        self.alias_storage_dir = Path(alias_storage_dir)
        self.alias_storage_dir.mkdir(exist_ok=True)
        
        self._lock = threading.RLock()
        self._current_alias_file = None
        self._alias_file_info = None
        
        # Load existing alias file on startup
        self._load_existing_alias_file()
        
        logger.info(f"AliasFileManager initialized with storage dir: {self.alias_storage_dir}")
    
    def _load_existing_alias_file(self):
        """Load existing alias file from storage directory on startup."""
        try:
            # Look for existing alias files
            alias_files = list(self.alias_storage_dir.glob("*.xlsx"))
            if alias_files:
                # Use the most recently modified file
                latest_file = max(alias_files, key=lambda f: f.stat().st_mtime)
                self._current_alias_file = str(latest_file)
                self._alias_file_info = {
                    "filename": latest_file.name,
                    "path": str(latest_file),
                    "uploaded_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                    "size": latest_file.stat().st_size
                }
                logger.info(f"Loaded existing alias file: {latest_file.name}")
            else:
                logger.info("No existing alias file found")
        except Exception as e:
            logger.error(f"Error loading existing alias file: {e}")
    
    def has_alias_file(self) -> bool:
        """
        Check if a global alias file is currently available.
        
        Returns:
            bool: True if alias file exists and is accessible
        """
        with self._lock:
            if not self._current_alias_file:
                return False
            
            # Verify file still exists
            if not os.path.exists(self._current_alias_file):
                logger.warning("Alias file path exists in memory but file is missing")
                self._current_alias_file = None
                self._alias_file_info = None
                return False
            
            return True
    
    def get_alias_file_path(self) -> Optional[str]:
        """
        Get the path to the current alias file.
        
        Returns:
            str or None: Path to alias file if available, None otherwise
        """
        with self._lock:
            if self.has_alias_file():
                return self._current_alias_file
            return None
    
    def get_alias_file_info(self) -> Optional[dict]:
        """
        Get information about the current alias file.
        
        Returns:
            dict or None: Alias file info if available, None otherwise
        """
        with self._lock:
            if self.has_alias_file():
                return self._alias_file_info.copy()
            return None
    
    def upload_alias_file(self, source_file_path: str, original_filename: str) -> dict:
        """
        Upload and set a new alias file as the system-wide alias file.
        Replaces any existing alias file.
        
        Args:
            source_file_path (str): Path to the source alias file
            original_filename (str): Original filename for display
            
        Returns:
            dict: Information about the uploaded alias file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If file is not a valid Excel file
        """
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Source file not found: {source_file_path}")
        
        # Validate file extension
        if not original_filename.lower().endswith(('.xlsx', '.xls')):
            raise ValueError("Alias file must be an Excel file (.xlsx or .xls)")
        
        with self._lock:
            try:
                # Remove existing alias file
                self._remove_current_alias_file()
                
                # Create new filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"alias_{timestamp}.xlsx"
                destination_path = self.alias_storage_dir / safe_filename
                
                # Copy file to alias storage
                shutil.copy2(source_file_path, destination_path)
                
                # Update current alias file info
                self._current_alias_file = str(destination_path)
                self._alias_file_info = {
                    "filename": original_filename,
                    "path": str(destination_path),
                    "uploaded_at": datetime.now().isoformat(),
                    "size": destination_path.stat().st_size
                }
                
                logger.info(f"Alias file uploaded successfully: {original_filename} -> {safe_filename}")
                
                return self._alias_file_info.copy()
                
            except Exception as e:
                logger.error(f"Error uploading alias file: {e}")
                # Clean up partial state
                self._current_alias_file = None
                self._alias_file_info = None
                raise
    
    def remove_alias_file(self) -> bool:
        """
        Remove the current alias file from the system.
        
        Returns:
            bool: True if file was removed successfully, False if no file existed
        """
        with self._lock:
            if not self._current_alias_file:
                return False
            
            return self._remove_current_alias_file()
    
    def _remove_current_alias_file(self) -> bool:
        """Internal method to remove current alias file."""
        if not self._current_alias_file:
            return False
        
        try:
            if os.path.exists(self._current_alias_file):
                os.remove(self._current_alias_file)
                logger.info(f"Removed alias file: {self._current_alias_file}")
            
            self._current_alias_file = None
            self._alias_file_info = None
            return True
            
        except Exception as e:
            logger.error(f"Error removing alias file: {e}")
            return False
    
    def get_system_status(self) -> dict:
        """
        Get the current status of the alias file system.
        
        Returns:
            dict: System status information
        """
        with self._lock:
            return {
                "has_alias_file": self.has_alias_file(),
                "alias_file_info": self.get_alias_file_info(),
                "storage_directory": str(self.alias_storage_dir),
                "system_ready": True
            }


# Global instance
_global_alias_manager = None
_manager_lock = threading.Lock()


def get_alias_manager() -> AliasFileManager:
    """
    Get the global alias file manager instance.
    Thread-safe singleton pattern.
    
    Returns:
        AliasFileManager: The global alias manager instance
    """
    global _global_alias_manager
    
    if _global_alias_manager is None:
        with _manager_lock:
            if _global_alias_manager is None:
                # Create alias files directory in backend folder
                alias_dir = os.path.join(os.path.dirname(__file__), "alias_files")
                _global_alias_manager = AliasFileManager(alias_dir)
    
    return _global_alias_manager


def has_system_alias_file() -> bool:
    """
    Quick check if system has an alias file available.
    
    Returns:
        bool: True if system alias file is available
    """
    return get_alias_manager().has_alias_file()


def get_system_alias_file_path() -> Optional[str]:
    """
    Get the path to the system alias file.
    
    Returns:
        str or None: Path to system alias file if available
    """
    return get_alias_manager().get_alias_file_path() 