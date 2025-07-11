// Table Flattening Module
console.log('🚀 Loading flatten.js...');

// Get table data from global storage
function getTableDataFromResult(resultIndex) {
    return window.AppConfig.globalTableData[resultIndex] || null;
}

// Store table data in global storage
function storeTableData(resultIndex, tableInfo, filename, featureRows = [], featureCols = []) {
    window.AppConfig.globalTableData[resultIndex] = {
        ...tableInfo,
        filename: filename,
        feature_rows: featureRows,
        feature_cols: featureCols
    };
}

// Store backend metadata for plotting
function storeBackendMetadata(resultIndex, metadata) {
    if (!window.AppConfig.globalTableData[resultIndex]) {
        window.AppConfig.globalTableData[resultIndex] = {};
    }
    window.AppConfig.globalTableData[resultIndex].backend_metadata = metadata;
}

// Create flattened table data based on flatten level
function createFlattenedTableData(originalTableInfo, flattenLevel) {
    // Debug logging for main function entry
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.logForLevel(flattenLevel, 'MAIN_FUNCTION', `createFlattenedTableData called with level ${flattenLevel}`);
        window.FlattenDebugLogger.logTableStructure(originalTableInfo, `Input to createFlattenedTableData level ${flattenLevel}`, flattenLevel);
    }
    
    if (!originalTableInfo.has_multiindex || !originalTableInfo.header_matrix) {
        if (window.FlattenDebugLogger) {
            window.FlattenDebugLogger.logForLevel(flattenLevel, 'EARLY_RETURN', 'No multiindex or header matrix, returning original');
        }
        return originalTableInfo;
    }

    const totalLevels = originalTableInfo.header_matrix.length;

    // Level 0 means no flattening (original hierarchical)
    if (flattenLevel <= 0) {
        if (window.FlattenDebugLogger) {
            window.FlattenDebugLogger.logForLevel(flattenLevel, 'NO_FLATTENING', `Level ${flattenLevel} <= 0, returning original table`);
        }
        return originalTableInfo;
    }

    // ALL flattening levels use the same normal table logic
    // flattenLevel 1 = combine first 2 levels (0+1)
    // flattenLevel 2 = combine first 3 levels (0+1+2), etc.
    // flattenLevel >= totalLevels-1 = combine ALL levels (normal table result)
    if (window.FlattenDebugLogger) {
        if (flattenLevel >= totalLevels - 1) {
            window.FlattenDebugLogger.logForLevel(flattenLevel, 'ALL_LEVELS_FLATTENING', `Level ${flattenLevel} >= ${totalLevels - 1}, combining all ${totalLevels} levels using normal table logic`);
        } else {
            window.FlattenDebugLogger.logForLevel(flattenLevel, 'PARTIAL_FLATTENING', `Level ${flattenLevel}, combining first ${flattenLevel + 1} levels`);
        }
    }
    const result = createPartiallyFlattenedTable(originalTableInfo, flattenLevel);
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.logTableStructure(result, `Flattening result for level ${flattenLevel}`, flattenLevel);
    }
    return result;
}

// Port of backend's calculate_rowspan function
function calculateRowspan(multiindexColumns, level, position, currentValue) {
    const nLevels = multiindexColumns.length;
    
    if (level === nLevels - 1) {
        return 1; // Last level, no spanning
    }
    
    // Check if all lower levels are "Header" for this position
    let allLowerAreHeaders = true;
    for (let lowerLevel = level + 1; lowerLevel < nLevels; lowerLevel++) {
        const lowerValue = getLevelValue(multiindexColumns, lowerLevel, position);
        const lowerValueStr = lowerValue ? String(lowerValue) : "";
        
        if (lowerValueStr !== "Header") {
            allLowerAreHeaders = false;
            break;
        }
    }
    
    if (allLowerAreHeaders) {
        return nLevels - level; // Span to the bottom
    } else {
        return 1; // No spanning
    }
}

// Port of backend's calculate_intelligent_colspan function
function calculateIntelligentColspan(multiindexColumns, level, startPosition, currentValueStr, coveredPositions) {
    const nLevels = multiindexColumns.length;
    const nCols = multiindexColumns[0] ? multiindexColumns[0].length : 0;
    
    if (level === nLevels - 1) {
        return 1; // Last level, no horizontal spanning
    }
    
    // Count consecutive identical values
    let consecutiveEnd = startPosition + 1;
    while (consecutiveEnd < nCols && 
           String(getLevelValue(multiindexColumns, level, consecutiveEnd)) === currentValueStr &&
           !coveredPositions.has(`${level},${consecutiveEnd}`)) {
        consecutiveEnd++;
    }
    
    const potentialColspan = consecutiveEnd - startPosition;
    
    if (potentialColspan === 1) {
        return 1; // No consecutive identical values
    }
    
    // Check if the lower levels have varied content that would justify merging
    let lowerLevelsVary = false;
    
    for (let lowerLevel = level + 1; lowerLevel < nLevels; lowerLevel++) {
        const firstLowerValue = String(getLevelValue(multiindexColumns, lowerLevel, startPosition));
        
        for (let pos = startPosition + 1; pos < consecutiveEnd; pos++) {
            if (String(getLevelValue(multiindexColumns, lowerLevel, pos)) !== firstLowerValue) {
                lowerLevelsVary = true;
                break;
            }
        }
        
        if (lowerLevelsVary) {
            break;
        }
    }
    
    // Only merge if lower levels vary OR if all lower levels are "Header"
    if (lowerLevelsVary) {
        return potentialColspan;
    } else {
        // Check if all lower levels are "Header" (empty placeholders)
        let allLowerAreHeaders = true;
        for (let lowerLevel = level + 1; lowerLevel < nLevels; lowerLevel++) {
            for (let pos = startPosition; pos < consecutiveEnd; pos++) {
                const lowerValStr = String(getLevelValue(multiindexColumns, lowerLevel, pos));
                if (lowerValStr !== "Header") {
                    allLowerAreHeaders = false;
                    break;
                }
            }
            if (!allLowerAreHeaders) {
                break;
            }
        }
        
        if (allLowerAreHeaders) {
            return potentialColspan; // Merge over empty placeholders
        } else {
            return 1; // Don't merge identical cells that are actually separate
        }
    }
}

