// Flatten Debug Logger
// Comprehensive logging system to debug flattening issues with real data

class FlattenDebugLogger {
    constructor() {
        this.debugMode = true;
        this.logs = [];
        this.sessionId = Date.now();
        this.levelLogs = {}; // Store logs separated by flatten level
    }

    log(category, message, data = null) {
        if (!this.debugMode) return;
        
        const logEntry = {
            timestamp: new Date().toISOString(),
            category: category,
            message: message,
            data: data ? JSON.parse(JSON.stringify(data)) : null
        };
        
        this.logs.push(logEntry);
        console.log(`[FLATTEN-DEBUG] ${category}: ${message}`, data || '');
    }

    // Log and save data specific to a flatten level
    logForLevel(flattenLevel, category, message, data = null) {
        if (!this.debugMode) return;
        
        const logEntry = {
            timestamp: new Date().toISOString(),
            category: category,
            message: message,
            data: data ? JSON.parse(JSON.stringify(data)) : null
        };
        
        // Initialize level logs if not exists
        if (!this.levelLogs[flattenLevel]) {
            this.levelLogs[flattenLevel] = {
                level: flattenLevel,
                session_id: this.sessionId,
                logs: []
            };
        }
        
        this.levelLogs[flattenLevel].logs.push(logEntry);
        this.logs.push({ ...logEntry, flatten_level: flattenLevel });
        
        console.log(`[FLATTEN-DEBUG-L${flattenLevel}] ${category}: ${message}`, data || '');
        
        // Auto-save disabled - use saveAllLevelDebugData() or saveLevelDebugToFile() manually if needed
        // if (this.levelLogs[flattenLevel].logs.length > 0) {
        //     this.saveLevelDebugToFile(flattenLevel);
        // }
    }

    // Save debug data for a specific level to file
    saveLevelDebugToFile(flattenLevel) {
        if (!this.levelLogs[flattenLevel] || this.levelLogs[flattenLevel].logs.length === 0) {
            return;
        }

        const filename = `level${flattenLevel}.json`;
        const debugData = {
            ...this.levelLogs[flattenLevel],
            export_time: new Date().toISOString(),
            total_logs: this.levelLogs[flattenLevel].logs.length
        };

        // Use the file saving utility from Utils
        if (window.Utils && window.Utils.saveJsonToFile) {
            window.Utils.saveJsonToFile(debugData, filename);
        } else {
            console.warn('⚠️ Utils.saveJsonToFile not available, falling back to console export');
            console.log(`Debug data for level ${flattenLevel}:`, debugData);
        }
    }

