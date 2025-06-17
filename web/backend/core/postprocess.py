"""
Post-processing module for hierarchical table rendering.
Handles the conversion of DataFrame results into frontend-ready table structures
with proper rowspan and colspan calculations for Excel-like table display.
"""

import pandas as pd
import logging
import re

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
        
        Returns both normal hierarchical table and flattened table structures.
        """
        logger.info(f"🔄 [POSTPROCESS] Starting table extraction for DataFrame shape: {df.shape}")
        logger.info(f"🔄 [POSTPROCESS] DataFrame columns: {df.columns}")
        logger.info(f"🔄 [POSTPROCESS] DataFrame columns type: {type(df.columns)}")
        
        # Check if we have MultiIndex columns
        has_multiindex = isinstance(df.columns, pd.MultiIndex)
        logger.info(f"📊 [POSTPROCESS] Has MultiIndex: {has_multiindex}")
        
        if has_multiindex:
            logger.info(f"🔧 [POSTPROCESS] Processing MultiIndex columns with {df.columns.nlevels} levels")
            
            # For proper vertical merging, we need to analyze the structure differently
            header_matrix = self.build_header_matrix(df.columns)
            logger.info(f"📋 [POSTPROCESS] Built header matrix with {len(header_matrix)} levels")
            
            # Get the actual column names for the final level
            final_columns = [self.clean_column_name(col) for col in df.columns.values]
            logger.info(f"📋 [POSTPROCESS] Final columns: {final_columns}")
            
            # Create flattened headers
            flattened_headers = self.create_flattened_headers(df.columns)
            logger.info(f"🔧 [POSTPROCESS] Created flattened headers: {flattened_headers}")
        else:
            logger.info(f"🔧 [POSTPROCESS] Processing simple single-level headers")
            # Simple single-level headers
            header_matrix = [[{
                "text": str(col),
                "colspan": 1,
                "rowspan": 1,
                "position": i
            } for i, col in enumerate(df.columns)]]
            final_columns = [str(col) for col in df.columns]
            flattened_headers = final_columns.copy()
            logger.info(f"📋 [POSTPROCESS] Single-level final columns: {final_columns}")
            logger.info(f"🔧 [POSTPROCESS] Single-level flattened headers: {flattened_headers}")
        
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
        
        logger.info(f"📊 [POSTPROCESS] Converted {len(data_rows)} data rows")
        
        # Return both normal and flattened table structures
        normal_table = {
            "has_multiindex": has_multiindex,
            "header_matrix": header_matrix,
            "final_columns": final_columns,
            "data_rows": data_rows,
            "row_count": len(data_rows),
            "col_count": len(final_columns)
        }
        
        flattened_table = {
            "has_multiindex": False,  # Flattened is always single level
            "header_matrix": [[{
                "text": header,
                "colspan": 1,
                "rowspan": 1,
                "position": i
            } for i, header in enumerate(flattened_headers)]],
            "final_columns": flattened_headers,
            "data_rows": data_rows,  # Same data, different headers
            "row_count": len(data_rows),
            "col_count": len(flattened_headers)
        }
        
        logger.info(f"✅ [POSTPROCESS] Normal table created with {normal_table['col_count']} columns, {normal_table['row_count']} rows")
        logger.info(f"✅ [POSTPROCESS] Flattened table created with {flattened_table['col_count']} columns, {flattened_table['row_count']} rows")
        logger.info(f"✅ [POSTPROCESS] Normal final_columns: {normal_table['final_columns']}")
        logger.info(f"✅ [POSTPROCESS] Flattened final_columns: {flattened_table['final_columns']}")
        
        result = {
            "normal_table": normal_table,
            "flattened_table": flattened_table
        }
        
        logger.info(f"🎯 [POSTPROCESS] Returning result with keys: {list(result.keys())}")
        return result
    
    def create_flattened_headers(self, multiindex_columns):
        """
        Create flattened headers from MultiIndex columns by combining all levels with acronyms.
        
        For horizontal merges: combine all levels with acronyms for intermediate levels, keep final level as-is
        For vertical merges: use the non-"Header" level
        
        Args:
            multiindex_columns: pandas MultiIndex columns
            
        Returns:
            list: Flattened header names
        """
        # logger.info(f"🔧 [FLATTEN] Starting flattened headers creation")
        # logger.info(f"🔧 [FLATTEN] MultiIndex columns: {multiindex_columns}")
        # logger.info(f"🔧 [FLATTEN] Number of columns: {len(multiindex_columns)}")
        
        flattened_headers = []
        
        for i, col_tuple in enumerate(multiindex_columns):
            # logger.info(f"🔧 [FLATTEN] Processing column {i}: {col_tuple}")
            
            # Get all non-"Header" parts of the column tuple
            meaningful_parts = [str(part) for part in col_tuple if str(part) != "Header" and str(part) != "nan"]
            # logger.info(f"🔧 [FLATTEN] Meaningful parts: {meaningful_parts}")
            
            if len(meaningful_parts) == 0:
                # All parts are "Header" or nan, use a default name
                flattened_name = "Column"
                # logger.info(f"🔧 [FLATTEN] No meaningful parts, using default: {flattened_name}")
            elif len(meaningful_parts) == 1:
                # Only one meaningful part (vertical merge case), use as is
                flattened_name = meaningful_parts[0]
                # logger.info(f"🔧 [FLATTEN] Single meaningful part (vertical merge): {flattened_name}")
            else:
                # Multiple meaningful parts (horizontal merge case)
                # Create acronyms for all parts EXCEPT the last one (leaf level)
                acronym_parts = []
                
                # Process all parts except the last one with acronyms
                for j, part in enumerate(meaningful_parts[:-1]):
                    acronym = self.create_acronym(part)
                    acronym_parts.append(acronym)
                    # logger.info(f"🔧 [FLATTEN] Part {j} '{part}' -> acronym '{acronym}'")
                
                # Keep the last part (leaf level) as-is
                acronym_parts.append(meaningful_parts[-1])
                # logger.info(f"🔧 [FLATTEN] Final part (kept as-is): {meaningful_parts[-1]}")
                
                flattened_name = " ".join(acronym_parts)
                # logger.info(f"🔧 [FLATTEN] Combined flattened name: {flattened_name}")
            
            flattened_headers.append(flattened_name)
            # logger.info(f"🔧 [FLATTEN] Added to flattened headers: {flattened_name}")
        
        logger.info(f"✅ [FLATTEN] Final flattened headers: {flattened_headers}")
        return flattened_headers
    
    def create_acronym(self, text):
        """
        Create acronym from text, keeping numbers intact and preserving case.
        
        Examples:
        - "chi phí" -> "cp"
        - "Chi Phí" -> "CP"
        - "cấp 1" -> "c1"
        - "Năm 2024" -> "N2024"
        - "Học Kì 1" -> "HK1"
        
        Args:
            text (str): Input text
            
        Returns:
            str: Acronym with numbers and case preserved
        """
        text = str(text).strip()
        
        # Split text into words
        words = re.split(r'\s+', text)
        
        acronym_parts = []
        for word in words:
            if re.match(r'^\d+$', word):
                # Pure number, keep as is
                acronym_parts.append(word)
            elif re.search(r'\d', word):
                # Word contains numbers, extract letters and numbers separately
                letters = re.sub(r'\d+', '', word)
                numbers = ''.join(re.findall(r'\d+', word))
                if letters:
                    acronym_parts.append(letters[0] + numbers)
                else:
                    acronym_parts.append(numbers)
            else:
                # Pure text, take first letter
                if word:
                    acronym_parts.append(word[0])
        
        return ''.join(acronym_parts)

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