// Helper function to get level value from multiindex structure
function getLevelValue(multiindexColumns, level, position) {
    if (!multiindexColumns[level] || position >= multiindexColumns[level].length) {
        return null;
    }
    return multiindexColumns[level][position];
}

// Convert original header matrix to multiindex columns format for algorithm
function convertToMultiindexColumns(originalHeaderMatrix, colCount) {
    const nLevels = originalHeaderMatrix.length;
    const multiindexColumns = [];
    
    // Initialize levels with null values
    for (let level = 0; level < nLevels; level++) {
        multiindexColumns.push(new Array(colCount).fill(null));
    }
    
    // Debug logging
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('CONVERSION_START', 'Starting convertToMultiindexColumns', {
            originalHeaderMatrix: originalHeaderMatrix,
            colCount: colCount,
            nLevels: nLevels
        });
    }
    
    // Fill values respecting both colspan and rowspan
    // Process in level order to ensure proper priority
    for (let level = 0; level < nLevels; level++) {
        const levelHeaders = originalHeaderMatrix[level];
        
        if (window.FlattenDebugLogger) {
            window.FlattenDebugLogger.log('LEVEL_PROCESSING', `Processing level ${level}`, {
                level: level,
                headers: levelHeaders
            });
        }
        
        for (const header of levelHeaders) {
            const startPos = header.position;
            const endPos = startPos + header.colspan;
            
            if (window.FlattenDebugLogger) {
                window.FlattenDebugLogger.log('HEADER_PROCESSING', `Processing header "${header.text}"`, {
                    header: header,
                    startPos: startPos,
                    endPos: endPos,
                    level: level
                });
            }
            
            // Fill this header's text in its own level and mark the cells it vertically
            // spans in lower levels with the special placeholder "Header"
            for (let pos = startPos; pos < endPos && pos < colCount; pos++) {
                for (let spanLevel = level; spanLevel < level + header.rowspan && spanLevel < nLevels; spanLevel++) {
                    const isTopMost = spanLevel === level;
                    const valueToWrite = isTopMost ? header.text : "Header";

                    // Only write if the position is null/empty or we're writing the actual text
                    // This ensures that actual header text takes priority over "Header" placeholders
                    const currentVal = multiindexColumns[spanLevel][pos];
                    const shouldWrite = currentVal === null || currentVal === undefined || currentVal === '' || 
                                       (isTopMost && currentVal === "Header");
                    
                    if (shouldWrite) {
                        multiindexColumns[spanLevel][pos] = valueToWrite;
                        
                        if (window.FlattenDebugLogger) {
                            window.FlattenDebugLogger.log('CELL_WRITE', `Writing to [${spanLevel}][${pos}]`, {
                                level: spanLevel,
                                position: pos,
                                value: valueToWrite,
                                isTopMost: isTopMost,
                                originalValue: currentVal
                            });
                        }
                    }
                }
            }
        }
    }
    
    // Debug: log the final multiindex structure
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('CONVERSION_RESULT', 'Final multiindex columns structure', {
            multiindexColumns: multiindexColumns,
            structure: multiindexColumns.map((level, idx) => ({
                level: idx,
                values: level
            }))
        });
        
        // Also log column-by-column breakdown for debugging
        for (let col = 0; col < colCount; col++) {
            const columnValues = multiindexColumns.map(level => level[col]);
            window.FlattenDebugLogger.log('COLUMN_BREAKDOWN', `Column ${col} values`, {
                column: col,
                values: columnValues
            });
        }
    }
    
    return multiindexColumns;
}

