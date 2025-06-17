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
    completely_flattened_data: dict = Field(..., description="Completely flattened JSON data for bar charts")
    normal_data: dict = Field(..., description="Normal hierarchical JSON data for sunburst charts")

class PlotResponse(BaseModel):
    success: bool
    plot_types: Optional[List[str]] = None  # Updated to support multiple plot types
    data_points_bar: Optional[int] = None
    data_points_sunburst: Optional[int] = None
    plots: Optional[dict] = None  # Contains bar_chart, column_first, row_first
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
    Generate plots from dual JSON inputs.
    
    This endpoint receives two JSON inputs from the frontend:
    1. completely_flattened_data: For bar chart generation (simple structure)
    2. normal_data: For sunburst chart generation (hierarchical structure)
    
    The system automatically:
    - Validates both inputs for appropriate chart types
    - Generates bar chart if flattened data is valid and simple
    - Always generates sunburst chart from normal data
    - Applies filtering to remove total/summary columns
    
    Returns:
    - Bar chart: For simple flat data visualization
    - Column-first sunburst: Time/Period hierarchy first, then categories
    - Row-first sunburst: Categories first, then time/period hierarchy
    """
    try:
        logger.info(f"📊 [PLOT] New dual-input plotting request received")
        
        # Validate both input data structures
        if not isinstance(request.completely_flattened_data, dict):
            logger.error(f"❌ [PLOT] Invalid completely_flattened_data type: {type(request.completely_flattened_data)}")
            raise HTTPException(status_code=400, detail="completely_flattened_data must be a dictionary")
            
        if not isinstance(request.normal_data, dict):
            logger.error(f"❌ [PLOT] Invalid normal_data type: {type(request.normal_data)}")
            raise HTTPException(status_code=400, detail="normal_data must be a dictionary")
        
        # Log comprehensive request details for both inputs
        flattened_data = request.completely_flattened_data
        normal_data = request.normal_data
        
        logger.info(f"📊 [PLOT] Dual input data structure analysis:")
        logger.info(f"📊 [FLATTENED] Completely flattened data:")
        logger.info(f"  📋 keys: {list(flattened_data.keys())}")
        logger.info(f"  📋 filename: {flattened_data.get('filename', 'MISSING')}")
        logger.info(f"  📋 has_multiindex: {flattened_data.get('has_multiindex', 'MISSING')}")
        logger.info(f"  📋 final_columns count: {len(flattened_data.get('final_columns', []))}")
        logger.info(f"  📋 data_rows count: {len(flattened_data.get('data_rows', []))}")
        logger.info(f"  📋 feature_rows: {flattened_data.get('feature_rows', 'MISSING')}")
        
        logger.info(f"🌅 [NORMAL] Normal hierarchical data:")
        logger.info(f"  📋 keys: {list(normal_data.keys())}")
        logger.info(f"  📋 filename: {normal_data.get('filename', 'MISSING')}")
        logger.info(f"  📋 has_multiindex: {normal_data.get('has_multiindex', 'MISSING')}")
        logger.info(f"  📋 final_columns count: {len(normal_data.get('final_columns', []))}")
        logger.info(f"  📋 data_rows count: {len(normal_data.get('data_rows', []))}")
        logger.info(f"  📋 header_matrix levels: {len(normal_data.get('header_matrix', []))}")
        
        # Validate flattened data for bar chart suitability
        logger.info(f"🔍 [VALIDATION] Checking flattened data for bar chart suitability...")
        flattened_valid = True
        flattened_error = None
        
        try:
            # Check required fields for bar chart
            required_fields = ['final_columns', 'data_rows', 'feature_rows']
            missing_fields = [field for field in required_fields if field not in flattened_data]
            if missing_fields:
                flattened_error = f"Missing required fields: {missing_fields}"
                flattened_valid = False
            elif flattened_data.get('has_multiindex', False):
                flattened_error = "Flattened data should not have multiindex structure"
                flattened_valid = False
            elif len(flattened_data.get('feature_rows', [])) != 1:
                flattened_error = f"Bar charts require exactly 1 categorical column, got {len(flattened_data.get('feature_rows', []))}"
                flattened_valid = False
        except Exception as e:
            flattened_error = f"Error validating flattened data: {str(e)}"
            flattened_valid = False
            
        logger.info(f"📊 [FLATTENED] Validation result: {'✅ VALID' if flattened_valid else '❌ INVALID'}")
        if flattened_error:
            logger.info(f"📊 [FLATTENED] Error: {flattened_error}")
            
        # Validate normal data for sunburst chart
        logger.info(f"🔍 [VALIDATION] Checking normal data for sunburst chart...")
        normal_valid = True
        normal_error = None
        
        try:
            # Check required fields for sunburst chart
            required_fields = ['final_columns', 'data_rows', 'feature_rows', 'feature_cols']
            missing_fields = [field for field in required_fields if field not in normal_data]
            if missing_fields:
                normal_error = f"Missing required fields: {missing_fields}"
                normal_valid = False
        except Exception as e:
            normal_error = f"Error validating normal data: {str(e)}"
            normal_valid = False
            
        logger.info(f"🌅 [NORMAL] Validation result: {'✅ VALID' if normal_valid else '❌ INVALID'}")
        if normal_error:
            logger.info(f"🌅 [NORMAL] Error: {normal_error}")
            
        # Ensure at least one input is valid
        if not flattened_valid and not normal_valid:
            logger.error(f"❌ [PLOT] Both inputs are invalid")
            raise HTTPException(
                status_code=400, 
                detail=f"Both inputs are invalid. Flattened: {flattened_error}. Normal: {normal_error}"
            )
        
        # CRITICAL: Sanitize data to remove numpy types before processing
        logger.info(f"🧹 [PLOT] Sanitizing both inputs to remove numpy types...")
        sanitized_flattened = sanitize_numpy_types(flattened_data) if flattened_valid else None
        sanitized_normal = sanitize_numpy_types(normal_data) if normal_valid else None
        logger.info(f"✅ [PLOT] Data sanitization completed")
        
        # Initialize plot generator
        plot_generator = PlotGenerator()
        
        # Generate plots based on valid inputs
        plots_generated = {}
        plot_types = []
        analysis_results = {}
        total_data_points = 0
        bar_data_points = None
        sunburst_data_points = None
        messages = []
        
        # Generate bar chart if flattened data is valid
        if flattened_valid and sanitized_flattened:
            logger.info(f"📊 [BAR] Generating bar chart from flattened data...")
            bar_result = plot_generator.generate_bar_plots(sanitized_flattened)
            
            if bar_result.get('success'):
                logger.info(f"✅ [BAR] Bar chart generated successfully")
                plot_types.append('bar')
                bar_data_points = bar_result.get('data_points')
                if bar_result.get('plots'):
                    plots_generated.update(bar_result['plots'])
                if bar_result.get('analysis'):
                    analysis_results['bar'] = bar_result['analysis']
                messages.append(f"Bar chart: {bar_result.get('message', 'Generated successfully')}")
            else:
                logger.warning(f"⚠️ [BAR] Bar chart generation failed: {bar_result.get('error')}")
                messages.append(f"Bar chart failed: {bar_result.get('error')}")
        
        # Generate sunburst chart if normal data is valid
        if normal_valid and sanitized_normal:
            logger.info(f"🌅 [SUNBURST] Generating sunburst chart from normal data...")
            sunburst_result = plot_generator.generate_sunburst_plots(sanitized_normal)
            
            if sunburst_result.get('success'):
                logger.info(f"✅ [SUNBURST] Sunburst chart generated successfully")
                plot_types.append('sunburst')
                sunburst_data_points = sunburst_result.get('data_points')
                if sunburst_result.get('plots'):
                    plots_generated.update(sunburst_result['plots'])
                if sunburst_result.get('analysis'):
                    analysis_results['sunburst'] = sunburst_result['analysis']
                messages.append(f"Sunburst chart: {sunburst_result.get('message', 'Generated successfully')}")
            else:
                logger.warning(f"⚠️ [SUNBURST] Sunburst chart generation failed: {sunburst_result.get('error')}")
                messages.append(f"Sunburst chart failed: {sunburst_result.get('error')}")
        
        # Determine overall success
        success = len(plot_types) > 0
        final_message = "; ".join(messages) if messages else "No plots generated"
        
        logger.info(f"📊 [PLOT] Dual plotting completed:")
        logger.info(f"  ✅ Success: {success}")
        logger.info(f"  📊 Plot types: {plot_types}")
        logger.info(f"  📊 Bar data points: {bar_data_points}")
        logger.info(f"  📊 Sunburst data points: {sunburst_data_points}")
        logger.info(f"  📈 Total plots: {len(plots_generated)}")
        
        # Convert to response format
        response = PlotResponse(
            success=success,
            plot_types=plot_types if plot_types else None,
            data_points_bar=bar_data_points,
            data_points_sunburst=sunburst_data_points,
            plots=plots_generated if plots_generated else None,
            analysis=analysis_results if analysis_results else None,
            message=final_message,
            error=None if success else "Failed to generate any plots"
        )
        
        logger.info(f"📤 [PLOT] Sending dual-input response: success={response.success}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ [PLOT] Unexpected error generating plot: {e}", exc_info=True)
        return PlotResponse(
            success=False,
            error=f"Failed to generate plot: {str(e)}"
        )

def sanitize_numpy_types(data):
    """
    Recursively sanitize data to convert numpy types to native Python types.
    This prevents JSON serialization errors with numpy.int64, numpy.float64, etc.
    """
    import numpy as np
    
    if isinstance(data, dict):
        return {key: sanitize_numpy_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_numpy_types(item) for item in data]
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data

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