    logTableStructure(tableInfo, description = "Table Structure", flattenLevel = null) {
        const data = {
            has_multiindex: tableInfo.has_multiindex,
            col_count: tableInfo.col_count,
            row_count: tableInfo.row_count,
            header_matrix_levels: tableInfo.header_matrix.length,
            final_columns_count: tableInfo.final_columns.length,
            final_columns: tableInfo.final_columns,
            header_matrix: tableInfo.header_matrix.map((level, levelIndex) => ({
                level: levelIndex,
                headers: level.map(h => ({
                    text: h.text,
                    colspan: h.colspan,
                    rowspan: h.rowspan,
                    position: h.position
                }))
            }))
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'TABLE_STRUCTURE', description, data);
        } else {
            this.log('TABLE_STRUCTURE', description, data);
        }
    }

    logFlattenOperation(originalTable, flattenLevel, result) {
        const data = {
            input: {
                original_levels: originalTable.header_matrix.length,
                original_has_multiindex: originalTable.has_multiindex,
                original_col_count: originalTable.col_count,
                original_final_columns: originalTable.final_columns
            },
            operation: {
                flatten_level: flattenLevel,
                operation_type: this.determineFlattenType(originalTable, flattenLevel)
            },
            output: {
                result_levels: result.header_matrix.length,
                result_has_multiindex: result.has_multiindex,
                result_col_count: result.col_count,
                result_final_columns: result.final_columns
            }
        };

        this.logForLevel(flattenLevel, 'FLATTEN_OPERATION', `Flatten Level ${flattenLevel} Operation`, data);
    }

    determineFlattenType(originalTable, flattenLevel) {
        const totalLevels = originalTable.header_matrix.length;
        if (flattenLevel <= 0) return "NO_FLATTENING";
        if (flattenLevel >= totalLevels - 1) return "COMPLETE_FLATTENING";
        return "PARTIAL_FLATTENING";
    }

    logMultiindexConversion(originalHeaderMatrix, multiindexColumns, colCount, flattenLevel = null) {
        const data = {
            input_levels: originalHeaderMatrix.length,
            col_count: colCount,
            original_structure: originalHeaderMatrix.map((level, idx) => ({
                level: idx,
                headers: level.map(h => `"${h.text}"(${h.colspan}c,${h.rowspan}r)`)
            })),
            converted_structure: multiindexColumns.map((level, idx) => ({
                level: idx,
                values: level
            }))
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'MULTIINDEX_CONVERSION', 'Converting header matrix to multiindex columns', data);
        } else {
            this.log('MULTIINDEX_CONVERSION', 'Converting header matrix to multiindex columns', data);
        }
    }

    logPartialFlattening(flattenLevel, levelsToCombine, originalLevels, combinedNames, newMultiindexColumns) {
        const data = {
            flatten_level: flattenLevel,
            levels_to_combine: levelsToCombine,
            original_levels: originalLevels,
            combined_names: combinedNames,
            new_structure_levels: newMultiindexColumns.length,
            new_multiindex_structure: newMultiindexColumns.map((level, idx) => ({
                level: idx,
                values: level
            }))
        };

        this.logForLevel(flattenLevel, 'PARTIAL_FLATTENING', `Partial flattening level ${flattenLevel}`, data);
    }

    logColumnCombination(colIndex, parts, meaningfulParts, finalName, flattenLevel = null) {
        const data = {
            column_index: colIndex,
            raw_parts: parts,
            meaningful_parts: meaningfulParts,
            final_combined_name: finalName,
            combination_logic: meaningfulParts.length === 0 ? "DEFAULT_COLUMN" :
                             meaningfulParts.length === 1 ? "SINGLE_PART" : "MULTIPLE_PARTS_WITH_ACRONYMS"
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'COLUMN_COMBINATION', `Column ${colIndex} combination`, data);
        } else {
            this.log('COLUMN_COMBINATION', `Column ${colIndex} combination`, data);
        }
    }

    logAcronymGeneration(originalText, acronym, flattenLevel = null) {
        const data = {
            input: originalText,
            output: acronym,
            words: originalText.split(/\s+/),
            processing_details: this.getAcronymProcessingDetails(originalText)
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'ACRONYM_GENERATION', `Acronym generation`, data);
        } else {
            this.log('ACRONYM_GENERATION', `Acronym generation`, data);
        }
    }

    getAcronymProcessingDetails(text) {
        const words = text.split(/\s+/);
        return words.map(word => {
            if (/^\d+$/.test(word)) {
                return { word, type: "PURE_NUMBER", result: word };
            } else if (/\d/.test(word)) {
                const letters = word.replace(/\d+/g, '');
                const numbers = word.match(/\d+/g)?.join('') || '';
                return { 
                    word, 
                    type: "MIXED_LETTERS_NUMBERS", 
                    letters, 
                    numbers, 
                    result: letters ? letters.charAt(0) + numbers : numbers 
                };
            } else {
                return { word, type: "PURE_TEXT", result: word.charAt(0) };
            }
        });
    }

    logHeaderMatrixBuilding(level, rowspanMatrix, coveredPositions, levelHeaders, flattenLevel = null) {
        const data = {
            level: level,
            rowspan_matrix_for_level: rowspanMatrix[level],
            covered_positions: Array.from(coveredPositions),
            resulting_headers: levelHeaders.map(h => ({
                text: h.text,
                colspan: h.colspan,
                rowspan: h.rowspan,
                position: h.position
            }))
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'HEADER_MATRIX_BUILDING', `Building header matrix level ${level}`, data);
        } else {
            this.log('HEADER_MATRIX_BUILDING', `Building header matrix level ${level}`, data);
        }
    }

    logCompleteFlattening(originalTable, finalColumns, flattenLevel = null) {
        const data = {
            original_structure: originalTable.header_matrix,
            column_tuples: this.extractColumnTuples(originalTable),
            final_flattened_columns: finalColumns
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'COMPLETE_FLATTENING', 'Complete flattening process', data);
        } else {
            this.log('COMPLETE_FLATTENING', 'Complete flattening process', data);
        }
    }

    extractColumnTuples(originalTable) {
        const columnTuples = [];
        for (let colIndex = 0; colIndex < originalTable.col_count; colIndex++) {
            const tuple = [];
            for (let levelIndex = 0; levelIndex < originalTable.header_matrix.length; levelIndex++) {
                const level = originalTable.header_matrix[levelIndex];
                const header = this.findHeaderForColumn(level, colIndex);
                if (header && header.text) {
                    tuple.push(header.text);
                }
            }
            columnTuples.push({ column: colIndex, tuple: tuple });
        }
        return columnTuples;
    }

    findHeaderForColumn(level, columnIndex) {
        let currentPosition = 0;
        for (const header of level) {
            const endPosition = currentPosition + header.colspan;
            if (columnIndex >= currentPosition && columnIndex < endPosition) {
                return header;
            }
            currentPosition = endPosition;
        }
        return null;
    }

    logError(operation, error, context = null, flattenLevel = null) {
        const data = {
            operation: operation,
            error_message: error.message,
            error_stack: error.stack,
            context: context
        };

        if (flattenLevel !== null) {
            this.logForLevel(flattenLevel, 'ERROR', `Error in ${operation}: ${error.message}`, data);
        } else {
            this.log('ERROR', `Error in ${operation}: ${error.message}`, data);
        }
    }

    exportLogs() {
        const exportData = {
            session_id: this.sessionId,
            export_time: new Date().toISOString(),
            total_logs: this.logs.length,
            logs: this.logs
        };
        
        console.log('='.repeat(80));
        console.log('FLATTEN DEBUG LOG EXPORT');
        console.log('='.repeat(80));
        console.log(JSON.stringify(exportData, null, 2));
        console.log('='.repeat(80));
        
        return exportData;
    }

    // Export all level logs as separate files
    exportAllLevelLogs() {
        console.log('💾 Exporting all level debug logs...');
        let exportCount = 0;
        
        for (const [level, levelData] of Object.entries(this.levelLogs)) {
            if (levelData.logs.length > 0) {
                this.saveLevelDebugToFile(parseInt(level));
                exportCount++;
            }
        }
        
        console.log(`✅ Exported debug data for ${exportCount} flatten levels`);
        return exportCount;
    }

    clearLogs() {
        this.logs = [];
        this.levelLogs = {};
        this.sessionId = Date.now();
    }

    enableDebug() {
        this.debugMode = true;
        this.log('SYSTEM', 'Debug mode enabled');
    }

    disableDebug() {
        this.debugMode = false;
    }
}