// Port of backend's build_header_matrix function for specific flatten level
function buildHeaderMatrixForLevel(originalTableInfo, flattenLevel) {
    const { header_matrix, col_count } = originalTableInfo;
    const nLevels = header_matrix.length;
    const nCols = col_count;
    
    // Convert to multiindex format for algorithm
    const multiindexColumns = convertToMultiindexColumns(header_matrix, nCols);
    
    // Determine how many levels to combine
    // flattenLevel 1 = combine first 2 levels (levels 0+1)
    // flattenLevel 2 = combine first 3 levels (levels 0+1+2), etc.
    const levelsToCombine = flattenLevel + 1;
    
    // Build combined names for flattened levels (0 to levelsToCombine-1 inclusive)
    const combinedNames = [];
    
    // Debug logging for partial flattening setup
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.logPartialFlattening(flattenLevel, levelsToCombine, nLevels, [], []);
    }
    
    for (let colIndex = 0; colIndex < nCols; colIndex++) {
        const parts = [];
        
        // Extract parts from the multiindex columns structure
        for (let lvl = 0; lvl < levelsToCombine && lvl < nLevels; lvl++) {
            const value = getLevelValue(multiindexColumns, lvl, colIndex);
            if (value && value !== null && value !== undefined) {
                parts.push(String(value));
            }
        }
        
        // Debug log the extracted parts for this column
        if (window.FlattenDebugLogger) {
            window.FlattenDebugLogger.log('COLUMN_PARTS_EXTRACTION', `Column ${colIndex} parts extraction`, {
                column: colIndex,
                levelsToCombine: levelsToCombine,
                extractedParts: parts,
                multiindexColumn: multiindexColumns.map(level => level[colIndex])
            });
        }
        
        // Apply backend flattening logic exactly as in the backend, but first
        // eliminate empty placeholders and then collapse consecutive duplicates
        // that originate from vertical row-span propagation (e.g. ["Tên", "Tên"]).
        const filtered = parts.filter(p => p && p !== 'Header' && p !== 'nan' && p.trim() !== '');
        const meaningfulParts = [];
        for (const part of filtered) {
            if (meaningfulParts.length === 0 || meaningfulParts[meaningfulParts.length - 1] !== part) {
                meaningfulParts.push(part);
            }
        }
        
        let combined;
        if (meaningfulParts.length === 0) {
            combined = 'Column';
        } else if (meaningfulParts.length === 1) {
            // Only one meaningful part (vertical merge case), use as is
            combined = meaningfulParts[0];
        } else {
            // Multiple meaningful parts (horizontal merge case)
            // Create acronyms for all parts EXCEPT the last one (leaf level)
            const acronymParts = [];
            for (let i = 0; i < meaningfulParts.length - 1; i++) {
                const acronym = createAcronym(meaningfulParts[i]);
                // Debug log acronym generation
                if (window.FlattenDebugLogger) {
                    window.FlattenDebugLogger.logAcronymGeneration(meaningfulParts[i], acronym, flattenLevel);
                }
                acronymParts.push(acronym);
            }
            // Keep the last part (leaf level) as-is
            acronymParts.push(meaningfulParts[meaningfulParts.length - 1]);
            combined = acronymParts.join(' ');
        }
        
        // Debug log column combination
        if (window.FlattenDebugLogger) {
            window.FlattenDebugLogger.logColumnCombination(colIndex, parts, meaningfulParts, combined, flattenLevel);
        }
        
        combinedNames.push(combined);
    }
    
    // Create new multiindex structure with combined level + remaining levels
    const newMultiindexColumns = [];
    
    // Level 0: combined names
    newMultiindexColumns.push(combinedNames);
    
    // Remaining levels (levelsToCombine onwards)
    for (let level = levelsToCombine; level < nLevels; level++) {
        newMultiindexColumns.push(multiindexColumns[level]);
    }
    
    const newNLevels = newMultiindexColumns.length;
    
    // Debug log the new structure before building header matrix
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('NEW_MULTIINDEX_STRUCTURE', 'New multiindex structure created', {
            combinedNames: combinedNames,
            newMultiindexColumns: newMultiindexColumns,
            newNLevels: newNLevels
        });
    }
    
    // Now apply the backend's two-pass algorithm
    
    // First pass: calculate all rowspans
    const rowspanMatrix = [];
    for (let level = 0; level < newNLevels; level++) {
        const levelRowspans = [];
        for (let i = 0; i < nCols; i++) {
            const currentValue = getLevelValue(newMultiindexColumns, level, i);
            const currentValueStr = currentValue ? String(currentValue) : "";
            const rowspan = calculateRowspan(newMultiindexColumns, level, i, currentValueStr);
            levelRowspans.push(rowspan);
        }
        rowspanMatrix.push(levelRowspans);
    }
    
    // Second pass: build header matrix, skipping cells covered by rowspan
    const newHeaderMatrix = [];
    const coveredPositions = new Set(); // Track positions covered by rowspan from previous levels
    
    for (let level = 0; level < newNLevels; level++) {
        const levelHeaders = [];
        
        let i = 0;
        while (i < nCols) {
            // Skip positions covered by rowspan from previous levels
            if (coveredPositions.has(`${level},${i}`)) {
                i++;
                continue;
            }
            
            const currentValue = getLevelValue(newMultiindexColumns, level, i);
            const currentValueStr = currentValue ? String(currentValue) : "";
            
            // Calculate intelligent colspan
            const colspan = calculateIntelligentColspan(newMultiindexColumns, level, i, currentValueStr, coveredPositions);
            
            // Get rowspan from pre-calculated matrix
            const rowspan = rowspanMatrix[level][i];
            
            levelHeaders.push({
                text: currentValueStr,
                colspan: colspan,
                rowspan: rowspan,
                position: i,
                level: level
            });
            
            // Mark positions as covered by this cell's rowspan
            for (let r = level + 1; r < level + rowspan; r++) {
                for (let c = i; c < i + colspan; c++) {
                    if (r < newNLevels) {
                        coveredPositions.add(`${r},${c}`);
                    }
                }
            }
            
            i += colspan;
        }
        
        newHeaderMatrix.push(levelHeaders);
    }
    
    // Debug log the final header matrix
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('FINAL_HEADER_MATRIX', 'Final header matrix built', {
            newHeaderMatrix: newHeaderMatrix,
            rowspanMatrix: rowspanMatrix,
            flattenLevel: flattenLevel
        });
    }
    
    // Determine the correct final_columns based on flattening level
    let finalColumns;
    if (newNLevels === 1) {
        // Completely flattened: use the combined names as final columns
        finalColumns = combinedNames;
    } else {
        // Still hierarchical: keep original final columns
        finalColumns = originalTableInfo.final_columns;
    }
    
    return {
        has_multiindex: newHeaderMatrix.length > 1,
        header_matrix: newHeaderMatrix,
        final_columns: finalColumns
    };
}

