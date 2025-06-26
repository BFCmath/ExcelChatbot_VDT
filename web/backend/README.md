# Excel Chatbot Backend

This directory contains the complete backend server for the Excel Chatbot application. It is a robust, security-first API built with FastAPI that empowers users to query complex Excel files using natural language.

The backend is designed to be completely decoupled from the frontend, handling all the heavy lifting of file processing, query understanding, data retrieval, and visualization generation.

## Core Architecture

The backend architecture is designed around a secure, multi-agent pipeline that processes user requests without ever exposing sensitive data to external services. The system first understands the *structure* of an Excel file and then uses that metadata context to interpret and execute a user's query locally.

This unified framework integrates query enrichment, multi-file routing, and a schema-based execution engine into a single, cohesive system.

![Final Unified Architecture](../../image/README_2025-06-26-18-56-07.png)

*The final, unified architecture of the Excel Chatbot framework. It integrates query enrichment, multi-file routing, and the schema-based single-file execution engine into a cohesive, end-to-end system.*

The main components are:
- **FastAPI Application (`app.py`)**: The main web server that defines all API endpoints, handles request validation, and manages the application lifecycle.
- **Session Manager (`managers.py`)**: The `ConversationManager` creates and manages isolated, stateful conversation sessions for each user, ensuring data privacy between concurrent users.
- **Alias Manager (`alias_manager.py`)**: Manages a global, system-wide alias file, allowing the chatbot to understand domain-specific jargon and abbreviations.
- **Core Engine (`core/`)**: The "brain" of the application. This is a self-contained module that performs the complex tasks of schema extraction, LLM-based query decomposition, and deterministic data retrieval. See the [Core Engine README](./core/README.md) for a detailed breakdown.

## Key Features

- **Security-First Design**: The core principle. Sensitive data from Excel files is **never** sent to an external service. The LLM only ever interacts with the file's structural metadata.
- **Dynamic & Template-Free**: The system can intelligently parse and process any complex, hierarchical Excel matrix table without needing pre-defined templates or custom code.
- **Multi-Agent LLM Pipeline**: Utilizes a chain of specialized LLM agents for highly accurate query decomposition, routing, and execution, significantly outperforming a single-prompt approach.
- **Multi-File Context**: A sophisticated routing agent can understand queries that span multiple documents, breaking them down and targeting the correct file(s) for a comprehensive answer.
- **Query Enrichment**: Automatically enriches user queries with definitions from a configurable alias file, allowing the system to understand jargon, acronyms, and synonyms.
- **On-the-Fly Plotting**: Capable of generating interactive `Plotly` charts (Sunburst and Bar) from the results of a query, turning raw data into insights.
- **Asynchronous by Default**: Built on FastAPI and `asyncio` to handle long-running I/O and processing tasks without blocking the server, ensuring a responsive user experience.

## Getting Started

Follow these instructions to set up and run the backend server on your local machine.

### Prerequisites

- Python 3.9+
- `pip` for package management

### 1. Installation

First, clone the repository to your local machine. From the **project root directory** (`xlsx_chatbot/`), install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

The core engine requires Google API keys to interact with the Gemini LLM.

1.  Navigate to the core engine directory: `cd web/backend/core`
2.  Make a copy of the environment variable template file. Rename `.txt.env` to `.env`:
    ```bash
    cp .txt.env .env
    ```
3.  Open the newly created `.env` file and add your Google API keys. You can add one or more keys; the system will automatically load-balance requests across them.

    ```dotenv
    # .env
    GOOGLE_API_KEY_1="YOUR_API_KEY_HERE"
    GOOGLE_API_KEY_2="ANOTHER_API_KEY_HERE"
    # ... and so on
    LLM_MODEL="gemini-2.5-flash-preview-04-17"
    ```

### 3. Running the Server

Once the dependencies are installed and the environment variables are set, navigate back to the `web/backend` directory and run the server using `uvicorn`.

```bash
# Make sure you are in the web/backend directory
cd web/backend

uvicorn app:app --host 127.0.0.1 --port 5001 --reload
```
- `--reload`: Enables hot-reloading, so the server will automatically restart when you make code changes.

The API server should now be running and accessible at `http://127.0.0.1:5001`. You can view the auto-generated API documentation at `http://127.0.0.1:5001/docs`.

## API Overview

The backend exposes a RESTful API for interaction. The main endpoints include:

-   `POST /conversations`: Starts a new, isolated user session.
-   `POST /conversations/{conversation_id}/upload`: Uploads one or more Excel files to a specific session.
-   `POST /conversations/{conversation_id}/query`: Submits a natural language query to a session for processing.
-   `GET /alias/status`: Checks the status of the global alias file.
-   `POST /alias/upload`: Uploads a new system-wide alias file.
-   `POST /plot/generate`: Generates interactive charts from structured JSON data.

For a complete and interactive list of all endpoints and their schemas, please refer to the auto-generated Swagger documentation at the `/docs` endpoint when the server is running.
