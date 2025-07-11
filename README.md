# Excel Chatbot

> This is my final project of 1st phase at Viettel Digital Talent Program

This repository contains the full source code for an advanced Excel Chatbot application. It is a powerful tool designed to bridge the gap between complex spreadsheet data and human intuition by allowing users to ask questions in natural language and receive precise, tabular, and visual answers.

The system is built with a security-first architecture, ensuring that sensitive data within the Excel files never leaves the user's local environment. All interactions with external Large Language Models (LLMs) are handled using only the file's structural metadata.

## Live Demo

A complete demonstration of the application's features, from file upload to interactive charting, can be viewed on YouTube:

[![Excel Chatbot Demo](https://img.youtube.com/vi/c8FGzOZ9wro/0.jpg)](https://www.youtube.com/watch?v=c8FGzOZ9wro)

[Watch the full demo on YouTube](https://www.youtube.com/watch?v=c8FGzOZ9wro)

## Key Features

-   **Natural Language Querying**: Ask questions like *"What were the sales for Q1?"* or *"Turnover of BU05 and BU06 in January and February"* and get back filtered, aggregated data tables.
-   **Security-First Architecture**: Sensitive data within Excel files is never sent to an external API. The core engine uses metadata-only processing with LLMs.
-   **Interactive Hierarchical Tables**: For Excel files with multi-level headers, the application displays an interactive hierarchical table that can be dynamically flattened or expanded on the client-side.
-   **Dynamic Chart Generation**: Instantly generate insightful charts (Sunburst, Bar) from your query results to visualize data relationships.
-   **Client-Side Performance**: The frontend is a highly performant Single-Page Application (SPA) that handles complex table manipulations (flattening, filtering, sorting) instantly in the browser.
-   **Query Enrichment**: The system uses a global "alias file" to map business-specific acronyms or terms to the corresponding data headers, improving the LLM's understanding of user queries.
-   **Multi-File Context**: The chatbot can understand queries that span multiple uploaded Excel files, routing the question to the most relevant file.

## Core Architecture

![Final Unified Architecture](image/README_2025-06-26-18-56-07.png)

### Further Reading

-   **[Backend Documentation](./web/backend/README.md)**: For a detailed breakdown of the FastAPI server, API endpoints, and core processing logic.
-   **[Frontend Documentation](./web/frontend/README.md)**: For a detailed explanation of the Single-Page Application (SPA) architecture and JavaScript modules.
-   **[Project Report & Slides](./demo/)**: For a comprehensive academic and technical overview of the project's goals, design, and innovations, please see the [`reports.pdf`](./demo/reports.pdf) and [`slides.pdf`](./demo/slides.pdf) files in the `/demo` directory.

## Technology Stack

-   **Backend**:
    -   **Framework**: FastAPI
    -   **LLM Integration**: LangChain, Google Gemini Pro
    -   **Data Manipulation**: Pandas
    -   **Charting**: Plotly
    -   **Server**: Uvicorn
-   **Frontend**:
    -   **Core**: Vanilla JavaScript (ES6 Modules)
    -   **Structure**: HTML5, CSS3
    -   **Architecture**: Single-Page Application (SPA)

## Setup and Installation

Follow these steps to run the entire application locally.

### Prerequisites

-   Python 3.9 or higher
-   pip package manager

### 1. Clone the Repository

```bash
git clone <repository-url>
cd xlsx_chatbot
```

### 2. Install Backend Dependencies

All required Python packages are listed in the `requirements.txt` file at the root of the project.

```bash
pip install -r requirements.txt
```

### 3. Configure the Backend

The backend requires API keys for the Google Gemini LLM.

-   Navigate to the `web/backend/core` directory.
-   Create a file named `.env` by copying the template from `.txt.env`.
-   Add your Google API keys to the `.env` file.

### 4. Run the Application

You need to run two separate processes in two separate terminals: the backend server and the frontend server.

**Terminal 1: Start the Backend**

```bash
# Navigate to the backend directory
cd web/backend

# Start the FastAPI server
uvicorn app:app --host 127.0.0.1 --port 5001 --reload
```
The backend API will now be running at `http://localhost:5001`.

**Terminal 2: Start the Frontend**

```bash
# Navigate to the frontend directory from the project root
cd web/frontend

# Start the simple Python web server
python start.py
```
The frontend application will now be running at `http://localhost:8000`.

### 5. Access the Chatbot

Open your web browser and navigate to **`http://localhost:8000`**. You can now upload an Excel file and start asking questions!