function createPartiallyFlattenedTable(originalTableInfo, flattenLevel) {
    // Use the proper header matrix building algorithm
    const result = buildHeaderMatrixForLevel(originalTableInfo, flattenLevel);
    
    return {
        ...originalTableInfo,
        has_multiindex: result.has_multiindex,
        header_matrix: result.header_matrix,
        final_columns: result.final_columns
    };
}



// Find header for specific column position
function findHeaderForColumn(level, columnIndex, levelIndex, headerMatrix) {
    // This function should find which header covers the given column at the given level
    // Priority: 
    // 1. If there's a header specifically at this level that covers this column, use it
    // 2. Otherwise, find a header from an upper level that spans down to this level
    
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('FIND_HEADER', `Finding header for column ${columnIndex} at level ${levelIndex}`, {
            levelIndex: levelIndex,
            columnIndex: columnIndex
        });
    }
    
    // First, check if there's a header at the exact target level
    if (levelIndex < headerMatrix.length) {
        const targetLevelHeaders = headerMatrix[levelIndex];
        
        for (const header of targetLevelHeaders) {
            const startPos = header.position;
            const endPos = header.position + header.colspan;
            
            if (columnIndex >= startPos && columnIndex < endPos) {
                if (window.FlattenDebugLogger) {
                    window.FlattenDebugLogger.log('HEADER_FOUND_EXACT', `Found exact header at level ${levelIndex}`, {
                        header: header,
                        level: levelIndex,
                        startPos: startPos,
                        endPos: endPos
                    });
                }
                return header;
            }
        }
    }
    
    // If no header found at exact level, look for spanning headers from upper levels
    for (let checkLevel = 0; checkLevel < levelIndex; checkLevel++) {
        const levelHeaders = headerMatrix[checkLevel];
        
        for (const header of levelHeaders) {
            const startPos = header.position;
            const endPos = header.position + header.colspan;
            const headerEndLevel = checkLevel + header.rowspan - 1;
            
            // Check if this header covers the column position horizontally AND spans to target level
            if (columnIndex >= startPos && columnIndex < endPos && headerEndLevel >= levelIndex) {
                if (window.FlattenDebugLogger) {
                    window.FlattenDebugLogger.log('HEADER_FOUND_SPANNING', `Found spanning header from level ${checkLevel}`, {
                        header: header,
                        checkLevel: checkLevel,
                        targetLevel: levelIndex,
                        startPos: startPos,
                        endPos: endPos,
                        headerEndLevel: headerEndLevel
                    });
                }
                return header;
            }
        }
    }
    
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.log('HEADER_NOT_FOUND', `No header found for column ${columnIndex} at level ${levelIndex}`, {
            columnIndex: columnIndex,
            levelIndex: levelIndex
        });
    }
    
    return null;
}

// Create acronym from text (matching backend logic exactly)
function createAcronym(text) {
    if (!text || typeof text !== 'string') return '';
    
    text = text.trim();
    
    // Split text into words
    const words = text.split(/\s+/);
    
    const acronymParts = [];
    for (const word of words) {
        if (/^\d+$/.test(word)) {
            // Pure number, keep as is
            acronymParts.push(word);
        } else if (/\d/.test(word)) {
            // Word contains numbers, extract letters and numbers separately
            const letters = word.replace(/\d+/g, '');
            const numbers = word.match(/\d+/g)?.join('') || '';
            if (letters) {
                acronymParts.push(letters.charAt(0) + numbers);
            } else {
                acronymParts.push(numbers);
            }
        } else {
            // Pure text, take first letter (preserving case)
            if (word) {
                acronymParts.push(word.charAt(0));
            }
        }
    }
    
    return acronymParts.join('');
}

