"""
Plotting module for Excel Chatbot
Handles plot generation based on user prompts and table data
"""

import json
import base64
import io
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tempfile
import os

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import GOOGLE_API_KEY, LLM_MODEL

# Configure matplotlib backend
matplotlib.use('Agg')

# Setup logging
logger = logging.getLogger(__name__)


class PlotGenerator:
    def __init__(self):
        """Initialize the PlotGenerator with basic plotting capabilities"""
        self.logger = logging.getLogger(__name__)
        self.supported_plot_types = ['sunburst', 'bar', 'line', 'scatter', 'pie']
    
    def _analyze_header_matrix_structure(self, header_matrix: List[List[Dict[str, Any]]], final_columns: List[str], data_rows: List[List]) -> Dict:
        """
        Analyze the header_matrix to understand the true hierarchical structure.
        """
        # Build position to header mapping for each level
        level_structures = {}
        for level_idx, level in enumerate(header_matrix):
            level_structures[level_idx] = {}
            for header in level:
                for pos in range(header['position'], header['position'] + header['colspan']):
                    level_structures[level_idx][pos] = header['text']
        
        # Determine the actual data structure
        data_length = len(data_rows[0]) if data_rows else 0
        columns_length = len(final_columns)
        
        # Find categorical vs numeric columns based on data analysis
        categorical_positions = []
        numeric_positions = []
        
        if data_rows:
            first_row = data_rows[0]
            for i, value in enumerate(first_row):
                try:
                    float(value)
                    numeric_positions.append(i)
                except (ValueError, TypeError):
                    categorical_positions.append(i)
        
        # Map data positions to header_matrix positions
        data_to_header_position = {}
        for i in range(data_length):
            data_to_header_position[i] = i
        
        return {
            "level_structures": level_structures,
            "categorical_positions": categorical_positions,
            "numeric_positions": numeric_positions,
            "data_to_header_position": data_to_header_position,
            "data_length": data_length,
            "columns_length": columns_length
        }

    def _build_column_hierarchy_paths(self, header_matrix: List[List[Dict[str, Any]]], position: int) -> List[str]:
        """
        Build the complete hierarchy path for a specific column position.
        """
        hierarchy_path = []
        
        # Go through each level and find the header that covers this position
        for level_idx, level in enumerate(header_matrix):
            for header in level:
                if header['position'] <= position < header['position'] + header['colspan']:
                    hierarchy_path.append(header['text'])
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_path = []
        for item in hierarchy_path:
            if item not in seen:
                seen.add(item)
                unique_path.append(item)
        
        return unique_path

    def _detect_plot_type(self, user_prompt: str) -> str:
        """
        Auto-detect plot type from user prompt.
        """
        prompt_lower = user_prompt.lower()
        
        if any(word in prompt_lower for word in ['sunburst', 'hierarchy', 'hierarchical', 'tree', 'nested']):
            return 'sunburst'
        elif any(word in prompt_lower for word in ['bar', 'column', 'histogram']):
            return 'bar'
        elif any(word in prompt_lower for word in ['line', 'trend', 'time series', 'over time']):
            return 'line'
        elif any(word in prompt_lower for word in ['scatter', 'correlation', 'relationship']):
            return 'scatter'
        elif any(word in prompt_lower for word in ['pie', 'donut', 'proportion', 'percentage']):
            return 'pie'
        else:
            return 'sunburst'  # Default to sunburst for hierarchical data

    def _determine_priority(self, user_prompt: str) -> str:
        """
        Determine hierarchy priority from user prompt.
        """
        prompt_lower = user_prompt.lower()
        
        if any(word in prompt_lower for word in ['column first', 'time first', 'date first', 'period first']):
            return 'column'
        elif any(word in prompt_lower for word in ['row first', 'category first', 'group first']):
            return 'row'
        else:
            return 'column'  # Default to column-first

    def create_sunburst_plot(self, frontend_data: Dict, user_prompt: str = "") -> Dict:
        """
        Create sunburst plot from frontend JSON data with proper hierarchical structure.
        """
        try:
            # Extract data from frontend format
            final_columns = frontend_data.get('final_columns', [])
            data_rows = frontend_data.get('data_rows', [])
            header_matrix = frontend_data.get('header_matrix', [])
            has_multiindex = frontend_data.get('has_multiindex', False)
            filename = frontend_data.get('filename', 'table')
            
            if not final_columns or not data_rows:
                return {
                    'success': False,
                    'error': 'No data found in JSON. Required: final_columns and data_rows'
                }

            # Analyze the header_matrix structure properly
            structure_info = self._analyze_header_matrix_structure(header_matrix, final_columns, data_rows)
            
            # Get categorical and numeric column information
            categorical_positions = structure_info["categorical_positions"]
            numeric_positions = structure_info["numeric_positions"]
            data_to_header_position = structure_info["data_to_header_position"]
            level_structures = structure_info["level_structures"]
            
            # Get categorical column names from the header_matrix
            categorical_names = []
            for cat_pos in categorical_positions:
                header_pos = data_to_header_position[cat_pos]
                # Get the name from level 0 of header_matrix
                if 0 in level_structures and header_pos in level_structures[0]:
                    categorical_names.append(level_structures[0][header_pos])
                else:
                    categorical_names.append(f"Category_{cat_pos}")
            
            # Prepare data for plotting
            plot_data = []
            
            for row_idx, data_row in enumerate(data_rows):
                # Extract categorical values
                row_categories = {}
                for i, cat_pos in enumerate(categorical_positions):
                    if cat_pos < len(data_row) and i < len(categorical_names):
                        row_categories[categorical_names[i]] = str(data_row[cat_pos])
                
                # Process each numeric column
                for num_pos in numeric_positions:
                    if num_pos >= len(data_row):
                        continue
                    
                    # Get the header position for this data position
                    header_pos = data_to_header_position[num_pos]
                    
                    # Build the complete hierarchy path for this column
                    hierarchy_path = self._build_column_hierarchy_paths(header_matrix, header_pos)
                    
                    record = {}
                    
                    # Add categorical data
                    for cat_name, cat_value in row_categories.items():
                        record[cat_name] = cat_value
                    
                    # Add column hierarchy levels
                    for level_idx, level_name in enumerate(hierarchy_path):
                        record[f'Col_Level_{level_idx}'] = level_name
                    
                    # Add data value
                    try:
                        actual_value = pd.to_numeric(data_row[num_pos], errors='coerce')
                        record['value'] = actual_value if pd.notna(actual_value) else 0
                    except (ValueError, TypeError, IndexError):
                        record['value'] = 0
                    
                    plot_data.append(record)
            
            if not plot_data:
                return {
                    'success': False,
                    'error': 'No data to plot after processing'
                }
                
            df = pd.DataFrame(plot_data)
            
            # Build plot path based on priority
            col_level_cols = [col for col in df.columns if col.startswith('Col_Level_')]
            col_level_cols.sort()  # Ensure proper order
            
            priority = self._determine_priority(user_prompt)
            if priority == 'column':
                plot_path = col_level_cols + categorical_names
            else:  # priority == 'row'
                plot_path = categorical_names + col_level_cols
                
            # Remove any columns from plot_path that don't exist in the DataFrame
            valid_plot_path = [col for col in plot_path if col in df.columns]
            plot_path = valid_plot_path

            # Handle None values in the path columns
            for col in plot_path:
                if col in df.columns:
                    df[col] = df[col].fillna('Unknown')
            
            # Create the sunburst plot
            title = f"Sunburst Chart: {filename} ({priority.capitalize()}-first Hierarchy)"
            
            fig = px.sunburst(
                df,
                path=plot_path,
                values='value',
                title=title,
                hover_data={'value': True}
            )

            # Enhanced sunburst configuration
            fig.update_layout(
                margin=dict(t=80, l=25, r=25, b=25), 
                font=dict(size=11),
                title_font_size=14,
                showlegend=False
            )
            
            fig.update_traces(
                insidetextorientation='radial',
                textinfo="label+percent parent",
                maxdepth=6,
                branchvalues="total"
            )
            
            fig.update_traces(
                hovertemplate='<b>%{label}</b><br>' +
                             'Value: %{value}<br>' +
                             'Percentage of parent: %{percentParent}<br>' +
                             'Path: %{currentPath}<br>' +
                             '<extra></extra>'
            )
            
            # Convert to HTML
            html_content = fig.to_html()
            
            return {
                'success': True,
                'plot_type': 'sunburst',
                'title': title,
                'html_content': html_content,
                'data_points': len(df),
                'hierarchy': plot_path,
                'priority': priority,
                'analysis': {
                    'categorical_columns': categorical_names,
                    'hierarchy_levels': len(col_level_cols),
                    'total_value': df['value'].sum(),
                    'unique_categories': {col: df[col].nunique() for col in categorical_names if col in df.columns}
                },
                'message': f'Successfully created {priority}-first sunburst chart with {len(df)} data points'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating sunburst plot: {str(e)}',
                'plot_type': 'sunburst'
            }

    def generate_plot(self, frontend_data: Dict, user_prompt: str = "") -> Dict:
        """
        Main plotting function that routes to appropriate plot type.
        """
        plot_type = self._detect_plot_type(user_prompt)
        
        if plot_type == 'sunburst':
            return self.create_sunburst_plot(frontend_data, user_prompt)
        else:
            # For other plot types, return a placeholder for now
            return {
                'success': False,
                'error': f'Plot type "{plot_type}" not yet implemented. Currently only sunburst is supported.',
                'plot_type': plot_type,
                'message': 'Please use sunburst chart or request implementation of other chart types.'
            }

