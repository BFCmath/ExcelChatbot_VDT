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
        self.supported_plot_types = ['sunburst', 'bar']  # Support both sunburst and bar charts
        self.remove_keywords = ['Tổng', 'Cộng']  # Default filter keywords for total columns
    
    def _is_simple_structure_for_bar_chart(self, frontend_data: Dict) -> bool:
        """
        Check if data structure is simple enough for bar charts.
        
        Criteria for bar chart suitability:
        - No multiindex structure (has_multiindex == False)
        - Only single categorical column (len(feature_rows) == 1)
        - Simple flat structure
        """
        feature_rows = frontend_data.get('feature_rows', [])
        has_multiindex = frontend_data.get('has_multiindex', False)
        
        is_simple = (
            not has_multiindex and 
            len(feature_rows) == 1  # Only single categorical column supported
        )
        
        logger.info(f"📊 [PLOTTING] Simple structure check:")
        logger.info(f"  📋 has_multiindex: {has_multiindex}")
        logger.info(f"  📋 feature_rows count: {len(feature_rows)}")
        logger.info(f"  📋 feature_rows: {feature_rows}")
        logger.info(f"  ✅ Is simple for bar chart: {is_simple}")
        
        return is_simple
    
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
            title = f"{filename} (Column-first Hierarchy)"
        else:  # priority == 'row'
            plot_path = categorical_names + col_level_cols
            title = f"{filename} (Row-first Hierarchy)"
        
        # Remove any columns from plot_path that don't exist in the DataFrame
        valid_plot_path = [col for col in plot_path if col in df.columns]
        plot_path = valid_plot_path

        # Handle None values in the path columns
        df_copy = df.copy()
        for col in plot_path:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna('Unknown')
        
        # Create the sunburst plot without title
        fig = px.sunburst(
            df_copy,
            path=plot_path,
            values='value',
            hover_data={'value': True}
        )

        # Enhanced sunburst configuration with square layout
        fig.update_layout(
            margin=dict(t=80, l=25, r=25, b=25),  # Reduced top margin since no title
            font=dict(size=11),
            showlegend=False,
            width=600,   # Set fixed width for square aspect
            height=600   # Set fixed height for square aspect
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
            logger.info(f"  🔢 Numeric positions (before filtering): {numeric_positions}")
            logger.info(f"  📏 Data length: {structure_info['data_length']}")
            logger.info(f"  📏 Columns length: {structure_info['columns_length']}")
            
            # Apply filtering to sunburst data - remove positions with total keywords
            logger.info(f"🔍 [SUNBURST FILTERING] Applying filtering to numeric positions...")
            original_numeric_positions = numeric_positions.copy()
            filtered_out_positions = []
            
            numeric_positions_filtered = []
            for pos in numeric_positions:
                if pos < len(final_columns):
                    column_name = final_columns[pos]
                    should_filter = any(keyword in column_name for keyword in self.remove_keywords)
                    if should_filter:
                        filtered_out_positions.append(pos)
                        logger.info(f"  ❌ FILTERED OUT position {pos}: {column_name}")
                    else:
                        numeric_positions_filtered.append(pos)
                        logger.info(f"  ✅ KEEPING position {pos}: {column_name}")
                else:
                    logger.warning(f"  ⚠️ Position {pos} >= final_columns length {len(final_columns)}")
            
            # Update numeric positions with filtered results
            numeric_positions = numeric_positions_filtered
            
            logger.info(f"📊 [SUNBURST FILTERING] Filtering results:")
            logger.info(f"  📋 Original numeric positions: {len(original_numeric_positions)}")
            logger.info(f"  📋 Filtered out positions: {len(filtered_out_positions)}")
            logger.info(f"  📋 Final numeric positions: {len(numeric_positions)}")
            logger.info(f"  🔢 Numeric positions (after filtering): {numeric_positions}")
            
            if not numeric_positions:
                logger.error(f"❌ [SUNBURST FILTERING] No valid numeric columns found after filtering")
                return {
                    'success': False,
                    'error': 'No valid numeric columns found to plot after filtering out totals'
                }
            
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
                    'unique_categories': unique_categories,
                    'numeric_positions_original': len(original_numeric_positions),
                    'numeric_positions_filtered': len(numeric_positions),
                    'filtered_out_count': len(filtered_out_positions),
                    'filtered_out_positions': filtered_out_positions
                },
                'message': f'Successfully created both column-first and row-first sunburst charts with {len(df)} data points (filtered out {len(filtered_out_positions)} total columns)'
            }
            
        except Exception as e:
            logger.error(f"❌ [PLOTTING] Error creating sunburst plots: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error creating sunburst plots: {str(e)}',
                'plot_type': 'sunburst'
            }

    def generate_bar_plots(self, frontend_data: Dict) -> Dict:
        """
        Generate bar chart from simple flat table data.
        
        This method handles completely flattened data structure with:
        - Single categorical column (feature_rows)
        - Multiple numeric columns representing time series or categories
        - Automatic filtering of total/summary columns
        """
        try:
            logger.info(f"📊 [BAR PLOTTING] Starting bar chart generation")
            
            # Extract data from frontend format
            final_columns = frontend_data.get('final_columns', [])
            data_rows = frontend_data.get('data_rows', [])
            feature_rows = frontend_data.get('feature_rows', [])
            filename = frontend_data.get('filename', 'table')
            
            logger.info(f"📋 [BAR PLOTTING] Input data analysis:")
            logger.info(f"  📋 final_columns: {len(final_columns)} items")
            logger.info(f"  📋 data_rows: {len(data_rows)} rows")
            logger.info(f"  📋 feature_rows: {feature_rows}")
            logger.info(f"  📋 filename: {filename}")
            
            if not final_columns or not data_rows or not feature_rows:
                logger.error(f"❌ [BAR PLOTTING] Missing required data")
                return {
                    'success': False,
                    'error': 'Missing required data for bar chart: final_columns, data_rows, feature_rows'
                }
            
            # Validate simple structure
            if len(feature_rows) != 1:
                logger.error(f"❌ [BAR PLOTTING] Bar charts only support single categorical column, got {len(feature_rows)}")
                return {
                    'success': False,
                    'error': f'Bar charts only support single categorical column, got {len(feature_rows)} columns'
                }
            
            categorical_col = feature_rows[0]
            logger.info(f"📊 [BAR PLOTTING] Categorical column: {categorical_col}")
            
            # Identify numeric columns (all columns except categorical)
            potential_numeric_cols = [col for col in final_columns if col not in feature_rows]
            
            # Filter out columns containing total keywords
            numeric_cols_to_plot = []
            filtered_out_cols = []
            
            for col in potential_numeric_cols:
                should_filter = any(keyword in col for keyword in self.remove_keywords)
                if should_filter:
                    filtered_out_cols.append(col)
                else:
                    numeric_cols_to_plot.append(col)
            
            logger.info(f"📊 [BAR PLOTTING] Column filtering:")
            logger.info(f"  📋 Potential numeric columns: {len(potential_numeric_cols)}")
            logger.info(f"  📋 Filtered out (totals): {filtered_out_cols}")
            logger.info(f"  📋 Columns to plot: {len(numeric_cols_to_plot)}")
            
            if not numeric_cols_to_plot:
                logger.error(f"❌ [BAR PLOTTING] No valid numeric columns found after filtering")
                return {
                    'success': False,
                    'error': 'No valid numeric columns found to plot after filtering out totals'
                }
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=final_columns)
            logger.info(f"📊 [BAR PLOTTING] DataFrame created: {df.shape}")
            
            # Melt the DataFrame to long format for plotting
            df_melted = df.melt(
                id_vars=[categorical_col],
                value_vars=numeric_cols_to_plot,
                var_name='Metric',
                value_name='Value'
            )
            
            logger.info(f"📊 [BAR PLOTTING] DataFrame melted: {df_melted.shape}")
            
            # Clean up data types
            df_melted['Value'] = pd.to_numeric(df_melted['Value'], errors='coerce')
            df_melted = df_melted.dropna(subset=['Value'])
            
            # Simplify metric labels for better readability
            def simplify_column_name(col_name):
                """
                Simplify complex column names like 'N2024 6Tđn QI Tháng 01' to 'Tháng 01'
                Extract the most meaningful part of the column name
                """
                # If contains 'Tháng' (Month), extract 'Tháng XX'
                if 'Tháng' in col_name:
                    parts = col_name.split()
                    tháng_idx = next(i for i, part in enumerate(parts) if 'Tháng' in part)
                    if tháng_idx + 1 < len(parts):
                        return f"{parts[tháng_idx]} {parts[tháng_idx + 1]}"
                    else:
                        return parts[tháng_idx]
                # Otherwise, take the last 2 meaningful parts
                else:
                    parts = col_name.split()
                    if len(parts) >= 2:
                        return ' '.join(parts[-2:])
                    else:
                        return col_name
            
            df_melted['MetricLabel'] = df_melted['Metric'].apply(simplify_column_name)
            
            # Sort by metric labels for consistent ordering
            try:
                # Try to extract numbers for sorting (for time-based data)
                df_melted['Metric_Number'] = df_melted['MetricLabel'].str.extract(r'(\d+)').astype(int)
                df_melted = df_melted.sort_values(by=['Metric_Number'])
                logger.info(f"📊 [BAR PLOTTING] Sorted by numeric metric order")
            except Exception:
                # Fallback to alphabetical sorting
                df_melted = df_melted.sort_values(by=['MetricLabel'])
                logger.info(f"📊 [BAR PLOTTING] Sorted alphabetically")
            
            # Create bar chart
            logger.info(f"🎨 [BAR PLOTTING] Creating bar chart...")
            fig = px.bar(
                df_melted,
                x='MetricLabel',
                y='Value',
                color=categorical_col,
                barmode='group',
                text_auto=True
            )
            
            # Clean layout - similar to sunburst style
            fig.update_layout(
                margin=dict(t=25, l=25, r=25, b=25),  # Minimal margins like sunburst
                font=dict(size=11),
                showlegend=True,  # Keep legend as requested
                legend=dict(
                    title="",  # Remove legend title for cleaner look
                    orientation="h",  # Horizontal legend
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                xaxis=dict(
                    title="",  # Remove axis title
                    categoryorder='array', 
                    categoryarray=df_melted['MetricLabel'].unique()
                ),
                yaxis=dict(
                    title=""  # Remove axis title
                ),
                template="simple_white",
                width=800,
                height=500
            )
            
            # Convert to HTML - consistent with sunburst approach
            html_content = fig.to_html()
            
            # Calculate analysis metrics
            total_value = float(df_melted['Value'].sum())
            unique_categories = int(df_melted[categorical_col].nunique())
            
            logger.info(f"✅ [BAR PLOTTING] Bar chart generation completed successfully")
            logger.info(f"📊 [BAR PLOTTING] Analysis: total_value={total_value}, unique_categories={unique_categories}")
            
            return {
                'success': True,
                'plot_type': 'bar',
                'data_points': len(df_melted),
                'plots': {
                    'bar_chart': {
                        'title': f"Bar Chart: {filename}",
                        'html_content': html_content,
                        'categorical_column': categorical_col,
                        'metrics_plotted': numeric_cols_to_plot,
                        'filtered_columns': filtered_out_cols
                    }
                },
                'analysis': {
                    'categorical_column': categorical_col,
                    'metrics_count': len(numeric_cols_to_plot),
                    'total_value': total_value,
                    'unique_categories': unique_categories,
                    'filtered_out_count': len(filtered_out_cols)
                },
                'message': f'Successfully created bar chart with {len(numeric_cols_to_plot)} metrics and {unique_categories} categories'
            }
            
        except Exception as e:
            logger.error(f"❌ [BAR PLOTTING] Error creating bar chart: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error creating bar chart: {str(e)}',
                'plot_type': 'bar'
            }

    def generate_plot(self, frontend_data: Dict) -> Dict:
        """
        Main plotting function - generates appropriate charts based on data structure.
        
        Decision logic:
        - Always generate sunburst chart (works for all data)
        - Additionally generate bar chart if simple structure (has_multiindex=False, single feature_rows)
        """
        try:
            logger.info(f"🎯 [PLOTTING] Starting plot generation...")
            
            # ALWAYS generate sunburst chart first
            logger.info(f"🌅 [PLOTTING] Generating SUNBURST CHART (always generated)")
            sunburst_result = self.generate_sunburst_plots(frontend_data)
            
            # Check if data structure is simple enough for bar charts
            is_simple = self._is_simple_structure_for_bar_chart(frontend_data)
            
            if is_simple:
                logger.info(f"📊 [PLOTTING] Simple structure detected - ALSO generating BAR CHART")
                bar_result = self.generate_bar_plots(frontend_data)
                
                # Combine both results
                if sunburst_result.get('success') and bar_result.get('success'):
                    combined_plots = {}
                    combined_plots.update(sunburst_result.get('plots', {}))
                    combined_plots.update(bar_result.get('plots', {}))
                    
                    return {
                        'success': True,
                        'plot_types': ['sunburst', 'bar'],  # Both generated
                        'data_points_sunburst': sunburst_result.get('data_points'),
                        'data_points_bar': bar_result.get('data_points'),
                        'plots': combined_plots,
                        'analysis': {
                            'sunburst': sunburst_result.get('analysis'),
                            'bar': bar_result.get('analysis')
                        },
                        'message': f'Generated both sunburst and bar charts for versatile visualization'
                    }
                elif sunburst_result.get('success'):
                    # Sunburst worked, bar failed - return sunburst
                    logger.warning(f"⚠️ [PLOTTING] Bar chart failed, returning sunburst only")
                    return sunburst_result
                else:
                    # Both failed
                    return {
                        'success': False,
                        'error': f'Both sunburst and bar chart generation failed'
                    }
            else:
                logger.info(f"📊 [PLOTTING] Complex structure - returning SUNBURST CHART only")
                return sunburst_result
                
        except Exception as e:
            logger.error(f"❌ [PLOTTING] Error in main plot generation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error determining plot type: {str(e)}'
            }