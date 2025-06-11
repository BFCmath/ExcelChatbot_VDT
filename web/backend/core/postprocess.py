"""
Post-processing module for hierarchical table rendering.
Handles the conversion of DataFrame results into frontend-ready table structures
with proper rowspan and colspan calculations for Excel-like table display.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TablePostProcessor:
    """
    Handles post-processing of DataFrame results into hierarchical table structures
    suitable for frontend rendering with merged cells (rowspan/colspan).
    """
    
    def extract_hierarchical_table_info(self, df):
        """
        Extract hierarchical table information from a DataFrame with potential MultiIndex columns.
        This preserves the structure needed for proper HTML table rendering with merged cells.
        Focuses on creating vertical merged cells (rowspan) for proper financial table display.
        """
        # Check if we have MultiIndex columns
        has_multiindex = isinstance(df.columns, pd.MultiIndex)
        
        if has_multiindex:
            # For proper vertical merging, we need to analyze the structure differently
            header_matrix = self.build_header_matrix(df.columns)
            
            # Get the actual column names for the final level
            final_columns = [self.clean_column_name(col) for col in df.columns.values]
        else:
            # Simple single-level headers
            header_matrix = [[{
                "text": str(col),
                "colspan": 1,
                "rowspan": 1,
                "position": i
            } for i, col in enumerate(df.columns)]]
            final_columns = [str(col) for col in df.columns]
        
        # Convert data to JSON-serializable format
        data_rows = []
        for _, row in df.iterrows():
            row_data = []
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    row_data.append(None)
                elif isinstance(value, (int, float)) and not pd.isna(value):
                    # Handle numeric values safely
                    if isinstance(value, float):
                        row_data.append(float(value))
                    else:
                        row_data.append(int(value))
                else:
                    row_data.append(str(value))
            data_rows.append(row_data)
        
        return {
            "has_multiindex": has_multiindex,
            "header_matrix": header_matrix,
            "final_columns": final_columns,
            "data_rows": data_rows,
            "row_count": len(data_rows),
            "col_count": len(final_columns)
        }
    
    def build_header_matrix(self, multiindex_columns):
        """
        Build a matrix representation of MultiIndex headers for proper HTML rendering with rowspan and colspan.
        """
        n_levels = multiindex_columns.nlevels
        n_cols = len(multiindex_columns)
        
        # Create a matrix to track cell information
        header_matrix = []
        
        # First pass: calculate all rowspans
        rowspan_matrix = []
        for level in range(n_levels):
            level_rowspans = []
            level_values = multiindex_columns.get_level_values(level)
            
            for i in range(n_cols):
                current_value = level_values[i]
                current_value_str = str(current_value) if not pd.isna(current_value) and str(current_value) != 'nan' else ""
                rowspan = self.calculate_rowspan(multiindex_columns, level, i, current_value_str)
                level_rowspans.append(rowspan)
            
            rowspan_matrix.append(level_rowspans)
        
        # Second pass: build header matrix, skipping cells covered by rowspan
        covered_positions = set()  # Track positions covered by rowspan from previous levels
        
        for level in range(n_levels):
            level_headers = []
            level_values = multiindex_columns.get_level_values(level)
            
            i = 0
            while i < n_cols:
                # Skip positions covered by rowspan from previous levels
                if (level, i) in covered_positions:
                    i += 1
                    continue
                    
                current_value = level_values[i]
                current_value_str = str(current_value) if not pd.isna(current_value) and str(current_value) != 'nan' else ""
                
                # Calculate intelligent colspan - only merge when it makes semantic sense
                colspan = self.calculate_intelligent_colspan(multiindex_columns, level, i, current_value_str, covered_positions)
                
                # Get rowspan from pre-calculated matrix
                rowspan = rowspan_matrix[level][i]
                
                level_headers.append({
                    "text": current_value_str,
                    "colspan": colspan,
                    "rowspan": rowspan,
                    "position": i,
                    "level": level
                })
                
                # Mark positions as covered by this cell's rowspan
                for r in range(level + 1, level + rowspan):
                    for c in range(i, i + colspan):
                        if r < n_levels:
                            covered_positions.add((r, c))
                
                i += colspan
            
            header_matrix.append(level_headers)
        
        return header_matrix
    
    def calculate_rowspan(self, multiindex_columns, level, position, current_value):
        """
        Calculate the rowspan for a header cell based on whether lower levels contain "Header".
        This works as postprocessing - when lower levels have "Header" (from preprocessing),
        the upper level should span vertically to cover that space.
        """
        if level == multiindex_columns.nlevels - 1:
            return 1  # Last level, no spanning
        
        # Check if all lower levels are "Header" for this position
        # "Header" indicates that the original was "Unnamed:" which means empty/should be spanned
        all_lower_are_headers = True
        for lower_level in range(level + 1, multiindex_columns.nlevels):
            lower_value = multiindex_columns.get_level_values(lower_level)[position]
            lower_value_str = str(lower_value) if not pd.isna(lower_value) and str(lower_value) != 'nan' else ""
            
            # If the lower level is NOT "Header", then we don't span
            if lower_value_str != "Header":
                all_lower_are_headers = False
                break
        
        if all_lower_are_headers:
            return multiindex_columns.nlevels - level  # Span to the bottom
        else:
            return 1  # No spanning
    
    def calculate_intelligent_colspan(self, multiindex_columns, level, start_position, current_value_str, covered_positions):
        """
        Calculate colspan intelligently - only merge consecutive identical values when
        the lower levels have different content that justifies the spanning.
        """
        if level == multiindex_columns.nlevels - 1:
            return 1  # Last level, no horizontal spanning
        
        level_values = multiindex_columns.get_level_values(level)
        n_cols = len(multiindex_columns)
        
        # Count consecutive identical values
        consecutive_end = start_position + 1
        while (consecutive_end < n_cols and 
               str(level_values[consecutive_end]) == current_value_str and
               (level, consecutive_end) not in covered_positions):
            consecutive_end += 1
        
        potential_colspan = consecutive_end - start_position
        
        if potential_colspan == 1:
            return 1  # No consecutive identical values
        
        # Check if the lower levels have varied content that would justify merging
        # If all lower levels are identical across the span, don't merge (they're separate cells)
        lower_levels_vary = False
        
        for lower_level in range(level + 1, multiindex_columns.nlevels):
            lower_values = multiindex_columns.get_level_values(lower_level)
            first_lower_value = str(lower_values[start_position])
            
            for pos in range(start_position + 1, consecutive_end):
                if str(lower_values[pos]) != first_lower_value:
                    lower_levels_vary = True
                    break
            
            if lower_levels_vary:
                break
        
        # Only merge if lower levels vary (indicating this is a parent header)
        # OR if lower levels are all "Header" (indicating they should be spanned over)
        if lower_levels_vary:
            return potential_colspan
        else:
            # Check if all lower levels are "Header" (empty placeholders)
            all_lower_are_headers = True
            for lower_level in range(level + 1, multiindex_columns.nlevels):
                lower_values = multiindex_columns.get_level_values(lower_level)
                for pos in range(start_position, consecutive_end):
                    lower_val_str = str(lower_values[pos])
                    if lower_val_str != "Header":
                        all_lower_are_headers = False
                        break
                if not all_lower_are_headers:
                    break
            
            if all_lower_are_headers:
                return potential_colspan  # Merge over empty placeholders
            else:
                return 1  # Don't merge identical cells that are actually separate
    
    def clean_column_name(self, col):
        """
        Clean column names for display while preserving hierarchical information.
        """
        if isinstance(col, tuple):
            # For MultiIndex, take the last non-"Header" level
            non_header_parts = [str(part) for part in col if str(part) != "Header"]
            if non_header_parts:
                return non_header_parts[-1]  # Take the most specific level
            else:
                return str(col[0])  # Fallback to first level
        else:
            return str(col) 