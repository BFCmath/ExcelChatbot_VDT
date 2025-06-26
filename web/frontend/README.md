# Excel Chatbot Frontend

This directory contains the complete frontend for the Excel Chatbot. It is a modern, responsive Single-Page Application (SPA) built with vanilla JavaScript, HTML, and CSS. It provides a rich, interactive user interface for uploading Excel files, asking complex questions, and visualizing the results through dynamic, hierarchical tables and charts.

The frontend is completely decoupled from the backend, communicating through a well-defined REST API. This separation allows for independent development, deployment, and scaling of the user interface.

## Live Demo

A complete demonstration of the application's features, including the interactive frontend, can be viewed on YouTube:

[![Excel Chatbot Demo](https://img.youtube.com/vi/c8FGzOZ9wro/0.jpg)](https://www.youtube.com/watch?v=c8FGzOZ9wro)

[Watch the full demo on YouTube](https://www.youtube.com/watch?v=c8FGzOZ9wro)

## Core Architecture

The frontend is designed as a modular SPA. A single `index.html` file serves as the application's skeleton, and all UI updates are handled dynamically by JavaScript, which manipulates the DOM without requiring page reloads.

-   **Modular Design**: The JavaScript code is organized into separate files (modules) in the `js/` directory, each with a specific responsibility (e.g., API communication, state management, DOM manipulation). These modules coordinate by attaching their public functions to the global `window` object.
-   **Client-Side Processing**: The application performs significant data processing on the client side. The innovative table flattening and filtering logic is implemented in JavaScript, allowing for instantaneous table interactions without needing to re-fetch data from the backend.
-   **State Management**: A central `config.js` module manages the application's global state, including conversation history and cached table data, which is persisted in the browser's `localStorage`.

---

## File Structure

### Key Files

-   `index.html`: The main and only HTML file. It defines the layout structure and includes all necessary CSS and JavaScript files.
-   `styles.css`: A single, comprehensive stylesheet that provides all the visual styling and responsiveness for the application.
-   `start.py`: A simple Python web server for local development. Its primary role is to serve the static frontend files and add the necessary CORS headers to allow communication with the backend API.

### JavaScript Modules (`js/`)

-   `config.js`: The central configuration and state management hub. Holds the API URL, conversation history, and a cache for table data.
-   `app.js`: The main entry point. It orchestrates the application's startup sequence.
-   `dom.js`: Centralizes all direct DOM manipulations, such as showing/hiding elements, displaying notifications, and managing element caches.
-   `events.js`: Sets up all global event listeners (clicks, key presses, drag-and-drop) and delegates actions to the appropriate modules.
-   `conversation.js`: Manages the lifecycle of conversations, including creation, switching, and persistence to `localStorage`.
-   `api.js`: Handles sending user queries to the backend API and receiving the results.
-   `upload.js` & `alias.js`: Manage the UI and logic for uploading user Excel files and the system-wide alias file.
-   `messages.js`: Responsible for rendering content in the chat window, including the complex HTML for data tables from API responses.
-   `table.js`: Manages the rendering of and interaction with the data tables, including setting up controls for flattening and filtering.
-   `flatten.js`: A client-side replication of the backend's sophisticated header-flattening algorithm. This allows for instant, interactive transformation of hierarchical tables.
-   `plotting.js`: Manages the entire data visualization workflow, from preparing data and sending it to the backend's `/plot/generate` endpoint to rendering the returned charts in an interactive modal.
-   `utils.js`: A collection of reusable helper functions.
-   `flatten_debug.js`: An advanced, in-browser tool for debugging the complex table flattening logic.

---

## How to Run

The frontend is designed to be run with a simple Python HTTP server.

1.  **Navigate to the `web/frontend` directory.**
    ```bash
    cd web/frontend
    ```

2.  **Start the server.**
    ```bash
    python start.py
    ```
    This will serve the application on `http://localhost:8000`.

3.  **Access the application** by opening `http://localhost:8000` in your web browser.

> **Note:** For the application to function, the backend server must also be running, as the frontend will make API calls to it (by default at `http://localhost:5001`).