// Debug helper function
function debugHeaders(resultIndex, level) {
    const tableData = getTableDataFromResult(resultIndex);
    if (!tableData) {
        console.log(`❌ No table data found for result index ${resultIndex}`);
        return;
    }
    
    const totalLevels = tableData.header_matrix.length;
    console.log(`🔍 Debug Headers for Result ${resultIndex}, Flatten Level ${level}`);
    console.log(`📊 Original table has ${totalLevels} levels`);
    
    if (level === 0) {
        console.log('🏗️ Level 0: No flattening (original hierarchical structure)');
    } else if (level >= totalLevels - 1) {
        console.log(`🔄 Level ${level}: All levels flattened (combining all ${totalLevels} levels)`);
    } else {
        console.log(`🔄 Level ${level}: Combining first ${level + 1} levels, leaving ${totalLevels - level - 1} levels hierarchical`);
    }
    
    console.log('Original header matrix:', tableData.header_matrix);
    
    if (level > 0) {
        const flattened = createFlattenedTableData(tableData, level);
        console.log('Flattened header matrix:', flattened.header_matrix);
        
        // Pretty print the matrix
        console.log('\n📋 Flattened Header Matrix Structure:');
        flattened.header_matrix.forEach((levelHeaders, levelIndex) => {
            console.log(`Level ${levelIndex}:`);
            levelHeaders.forEach(header => {
                console.log(`  [${header.position}] "${header.text}" (colspan: ${header.colspan}, rowspan: ${header.rowspan})`);
            });
        });
    }
}

// Test function to verify flatten logic with user's example
function testFlattenLogic() {
    console.log('🧪 Testing Flatten Logic with User Example');
    console.log('='.repeat(60));
    
    // Create mock table data matching user's example:
    // Level 1: Năm 2024
    //     Level 2: quý 1 -> tháng 1, tháng 2
    //     Level 2: Quý 2 -> tháng 4
    
    const mockTableData = {
        has_multiindex: true,
        header_matrix: [
            // Level 0
            [
                { text: "Năm 2024", colspan: 3, rowspan: 1, position: 0, level: 0 }
            ],
            // Level 1
            [
                { text: "quý 1", colspan: 2, rowspan: 1, position: 0, level: 1 },
                { text: "Quý 2", colspan: 1, rowspan: 1, position: 2, level: 1 }
            ],
            // Level 2
            [
                { text: "tháng 1", colspan: 1, rowspan: 1, position: 0, level: 2 },
                { text: "tháng 2", colspan: 1, rowspan: 1, position: 1, level: 2 },
                { text: "tháng 4", colspan: 1, rowspan: 1, position: 2, level: 2 }
            ]
        ],
        final_columns: ["tháng 1", "tháng 2", "tháng 4"],
        col_count: 3,
        row_count: 5,
        data_rows: [[100, 200, 300], [110, 210, 310], [120, 220, 320], [130, 230, 330], [140, 240, 340]]
    };
    
    console.log('\n🏗️ Level 0 (Original):');
    console.log('Expected: Năm 2024 -> quý 1 -> tháng 1, tháng 2; Năm 2024 -> Quý 2 -> tháng 4');
    const level0 = createFlattenedTableData(mockTableData, 0);
    console.log('Headers:', level0.final_columns);
    
    console.log('\n🔄 Level 1 (Combine first 2 levels):');
    console.log('Expected: "N2024 quý 1" -> tháng 1, tháng 2; "N2024 Quý 2" -> tháng 4');
    const level1 = createFlattenedTableData(mockTableData, 1);
    console.log('Headers:', level1.final_columns);
    console.log('Level 1 matrix:');
    level1.header_matrix.forEach((levelHeaders, i) => {
        console.log(`  Level ${i}:`, levelHeaders.map(h => `"${h.text}" (${h.colspan}c,${h.rowspan}r)`));
    });
    
    console.log('\n🔄 Level 2 (Combine all 3 levels):');
    console.log('Expected: "N2024 Q1 tháng 1", "N2024 Q1 tháng 2", "N2024 Q2 tháng 4"');
    const level2 = createFlattenedTableData(mockTableData, 2);
    console.log('Headers:', level2.final_columns);
    console.log('Level 2 matrix:');
    level2.header_matrix.forEach((levelHeaders, i) => {
        console.log(`  Level ${i}:`, levelHeaders.map(h => `"${h.text}" (${h.colspan}c,${h.rowspan}r)`));
    });
    
    console.log('\n✅ Test completed');
}

// Identify redundant feature columns (columns with only one unique value)
function identifyRedundantFeatureColumns(tableData) {
    console.log('🔍 identifyRedundantFeatureColumns called with:', {
        hasDataRows: !!tableData?.data_rows,
        hasFeatureRows: !!tableData?.feature_rows,
        featureRowsLength: tableData?.feature_rows?.length || 0,
        dataRowsLength: tableData?.data_rows?.length || 0,
        firstDataRow: tableData?.data_rows?.[0]
    });
    
    if (!tableData || !tableData.data_rows || !tableData.feature_rows) {
        console.log('❌ Missing required data for redundant column detection');
        return [];
    }
    
    const featureRowCount = tableData.feature_rows.length;
    const redundantColumns = [];
    
    console.log('📊 Analyzing feature columns:', tableData.feature_rows);
    
    // Analyze each feature column
    for (let colIndex = 0; colIndex < featureRowCount; colIndex++) {
        const uniqueValues = new Set();
        
        // Collect all values in this feature column
        tableData.data_rows.forEach(row => {
            const value = row[colIndex];
            if (value !== null && value !== undefined && value !== '') {
                uniqueValues.add(String(value).trim());
            }
        });
        
        console.log(`🔍 Column ${colIndex} (${tableData.feature_rows[colIndex]}):`, {
            uniqueValues: Array.from(uniqueValues),
            uniqueCount: uniqueValues.size
        });
        
        // If only one unique value (or all empty), mark as redundant
        if (uniqueValues.size <= 1) {
            const redundantCol = {
                index: colIndex,
                uniqueValue: uniqueValues.size === 1 ? Array.from(uniqueValues)[0] : '',
                featureName: tableData.feature_rows[colIndex] || `Column ${colIndex}`
            };
            redundantColumns.push(redundantCol);
            console.log('🚫 Marked as redundant:', redundantCol);
        }
    }
    
    console.log('✅ Total redundant columns found:', redundantColumns.length);
    return redundantColumns;
}

