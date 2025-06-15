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
        self.supported_plot_types = ['sunburst']  # Only sunburst for now
    
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

    def _create_single_sunburst(self, df: pd.DataFrame, categorical_names: List[str], col_level_cols: List[str], 
                               priority: str, filename: str) -> Dict:
        """
        Create a single sunburst plot with specified priority.
        """
        if priority == 'column':
            plot_path = col_level_cols + categorical_names
            title = f"Sunburst Chart: {filename} (Column-first Hierarchy)"
        else:  # priority == 'row'
            plot_path = categorical_names + col_level_cols
            title = f"Sunburst Chart: {filename} (Row-first Hierarchy)"
        
        # Remove any columns from plot_path that don't exist in the DataFrame
        valid_plot_path = [col for col in plot_path if col in df.columns]
        plot_path = valid_plot_path

        # Handle None values in the path columns
        df_copy = df.copy()
        for col in plot_path:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna('Unknown')
        
        # Create the sunburst plot
        fig = px.sunburst(
            df_copy,
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
            'title': title,
            'html_content': html_content,
            'hierarchy': plot_path,
            'priority': priority
        }

    def generate_sunburst_plots(self, frontend_data: Dict) -> Dict:
        """
        Generate both column-first and row-first sunburst plots from frontend JSON data.
        Returns both variants for maximum flexibility.
        """
        try:
            logger.info(f"🎨 [PLOTTING] Starting sunburst plot generation")
            
            # Extract data from frontend format
            final_columns = frontend_data.get('final_columns', [])
            data_rows = frontend_data.get('data_rows', [])
            header_matrix = frontend_data.get('header_matrix', [])
            has_multiindex = frontend_data.get('has_multiindex', False)
            filename = frontend_data.get('filename', 'table')
            
            logger.info(f"🔍 [PLOTTING] Input data analysis:")
            logger.info(f"  📋 final_columns: {len(final_columns)} items")
            logger.info(f"  📋 data_rows: {len(data_rows)} rows")
            logger.info(f"  📋 header_matrix: {len(header_matrix)} levels")
            logger.info(f"  📋 has_multiindex: {has_multiindex}")
            logger.info(f"  📋 filename: {filename}")
            
            if not final_columns or not data_rows:
                logger.error(f"❌ [PLOTTING] Missing required data: final_columns={len(final_columns)}, data_rows={len(data_rows)}")
                return {
                    'success': False,
                    'error': 'No data found in JSON. Required: final_columns and data_rows'
                }

            # Log first data row for type analysis
            if data_rows:
                first_row = data_rows[0]
                logger.info(f"🔍 [PLOTTING] First data row analysis:")
                logger.info(f"  📊 Length: {len(first_row)}")
                logger.info(f"  📊 Values: {first_row}")
                logger.info(f"  📊 Types: {[type(cell).__name__ for cell in first_row]}")
                
                # Check for problematic types
                for i, cell in enumerate(first_row):
                    cell_type = str(type(cell))
                    if 'numpy' in cell_type:
                        logger.warning(f"  ⚠️ NUMPY TYPE at position {i}: {cell_type} = {cell}")

            # Analyze the header_matrix structure properly
            logger.info(f"🔧 [PLOTTING] Analyzing header matrix structure...")
            structure_info = self._analyze_header_matrix_structure(header_matrix, final_columns, data_rows)
            
            # Get categorical and numeric column information
            categorical_positions = structure_info["categorical_positions"]
            numeric_positions = structure_info["numeric_positions"]
            data_to_header_position = structure_info["data_to_header_position"]
            level_structures = structure_info["level_structures"]
            
            logger.info(f"📊 [PLOTTING] Structure analysis results:")
            logger.info(f"  🏷️ Categorical positions: {categorical_positions}")
            logger.info(f"  🔢 Numeric positions: {numeric_positions}")
            logger.info(f"  📏 Data length: {structure_info['data_length']}")
            logger.info(f"  📏 Columns length: {structure_info['columns_length']}")
            
            # Get categorical column names from the header_matrix
            categorical_names = []
            for cat_pos in categorical_positions:
                header_pos = data_to_header_position[cat_pos]
                # Get the name from level 0 of header_matrix
                if 0 in level_structures and header_pos in level_structures[0]:
                    categorical_names.append(level_structures[0][header_pos])
                else:
                    categorical_names.append(f"Category_{cat_pos}")
            
            logger.info(f"🏷️ [PLOTTING] Categorical column names: {categorical_names}")
            
            # Prepare data for plotting
            logger.info(f"🔄 [PLOTTING] Processing data rows for plotting...")
            plot_data = []
            
            for row_idx, data_row in enumerate(data_rows):
                if row_idx == 0:
                    logger.info(f"🔍 [PLOTTING] Processing first row (index {row_idx}):")
                    logger.info(f"  📊 Row data: {data_row}")
                    logger.info(f"  📊 Row types: {[type(cell).__name__ for cell in data_row]}")
                
                # Extract categorical values
                row_categories = {}
                for i, cat_pos in enumerate(categorical_positions):
                    if cat_pos < len(data_row) and i < len(categorical_names):
                        cat_value = str(data_row[cat_pos])
                        row_categories[categorical_names[i]] = cat_value
                        if row_idx == 0:
                            logger.info(f"    🏷️ {categorical_names[i]} = {cat_value}")
                
                # Process each numeric column
                for num_pos in numeric_positions:
                    if num_pos >= len(data_row):
                        logger.warning(f"⚠️ [PLOTTING] Numeric position {num_pos} >= row length {len(data_row)}")
                        continue
                    
                    # Get the header position for this data position
                    header_pos = data_to_header_position[num_pos]
                    
                    # Build the complete hierarchy path for this column
                    hierarchy_path = self._build_column_hierarchy_paths(header_matrix, header_pos)
                    
                    if row_idx == 0:
                        logger.info(f"    🔢 Numeric position {num_pos} -> header {header_pos} -> path {hierarchy_path}")
                    
                    record = {}
                    
                    # Add categorical data
                    for cat_name, cat_value in row_categories.items():
                        record[cat_name] = cat_value
                    
                    # Add column hierarchy levels
                    for level_idx, level_name in enumerate(hierarchy_path):
                        record[f'Col_Level_{level_idx}'] = level_name
                    
                    # Add data value - CRITICAL: Convert to native Python types
                    raw_value = data_row[num_pos]
                    if row_idx == 0:
                        logger.info(f"    💰 Raw value at position {num_pos}: {raw_value} (type: {type(raw_value).__name__})")
                    
                    try:
                        # Convert to pandas numeric, then to native Python type
                        actual_value = pd.to_numeric(raw_value, errors='coerce')
                        if pd.notna(actual_value):
                            # Convert numpy types to native Python types
                            if hasattr(actual_value, 'item'):
                                # numpy scalar -> Python scalar
                                python_value = actual_value.item()
                            else:
                                # Already Python type
                                python_value = float(actual_value)
                            record['value'] = python_value
                            if row_idx == 0:
                                logger.info(f"    ✅ Converted value: {python_value} (type: {type(python_value).__name__})")
                        else:
                            record['value'] = 0
                            if row_idx == 0:
                                logger.info(f"    ⚠️ NaN value converted to 0")
                    except (ValueError, TypeError, IndexError) as e:
                        record['value'] = 0
                        if row_idx == 0:
                            logger.warning(f"    ❌ Value conversion failed: {e}, using 0")
                    
                    plot_data.append(record)
            
            logger.info(f"📊 [PLOTTING] Created {len(plot_data)} plot records")
            
            if not plot_data:
                logger.error(f"❌ [PLOTTING] No plot data generated")
                return {
                    'success': False,
                    'error': 'No data to plot after processing'
                }
                
            # Create DataFrame and log its structure
            logger.info(f"🐼 [PLOTTING] Creating pandas DataFrame...")
            df = pd.DataFrame(plot_data)
            logger.info(f"📊 [PLOTTING] DataFrame created:")
            logger.info(f"  📏 Shape: {df.shape}")
            logger.info(f"  📋 Columns: {list(df.columns)}")
            logger.info(f"  📊 Data types: {dict(df.dtypes)}")
            
            # Check for any remaining numpy types in DataFrame
            for col in df.columns:
                col_dtype = str(df[col].dtype)
                if 'int64' in col_dtype or 'float64' in col_dtype:
                    logger.info(f"  🔢 Column '{col}' has pandas dtype: {col_dtype}")
                    # Convert pandas dtypes to native Python types
                    if 'int64' in col_dtype:
                        df[col] = df[col].astype(int)
                        logger.info(f"    ✅ Converted {col} to native int")
                    elif 'float64' in col_dtype:
                        df[col] = df[col].astype(float)
                        logger.info(f"    ✅ Converted {col} to native float")
            
            # Get column level columns
            col_level_cols = [col for col in df.columns if col.startswith('Col_Level_')]
            col_level_cols.sort()  # Ensure proper order
            
            logger.info(f"📊 [PLOTTING] Column hierarchy levels: {col_level_cols}")
            logger.info(f"🏷️ [PLOTTING] Categorical columns: {categorical_names}")
            
            # Generate both priority variants
            logger.info(f"🎨 [PLOTTING] Generating column-first sunburst...")
            column_first = self._create_single_sunburst(df, categorical_names, col_level_cols, 'column', filename)
            
            logger.info(f"🎨 [PLOTTING] Generating row-first sunburst...")
            row_first = self._create_single_sunburst(df, categorical_names, col_level_cols, 'row', filename)
            
            # Calculate analysis metrics
            total_value = float(df['value'].sum())  # Ensure native Python float
            unique_categories = {}
            for col in categorical_names:
                if col in df.columns:
                    unique_categories[col] = int(df[col].nunique())  # Ensure native Python int
            
            logger.info(f"✅ [PLOTTING] Plot generation completed successfully")
            logger.info(f"📊 [PLOTTING] Analysis: total_value={total_value}, unique_categories={unique_categories}")
            
            return {
                'success': True,
                'plot_type': 'sunburst',
                'data_points': len(df),
                'plots': {
                    'column_first': column_first,
                    'row_first': row_first
                },
                'analysis': {
                    'categorical_columns': categorical_names,
                    'hierarchy_levels': len(col_level_cols),
                    'total_value': total_value,
                    'unique_categories': unique_categories
                },
                'message': f'Successfully created both column-first and row-first sunburst charts with {len(df)} data points'
            }
            
        except Exception as e:
            logger.error(f"❌ [PLOTTING] Error creating sunburst plots: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error creating sunburst plots: {str(e)}',
                'plot_type': 'sunburst'
            }

    def generate_plot(self, frontend_data: Dict) -> Dict:
        """
        Main plotting function - currently only supports sunburst charts.
        Future: Will add LLM column selection and bar charts.
        """
        return self.generate_sunburst_plots(frontend_data)