// Create global debug logger instance
window.FlattenDebugLogger = window.FlattenDebugLogger || new FlattenDebugLogger();

// Enhanced debugging wrapper for the main flatten function
window.FlattenManager = window.FlattenManager || {};

// Store original function if it exists
if (window.FlattenManager.createFlattenedTableData) {
    window.FlattenManager._originalCreateFlattenedTableData = window.FlattenManager.createFlattenedTableData;
}

// Enhanced createFlattenedTableData with comprehensive debugging
window.FlattenManager.createFlattenedTableDataWithDebug = function(originalTableInfo, flattenLevel) {
    const debugLogger = window.FlattenDebugLogger;
    
    try {
        debugLogger.log('OPERATION_START', `Starting flatten operation - Level ${flattenLevel}`);
        debugLogger.logTableStructure(originalTableInfo, `Input table for flatten level ${flattenLevel}`);
        
        // Call original function
        const result = window.FlattenManager._originalCreateFlattenedTableData 
            ? window.FlattenManager._originalCreateFlattenedTableData(originalTableInfo, flattenLevel)
            : window.FlattenManager.createFlattenedTableData(originalTableInfo, flattenLevel);
        
        debugLogger.logFlattenOperation(originalTableInfo, flattenLevel, result);
        debugLogger.logTableStructure(result, `Output table from flatten level ${flattenLevel}`);
        debugLogger.log('OPERATION_END', `Completed flatten operation - Level ${flattenLevel}`);
        
        return result;
        
    } catch (error) {
        debugLogger.logError('createFlattenedTableData', error, {
            flattenLevel: flattenLevel,
            originalTableInfo: originalTableInfo
        });
        throw error;
    }
};

