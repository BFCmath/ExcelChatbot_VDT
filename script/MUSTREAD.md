# MUSTREAD: Key Concepts & Developer Guide

This document provides essential information for any developer working on this Excel Chatbot project. It highlights the core design patterns, the roles of the different LLM agents, and other critical components.

---

## 1. Core Architecture: From Metadata to Data Extraction

The fundamental principle of this system is to **avoid feeding the entire Excel file content directly to the LLM for every query**. Instead, it performs a one-time (and cached) **metadata extraction** process to understand the *structure* of the file. User queries are then used to intelligently navigate this pre-parsed structure.

The process is as follows:
1.  **Structural Analysis**: On first load, the system uses an LLM (`FEATURE_ANALYSIS_PROMPT`) to identify which columns in the Excel file define the row hierarchy (`Feature Rows`) and which define the column hierarchy (`Feature Cols`).
2.  **Hierarchy Conversion**: The identified hierarchical columns are converted into nested dictionaries (`row_dict`, `col_dict`) which represent the full tree structure of the rows and columns.
3.  **LLM-Friendly Formatting**: These dictionaries are formatted into a simplified, indented string format (`row_structure`, `col_structure`) that is easier for the LLM to understand in subsequent prompts.
4.  **Querying**: When a user asks a question, the LLM is given the query and the formatted `row_structure` and `col_structure`. Its task is *not* to find the data, but to identify the *path* to the data within the hierarchies.
5.  **Extraction**: The system translates the path provided by the LLM into concrete pandas DataFrame filters and selectors to retrieve the final data.

---

## 2. The Two Agent Architectures

The system implements two distinct architectures for processing user queries.

### a) The `splitter` (Multi-Agent) Architecture
This is the primary, more advanced architecture. It breaks down the query-to-data process into a sequence of specialized LLM calls (a "chain of thought").

-   **`DECOMPOSER_PROMPT`**: The first agent in the chain.
    -   **Input**: User query + row/col structures.
    -   **Output**: A list of `Row Keywords` and `Col Keywords`.
    -   **Purpose**: To dissect the query and isolate the parts that refer to rows vs. columns.

-   **`ROW_HANDLER_PROMPT`**: The second agent, focused on rows.
    -   **Input**: User query + `Row Keywords` + row structure.
    -   **Output**: A structured `Row Identifier` showing the hierarchical path to the selected rows.
    -   **Purpose**: To translate row-specific keywords into a precise selection path. It uses `"Undefined"` to handle levels in the hierarchy that the user didn't specify.

-   **`COL_HANDLER_PROMPT`**: The third agent, focused on columns.
    -   **Input**: User query + `Col Keywords` + col structure.
    -   **Output**: A structured `Col Identifier` showing the hierarchical path(s) to the selected columns.
    -   **Purpose**: To translate column-specific keywords into a precise selection path.

**Advantage**: This approach is more robust and accurate because each agent has a single, focused task.

### b) The `single_agent` Architecture
This is a simpler, legacy architecture where a single, large prompt is responsible for the entire interpretation task.

-   **`SINGLE_AGENT_PROMPT`**: A monolithic agent.
    -   **Input**: User query + row/col structures (as JSON).
    -   **Output**: A JSON object containing both the `Row Choose` and `Col Choose` selections.
    -   **Purpose**: To perform the job of the decomposer, row handler, and column handler all in one step.

**Disadvantage**: While simpler to orchestrate, it can be less reliable for complex queries as the LLM has to manage multiple complex tasks simultaneously.

---

## 3. Multi-File Strategy: Summarize then Route

The `multifile.py` script employs a sophisticated strategy to handle queries that could involve multiple files.

-   **Caching is Key**: All extracted metadata and file summaries are cached in `script/cache/file_metadata.pkl`. The cache is invalidated if a file's hash changes, preventing unnecessary reprocessing.

-   **The "Fingerprint" (`FILE_SUMMARY_PROMPT`)**: For each file, the system uses an LLM to generate a structured, natural language summary. This summary acts as a "fingerprint", describing the file's purpose, time coverage, and the kinds of questions it can answer.

-   **The Router (`QUERY_SEPARATOR_PROMPT`)**: When the user asks a query in the multi-file mode, this LLM agent is called first.
    -   **Input**: The user's query + the pre-computed summaries (fingerprints) of all available files.
    -   **Output**: The query is broken down into one or more sub-queries, each assigned to the most relevant file.
    -   **Purpose**: To act as an intelligent router, ensuring that sub-queries are directed only to the files that can actually answer them. This avoids wasting time and tokens querying irrelevant files.

---

## 4. Important Files to Check First

-   **`prompt.py`**: **This is the most important file for understanding the system's logic.** The quality and detail of these prompts dictate the performance of the entire application. Any changes to the logic should start with reviewing and potentially modifying these prompts.
-   **`multifile.py`**: Contains the core logic for the advanced multi-file processing, including caching and the query separation strategy.
-   **`llm.py`**: Shows how the prompts are used to build the different agents (`splitter`, `single_agent`, etc.).
-   **`extract_df.py`**: Contains the logic for parsing the LLM's selection output and turning it into actual DataFrame filters. The `parse_*` functions here are critical. 