// Filter table data to hide redundant feature columns
function filterTableDataByRedundantColumns(tableData, hideRedundantColumns = true) {
    console.log('🧹 filterTableDataByRedundantColumns called:', {
        hasTableData: !!tableData,
        hideRedundantColumns: hideRedundantColumns,
        hasMultiindex: tableData?.has_multiindex,
        colCount: tableData?.col_count,
        headerMatrixLength: tableData?.header_matrix?.length
    });
    
    if (!tableData || !hideRedundantColumns) {
        console.log('⏭️ Skipping redundant column filtering');
        return tableData;
    }
    
    const redundantColumns = identifyRedundantFeatureColumns(tableData);
    if (redundantColumns.length === 0) {
        console.log('✅ No redundant columns found, returning original data');
        return tableData;
    }
    
    console.log('🚫 Found redundant columns:', redundantColumns);
    const redundantIndices = redundantColumns.map(col => col.index);
    console.log('📍 Redundant indices to remove:', redundantIndices);
    
    // Filter feature_rows array
    const filteredFeatureRows = tableData.feature_rows.filter((_, index) => 
        !redundantIndices.includes(index)
    );
    console.log('📋 Original feature_rows:', tableData.feature_rows);
    console.log('📋 Filtered feature_rows:', filteredFeatureRows);
    
    // Filter data_rows by removing redundant columns
    const filteredDataRows = tableData.data_rows.map(row => 
        row.filter((_, index) => !redundantIndices.includes(index))
    );
    console.log('📊 Original first data row:', tableData.data_rows[0]);
    console.log('📊 Filtered first data row:', filteredDataRows[0]);
    
    // Update header_matrix to reflect removed columns
    let filteredHeaderMatrix = tableData.header_matrix;
    if (tableData.header_matrix && redundantIndices.length > 0) {
        console.log('🔄 Updating header matrix...');
        filteredHeaderMatrix = updateHeaderMatrixAfterColumnRemoval(tableData.header_matrix, redundantIndices);
        console.log('📋 Original header matrix:', tableData.header_matrix);
        console.log('📋 Filtered header matrix:', filteredHeaderMatrix);
        
        // 🔧 FIX: If header matrix became empty but we still have columns, rebuild it
        const hasEmptyLevels = filteredHeaderMatrix.some(level => level.length === 0);
        if (hasEmptyLevels && filteredFinalColumns.length > 0) {
            console.log('🔧 [REBUILD] Header matrix has empty levels, rebuilding from final_columns...');
            console.log(`  - final_columns to use: [${filteredFinalColumns.join(', ')}]`);
            
            // Rebuild header matrix with single level containing all remaining columns
            filteredHeaderMatrix = [filteredFinalColumns.map((col, index) => ({
                text: col,
                colspan: 1,
                rowspan: 1,
                position: index,
                level: 0
            }))];
            
            console.log('🔧 [REBUILD] Rebuilt header matrix:', filteredHeaderMatrix);
        }
    }
    
    // Filter final_columns consistently for all table types
    let filteredFinalColumns = tableData.final_columns;
    if (tableData.final_columns && tableData.final_columns.length > 0) {
        console.log('🔄 Filtering final_columns...');
        filteredFinalColumns = tableData.final_columns.filter((_, index) => 
            !redundantIndices.includes(index)
        );
        console.log('📋 Original final_columns:', tableData.final_columns);
        console.log('📋 Filtered final_columns:', filteredFinalColumns);
    }
    
    const result = {
        ...tableData,
        feature_rows: filteredFeatureRows,
        data_rows: filteredDataRows,
        final_columns: filteredFinalColumns,
        header_matrix: filteredHeaderMatrix,
        col_count: filteredDataRows.length > 0 ? filteredDataRows[0].length : 0,
        redundant_columns_hidden: redundantColumns.length,
        hidden_redundant_columns: redundantColumns
    };
    
    console.log('✅ Filtered table data result:', result);
    return result;
}