// Simple Debug System for Flatten Logic
window.debugFlatten = function(resultIndex, flattenLevel) {
    console.log(`\n========== FLATTEN DEBUG: Result ${resultIndex}, Level ${flattenLevel} ==========`);
    
    const tableData = window.AppConfig.globalTableData[resultIndex];
    if (!tableData) {
        console.log("❌ No table data found");
        return;
    }

    console.log(`📊 Original table: ${tableData.header_matrix.length} levels, ${tableData.col_count} columns`);
    
    // Show original header matrix structure
    console.log("\n🏗️ ORIGINAL HEADER MATRIX:");
    tableData.header_matrix.forEach((level, levelIndex) => {
        console.log(`Level ${levelIndex}:`);
        level.forEach(header => {
            console.log(`  "${header.text}" (pos:${header.position}, span:${header.colspan}x${header.rowspan})`);
        });
    });

    // Show what each column position contains at each level
    console.log("\n📋 COLUMN BREAKDOWN (what's in each column at each level):");
    for (let col = 0; col < tableData.col_count; col++) {
        console.log(`Column ${col}:`);
        for (let level = 0; level < tableData.header_matrix.length; level++) {
            const header = findHeaderForColumnSimple(tableData.header_matrix[level], col);
            console.log(`  Level ${level}: "${header ? header.text : 'MISSING'}"`);
        }
    }

    if (flattenLevel <= 0) {
        console.log("\n✅ Level 0: No flattening applied");
        // Still run flattening to generate debug data
        if (window.FlattenManager && window.FlattenManager.createFlattenedTableData) {
            window.FlattenManager.createFlattenedTableData(tableData, flattenLevel);
        }
        return;
    }

    // Test the flattening logic step by step
    console.log(`\n🔄 FLATTENING LOGIC FOR LEVEL ${flattenLevel}:`);
    
    // Run the actual flattening to trigger debug logging and file saving
    if (window.FlattenManager && window.FlattenManager.createFlattenedTableData) {
        const result = window.FlattenManager.createFlattenedTableData(tableData, flattenLevel);
        console.log(`✅ Flattening completed. Debug data saved to level${flattenLevel}.json`);
    }
    
    if (flattenLevel >= tableData.header_matrix.length - 1) {
        console.log("Complete flattening (all levels combined)");
        testCompleteFlattening(tableData);
    } else {
        console.log(`Partial flattening (combine first ${flattenLevel + 1} levels)`);
        testPartialFlattening(tableData, flattenLevel);
    }
};

// Function to save debug data for all levels at once
window.saveAllLevelDebugData = function(resultIndex) {
    console.log(`💾 Saving debug data for all levels of result ${resultIndex}...`);
    
    const tableData = window.AppConfig.globalTableData[resultIndex];
    if (!tableData) {
        console.log("❌ No table data found");
        return;
    }

    const maxLevels = tableData.header_matrix.length;
    console.log(`📊 Table has ${maxLevels} levels, generating debug data for levels 0-${maxLevels}`);
    
    // Generate debug data for each level
    for (let level = 0; level <= maxLevels; level++) {
        console.log(`🔄 Processing level ${level}...`);
        if (window.FlattenManager && window.FlattenManager.createFlattenedTableData) {
            window.FlattenManager.createFlattenedTableData(tableData, level);
        }
    }
    
    // Export all level logs
    if (window.FlattenDebugLogger) {
        const exportCount = window.FlattenDebugLogger.exportAllLevelLogs();
        console.log(`✅ Generated and saved debug data for ${exportCount} levels`);
    }
};

