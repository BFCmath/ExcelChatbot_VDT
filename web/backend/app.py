import os
import shutil
import logging
from typing import List, Optional
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from managers import conversation_manager
from middleware import FileValidator, RequestValidator
from core.config import setup_logging, UPLOAD_FOLDER, ALLOWED_ORIGINS, MAX_CONTENT_LENGTH
from alias_manager import get_alias_manager, has_system_alias_file
from core.plotting import PlotGenerator

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting Excel Chatbot API")
    
    # Create upload folder
    Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
    logger.info(f"Upload folder ready: {UPLOAD_FOLDER}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Excel Chatbot API")

# Initialize FastAPI app
app = FastAPI(
    title="Excel Chatbot API",
    description="API for processing Excel files and natural language queries",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request size limit middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit request size to prevent large uploads."""
    if request.method == "POST" and "upload" in str(request.url):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_LENGTH:
            logger.warning(f"WARNING: Request too large: {content_length} bytes")
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Maximum size: {MAX_CONTENT_LENGTH} bytes"}
            )
    response = await call_next(request)
    return response

# Exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError on {request.url}: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")

class ConversationResponse(BaseModel):
    conversation_id: str

class UploadResponse(BaseModel):
    message: str
    uploaded_files: List[str]
    all_processed_files_in_conversation: List[str]

class FilesResponse(BaseModel):
    processed_files: List[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    active_conversations: int

class QueryResponse(BaseModel):
    results: dict

class AliasFileResponse(BaseModel):
    message: str
    alias_file_info: dict

class AliasSystemStatus(BaseModel):
    has_alias_file: bool
    alias_file_info: Optional[dict] = None
    storage_directory: str
    system_ready: bool

class PlotRequest(BaseModel):
    table_data: dict = Field(..., description="JSON table data from frontend download")
    prompt: str = Field(..., min_length=1, max_length=500, description="User's plotting request")

class PlotResponse(BaseModel):
    success: bool
    plot_data: Optional[str] = None
    plot_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    html_content: Optional[str] = None
    data_points: Optional[int] = None
    hierarchy: Optional[List[str]] = None
    priority: Optional[str] = None
    analysis: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

# --- API Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        active_conversations=conversation_manager.get_conversation_count()
    )

# --- Alias File Management Endpoints ---

@app.get("/alias/status", response_model=AliasSystemStatus)
async def get_alias_system_status():
    """
    Get the current status of the alias file system.
    """
    try:
        alias_manager = get_alias_manager()
        status = alias_manager.get_system_status()
        logger.info(f"Alias system status: {status}")
        return AliasSystemStatus(**status)
    except Exception as e:
        logger.error(f"Failed to get alias system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get alias system status: {str(e)}")

@app.post("/alias/upload", response_model=AliasFileResponse)
async def upload_alias_file(
    file: UploadFile = File(...)
):
    """
    Upload a new alias file to the system.
    Replaces any existing alias file.
    """
    try:
        # Validate file
        FileValidator.validate_file(file)
        
        # Check if it's an Excel file
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Alias file must be an Excel file (.xlsx or .xls)")
        
        # Create a temporary file path
        safe_filename = FileValidator.sanitize_filename(file.filename)
        temp_file_path = os.path.join(UPLOAD_FOLDER, f"temp_alias_{safe_filename}")
        
        # Save file temporarily
        await save_file_async(file, temp_file_path)
        
        # Upload to alias manager
        alias_manager = get_alias_manager()
        alias_info = alias_manager.upload_alias_file(temp_file_path, file.filename)
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        logger.info(f"Alias file uploaded successfully: {file.filename}")
        
        return AliasFileResponse(
            message=f"Alias file '{file.filename}' uploaded successfully",
            alias_file_info=alias_info
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to upload alias file: {e}")
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload alias file: {str(e)}")

@app.delete("/alias", response_model=dict)
async def remove_alias_file():
    """
    Remove the current alias file from the system.
    """
    try:
        alias_manager = get_alias_manager()
        success = alias_manager.remove_alias_file()
        
        if success:
            logger.info("Alias file removed successfully")
            return {"message": "Alias file removed successfully"}
        else:
            return {"message": "No alias file was present to remove"}
            
    except Exception as e:
        logger.error(f"Failed to remove alias file: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove alias file")

@app.post("/conversations", status_code=201, response_model=ConversationResponse)
async def create_conversation():
    """
    Starts a new conversation and returns its unique ID.
    """
    try:
        conv_id = conversation_manager.create_conversation()
        logger.info(f"Created conversation: {conv_id}")
        return ConversationResponse(conversation_id=conv_id)
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@app.post("/upload", response_model=UploadResponse)
async def upload_file_simple(
    file: UploadFile = File(...),
    conversation_id: str = Form(...)
):
    """
    Simple upload endpoint for single file (for frontend compatibility).
    """
    # Delegate to the main upload function
    return await upload_files(conversation_id, [file])

@app.post("/conversations/{conversation_id}/upload", response_model=UploadResponse)
async def upload_files(
    conversation_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Uploads one or more Excel files to a specific conversation.
    """
    # Validate conversation ID
    RequestValidator.validate_conversation_id(conversation_id)
    
    # Get conversation
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        logger.warning(f"WARNING: Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Validate files
    FileValidator.validate_multiple_files(files)

    processed_files = []
    failed_files = []
    
    for file in files:
        file_location = None
        try:
            # Sanitize filename
            safe_filename = FileValidator.sanitize_filename(file.filename)
            file_location = os.path.join(UPLOAD_FOLDER, safe_filename)
            
            logger.info(f"Processing file: {file.filename} -> {safe_filename}")
            logger.info(f"File will be saved to: {file_location}")
            
            # Save file asynchronously
            await save_file_async(file, file_location)
            
            # Process the file
            logger.info(f"Starting file processing for: {file_location}")
            await process_file_async(conv, file_location, file.filename)
            processed_files.append(file.filename)
            
            logger.info(f"Successfully processed file: {file.filename}")
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to process file {file.filename}: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            failed_files.append(file.filename)
            
            # Clean up failed file
            if file_location and os.path.exists(file_location):
                os.remove(file_location)

    if not processed_files:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to process any files. Failed files: {failed_files}"
        )

    return UploadResponse(
        message=f"Successfully uploaded {len(processed_files)} files.",
        uploaded_files=processed_files,
        all_processed_files_in_conversation=conv.get_processed_files()
    )

@app.get("/conversations/{conversation_id}/validate")
async def validate_conversation(conversation_id: str):
    """Validate if a conversation exists in the backend."""
    try:
        # Validate conversation ID format
        RequestValidator.validate_conversation_id(conversation_id)
        
        # Check if conversation exists (this will also trigger cleanup)
        conv = conversation_manager.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"valid": True, "conversation_id": conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/conversations/{conversation_id}/files", response_model=FilesResponse)
async def get_processed_files(conversation_id: str):
    """
    Retrieves the list of processed files for a conversation.
    """
    RequestValidator.validate_conversation_id(conversation_id)
    
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        logger.warning(f"WARNING: Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return FilesResponse(processed_files=conv.get_processed_files())

@app.post("/conversations/{conversation_id}/query", response_model=QueryResponse)
async def handle_query(conversation_id: str, request: QueryRequest):
    """
    Receives a query, processes it, and returns the result.
    """
    RequestValidator.validate_conversation_id(conversation_id)
    RequestValidator.validate_query(request.query)
    
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        logger.warning(f"WARNING: Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conv.get_processed_files():
        logger.warning(f"WARNING: No files uploaded to conversation: {conversation_id}")
        raise HTTPException(
            status_code=400, 
            detail="No files have been uploaded to this conversation yet."
        )

    try:
        # Process query asynchronously
        result = await process_query_async(conv, request.query)
        
        # Add comprehensive logging for debugging
        logger.info(f"🔄 [API] Query processing completed for conversation {conversation_id}")
        logger.info(f"📊 [API] Result type: {type(result)}")
        logger.info(f"📊 [API] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            logger.info(f"✅ [API] Result success: {result.get('success', 'MISSING')}")
            logger.info(f"✅ [API] Result query: {result.get('query', 'MISSING')}")
            logger.info(f"✅ [API] Result has results: {'results' in result}")
            
            if 'results' in result and isinstance(result['results'], list):
                logger.info(f"📋 [API] Results list length: {len(result['results'])}")
                
                for i, res in enumerate(result['results']):
                    logger.info(f"📄 [API] Result {i} keys: {list(res.keys()) if isinstance(res, dict) else 'Not a dict'}")
                    if isinstance(res, dict):
                        logger.info(f"📄 [API] Result {i} filename: {res.get('filename', 'MISSING')}")
                        logger.info(f"📄 [API] Result {i} success: {res.get('success', 'MISSING')}")
                        logger.info(f"📄 [API] Result {i} has table_info: {'table_info' in res}")
                        logger.info(f"📄 [API] Result {i} has flattened_table_info: {'flattened_table_info' in res}")
                        
                        if 'flattened_table_info' in res:
                            if res['flattened_table_info']:
                                logger.info(f"📄 [API] Result {i} flattened_table_info keys: {list(res['flattened_table_info'].keys())}")
                                logger.info(f"📄 [API] Result {i} flattened final_columns: {res['flattened_table_info'].get('final_columns', 'MISSING')}")
                            else:
                                logger.warning(f"⚠️ [API] Result {i} flattened_table_info is None or empty!")
                        else:
                            logger.error(f"❌ [API] Result {i} MISSING flattened_table_info!")
        
        return QueryResponse(results=result)
    except ValueError as e:
        # Re-raise ValueError to be handled by the exception handler
        raise e
    except Exception as e:
        logger.error(f"Unexpected error processing query for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

# --- Plotting Endpoint ---

@app.post("/plot/generate", response_model=PlotResponse)
async def generate_plot(request: PlotRequest):
    """
    Generate plots based on table data and user prompt using LLM and tool calling.
    
    This endpoint receives JSON table data (from frontend download) and a plotting prompt,
    then uses structured LLM prompts with tool calling to generate appropriate visualizations.
    
    Supports:
    - Bar charts for categorical comparisons
    - Sunburst charts for hierarchical data
    - Line charts for time series/trends
    - Scatter plots for relationships
    - Histograms for distributions
    - Pie charts for proportional data
    """
    try:
        # Validate table data structure
        if not isinstance(request.table_data, dict):
            raise HTTPException(status_code=400, detail="table_data must be a dictionary")
        
        # Validate expected frontend JSON format (from table.js downloadAsJSON)
        required_fields = ['final_columns', 'data_rows', 'feature_rows', 'feature_cols']
        missing_fields = [field for field in required_fields if field not in request.table_data]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields in table_data: {missing_fields}. Expected frontend JSON format with final_columns, data_rows, feature_rows, feature_cols."
            )
        
        # Log the plotting request
        logger.info(f"📊 [PLOT] New plotting request")
        logger.info(f"📊 [PLOT] Prompt: {request.prompt}")
        logger.info(f"📊 [PLOT] Table shape: {len(request.table_data.get('data_rows', []))} rows × {len(request.table_data.get('final_columns', []))} columns")
        logger.info(f"📊 [PLOT] Has hierarchical: {request.table_data.get('has_multiindex', False)}")
        logger.info(f"📊 [PLOT] Flatten level: {request.table_data.get('flatten_level_applied', 'unknown')}")
        logger.info(f"📊 [PLOT] Feature rows: {request.table_data.get('feature_rows', [])}")
        logger.info(f"📊 [PLOT] Feature cols: {request.table_data.get('feature_cols', [])}")
        
        # Initialize plot generator
        plot_generator = PlotGenerator()
        
        # Generate plot using LLM and tools
        plot_result = await plot_generator.generate_plot(request.table_data, request.prompt)
        
        logger.info(f"📊 [PLOT] Plot generation completed: {plot_result.get('success', False)}")
        
        # Convert to response format
        return PlotResponse(
            success=plot_result.get('success', False),
            plot_data=plot_result.get('plot_data'),
            plot_type=plot_result.get('plot_type'),
            title=plot_result.get('title'),
            description=plot_result.get('description'),
            html_content=plot_result.get('html_content'),
            data_points=plot_result.get('data_points'),
            hierarchy=plot_result.get('hierarchy'),
            priority=plot_result.get('priority'),
            analysis=plot_result.get('analysis'),
            message=plot_result.get('message'),
            error=plot_result.get('error')
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ [PLOT] Error generating plot: {e}", exc_info=True)
        return PlotResponse(
            success=False,
            error=f"Failed to generate plot: {str(e)}"
        )

# --- Async Helper Functions ---

async def save_file_async(file: UploadFile, file_location: str):
    """Save uploaded file asynchronously with proper error handling."""
    def save_file():
        try:
            # Ensure uploads directory exists
            os.makedirs(os.path.dirname(file_location), exist_ok=True)
            
            # Reset file pointer to beginning before saving
            file.file.seek(0)
            
            # Save file with proper error handling
            with open(file_location, "wb") as file_object:
                shutil.copyfileobj(file.file, file_object)
            
            # Verify file was saved correctly
            if not os.path.exists(file_location):
                raise FileNotFoundError(f"Failed to save file to {file_location}")
            
            file_size = os.path.getsize(file_location)
            logger.info(f"File saved successfully: {file_location} ({file_size} bytes)")
            
        except Exception as e:
            logger.error(f"Error saving file to {file_location}: {e}")
            # Clean up partial file if it exists
            if os.path.exists(file_location):
                try:
                    os.remove(file_location)
                except:
                    pass
            raise
    
    # Run file I/O in thread pool
    await asyncio.get_event_loop().run_in_executor(None, save_file)

async def process_file_async(conversation, file_location: str, original_filename: str = None):
    """Process file asynchronously."""
    def process_file():
        conversation.process_file(file_location, original_filename)
    
    # Run processing in thread pool
    await asyncio.get_event_loop().run_in_executor(None, process_file)

async def process_query_async(conversation, query: str):
    """Process query asynchronously."""
    def process_query():
        return conversation.get_response(query)
    
    # Run query processing in thread pool
    return await asyncio.get_event_loop().run_in_executor(None, process_query)

# --- Development Server ---
if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host='127.0.0.1',
        port=5001,
        reload=True,
        log_level="info"
    ) 