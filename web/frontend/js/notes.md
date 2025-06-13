# JavaScript Files Documentation

This document provides a comprehensive overview of all JavaScript files in the Excel Chatbot frontend application, explaining the purpose of each file and all functions within them.

## File Structure Overview

The frontend JavaScript is organized into 12 modular files, each with a specific responsibility:

1. **config.js** - Application configuration and global state
2. **utils.js** - Utility functions used across the application
3. **dom.js** - DOM manipulation and UI management
4. **events.js** - Event listener setup and handling
5. **api.js** - API communication with the backend
6. **messages.js** - Message display and formatting
7. **conversation.js** - Conversation management
8. **upload.js** - File upload functionality
9. **table.js** - Table rendering and display
10. **flatten.js** - Table flattening logic
11. **flatten_debug.js** - Debug system for flattening operations
12. **app.js** - Main application initialization

---

## 1. config.js (1.1KB, 49 lines)

**Purpose**: Defines application configuration constants and manages global state.

### Global Variables:
- `API_BASE_URL`: Backend API endpoint (http://localhost:5001)
- `currentConversationId`: Currently active conversation ID
- `conversations`: Object storing all conversation data
- `uploadStates`: Tracks file upload states to prevent duplicates
- `isSending`: Boolean flag for message sending state
- `elementsCache`: Cache for DOM elements to improve performance
- `globalTableData`: Stores table data for flattening operations

### Functions:
- `setCurrentConversationId(id)`: Sets the active conversation ID and updates global state
- `getCurrentConversationId()`: Returns the current conversation ID
- `setIsSending(state)`: Sets the message sending state
- `getIsSending()`: Returns the current sending state

---

## 2. utils.js (3.3KB, 116 lines)

**Purpose**: Provides utility functions for text processing, HTML escaping, cell formatting, and file operations.

### Functions:

#### `escapeHtml(text)`
- **Purpose**: Safely escapes HTML characters to prevent XSS attacks
- **Parameters**: `text` (string) - Text to escape
- **Returns**: HTML-escaped string

#### `formatCodeBlocks(content)`
- **Purpose**: Converts markdown-style code blocks to HTML
- **Parameters**: `content` (string) - Content with ```code``` blocks
- **Returns**: HTML with `<pre><code>` tags

#### `truncateText(text, maxLength)`
- **Purpose**: Truncates text to specified length with ellipsis
- **Parameters**: `text` (string), `maxLength` (number)
- **Returns**: Truncated text with "..." if needed

#### `formatCellValue(value)`
- **Purpose**: Formats cell values for table display with proper styling
- **Parameters**: `value` (any) - Cell value to format
- **Returns**: HTML-formatted cell content
- **Features**:
  - Handles null/undefined values with em dash
  - Formats numbers with locale-specific formatting
  - Truncates long strings with tooltips
  - Escapes HTML in string values

#### `saveJsonToFile(data, filename)`
- **Purpose**: Downloads JSON data as a file
- **Parameters**: `data` (object), `filename` (string)
- **Returns**: Boolean success status
- **Implementation**: Creates blob URL and triggers download

#### `saveTextToFile(text, filename)`
- **Purpose**: Downloads text content as a file
- **Parameters**: `text` (string), `filename` (string)
- **Returns**: Boolean success status

---

## 3. dom.js (4.1KB, 133 lines)

**Purpose**: Manages DOM elements, UI states, notifications, and user interactions.

### Functions:

#### `initializeElements()`
- **Purpose**: Caches DOM elements for performance optimization
- **Elements Cached**: All major UI elements (buttons, containers, inputs, etc.)

#### `showLoading(message = 'Loading...')`
- **Purpose**: Displays loading overlay with custom message
- **Parameters**: `message` (string, optional) - Loading message

#### `hideLoading()`
- **Purpose**: Hides the loading overlay

#### `showError(message)`
- **Purpose**: Displays error notification
- **Parameters**: `message` (string) - Error message to display

#### `showSuccess(message)`
- **Purpose**: Displays success notification
- **Parameters**: `message` (string) - Success message to display

#### `showNotification(message, type)`
- **Purpose**: Creates and displays notifications with auto-removal
- **Parameters**: `message` (string), `type` (string) - 'error' or 'success'
- **Features**: Auto-removes after 5 seconds

#### `updateInputState()`
- **Purpose**: Updates input field and send button states based on current conditions
- **Logic**:
  - Enables send button only if: has text, not sending, has uploaded files
  - Updates placeholder text based on file upload status
  - Disables input if no files uploaded

#### `scrollToBottom()`
- **Purpose**: Smoothly scrolls messages container to bottom
- **Features**: Hides scroll-to-bottom button after scrolling

#### `handleScroll()`
- **Purpose**: Manages scroll-to-bottom button visibility
- **Logic**: Shows button when user is not at bottom of messages

---

## 4. events.js (3.1KB, 74 lines)

**Purpose**: Sets up event listeners for all user interactions.

### Functions:

#### `setupEventListeners()`
- **Purpose**: Initializes all main event listeners
- **Events Setup**:
  - Navigation events (new conversation, upload file)
  - Input events (typing, enter key, send button)
  - Auto-resize for textarea
  - Scroll events
  - Upload modal events

#### `setupUploadModalEvents()`
- **Purpose**: Sets up upload modal specific event listeners
- **Events Setup**:
  - Modal close events (close button, backdrop click, ESC key)
  - File input change event
  - Choose file button click
  - Drag and drop events
  - Upload area click to trigger file selection

---

## 5. api.js (6.9KB, 187 lines)

**Purpose**: Handles all API communication with the backend server.

### Functions:

#### `sendMessage()`
- **Purpose**: Sends user messages to backend and handles responses
- **Process**:
  1. Validates input and conversation state
  2. Checks for uploaded files
  3. Updates UI state and adds user message
  4. Sends POST request to `/conversations/{id}/query`
  5. Processes response and displays bot reply
  6. Handles errors gracefully
- **Features**:
  - Shows typing indicator during processing
  - Updates conversation title for first message
  - Auto-saves conversations after each message

#### `updateConversationTitleFromMessage(message, conversationId)`
- **Purpose**: Creates meaningful conversation titles from first user message
- **Parameters**: `message` (string), `conversationId` (string)
- **Logic**: Truncates to 30 chars, cleans special characters

#### `handleInputChange()`
- **Purpose**: Handles input field changes
- **Features**:
  - Auto-resizes textarea based on content
  - Updates send button state

#### `handleKeyDown(e)`
- **Purpose**: Handles keyboard shortcuts
- **Features**: Enter key sends message (Shift+Enter for new line)

---

## 6. messages.js (10KB, 258 lines)

**Purpose**: Manages message display, formatting, and conversation UI elements.

### Functions:

#### `addMessageToUI(content, type, animate = true)`
- **Purpose**: Adds messages to the UI with proper formatting and animations
- **Parameters**: `content` (string/object), `type` ('user'/'bot'), `animate` (boolean)
- **Features**:
  - Handles different content types (text, HTML, table data)
  - Sets up table flattening controls for hierarchical tables
  - Auto-scrolls for user messages or when user is at bottom
  - Shows scroll-to-bottom button when needed

#### `addMessageToConversation(content, type)`
- **Purpose**: Saves messages to conversation history
- **Parameters**: `content` (string), `type` ('user'/'bot')

#### `addTypingIndicator()`
- **Purpose**: Shows animated typing indicator during bot processing
- **Returns**: DOM element reference for later removal

#### `removeTypingIndicator(indicator)`
- **Purpose**: Removes typing indicator from UI
- **Parameters**: `indicator` (DOM element)

#### `clearMessages()`
- **Purpose**: Clears all messages from the UI

#### `showWelcomeMessage()`
- **Purpose**: Displays welcome screen with example queries
- **Features**: Shows helpful example questions users can ask

#### `formatResponse(result)`
- **Purpose**: Formats different types of API responses for display
- **Parameters**: `result` (string/object) - API response
- **Returns**: Formatted HTML string
- **Handles**: String responses, structured data, legacy formats, fallback to JSON

#### `formatQueryResults(response)`
- **Purpose**: Formats query results with table data and flattening controls
- **Parameters**: `response` (object) - Structured API response
- **Features**:
  - Creates result sections for each file
  - Stores table data for flattening functionality
  - Adds flattening controls for hierarchical tables
  - Handles both hierarchical and simple tables

---

## 7. conversation.js (13KB, 349 lines)

**Purpose**: Manages conversation lifecycle, persistence, and backend synchronization.

### Functions:

#### `createNewConversation()`
- **Purpose**: Creates a new conversation via backend API
- **Process**:
  1. Shows loading indicator
  2. Sends POST request to `/conversations`
  3. Stores conversation data locally
  4. Switches to new conversation
  5. Shows welcome message

#### `switchToConversation(conversationId)`
- **Purpose**: Switches to an existing conversation
- **Parameters**: `conversationId` (string)
- **Process**:
  1. Validates conversation exists locally
  2. Validates with backend via `/conversations/{id}/validate`
  3. Updates UI and loads conversation messages
  4. Syncs uploaded files
  5. Handles invalid conversations by creating new one

#### `updateConversationsList()`
- **Purpose**: Updates the sidebar conversations list
- **Features**:
  - Sorts conversations by creation date
  - Shows conversation titles and message previews
  - Highlights active conversation
  - Optimizes to avoid unnecessary rebuilds

#### `updateConversationTitle(title)`
- **Purpose**: Updates the current conversation title in UI
- **Parameters**: `title` (string)

#### `loadConversationMessages(conversation)`
- **Purpose**: Loads and displays messages for a conversation
- **Parameters**: `conversation` (object)
- **Features**: Shows welcome message if no messages exist

#### `loadConversations()`
- **Purpose**: Loads conversations from localStorage on app startup
- **Features**: Handles JSON parsing errors gracefully

#### `saveConversations()`
- **Purpose**: Saves conversations to localStorage
- **Features**:
  - Checks data size limit (5MB)
  - Triggers cleanup for large datasets
  - Handles quota exceeded errors

#### `initializeConversationState()`
- **Purpose**: Initializes conversation state on app startup
- **Logic**:
  1. Tries to restore current conversation
  2. Falls back to most recent conversation
  3. Creates new conversation if none exist
  4. Validates conversations with backend

#### `validateConversationsWithBackend()`
- **Purpose**: Validates all local conversations against backend
- **Process**: Loops through conversations, removes invalid ones

#### `cleanupOldConversations()`
- **Purpose**: Keeps only the 5 most recent conversations
- **Features**: Prevents localStorage bloat

#### Background Tasks:
- Auto-saves every 5 seconds
- Saves before page unload

---

## 8. upload.js (13KB, 343 lines)

**Purpose**: Handles Excel file uploads, progress tracking, and file management.

### Functions:

#### `openUploadModal()`
- **Purpose**: Opens the file upload modal
- **Validation**: Checks for active conversation

#### `closeUploadModal()`
- **Purpose**: Closes the upload modal and resets state

#### `resetUploadModal()`
- **Purpose**: Resets modal UI to initial state
- **Actions**: Clears file input, hides progress, removes drag state

#### `handleFileSelect(e)`
- **Purpose**: Handles file selection from input or drag-drop
- **Parameters**: `e` (event) - File selection event

#### `uploadFile(file)`
- **Purpose**: Uploads Excel file to backend with progress tracking
- **Parameters**: `file` (File object)
- **Process**:
  1. Validates file type (.xlsx, .xls) and size (50MB max)
  2. Prevents duplicate uploads
  3. Shows progress with animated bar
  4. Sends FormData to `/upload` endpoint
  5. Updates conversation files list
  6. Updates conversation title if needed
- **Features**:
  - Simulated progress for better UX
  - Handles both new and legacy backend response formats
  - Updates UI state after successful upload

#### `updateProgress(percent)`
- **Purpose**: Updates the upload progress bar
- **Parameters**: `percent` (number) - Progress percentage

#### `updateUploadedFiles()`
- **Purpose**: Updates the uploaded files display
- **Features**:
  - Shows file icons and names
  - Adds remove buttons for each file
  - Updates CSS classes for message container

#### `syncFilesWithBackend()`
- **Purpose**: Synchronizes local file list with backend
- **Process**: Gets files via `/conversations/{id}/files` endpoint
- **Handles**: Both new and legacy backend response formats

#### `removeFile(index)`
- **Purpose**: Removes a file from the uploaded files list
- **Parameters**: `index` (number) - File index to remove
- **Note**: TODO - Add backend API call for server-side removal

#### Drag & Drop Handlers:
- `handleDragOver(e)`: Handles drag over events, adds visual feedback
- `handleDragLeave(e)`: Handles drag leave events, removes visual feedback
- `handleDrop(e)`: Handles file drop events, triggers upload

---

## 9. table.js (7.4KB, 201 lines)

**Purpose**: Renders hierarchical HTML tables and manages table flattening controls.

### Functions:

#### `createHierarchicalHtmlTable(tableInfo, filename)`
- **Purpose**: Creates HTML table with proper hierarchical headers
- **Parameters**: `tableInfo` (object), `filename` (string)
- **Returns**: HTML string for the table
- **Features**:
  - Handles multi-level headers with colspan/rowspan
  - Tracks cell coverage to prevent overlap
  - Applies appropriate CSS classes for styling
  - Limits display to first 100 rows for performance
  - Wraps table for horizontal scrolling

#### `formatTableData(data)`
- **Purpose**: Legacy support for simple array data
- **Parameters**: `data` (array) - Simple data array
- **Returns**: Formatted table HTML
- **Use**: Fallback for non-hierarchical data structures

#### `setupTableToggleEvents(container)`
- **Purpose**: Sets up flattening control event handlers
- **Parameters**: `container` (DOM element) - Container with flatten controls
- **Process**:
  - Finds flatten control buttons and level display
  - Gets original table data from global storage
  - Sets up click handlers for up/down buttons
  - Updates table display and button states
- **Features**:
  - Live table transformation without page refresh
  - Button enable/disable based on flatten level limits
  - Visual feedback for current flatten level

#### `debugHeaders(resultIndex, level)`
- **Purpose**: Debug helper function (delegates to FlattenManager)
- **Parameters**: `resultIndex` (number), `level` (number)

---

## 10. flatten.js (35KB, 891 lines)

**Purpose**: Implements complex table flattening algorithms to transform hierarchical tables.

### Core Functions:

#### `getTableDataFromResult(resultIndex)`
- **Purpose**: Retrieves table data from global storage
- **Parameters**: `resultIndex` (number)
- **Returns**: Table info object or null

#### `storeTableData(resultIndex, tableInfo, filename)`
- **Purpose**: Stores table data in global storage
- **Parameters**: `resultIndex` (number), `tableInfo` (object), `filename` (string)

#### `createFlattenedTableData(originalTableInfo, flattenLevel)`
- **Purpose**: Main flattening function - transforms hierarchical tables
- **Parameters**: `originalTableInfo` (object), `flattenLevel` (number)
- **Returns**: Transformed table info object
- **Logic**:
  - Level 0: No flattening (returns original)
  - Level >= max-1: Complete flattening
  - Other levels: Partial flattening
- **Features**: Comprehensive debug logging support

### Algorithm Implementation Functions:

#### `calculateRowspan(multiindexColumns, level, position, currentValue)`
- **Purpose**: Calculates vertical span for header cells
- **Parameters**: multiindex structure, level, position, value
- **Returns**: Number of rows to span
- **Logic**: Spans to bottom if all lower levels are "Header" placeholders

#### `calculateIntelligentColspan(multiindexColumns, level, startPosition, currentValueStr, coveredPositions)`
- **Purpose**: Calculates horizontal span for header cells
- **Parameters**: multiindex structure, level, position, value, covered positions
- **Returns**: Number of columns to span
- **Logic**: 
  - Finds consecutive identical values
  - Only merges if lower levels vary or are all "Header"
  - Prevents inappropriate merging of separate headers

#### `getLevelValue(multiindexColumns, level, position)`
- **Purpose**: Safe accessor for multiindex column values
- **Parameters**: multiindex array, level, position
- **Returns**: Value at position or null

#### `convertToMultiindexColumns(originalHeaderMatrix, colCount)`
- **Purpose**: Converts header matrix to column-based multiindex format
- **Parameters**: original matrix, column count
- **Returns**: Multiindex columns array
- **Process**:
  1. Initializes levels with null values
  2. Fills values respecting colspan and rowspan
  3. Uses "Header" placeholders for spanned cells
  4. Prioritizes actual header text over placeholders

#### `buildHeaderMatrixForLevel(originalTableInfo, flattenLevel)`
- **Purpose**: Builds header matrix for partial flattening
- **Parameters**: table info, flatten level
- **Returns**: New header matrix structure
- **Process**:
  1. Combines specified number of levels
  2. Applies acronym generation for parent levels
  3. Keeps leaf level text intact
  4. Rebuilds matrix using two-pass algorithm

### Flattening Strategy Functions:

#### `createPartiallyFlattenedTable(originalTableInfo, flattenLevel)`
- **Purpose**: Creates partially flattened table (combines some levels)
- **Parameters**: table info, flatten level
- **Returns**: Partially flattened table structure

#### `createCompletelyFlattenedTable(originalTableInfo, flattenLevel)`
- **Purpose**: Creates completely flattened table (single level headers)
- **Parameters**: table info, flatten level (optional)
- **Returns**: Completely flattened table structure
- **Process**:
  1. Extracts column tuples for each column
  2. Filters out placeholders and duplicates
  3. Applies acronym generation for parent levels
  4. Creates single-level header matrix

### Helper Functions:

#### `findHeaderForColumn(level, columnIndex, levelIndex, headerMatrix)`
- **Purpose**: Finds which header covers a specific column at a specific level
- **Parameters**: level headers, column index, level index, full matrix
- **Returns**: Header object or null
- **Logic**:
  1. Checks for exact match at target level
  2. Falls back to spanning headers from upper levels

#### `createAcronym(text)`
- **Purpose**: Creates acronyms from header text (matches backend logic)
- **Parameters**: `text` (string)
- **Returns**: Acronym string
- **Rules**:
  - Pure numbers: kept as-is
  - Mixed text/numbers: first letter + numbers
  - Pure text: first letter of each word

### Debug Functions:

#### `debugHeaders(resultIndex, level)`
- **Purpose**: Debug helper for analyzing flattening results
- **Parameters**: result index, flatten level
- **Output**: Console logs with detailed analysis

#### `testFlattenLogic()`
- **Purpose**: Test function with mock data to verify flattening logic

#### `testMultiindexConversion(resultIndex)`
- **Purpose**: Tests multiindex conversion specifically

#### `analyzeColumnStructure(resultIndex)`
- **Purpose**: Analyzes expected vs actual column structure

---

## 11. flatten_debug.js (30KB, 765 lines)

**Purpose**: Comprehensive debugging system for flatten operations with detailed logging.

### Main Debug Class:

#### `FlattenDebugLogger`
- **Purpose**: Central logging class for flatten operations
- **Features**:
  - Session-based logging with timestamps
  - Level-specific log separation
  - Automatic file export capabilities
  - Detailed operation tracking

### Core Logging Methods:

#### `log(category, message, data = null)`
- **Purpose**: Basic logging with categorization
- **Parameters**: category string, message, optional data object

#### `logForLevel(flattenLevel, category, message, data = null)`
- **Purpose**: Logs data specific to a flatten level
- **Parameters**: flatten level, category, message, optional data
- **Features**: Automatically saves to level-specific log collections

#### `saveLevelDebugToFile(flattenLevel)`
- **Purpose**: Exports debug data for a specific level to JSON file
- **Parameters**: flatten level number
- **Uses**: Utils.saveJsonToFile for automatic download

### Specialized Logging Functions:

#### `logTableStructure(tableInfo, description, flattenLevel)`
- **Purpose**: Logs complete table structure information
- **Parameters**: table info object, description, level (optional)
- **Captures**: Headers, counts, structure details

#### `logFlattenOperation(originalTable, flattenLevel, result)`
- **Purpose**: Logs complete flatten operation details
- **Parameters**: original table, level, result
- **Captures**: Input/output comparison, operation type

#### `logMultiindexConversion(originalHeaderMatrix, multiindexColumns, colCount, flattenLevel)`
- **Purpose**: Logs multiindex conversion process
- **Parameters**: original matrix, converted columns, count, level
- **Captures**: Before/after structure comparison

#### `logPartialFlattening(flattenLevel, levelsToCombine, originalLevels, combinedNames, newMultiindexColumns)`
- **Purpose**: Logs partial flattening process details
- **Parameters**: level info, combined names, new structure

#### `logColumnCombination(colIndex, parts, meaningfulParts, finalName, flattenLevel)`
- **Purpose**: Logs how individual columns are combined
- **Parameters**: column index, parts, meaningful parts, final name
- **Captures**: Step-by-step combination logic

#### `logAcronymGeneration(originalText, acronym, flattenLevel)`
- **Purpose**: Logs acronym generation process
- **Parameters**: original text, generated acronym, level
- **Includes**: Word-by-word processing details

#### `logCompleteFlattening(originalTable, finalColumns, flattenLevel)`
- **Purpose**: Logs complete flattening results
- **Parameters**: original table, final columns, level

### Debug Helper Functions:

#### `debugFlatten(resultIndex, flattenLevel)`
- **Purpose**: Main debug function for analyzing specific flatten operations
- **Parameters**: result index, flatten level
- **Output**: Comprehensive console analysis

#### `saveAllLevelDebugData(resultIndex)`
- **Purpose**: Generates debug data for all possible flatten levels
- **Parameters**: result index
- **Output**: Multiple JSON files with level-specific debug data

#### `testCompleteFlattening(tableData)`
- **Purpose**: Tests complete flattening with detailed logging

#### `testPartialFlattening(tableData, flattenLevel)`
- **Purpose**: Tests partial flattening with detailed logging

### Export Functions:

#### `exportLogs()`
- **Purpose**: Exports all session logs
- **Returns**: Complete debug export object

#### `exportAllLevelLogs()`
- **Purpose**: Exports all level-specific logs as separate files
- **Returns**: Number of files exported

#### `clearLogs()`
- **Purpose**: Clears all logs and resets session

---

## 12. app.js (2.4KB, 84 lines)

**Purpose**: Main application entry point and initialization controller.

### Functions:

#### `initializeApp()`
- **Purpose**: Main application initialization sequence
- **Process**:
  1. Cache DOM elements
  2. Setup event listeners
  3. Load conversations from localStorage
  4. Initialize conversation state
- **Features**: Comprehensive initialization logging

#### DOM Ready Handler:
- **Purpose**: Ensures all modules are loaded before initialization
- **Validation**: Checks for all required modules
- **Required Modules**: AppConfig, Utils, DOMManager, FlattenManager, TableManager, MessageManager, UploadManager, ConversationManager, APIManager, EventManager
- **Error Handling**: Shows alert if modules are missing

#### Global Error Handlers:
- **`window.addEventListener('error')`**: Catches unhandled JavaScript errors
- **`window.addEventListener('unhandledrejection')`**: Catches unhandled promise rejections
- **Features**: User-friendly error messages, prevents default browser behavior

---

## Module Dependencies

### Dependency Flow:
1. **config.js** → Provides global state and configuration
2. **utils.js** → Provides utility functions for all modules
3. **dom.js** → Manages UI elements and states
4. **events.js** → Sets up user interaction handlers
5. **api.js** → Handles backend communication
6. **messages.js** → Manages message display (uses Utils, TableManager)
7. **conversation.js** → Manages conversation lifecycle (uses API, Messages, Upload)
8. **upload.js** → Handles file operations (uses API, DOM)
9. **table.js** → Renders tables (uses Utils, FlattenManager)
10. **flatten.js** → Core flattening logic (can use FlattenDebugLogger)
11. **flatten_debug.js** → Debug system (uses Utils)
12. **app.js** → Coordinates all modules

### Global Objects Exposed:
- `window.AppConfig` - Configuration and state
- `window.Utils` - Utility functions
- `window.DOMManager` - DOM manipulation
- `window.EventManager` - Event handling
- `window.APIManager` - API communication
- `window.MessageManager` - Message handling
- `window.ConversationManager` - Conversation management
- `window.UploadManager` - File upload
- `window.TableManager` - Table rendering
- `window.FlattenManager` - Table flattening
- `window.FlattenDebugLogger` - Debug logging
- `window.App` - Main application

## Key Features

### Table Flattening System:
- **Hierarchical Headers**: Supports multi-level Excel headers with colspan/rowspan
- **Progressive Flattening**: Level 0 (hierarchical) to Level N (completely flat)
- **Intelligent Algorithms**: Proper cell spanning calculation and acronym generation
- **Live UI Controls**: Users can toggle between flatten levels without page refresh
- **Debug System**: Comprehensive logging and file export for troubleshooting

### Conversation Management:
- **Persistent Storage**: LocalStorage with auto-save and cleanup
- **Backend Sync**: Validates conversations and files with backend
- **Multi-file Support**: Each conversation can have multiple Excel files
- **Smart Titles**: Auto-generates meaningful conversation titles

### File Upload System:
- **Drag & Drop Support**: Modern file upload interface
- **Progress Tracking**: Visual progress bars with simulated progress
- **Validation**: File type and size validation
- **Error Handling**: Comprehensive error messages and recovery

### Error Handling:
- **Global Error Catching**: Unhandled errors are caught and displayed nicely
- **Network Error Recovery**: API failures are handled gracefully
- **User-Friendly Messages**: Technical errors are translated to user-friendly language
- **Debug Support**: Comprehensive logging for development and troubleshooting

This modular architecture ensures maintainability, testability, and clear separation of concerns while providing a rich user experience for Excel data analysis. 