#     """Handles plot generation using LLM and plotting tools"""
    
#     def __init__(self):
#         """Initialize with LLM and plotting tools"""
#         self.llm = ChatGoogleGenerativeAI(
#             model=LLM_MODEL,
#             google_api_key=GOOGLE_API_KEY,
#             temperature=0.1
#         )
        
#         # Available plotting tools
#         self.tools = [
#             create_bar_chart,
#             create_sunburst_chart,
#             create_line_chart,
#             create_scatter_plot,
#             create_histogram,
#             create_pie_chart
#         ]
        
#         # LLM with tools
#         self.llm_with_tools = self.llm.bind_tools(self.tools)
        
#     async def generate_plot(self, table_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
#         """
#         Generate plot based on table data and user prompt
        
#         Args:
#             table_data: JSON table data from frontend download
#             user_prompt: User's plotting request
            
#         Returns:
#             Dict containing plot data and metadata
#         """
#         try:
#             # Convert table data to DataFrame
#             df = self._convert_to_dataframe(table_data)
            
#             # Create plotting prompt
#             prompt = self._create_plotting_prompt(table_data, user_prompt, df)
            
#             # Get LLM response with tool calls
#             response = await self.llm_with_tools.ainvoke(prompt)
            
#             # Execute tool calls
#             plot_result = await self._execute_tool_calls(response, df, table_data)
            