// Update header matrix after column removal
function updateHeaderMatrixAfterColumnRemoval(headerMatrix, removedIndices) {
    if (!headerMatrix || removedIndices.length === 0) {
        return headerMatrix;
    }
    
    console.log(`🔧 [HEADER_MATRIX_UPDATE] Updating header matrix after column removal:`);
    console.log(`  - Original matrix levels: ${headerMatrix.length}`);
    console.log(`  - Removed indices: [${removedIndices.join(', ')}]`);
    
    // Sort removed indices in descending order to avoid position shifting issues
    const sortedRemovedIndices = [...removedIndices].sort((a, b) => b - a);
    
    const updatedMatrix = headerMatrix.map((level, levelIdx) => {
        const updatedLevel = [];
        
        level.forEach(header => {
            const startPos = header.position;
            const endPos = startPos + header.colspan;
            
            // Check how many removed columns affect this header
            let removedCount = 0;
            let newStartPos = startPos;
            
            // Count removed columns before this header's start position
            for (const removedIndex of sortedRemovedIndices) {
                if (removedIndex < startPos) {
                    newStartPos--;
                } else if (removedIndex >= startPos && removedIndex < endPos) {
                    removedCount++;
                }
            }
            
            // Only include this header if it still spans some columns after removal
            const newColspan = header.colspan - removedCount;
            if (newColspan > 0) {
                updatedLevel.push({
                    ...header,
                    position: newStartPos,
                    colspan: newColspan
                });
            }
        });
        
        console.log(`  - Level ${levelIdx}: ${level.length} → ${updatedLevel.length} headers`);
        return updatedLevel;
    });
    
    // 🔧 FIX: Check if any level became empty after filtering
    const hasEmptyLevels = updatedMatrix.some(level => level.length === 0);
    
    if (hasEmptyLevels) {
        console.log(`⚠️ [HEADER_MATRIX_UPDATE] Some levels became empty after filtering!`);
        console.log(`  - Matrix before fix:`, updatedMatrix.map(level => level.length));
        
        // If we have empty levels, we need to rebuild the matrix
        // This can happen when all headers in a level are completely removed
        
        // Calculate the number of remaining columns
        const totalRemovedCols = removedIndices.length;
        let originalColCount = 0;
        if (headerMatrix.length > 0 && headerMatrix[0].length > 0) {
            // Find the maximum position + colspan in the original matrix
            originalColCount = Math.max(...headerMatrix.flat().map(h => h.position + h.colspan));
        }
        const remainingColCount = originalColCount - totalRemovedCols;
        
        console.log(`  - Original columns: ${originalColCount}, Remaining: ${remainingColCount}`);
        
        if (remainingColCount > 0) {
            // Filter out empty levels and rebuild positions
            const nonEmptyLevels = updatedMatrix.filter(level => level.length > 0);
            
            if (nonEmptyLevels.length === 0) {
                console.log(`  - All levels empty, creating minimal single-level matrix`);
                // If all levels are empty, create a minimal structure
                // This will be fixed later when we know the actual final_columns
                return [[]]; // Return empty but valid structure
            } else {
                console.log(`  - Using ${nonEmptyLevels.length} non-empty levels`);
                return nonEmptyLevels;
            }
        } else {
            console.log(`  - No remaining columns, returning empty structure`);
            return [[]]; // Return empty but valid structure
        }
    }
    
    console.log(`✅ [HEADER_MATRIX_UPDATE] Updated matrix:`, updatedMatrix.map(level => level.length));
    return updatedMatrix;
}

// Identify NaN rows (rows where all data columns are null/undefined)
function identifyNaNRows(tableData) {
    if (!tableData || !tableData.data_rows || !tableData.feature_rows) {
        return [];
    }
    
    const featureRowCount = tableData.feature_rows.length;
    const nanRows = [];
    

    
    tableData.data_rows.forEach((row, rowIndex) => {
        // Only check columns beyond the feature row columns
        const dataColumns = row.slice(featureRowCount);

        
        // Check if all data columns are null, undefined, empty string, or "—"
        const isNaNRow = dataColumns.every(cell => 
            cell === null || 
            cell === undefined || 
            cell === '' || 
            cell === '—' ||
            (typeof cell === 'string' && cell.trim() === '') ||
            (typeof cell === 'number' && isNaN(cell))
        );
        
        if (isNaNRow) {
            nanRows.push(rowIndex);
        }
    });
    
    return nanRows;
}

// Filter table data to hide/show NaN rows
function filterTableDataByNaNRows(tableData, hideNaNRows = true) {
    if (!tableData || !hideNaNRows) {
        return tableData;
    }
    
    const nanRows = identifyNaNRows(tableData);
    if (nanRows.length === 0) {
        return tableData;
    }
    
    // Filter out NaN rows
    const filteredDataRows = tableData.data_rows.filter((row, index) => 
        !nanRows.includes(index)
    );
    
    return {
        ...tableData,
        data_rows: filteredDataRows,
        row_count: filteredDataRows.length,
        nan_rows_hidden: nanRows.length,
        original_row_count: tableData.data_rows.length
    };
}

// Export flattening functions
window.FlattenManager = {
    getTableDataFromResult,
    storeTableData,
    storeBackendMetadata,
    createFlattenedTableData,
    findHeaderForColumn,
    createAcronym,
    debugHeaders,
    testFlattenLogic,
    // Internal functions for debugging
    convertToMultiindexColumns,
    buildHeaderMatrixForLevel,
    getLevelValue,
    calculateRowspan,
    calculateIntelligentColspan,
    // New debug functions
    testMultiindexConversion,
    analyzeColumnStructure,
    // NaN row handling functions
    identifyNaNRows,
    filterTableDataByNaNRows,
    // Redundant feature column handling functions
    identifyRedundantFeatureColumns,
    filterTableDataByRedundantColumns,
    updateHeaderMatrixAfterColumnRemoval,
    // Debug function
    debugRedundantColumns
};