// Function to manually save debug data for a specific level
window.saveDebugLevel = function(flattenLevel) {
    if (window.FlattenDebugLogger) {
        window.FlattenDebugLogger.saveLevelDebugToFile(flattenLevel);
        console.log(`💾 Debug data for level ${flattenLevel} saved to level${flattenLevel}.json`);
    } else {
        console.log("❌ FlattenDebugLogger not available");
    }
};

// Function to test multiindex conversion specifically
window.testMultiindexConversion = function(resultIndex) {
    console.log(`🔍 Testing multiindex conversion for result ${resultIndex}...`);
    
    const tableData = window.AppConfig.globalTableData[resultIndex];
    if (!tableData) {
        console.log("❌ No table data found");
        return;
    }

    const { header_matrix, col_count } = tableData;
    console.log(`📊 Original header matrix:`, header_matrix);
    console.log(`📊 Column count:`, col_count);
    
    // Test the conversion directly
    if (window.FlattenManager && window.FlattenManager.convertToMultiindexColumns) {
        console.log("⚠️ convertToMultiindexColumns is not exposed in FlattenManager");
    }
    
    // Manually call the flattening to trigger conversion debug logs
    console.log("🔄 Running flatten level 1 to trigger conversion...");
    if (window.FlattenManager && window.FlattenManager.createFlattenedTableData) {
        window.FlattenManager.createFlattenedTableData(tableData, 1);
    }
    
    console.log("✅ Check the debug logs above for multiindex conversion details");
};

// Function to analyze column structure expectations vs reality
window.analyzeColumnStructure = function(resultIndex) {
    console.log(`📋 Analyzing column structure for result ${resultIndex}...`);
    
    const tableData = window.AppConfig.globalTableData[resultIndex];
    if (!tableData) {
        console.log("❌ No table data found");
        return;
    }

    const { header_matrix, col_count } = tableData;
    
    console.log("\n🎯 EXPECTED COLUMN STRUCTURE:");
    for (let col = 0; col < col_count; col++) {
        console.log(`\nColumn ${col}:`);
        
        for (let level = 0; level < header_matrix.length; level++) {
            // Find which header covers this column at this level
            let coveringHeader = null;
            let currentPos = 0;
            
            for (let checkLevel = 0; checkLevel <= level; checkLevel++) {
                const levelHeaders = header_matrix[checkLevel];
                currentPos = 0;
                
                for (const header of levelHeaders) {
                    const endPos = currentPos + header.colspan;
                    
                    if (col >= currentPos && col < endPos) {
                        // Check if this header spans to the target level
                        if (checkLevel + header.rowspan > level) {
                            coveringHeader = header;
                            break;
                        }
                    }
                    currentPos = endPos;
                }
                
                if (coveringHeader) break;
            }
            
            if (coveringHeader) {
                const isSpanned = coveringHeader.level < level;
                const expectedValue = isSpanned ? "Header" : coveringHeader.text;
                console.log(`  Level ${level}: "${expectedValue}" ${isSpanned ? '(spanned from level ' + coveringHeader.level + ')' : '(actual header)'}`);
            } else {
                console.log(`  Level ${level}: NO HEADER FOUND ❌`);
            }
        }
    }
};