#             return plot_result
            
#         except Exception as e:
#             logger.error(f"Error generating plot: {e}", exc_info=True)
#             raise Exception(f"Failed to generate plot: {str(e)}")
    
#     def _convert_to_dataframe(self, table_data: Dict[str, Any]) -> pd.DataFrame:
#         """Convert JSON table data to pandas DataFrame"""
#         try:
#             columns = table_data.get('columns', [])
#             data_rows = table_data.get('data', [])
            
#             if not columns or not data_rows:
#                 raise ValueError("Table data is missing columns or data rows")
            
#             # Create DataFrame
#             df = pd.DataFrame(data_rows, columns=columns)
            
#             # Convert numeric columns
#             for col in df.columns:
#                 df[col] = pd.to_numeric(df[col], errors='ignore')
            
#             logger.info(f"Created DataFrame: {df.shape} with columns: {list(df.columns)}")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error converting to DataFrame: {e}")
#             raise ValueError(f"Failed to convert table data to DataFrame: {str(e)}")
    
#     def _create_plotting_prompt(self, table_data: Dict[str, Any], user_prompt: str, df: pd.DataFrame) -> str:
#         """Create structured prompt for LLM plot generation"""
        
#         # Analyze data structure
#         data_info = {
#             "shape": df.shape,
#             "columns": list(df.columns),
#             "dtypes": df.dtypes.to_dict(),
#             "has_hierarchical": table_data.get('has_multiindex', False),
#             "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
#         }
        
#         prompt = f"""
# You are a data visualization expert. Analyze the user's request and the provided table data to determine the best plotting approach.

# USER REQUEST: {user_prompt}

# TABLE DATA ANALYSIS:
# - Shape: {data_info['shape']} (rows × columns)
# - Columns: {', '.join(data_info['columns'])}
# - Data types: {data_info['dtypes']}
# - Has hierarchical structure: {data_info['has_hierarchical']}
# - Sample data: {json.dumps(data_info['sample_data'], indent=2)}

