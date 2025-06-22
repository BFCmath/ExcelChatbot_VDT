import os
import logging
from pathlib import Path
import dotenv
import threading
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path=env_path)

# --- LLM Configuration with Pre-loaded Pool ---

# Find all GOOGLE_API_KEY_n variables in the environment
api_keys = [
    key for key in [os.getenv(f"GOOGLE_API_KEY_{i+1}") for i in range(4)] # Check for up to 4 keys
    if key is not None and key.strip() != ""
]

if not api_keys:
    raise ValueError("At least one GOOGLE_API_KEY_n environment variable is required (e.g., GOOGLE_API_KEY_1)")

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-preview-04-17")

# Pre-load all LLM instances at startup to avoid threading issues
_llm_pool = []
_llm_index = 0
_llm_lock = threading.Lock()
_pool_initialized = False

def _initialize_llm_pool():
    """
    Initialize the LLM pool with all available API keys.
    This is called once during module import.
    """
    global _llm_pool, _pool_initialized
    
    if _pool_initialized:
        return
        
    try:
        for i, api_key in enumerate(api_keys):
            llm_instance = ChatGoogleGenerativeAI(
                model=LLM_MODEL, 
                google_api_key=api_key, 
                temperature=0
            )
            _llm_pool.append(llm_instance)
            logging.getLogger(__name__).info(f"Initialized LLM instance {i+1}/{len(api_keys)}")
        
        _pool_initialized = True
        logging.getLogger(__name__).info(f"LLM pool initialized with {len(_llm_pool)} instances")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize LLM pool: {e}")
        raise

def get_next_llm_instance():
    """
    Returns the next LLM instance from the pre-loaded pool in a thread-safe manner.
    Uses round-robin selection with minimal lock time.
    
    Returns:
        ChatGoogleGenerativeAI: A pre-initialized LLM instance
    """
    global _llm_index
    
    if not _pool_initialized:
        _initialize_llm_pool()
    
    if not _llm_pool:
        raise RuntimeError("No LLM instances available in pool")
    
    # Use atomic operation with minimal lock time
    with _llm_lock:
        current_index = _llm_index
        _llm_index = (_llm_index + 1) % len(_llm_pool)
    
    return _llm_pool[current_index]

def get_next_api_key():
    """
    DEPRECATED: Use get_next_llm_instance() instead.
    This function is kept for backward compatibility but should not be used.
    """
    logging.getLogger(__name__).warning("get_next_api_key() is deprecated. Use get_next_llm_instance() instead.")
    
    # Fallback to simple round-robin API key selection
    global _llm_index
    with _llm_lock:
        current_index = _llm_index
        _llm_index = (_llm_index + 1) % len(api_keys)
    
    return api_keys[current_index]

# Initialize the pool when module is imported
_initialize_llm_pool()

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