// Add a simple inspection function
window.inspectTable = function(resultIndex) {
    console.log(`\n========== TABLE INSPECTION: Result ${resultIndex} ==========`);
    
    const tableData = window.AppConfig.globalTableData[resultIndex];
    if (!tableData) {
        console.log("❌ No table data found");
        return;
    }
    
    console.log("Raw table data:");
    console.log("has_multiindex:", tableData.has_multiindex);
    console.log("col_count:", tableData.col_count);
    console.log("row_count:", tableData.row_count);
    console.log("final_columns:", tableData.final_columns);
    
    console.log("\nHeader matrix raw structure:");
    console.log(JSON.stringify(tableData.header_matrix, null, 2));
    
    console.log("\nData rows sample:");
    if (tableData.data_rows && tableData.data_rows.length > 0) {
        console.log("First few data rows:");
        tableData.data_rows.slice(0, 3).forEach((row, i) => {
            console.log(`Row ${i}:`, row);
        });
    }
};

function findHeaderForColumnSimple(levelHeaders, columnIndex) {
    let currentPos = 0;
    for (const header of levelHeaders) {
        if (columnIndex >= currentPos && columnIndex < currentPos + header.colspan) {
            return header;
        }
        currentPos += header.colspan;
    }
    return null;
}

function testCompleteFlattening(tableData) {
    console.log("\n🔍 COMPLETE FLATTENING TRACE:");
    
    for (let colIndex = 0; colIndex < tableData.col_count; colIndex++) {
        console.log(`\nColumn ${colIndex}:`);
        
        // Get all parts for this column
        const columnTuple = [];
        for (let levelIndex = 0; levelIndex < tableData.header_matrix.length; levelIndex++) {
            const header = findHeaderForColumnSimple(tableData.header_matrix[levelIndex], colIndex);
            if (header && header.text) {
                columnTuple.push(header.text);
                console.log(`  Level ${levelIndex}: "${header.text}"`);
            } else {
                console.log(`  Level ${levelIndex}: MISSING`);
            }
        }
        
        console.log(`  Raw parts: [${columnTuple.map(p => `"${p}"`).join(', ')}]`);
        
        // Filter meaningful parts
        const meaningfulParts = columnTuple.filter(part => 
            part && part !== 'Header' && part !== 'nan' && part.trim() !== ''
        );
        console.log(`  Meaningful parts: [${meaningfulParts.map(p => `"${p}"`).join(', ')}]`);
        
        // Apply flattening logic
        let result;
        if (meaningfulParts.length === 0) {
            result = "Column";
            console.log(`  Result: "${result}" (no meaningful parts)`);
        } else if (meaningfulParts.length === 1) {
            result = meaningfulParts[0];
            console.log(`  Result: "${result}" (single part, keep as-is)`);
        } else {
            // Multiple parts - create acronyms for all except last
            const acronymParts = [];
            console.log(`  Processing ${meaningfulParts.length} parts:`);
            
            for (let j = 0; j < meaningfulParts.length - 1; j++) {
                const original = meaningfulParts[j];
                const acronym = createAcronymSimple(original);
                acronymParts.push(acronym);
                console.log(`    Part ${j}: "${original}" -> "${acronym}" (acronym)`);
            }
            
            // Keep last part as-is
            const lastPart = meaningfulParts[meaningfulParts.length - 1];
            acronymParts.push(lastPart);
            console.log(`    Part ${meaningfulParts.length - 1}: "${lastPart}" (keep as-is)`);
            
            result = acronymParts.join(' ');
            console.log(`  Result: "${result}" (joined: ${acronymParts.map(p => `"${p}"`).join(' + ')})`);
        }
    }
}