# FLATTENING INFO:
# - Flattening applied: {table_data.get('flattening_applied', False)}
# - Filters applied: {table_data.get('filters_applied', {})}

# AVAILABLE PLOTTING TOOLS:
# 1. create_bar_chart - For categorical data comparisons
# 2. create_sunburst_chart - For hierarchical data visualization (excellent for nested categories)
# 3. create_line_chart - For time series or continuous data trends
# 4. create_scatter_plot - For relationship between two numeric variables
# 5. create_histogram - For distribution of numeric data
# 6. create_pie_chart - For proportional data

# INSTRUCTIONS:
# 1. Analyze the user's request to understand what type of visualization they want
# 2. Consider the data structure and types to determine the most appropriate chart
# 3. For hierarchical data, consider using sunburst charts
# 4. Choose appropriate columns for x-axis, y-axis, and grouping
# 5. Call the appropriate tool with the correct parameters

# Choose the best tool and provide the parameters needed.
# """
#         return prompt
    
#     async def _execute_tool_calls(self, response, df: pd.DataFrame, table_data: Dict[str, Any]) -> Dict[str, Any]:
#         """Execute LLM tool calls to generate plots"""
#         try:
#             if not hasattr(response, 'tool_calls') or not response.tool_calls:
#                 # No tool calls, return error
#                 return {
#                     "success": False,
#                     "error": "No plotting tool was selected. Please provide a more specific plotting request.",
#                     "message": response.content if hasattr(response, 'content') else "No response content"
#                 }
            
#             # Execute the first tool call
#             tool_call = response.tool_calls[0]
#             tool_name = tool_call['name']
#             tool_args = tool_call['args']
            
#             logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
#             # Add DataFrame to args
#             tool_args['df'] = df
#             tool_args['table_data'] = table_data
            
#             # Find and execute the tool
#             for tool in self.tools:
#                 if tool.name == tool_name:
#                     plot_result = tool.func(**tool_args)
#                     return plot_result
            
#             raise ValueError(f"Tool {tool_name} not found")
            
#         except Exception as e:
#             logger.error(f"Error executing tool calls: {e}", exc_info=True)
#             return {
#                 "success": False,
#                 "error": f"Failed to execute plotting tool: {str(e)}"
#             }

# # Plotting tool functions

# @tool
# def create_bar_chart(df: pd.DataFrame, x_column: str, y_column: str, 
#                     title: str = "Bar Chart", table_data: Dict = None) -> Dict[str, Any]:
#     """
#     Create a bar chart from the data
    
#     Args:
#         df: DataFrame with the data
#         x_column: Column name for x-axis (categories)
#         y_column: Column name for y-axis (values)
#         title: Chart title
#         table_data: Original table data for context
#     """
#     try:
#         # Validate columns
#         if x_column not in df.columns:
#             raise ValueError(f"Column '{x_column}' not found in data")
#         if y_column not in df.columns:
#             raise ValueError(f"Column '{y_column}' not found in data")
        
#         # Create plotly bar chart
#         fig = px.bar(
#             df, 
#             x=x_column, 
#             y=y_column,
#             title=title,
#             labels={x_column: x_column, y_column: y_column}
#         )
        
#         fig.update_layout(
#             font=dict(size=12),
#             title_font_size=16,
#             xaxis_title_font_size=14,
#             yaxis_title_font_size=14
#         )
        
#         # Convert to JSON
#         plot_json = fig.to_json()
        
#         return {
#             "success": True,
#             "plot_type": "bar_chart",
#             "plot_data": plot_json,
#             "title": title,
#             "description": f"Bar chart showing {y_column} by {x_column}"
#         }
        
#     except Exception as e:
#         logger.error(f"Error creating bar chart: {e}")
#         return {
#             "success": False,
#             "error": f"Failed to create bar chart: {str(e)}"
#         }

# @tool  
# def create_sunburst_chart(df: pd.DataFrame, hierarchy_columns: List[str], 
#                          value_column: str, title: str = "Sunburst Chart",
#                          table_data: Dict = None) -> Dict[str, Any]:
#     """
#     Create a sunburst chart for hierarchical data
    
#     Args:
#         df: DataFrame with the data
#         hierarchy_columns: List of column names representing hierarchy levels (inner to outer)
#         value_column: Column name for values
#         title: Chart title
#         table_data: Original table data for context
#     """
#     try:
#         # Validate columns
#         for col in hierarchy_columns:
#             if col not in df.columns:
#                 raise ValueError(f"Hierarchy column '{col}' not found in data")
#         if value_column not in df.columns:
#             raise ValueError(f"Value column '{value_column}' not found in data")
        