// Test multiindex conversion specifically
function testMultiindexConversion(resultIndex) {
    const tableData = getTableDataFromResult(resultIndex);
    if (!tableData) {
        console.log(`❌ No table data found for result index ${resultIndex}`);
        return;
    }
    
    console.log('🧪 Testing Multiindex Conversion for Result', resultIndex);
    console.log('Original header matrix:', tableData.header_matrix);
    
    const multiindexColumns = convertToMultiindexColumns(tableData.header_matrix, tableData.col_count);
    console.log('Converted multiindex columns:', multiindexColumns);
    
    // Analyze each column
    for (let col = 0; col < tableData.col_count; col++) {
        const columnValues = multiindexColumns.map(level => level[col]);
        console.log(`Column ${col}:`, columnValues);
    }
    
    return multiindexColumns;
}

// Analyze expected vs actual column structure
function analyzeColumnStructure(resultIndex) {
    const tableData = getTableDataFromResult(resultIndex);
    if (!tableData) {
        console.log(`❌ No table data found for result index ${resultIndex}`);
        return;
    }
    
    console.log('🔍 Analyzing Column Structure for Result', resultIndex);
    console.log('='.repeat(80));
    
    const headerMatrix = tableData.header_matrix;
    const colCount = tableData.col_count;
    
    console.log(`📊 Table has ${headerMatrix.length} levels and ${colCount} columns`);
    
    // Print header matrix structure
    console.log('\n📋 Header Matrix Structure:');
    headerMatrix.forEach((levelHeaders, levelIndex) => {
        console.log(`Level ${levelIndex}:`);
        levelHeaders.forEach(header => {
            const endPos = header.position + header.colspan;
            const endLevel = levelIndex + header.rowspan;
            console.log(`  "${header.text}" covers cols [${header.position}-${endPos-1}], levels [${levelIndex}-${endLevel-1}]`);
        });
    });
    
    // Analyze what each column should get at each level
    console.log('\n🎯 Expected Column Structure:');
    for (let col = 0; col < colCount; col++) {
        const columnTuple = [];
        console.log(`\nColumn ${col}:`);
        
        for (let level = 0; level < headerMatrix.length; level++) {
            const header = findHeaderForColumn(headerMatrix[level], col, level, headerMatrix);
            if (header) {
                columnTuple.push(header.text);
                console.log(`  Level ${level}: "${header.text}" (from level ${header.level || 'unknown'})`);
            } else {
                console.log(`  Level ${level}: NO HEADER FOUND`);
            }
        }
        
        console.log(`  Full tuple: [${columnTuple.join(', ')}]`);
    }
    
    // Test all-level flattening using normal table logic
    console.log('\n🔄 Testing All-Level Flattening:');
    const totalLevels = tableData.header_matrix.length;
    const flattened = createFlattenedTableData(tableData, totalLevels - 1);
    console.log('Final columns:', flattened.final_columns);
    
    return {
        headerMatrix: headerMatrix,
        expectedStructure: 'See console output above',
        flattenedColumns: flattened.final_columns
    };
}

// Debug function to test redundant column filtering
function debugRedundantColumns(resultIndex) {
    console.log('🔍 Debug Redundant Columns for Result', resultIndex);
    console.log('='.repeat(60));
    
    const tableData = getTableDataFromResult(resultIndex);
    if (!tableData) {
        console.log('❌ No table data found');
        return;
    }
    
    console.log('📊 Original Table Data:');
    console.log('- Feature rows:', tableData.feature_rows);
    console.log('- Data rows count:', tableData.data_rows.length);
    console.log('- Column count:', tableData.col_count);
    console.log('- First few data rows:');
    tableData.data_rows.slice(0, 3).forEach((row, i) => {
        console.log(`  Row ${i}:`, row);
    });
    
    console.log('\n🔍 Analyzing redundant columns:');
    const redundantColumns = identifyRedundantFeatureColumns(tableData);
    console.log('- Redundant columns found:', redundantColumns);
    
    if (redundantColumns.length > 0) {
        console.log('\n🧹 Filtered Table Data:');
        const filteredData = filterTableDataByRedundantColumns(tableData, true);
        console.log('- Filtered feature rows:', filteredData.feature_rows);
        console.log('- Filtered data rows count:', filteredData.data_rows.length);
        console.log('- Filtered column count:', filteredData.col_count);
        console.log('- First few filtered data rows:');
        filteredData.data_rows.slice(0, 3).forEach((row, i) => {
            console.log(`  Row ${i}:`, row);
        });
        
        console.log('\n📋 Header Matrix Comparison:');
        console.log('- Original header matrix:', tableData.header_matrix);
        console.log('- Filtered header matrix:', filteredData.header_matrix);
    }
    
    console.log('\n✅ Debug completed');
}

console.log('✅ Flatten.js loaded'); 