function testPartialFlattening(tableData, flattenLevel) {
    const levelsToCombine = flattenLevel + 1;
    console.log(`\n🔍 PARTIAL FLATTENING TRACE (combine first ${levelsToCombine} levels):`);
    
    for (let colIndex = 0; colIndex < tableData.col_count; colIndex++) {
        console.log(`\nColumn ${colIndex}:`);
        
        // Get parts from levels to combine
        const parts = [];
        for (let level = 0; level < levelsToCombine && level < tableData.header_matrix.length; level++) {
            const header = findHeaderForColumnSimple(tableData.header_matrix[level], colIndex);
            if (header && header.text) {
                parts.push(header.text);
                console.log(`  Level ${level}: "${header.text}"`);
            } else {
                console.log(`  Level ${level}: MISSING`);
            }
        }
        
        console.log(`  Raw parts: [${parts.map(p => `"${p}"`).join(', ')}]`);
        
        // Filter meaningful parts
        const meaningfulParts = parts.filter(p => p && p !== 'Header' && p !== 'nan' && p.trim() !== '');
        console.log(`  Meaningful parts: [${meaningfulParts.map(p => `"${p}"`).join(', ')}]`);
        
        // Apply same logic as complete flattening
        let result;
        if (meaningfulParts.length === 0) {
            result = "Column";
            console.log(`  Result: "${result}" (no meaningful parts)`);
        } else if (meaningfulParts.length === 1) {
            result = meaningfulParts[0];
            console.log(`  Result: "${result}" (single part, keep as-is)`);
        } else {
            const acronymParts = [];
            console.log(`  Processing ${meaningfulParts.length} parts:`);
            
            for (let j = 0; j < meaningfulParts.length - 1; j++) {
                const original = meaningfulParts[j];
                const acronym = createAcronymSimple(original);
                acronymParts.push(acronym);
                console.log(`    Part ${j}: "${original}" -> "${acronym}" (acronym)`);
            }
            
            const lastPart = meaningfulParts[meaningfulParts.length - 1];
            acronymParts.push(lastPart);
            console.log(`    Part ${meaningfulParts.length - 1}: "${lastPart}" (keep as-is)`);
            
            result = acronymParts.join(' ');
            console.log(`  Result: "${result}" (joined: ${acronymParts.map(p => `"${p}"`).join(' + ')})`);
        }
    }
}

function createAcronymSimple(text) {
    if (!text || typeof text !== 'string') return '';
    
    text = text.trim();
    console.log(`      createAcronym("${text}"):`);
    
    const words = text.split(/\s+/);
    console.log(`        Words: [${words.map(w => `"${w}"`).join(', ')}]`);
    
    const acronymParts = [];
    for (const word of words) {
        if (/^\d+$/.test(word)) {
            // Pure number
            acronymParts.push(word);
            console.log(`        "${word}" -> "${word}" (pure number)`);
        } else if (/\d/.test(word)) {
            // Contains numbers
            const letters = word.replace(/\d+/g, '');
            const numbers = word.match(/\d+/g)?.join('') || '';
            const result = letters ? letters.charAt(0) + numbers : numbers;
            acronymParts.push(result);
            console.log(`        "${word}" -> "${result}" (mixed: first letter + numbers)`);
        } else {
            // Pure text
            const result = word.charAt(0);
            acronymParts.push(result);
            console.log(`        "${word}" -> "${result}" (pure text: first letter)`);
        }
    }
    
    const finalResult = acronymParts.join('');
    console.log(`        Final acronym: "${finalResult}"`);
    return finalResult;
}

console.log('✅ Enhanced Debug System loaded with file saving capabilities!');
console.log('📋 Available functions:');
console.log('  • debugFlatten(resultIndex, flattenLevel) - Debug specific level and save to levelX.json');
console.log('  • saveAllLevelDebugData(resultIndex) - Generate and save debug data for all levels');
console.log('  • saveDebugLevel(flattenLevel) - Manually save debug data for a specific level');
console.log('  • inspectTable(resultIndex) - Inspect raw table structure');
console.log('  • testMultiindexConversion(resultIndex) - Test multiindex conversion process');
console.log('  • analyzeColumnStructure(resultIndex) - Analyze expected vs actual column structure');

// Auto-enable debug mode
window.FlattenDebugLogger.enableDebug();

console.log('🔍 Flatten Debug Logger loaded with automatic file saving.');
console.log('💾 Debug data will be automatically saved to level0.json, level1.json, level2.json, etc.');
console.log('📝 All flatten operations will now be logged and saved to files.'); 