#         # Create sunburst chart
#         fig = px.sunburst(
#             df,
#             path=hierarchy_columns,
#             values=value_column,
#             title=title
#         )
        
#         fig.update_layout(
#             font=dict(size=12),
#             title_font_size=16
#         )
        
#         # Convert to JSON
#         plot_json = fig.to_json()
        
#         return {
#             "success": True,
#             "plot_type": "sunburst_chart", 
#             "plot_data": plot_json,
#             "title": title,
#             "description": f"Sunburst chart showing hierarchical breakdown of {value_column}"
#         }
        
#     except Exception as e:
#         logger.error(f"Error creating sunburst chart: {e}")
#         return {
#             "success": False,
#             "error": f"Failed to create sunburst chart: {str(e)}"
#         }

# @tool
# def create_line_chart(df: pd.DataFrame, x_column: str, y_column: str,
#                      title: str = "Line Chart", table_data: Dict = None) -> Dict[str, Any]:
#     """Create a line chart from the data"""
#     try:
#         if x_column not in df.columns or y_column not in df.columns:
#             raise ValueError(f"Columns not found: {x_column}, {y_column}")
        
#         fig = px.line(df, x=x_column, y=y_column, title=title)
#         fig.update_layout(font=dict(size=12), title_font_size=16)
        
#         return {
#             "success": True,
#             "plot_type": "line_chart",
#             "plot_data": fig.to_json(),
#             "title": title,
#             "description": f"Line chart showing {y_column} over {x_column}"
#         }
#     except Exception as e:
#         return {"success": False, "error": f"Failed to create line chart: {str(e)}"}

# @tool
# def create_scatter_plot(df: pd.DataFrame, x_column: str, y_column: str,
#                        title: str = "Scatter Plot", table_data: Dict = None) -> Dict[str, Any]:
#     """Create a scatter plot from the data"""
#     try:
#         if x_column not in df.columns or y_column not in df.columns:
#             raise ValueError(f"Columns not found: {x_column}, {y_column}")
        
#         fig = px.scatter(df, x=x_column, y=y_column, title=title)
#         fig.update_layout(font=dict(size=12), title_font_size=16)
        
#         return {
#             "success": True,
#             "plot_type": "scatter_plot",
#             "plot_data": fig.to_json(),
#             "title": title,
#             "description": f"Scatter plot of {y_column} vs {x_column}"
#         }
#     except Exception as e:
#         return {"success": False, "error": f"Failed to create scatter plot: {str(e)}"}

# @tool
# def create_histogram(df: pd.DataFrame, column: str, bins: int = 20,
#                     title: str = "Histogram", table_data: Dict = None) -> Dict[str, Any]:
#     """Create a histogram from the data"""
#     try:
#         if column not in df.columns:
#             raise ValueError(f"Column '{column}' not found in data")
        
#         fig = px.histogram(df, x=column, nbins=bins, title=title)
#         fig.update_layout(font=dict(size=12), title_font_size=16)
        
#         return {
#             "success": True,
#             "plot_type": "histogram",
#             "plot_data": fig.to_json(),
#             "title": title,
#             "description": f"Distribution of {column}"
#         }
#     except Exception as e:
#         return {"success": False, "error": f"Failed to create histogram: {str(e)}"}

# @tool
# def create_pie_chart(df: pd.DataFrame, labels_column: str, values_column: str,
#                     title: str = "Pie Chart", table_data: Dict = None) -> Dict[str, Any]:
#     """Create a pie chart from the data"""
#     try:
#         if labels_column not in df.columns or values_column not in df.columns:
#             raise ValueError(f"Columns not found: {labels_column}, {values_column}")
        
#         fig = px.pie(df, names=labels_column, values=values_column, title=title)
#         fig.update_layout(font=dict(size=12), title_font_size=16)
        
#         return {
#             "success": True,
#             "plot_type": "pie_chart",
#             "plot_data": fig.to_json(),
#             "title": title,
#             "description": f"Pie chart of {values_column} by {labels_column}"
#         }
#     except Exception as e:
#         return {"success": False, "error": f"Failed to create pie chart: {str(e)}"} 