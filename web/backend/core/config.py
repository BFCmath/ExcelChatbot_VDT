import os
import logging
from pathlib import Path
import dotenv
import threading
from itertools import cycle

# Load environment variables from the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path=env_path)

# --- LLM Configuration with Key Cycling ---

# Find all GOOGLE_API_KEY_n variables in the environment
api_keys = [
    key for key in [os.getenv(f"GOOGLE_API_KEY_{i+1}") for i in range(10)] # Check for up to 10 keys
    if key is not None and key.strip() != ""
]

if not api_keys:
    raise ValueError("At least one GOOGLE_API_KEY_n environment variable is required (e.g., GOOGLE_API_KEY_1)")

# Create a thread-safe, cycling iterator for the API keys
_api_key_cycler = cycle(api_keys)
_api_key_lock = threading.Lock()

def get_next_api_key():
    """
    Safely returns the next API key from the list in a thread-safe manner.
    """
    with _api_key_lock:
        return next(_api_key_cycler)

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-preview-04-17")
# Note: GOOGLE_API_KEY is now managed by get_next_api_key()
# The old GOOGLE_API_KEY constant is deprecated.

# --- End LLM Configuration ---

# Application Configuration
# Use absolute path for uploads folder to ensure consistent access from all modules
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """Configure logging for the application with Unicode support."""
    import sys
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create handlers with explicit UTF-8 encoding
    file_handler = logging.FileHandler(
        log_dir / "app.log", 
        encoding='utf-8',
        errors='replace'  # Replace problematic characters instead of failing
    )
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set encoding for console handler on Windows
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Fallback if reconfigure fails
            pass
    
    # Configure formatters
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        handlers=[file_handler, console_handler],
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# File validation
def is_allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
