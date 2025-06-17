/**
 * Plotting Manager - Frontend Sunburst Chart Integration
 * ====================================================
 * 
 * This module handles the complete plotting workflow:
 * 1. Extract table data from existing download system
 * 2. Send data to backend plotting endpoint
 * 3. Display both column-first and row-first sunburst charts
 * 4. Handle chart preview and download functionality
 */

window.PlottingManager = {
    currentPlotData: null,
    
    // Initialize plotting for a specific table
    async initializePlotting(resultIndex) {
        try {
            console.log(`🎨 [PLOT] Initializing dual-input plotting for result ${resultIndex}`);
            
            // Get dual table data (current + most flattened)
            const dualData = this.getDualProcessedTableData(resultIndex);
            if (!dualData) {
                showError('Unable to extract table data for plotting');
                return;
            }
            
            // Show modal and start plotting
            this.showPlotModal();
            await this.sendDualPlotRequest(dualData, resultIndex);
            
        } catch (error) {
            console.error('Error initializing plotting:', error);
            showError(`Failed to initialize plotting: ${error.message}`);
        }
    },
    
    // Get dual processed table data for new backend endpoint
    getDualProcessedTableData(resultIndex) {
        try {
            console.log(`📊 [PLOT] Getting dual processed table data for result index: ${resultIndex}`);
            
            // STEP 1: Get original table data
            const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
            if (!tableData) {
                console.error('No table data found for result index:', resultIndex);
                return null;
            }
            
            // STEP 2: Find container and determine max flatten level
            const container = this.findActiveContainer(resultIndex);
            if (!container) {
                console.error('❌ [PLOT] No main container found for result index:', resultIndex);
                return null;
            }
            
            console.log(`🔍 [PLOT] CONTAINER DEBUG:`);
            console.log(`  - Container found:`, container);
            console.log(`  - Container class:`, container.className);
            console.log(`  - Container data-max-levels:`, container.getAttribute('data-max-levels'));
            console.log(`  - Container data-result-index:`, container.getAttribute('data-result-index'));
            
            // STEP 3: Prepare CURRENT table data (for sunburst)
            const currentTableData = this.getCurrentTableData(tableData, container);
            
            // STEP 4: Prepare MOST FLATTENED table data (for bar chart)
            const mostFlattenedResult = this.getMostFlattenedData(tableData, container);
            
            console.log(`✅ [PLOT] Prepared dual table data successfully`);
            console.log(`🔍 [PLOT] DUAL DATA SUMMARY:`);
            console.log(`  - Current data flatten_level_applied: ${currentTableData?.flatten_level_applied || 'N/A'}`);
            console.log(`  - Flattened data flatten_level_applied: ${mostFlattenedResult.data?.flatten_level_applied || 'N/A'}`);
            console.log(`  - Flattened level to pass to schema: ${mostFlattenedResult.flattenLevel}`);
            console.log(`  - Expected: This should be maxLevel for completely flattened bar chart data`);
            
            return {
                currentData: currentTableData,
                flattenedData: mostFlattenedResult.data,
                flattenedLevel: mostFlattenedResult.flattenLevel
            };
            
        } catch (error) {
            console.error('Error getting processed table data:', error);
            return null;
        }
    },
    
    // Find the active container for the given result index
    findActiveContainer(resultIndex) {
        const specificContainerSelector = `div[data-result-index="${resultIndex}"]`;
        const allContainers = document.querySelectorAll(specificContainerSelector);
        
        console.log(`🔍 [PLOT CONTAINER] Looking for result index ${resultIndex}:`);
        console.log(`  - Found ${allContainers.length} elements with data-result-index="${resultIndex}"`);
        
        // Filter out detached/invisible elements first  
        const visibleContainers = Array.from(allContainers).filter(elem => {
            const isAttached = document.contains(elem);
            const isVisible = elem.offsetParent !== null || elem.style.display !== 'none';
            return isAttached && isVisible;
        });
        
        // Find the active container
        for (const elem of visibleContainers) {
            const hasTableControls = elem.querySelector('.table-controls') !== null;
            const hasFlattening = elem.classList.contains('table-flatten-container');
            const isSimple = elem.classList.contains('table-simple-container');
            
            let isActiveContainer = false;
            if (hasFlattening) {
                const upBtn = elem.querySelector('.flatten-up');
                const downBtn = elem.querySelector('.flatten-down');
                const levelDisplay = elem.querySelector('.flatten-level-display');
                
                if (upBtn && downBtn && levelDisplay && levelDisplay.getAttribute('data-current-level') !== null) {
                    isActiveContainer = true;
                }
            } else {
                isActiveContainer = hasTableControls || isSimple;
            }
            
            if (isActiveContainer) {
                console.log(`    ✅ Selected as VISIBLE ACTIVE main container for plotting`);
                return elem;
            }
        }
        
        return null;
    },
    
    // Get current table data (whatever is currently displayed)
    getCurrentTableData(tableData, container) {
        let currentTableData = { ...tableData };
        
        // Apply current flatten level
        const levelDisplay = container.querySelector('.flatten-level-display');
        const currentLevel = levelDisplay ? parseInt(levelDisplay.getAttribute('data-current-level')) || 0 : 0;
        
        console.log(`🔍 [CURRENT DATA] Current level: ${currentLevel}`);
        
        if (currentLevel > 0 && levelDisplay) {
            currentTableData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
        }
        
        // Apply current filters
        const featureColCheckbox = container.querySelector('.feature-col-checkbox');
        const showAllFeatureCols = featureColCheckbox ? featureColCheckbox.checked : false;
        
        if (!showAllFeatureCols) {
            currentTableData = window.FlattenManager.filterTableDataByRedundantColumns(currentTableData, true);
        }
        
        const nanRowCheckbox = container.querySelector('.nan-row-checkbox');
        const showNaNRows = nanRowCheckbox ? nanRowCheckbox.checked : false;
        
        if (!showNaNRows) {
            currentTableData = window.FlattenManager.filterTableDataByNaNRows(currentTableData, true);
        }
        
        return currentTableData;
    },
    
    // Get most flattened data (for bar chart)
    getMostFlattenedData(tableData, container) {
        // Find the maximum flatten level available
        const maxLevels = parseInt(container.getAttribute('data-max-levels')) || 0;
        
        // For hierarchical tables: use the maximum flatten level (fully flattened)
        // For simple tables: maxLevels = 1, so maxFlattenLevel = 1 (but should be 0)
        let maxFlattenLevel = maxLevels; // do not change this line
        
        console.log(`🔍 [FLATTENED DATA] DETAILED DEBUG:`);
        console.log(`  - Container element:`, container);
        console.log(`  - Container class:`, container.className);
        console.log(`  - Container data-max-levels attribute:`, container.getAttribute('data-max-levels'));
        console.log(`  - Parsed maxLevels: ${maxLevels}`);
        console.log(`  - Calculated maxFlattenLevel: ${maxFlattenLevel}`);
        console.log(`  - Logic: ${container.classList.contains('table-simple-container') ? 'Simple table, level=0' : `Hierarchical table, level=${maxLevels}-1=${maxFlattenLevel}`}`);
        
        // Use FlattenManager to create the completely flattened version
        let mostFlattenedData;
        if (maxFlattenLevel === 0) {
            // For simple tables or level 0, just use the original data
            mostFlattenedData = { ...tableData };
        } else {
            // Use existing flatten logic from flatten.js
            mostFlattenedData = window.FlattenManager.createFlattenedTableData(tableData, maxFlattenLevel);
        }
        
        // Apply same filters as current table for consistency
        const featureColCheckbox = container.querySelector('.feature-col-checkbox');
        const showAllFeatureCols = featureColCheckbox ? featureColCheckbox.checked : false;
        
        if (!showAllFeatureCols) {
            mostFlattenedData = window.FlattenManager.filterTableDataByRedundantColumns(mostFlattenedData, true);
        }
        
        const nanRowCheckbox = container.querySelector('.nan-row-checkbox');
        const showNaNRows = nanRowCheckbox ? nanRowCheckbox.checked : false;
        
        if (!showNaNRows) {
            mostFlattenedData = window.FlattenManager.filterTableDataByNaNRows(mostFlattenedData, true);
        }
        
        // Return both data and the flatten level that was applied
        return {
            data: mostFlattenedData,
            flattenLevel: maxFlattenLevel
        };
    },
    
    // Create plot data schema using EXACT same logic as downloadAsJSON()
    createPlotDataSchema(tableData, resultIndex, overrideFlattenLevel = null) {
        try {
            // Get the original backend data (same as downloadAsJSON)
            const originalTableData = window.FlattenManager.getTableDataFromResult(resultIndex);
            
            // Find the correct table container (same as downloadAsJSON)
            const container = document.querySelector(`div[data-result-index="${resultIndex}"].table-flatten-container, div[data-result-index="${resultIndex}"].table-simple-container`);
            const levelDisplay = container?.querySelector('.flatten-level-display');
            const currentFlattenLevel = levelDisplay ? parseInt(levelDisplay.getAttribute('data-current-level')) || 0 : 0;
            
            // Use override flatten level if provided (for flattened data), otherwise use current level
            const actualFlattenLevel = overrideFlattenLevel !== null ? overrideFlattenLevel : currentFlattenLevel;
            
            // Get current feature_rows (same as downloadAsJSON)
            const currentFeatureRows = tableData.feature_rows || [];
            
            // Get feature_cols (same as downloadAsJSON)
            const currentFeatureCols = window.TableManager.identifyCurrentFeatureCols(tableData, originalTableData, currentFeatureRows);
            
            console.log(`🔍 [PLOT] Feature cols calculation result: [${currentFeatureCols.join(', ')}]`);
            console.log(`🔍 [PLOT] Using flatten level: ${actualFlattenLevel} (override: ${overrideFlattenLevel}, current: ${currentFlattenLevel})`);
            
            // Create plotting data structure (EXACT same as downloadAsJSON)
            // BUT ensure all numbers are plain JavaScript numbers (not numpy types)
            const plotDataSchema = {
                filename: tableData.filename,
                has_multiindex: tableData.has_multiindex,
                header_matrix: tableData.header_matrix,       // Current header structure
                final_columns: tableData.final_columns,       // Current column names
                data_rows: this.sanitizeDataRows(tableData.data_rows), // Sanitize numbers
                row_count: Number(tableData.row_count),       // Ensure plain number
                col_count: Number(tableData.col_count),       // Ensure plain number
                
                // CRITICAL FOR PLOTTING:
                feature_rows: currentFeatureRows,             // Filtered feature rows (grouping columns)
                feature_cols: currentFeatureCols,             // Data columns in flattened table
                
                export_timestamp: new Date().toISOString(),
                flatten_level_applied: actualFlattenLevel,    // Use the actual flatten level applied
                filters_applied: {
                    nan_rows_hidden: Number(tableData.nan_rows_hidden || 0),
                    redundant_columns_hidden: Number(tableData.redundant_columns_hidden || 0)
                }
            };
            
            console.log(`📊 [PLOT] Created plot data schema:`, {
                filename: plotDataSchema.filename,
                rows: plotDataSchema.data_rows?.length,
                columns: plotDataSchema.final_columns?.length,
                feature_rows: plotDataSchema.feature_rows,
                feature_cols: plotDataSchema.feature_cols,
                flatten_level: plotDataSchema.flatten_level_applied,
                row_count: plotDataSchema.row_count,
                col_count: plotDataSchema.col_count,
                data_row_length: plotDataSchema.data_rows?.[0]?.length
            });
            
            // CRITICAL DEBUG: Compare with success_1.json structure
            console.log(`🔍 [PLOT] DETAILED COMPARISON:`);
            console.log(`  final_columns (${plotDataSchema.final_columns?.length}):`, plotDataSchema.final_columns);
            console.log(`  data_rows[0] (${plotDataSchema.data_rows?.[0]?.length}):`, plotDataSchema.data_rows?.[0]);
            console.log(`  feature_rows (${plotDataSchema.feature_rows?.length}):`, plotDataSchema.feature_rows);
            console.log(`  feature_cols (${plotDataSchema.feature_cols?.length}):`, plotDataSchema.feature_cols);
            console.log(`  row_count: ${plotDataSchema.row_count}, col_count: ${plotDataSchema.col_count}`);
            console.log(`  has_multiindex: ${plotDataSchema.has_multiindex}`);
            console.log(`  header_matrix levels: ${plotDataSchema.header_matrix?.length}`);
            
            // Validate data consistency
            const dataRowLength = plotDataSchema.data_rows?.[0]?.length || 0;
            const expectedLength = plotDataSchema.col_count;
            if (dataRowLength !== expectedLength) {
                console.error(`❌ [PLOT] DATA MISMATCH: data_rows[0].length=${dataRowLength} but col_count=${expectedLength}`);
            } else {
                console.log(`✅ [PLOT] DATA CONSISTENCY: data_rows[0].length matches col_count (${dataRowLength})`);
            }
            
            return plotDataSchema;
            
        } catch (error) {
            console.error('Error creating plot data schema:', error);
            return null;
        }
    },
    
    // Sanitize data rows to ensure all numbers are plain JavaScript numbers
    sanitizeDataRows(dataRows) {
        if (!Array.isArray(dataRows)) return dataRows;
        
        return dataRows.map(row => {
            if (!Array.isArray(row)) return row;
            
            return row.map(cell => {
                // Convert any numeric values to plain JavaScript numbers
                if (typeof cell === 'number') {
                    return Number(cell);
                }
                // Handle string numbers
                if (typeof cell === 'string' && !isNaN(cell) && !isNaN(parseFloat(cell))) {
                    return Number(cell);
                }
                // Keep non-numeric values as-is
                return cell;
            });
        });
    },
    
    // Send plot request to backend
    async sendDualPlotRequest(dualData, resultIndex) {
        try {
            this.updateModalState('loading');
            
            console.log(`📤 [PLOT] Sending dual plot request to backend`);
            console.log(`📤 [PLOT] FUNCTION PARAMETER CHECK:`);
            console.log(`  - dualData.flattenedLevel: ${dualData.flattenedLevel}`);
            console.log(`  - typeof dualData.flattenedLevel: ${typeof dualData.flattenedLevel}`);
            console.log(`  - dualData.flattenedLevel === null: ${dualData.flattenedLevel === null}`);
            console.log(`  - dualData.flattenedLevel === undefined: ${dualData.flattenedLevel === undefined}`);
            
            // Create both plot data structures
            const currentPlotSchema = this.createPlotDataSchema(dualData.currentData, resultIndex);
            console.log(`📤 [PLOT] About to call createPlotDataSchema for flattened data with override level: ${dualData.flattenedLevel}`);
            const flattenedPlotSchema = this.createPlotDataSchema(dualData.flattenedData, resultIndex, dualData.flattenedLevel);
            
            if (!currentPlotSchema || !flattenedPlotSchema) {
                throw new Error('Failed to create plot data schemas');
            }
            
            console.log(`📤 [PLOT] Dual plot request summary:`, {
                current_data_rows: currentPlotSchema?.data_rows?.length || 'missing',
                current_columns: currentPlotSchema?.final_columns?.length || 'missing',
                flattened_data_rows: flattenedPlotSchema?.data_rows?.length || 'missing',
                flattened_columns: flattenedPlotSchema?.final_columns?.length || 'missing',
                current_flatten_level: currentPlotSchema?.flatten_level_applied || 'missing',
                flattened_flatten_level: flattenedPlotSchema?.flatten_level_applied || 'missing'
            });
            
            console.log(`🎯 [PLOT] CRITICAL BAR CHART FLATTEN LEVEL CHECK:`);
            console.log(`  - Flattened data flatten_level_applied: ${flattenedPlotSchema?.flatten_level_applied}`);
            console.log(`  - Current data flatten_level_applied: ${currentPlotSchema?.flatten_level_applied}`);
            
            // Determine table type from dualData context
            const isSimpleTable = dualData.flattenedLevel === 0 && dualData.currentData?.flatten_level_applied === 0;
            if (isSimpleTable) {
                console.log(`  - ✅ SIMPLE TABLE: Both levels = 0 (correct for non-hierarchical data)`);
                console.log(`  - For simple tables: completely_flattened_data = normal_data (same flatten level)`);
            } else {
                console.log(`  - ✅ HIERARCHICAL TABLE: Flattened level should be (maxLevels - 1)`);
                console.log(`  - Current level is user's view, flattened level is completely flattened for bar chart`);
            }
            
            // Create dual request payload
            const requestPayload = {
                completely_flattened_data: flattenedPlotSchema,
                normal_data: currentPlotSchema
            };
            console.log(`📤 [PLOT] EXACT REQUEST PAYLOAD:`, requestPayload);
            
            // Validate critical fields before sending
            if (!currentPlotSchema.final_columns || !currentPlotSchema.data_rows) {
                throw new Error('Missing required fields in current data: final_columns or data_rows');
            }
            
            if (!flattenedPlotSchema.final_columns || !flattenedPlotSchema.data_rows) {
                throw new Error('Missing required fields in flattened data: final_columns or data_rows');
            }
            
            console.log(`🔍 [PLOT] Data validation passed - sending request to backend`);
            
            const response = await fetch(`${window.AppConfig.API_BASE_URL}/plot/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPayload)
            });
            
            console.log(`📥 [PLOT] Response status: ${response.status} ${response.statusText}`);
            console.log(`📥 [PLOT] Response headers:`, Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                // Get response body for error details
                let errorBody = '';
                try {
                    errorBody = await response.text();
                    console.error(`❌ [PLOT] Error response body:`, errorBody);
                } catch (e) {
                    console.error(`❌ [PLOT] Could not read error response body:`, e);
                }
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
            }
            
            const result = await response.json();
            console.log(`📥 [PLOT] Received dual plot response:`, {
                success: result.success,
                plot_types: result.plot_types,
                bar_chart_message: result.bar_chart_message,
                has_sunburst_plots: !!(result.plots?.column_first && result.plots?.row_first),
                has_bar_plot: !!result.plots?.bar_chart,
                response_keys: Object.keys(result)
            });
            
            if (result.success) {
                // Check if bar chart was generated
                const hasBarChart = result.plot_types && result.plot_types.includes('bar');
                
                if (!hasBarChart && result.bar_chart_message) {
                    // Show the bar chart validation message
                    showError(result.bar_chart_message);
                    console.log(`⚠️ [PLOT] Bar chart validation message: ${result.bar_chart_message}`);
                }
                
                // Store and display the results
                this.currentPlotData = result;
                this.displayDualPlotResults(result);
            } else {
                this.showError(result.error || 'Failed to generate plots');
            }
            
        } catch (error) {
            console.error('Error sending plot request:', error);
            this.showError(`Failed to generate plots: ${error.message}`);
        }
    },
    
    // Display dual plot results in modal
    displayDualPlotResults(plotData) {
        try {
            this.updateModalState('success');
            
            console.log(`🎨 [PLOT] Displaying dual plot results`);
            
            // Check what plot types are available
            const plotTypes = plotData.plot_types || [];
            const hasBarChart = plotTypes.includes('bar');
            const hasSunburst = plotTypes.includes('sunburst');
            
            console.log(`📊 [PLOT] Available plot types:`, {
                bar: hasBarChart,
                sunburst: hasSunburst,
                plot_types: plotTypes
            });
            
            // Update UI to show/hide relevant tabs based on available charts
            this.updatePlotTabs(hasBarChart, hasSunburst);
            
            console.log(`✅ [PLOT] Successfully displayed dual plot results`);
            
        } catch (error) {
            console.error('Error displaying dual plot results:', error);
            this.showError('Error displaying chart results');
        }
    },
    
    // Update plot tabs based on available chart types
    updatePlotTabs(hasBarChart, hasSunburst) {
        try {
            console.log(`📋 [PLOT] Updating tabs - Bar: ${hasBarChart}, Sunburst: ${hasSunburst}`);
            
            // Get tab elements
            const barTab = document.querySelector('.plot-tab[data-chart="bar"]');
            const columnTab = document.querySelector('.plot-tab[data-chart="column"]');
            const rowTab = document.querySelector('.plot-tab[data-chart="row"]');
            
            // Show/hide tabs based on available charts
            if (barTab) {
                if (hasBarChart) {
                    barTab.style.display = '';
                    barTab.style.visibility = 'visible';
                } else {
                    barTab.style.display = 'none';
                }
            }
            if (columnTab) {
                if (hasSunburst) {
                    columnTab.style.display = '';
                    columnTab.style.visibility = 'visible';
                } else {
                    columnTab.style.display = 'none';
                }
            }
            if (rowTab) {
                if (hasSunburst) {
                    rowTab.style.display = '';
                    rowTab.style.visibility = 'visible';
                } else {
                    rowTab.style.display = 'none';
                }
            }
            
            // Set default active tab (prefer bar chart if available)
            let defaultTab = 'column'; // Default to sunburst
            if (hasBarChart) {
                defaultTab = 'bar'; // Prefer bar chart if available
                console.log(`📋 [PLOT] Defaulting to bar chart (preferred)`);
            } else if (hasSunburst) {
                defaultTab = 'column'; // Fall back to sunburst
                console.log(`📋 [PLOT] Defaulting to column sunburst (bar not available)`);
            }
            
            // Switch to the default tab
            this.switchChartTab(defaultTab);
            
            console.log(`📋 [PLOT] Set default tab to: ${defaultTab}`);
            
        } catch (error) {
            console.error('Error updating plot tabs:', error);
        }
    },
    
    // Preview chart in modal
    previewChart(chartType) {
        try {
            console.log(`👁️ [PLOT] Previewing ${chartType} chart`);
            
            // Handle different chart types and their data locations
            let chartData = null;
            
            if (chartType === 'bar' && this.currentPlotData?.plots?.bar_chart) {
                chartData = this.currentPlotData.plots.bar_chart;
                console.log(`👁️ [PLOT] Found bar chart data`);
            } else if (chartType === 'column' && this.currentPlotData?.plots?.column_first) {
                chartData = this.currentPlotData.plots.column_first;
                console.log(`👁️ [PLOT] Found column sunburst data`);
            } else if (chartType === 'row' && this.currentPlotData?.plots?.row_first) {
                chartData = this.currentPlotData.plots.row_first;
                console.log(`👁️ [PLOT] Found row sunburst data`);
            } else {
                console.log(`👁️ [PLOT] No data found for ${chartType}. Available:`, {
                    plots_bar_chart: !!this.currentPlotData?.plots?.bar_chart,
                    plots_column_first: !!this.currentPlotData?.plots?.column_first,
                    plots_row_first: !!this.currentPlotData?.plots?.row_first
                });
            }
            
            if (!chartData) {
                console.error(`❌ [PLOT] No chart data found for ${chartType}`);
                showError(`${chartType} chart data not available`);
                return;
            }
            
            const previewContainer = document.getElementById(`plot-preview-${chartType}`);
            
            // Create iframe to display HTML chart
            const iframe = document.createElement('iframe');
            iframe.className = 'plot-chart-iframe';
            iframe.srcdoc = chartData.html_content;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '8px';
            
            // Clear preview container and add iframe
            previewContainer.innerHTML = '';
            previewContainer.appendChild(iframe);
            
            console.log(`✅ [PLOT] ${chartType} chart preview loaded`);
            
        } catch (error) {
            console.error('Error previewing chart:', error);
            showError('Failed to preview chart');
        }
    },
    
    // Download single chart
    downloadChart(chartType) {
        try {
            console.log(`💾 [PLOT] Downloading ${chartType} chart`);
            
            // Handle different chart types and their data locations
            let chartData = null;
            let filename = '';
            
            if (chartType === 'bar' && this.currentPlotData?.plots?.bar_chart) {
                chartData = this.currentPlotData.plots.bar_chart;
                filename = 'bar_chart.html';
            } else if (chartType === 'column' && this.currentPlotData?.plots?.column_first) {
                chartData = this.currentPlotData.plots.column_first;
                filename = 'sunburst_column_first.html';
            } else if (chartType === 'row' && this.currentPlotData?.plots?.row_first) {
                chartData = this.currentPlotData.plots.row_first;
                filename = 'sunburst_row_first.html';
            }
            
            if (!chartData) {
                showError(`${chartType} chart data not available`);
                return;
            }
            
            // Create blob and download
            const blob = new Blob([chartData.html_content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showSuccess(`Downloaded ${chartType} chart as ${filename}`);
            console.log(`✅ [PLOT] Successfully downloaded ${filename}`);
            
        } catch (error) {
            console.error('Error downloading chart:', error);
            showError('Failed to download chart');
        }
    },
    
    // Download all available charts
    downloadBothCharts() {
        try {
            console.log(`💾 [PLOT] Downloading all available charts`);
            
            if (!this.currentPlotData) {
                showError('Chart data not available');
                return;
            }
            
            let downloadCount = 0;
            
            // Download bar chart if available
            if (this.currentPlotData.plots?.bar) {
                const blob = new Blob([this.currentPlotData.plots.bar.html_content], { type: 'text/html' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'bar_chart.html';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                downloadCount++;
            }
            
            // Download column-first sunburst chart
            if (this.currentPlotData.plots?.column_first) {
                setTimeout(() => {
                    const blob = new Blob([this.currentPlotData.plots.column_first.html_content], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sunburst_column_first.html';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }, 200);
                downloadCount++;
            }
            
            // Download row-first sunburst chart
            if (this.currentPlotData.plots?.row_first) {
                setTimeout(() => {
                    const blob = new Blob([this.currentPlotData.plots.row_first.html_content], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sunburst_row_first.html';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }, 400);
                downloadCount++;
            }
            
            showSuccess(`Downloading ${downloadCount} chart(s)...`);
            console.log(`✅ [PLOT] Initiated download of ${downloadCount} charts`);
            
        } catch (error) {
            console.error('Error downloading charts:', error);
            showError('Failed to download charts');
        }
    },
    
    // Modal management
    showPlotModal() {
        console.log(`🪟 [PLOT] Opening plot modal`);
        
        const modal = document.getElementById('plot-modal');
        if (modal) {
            modal.style.display = 'block';
            this.updateModalState('loading');
            this.setupModalEvents();
            
            // Prevent background scroll
            document.body.style.overflow = 'hidden';
        }
    },
    
    hidePlotModal() {
        console.log(`🪟 [PLOT] Closing plot modal`);
        
        const modal = document.getElementById('plot-modal');
        if (modal) {
            modal.style.display = 'none';
            this.currentPlotData = null;
            
            // Reset modal state
            this.updateModalState('loading');
            
            // Clear previews
            const previewContainers = modal.querySelectorAll('.plot-chart-preview');
            previewContainers.forEach(container => {
                container.innerHTML = `
                    <div class="plot-preview-placeholder">
                        <i class="fas fa-chart-pie"></i>
                        <p>Click Preview to see chart</p>
                    </div>
                `;
            });
            
            // Reset tabs to default state
            const allTabs = modal.querySelectorAll('.plot-tab');
            allTabs.forEach(tab => {
                tab.style.display = '';
                tab.style.visibility = 'visible';
                tab.classList.remove('active');
            });
            
            // Set default active tab
            this.switchChartTab('column');
            
            // Restore background scroll
            document.body.style.overflow = '';
        }
    },
    
    updateModalState(state) {
        const loadingEl = document.getElementById('plot-loading');
        const errorEl = document.getElementById('plot-error');
        const resultsEl = document.getElementById('plot-results');
        
        if (!loadingEl || !errorEl || !resultsEl) {
            console.warn('Plot modal elements not found');
            return;
        }
        
        // Hide all states
        loadingEl.style.display = 'none';
        errorEl.style.display = 'none';
        resultsEl.style.display = 'none';
        
        // Show requested state
        switch (state) {
            case 'loading':
                loadingEl.style.display = 'block';
                break;
            case 'error':
                errorEl.style.display = 'block';
                break;
            case 'success':
                resultsEl.style.display = 'block';
                break;
        }
    },
    
    showError(message) {
        console.error(`❌ [PLOT] Error: ${message}`);
        
        this.updateModalState('error');
        const errorMsgEl = document.getElementById('plot-error-message');
        if (errorMsgEl) {
            errorMsgEl.textContent = message;
        }
    },
    
    setupModalEvents() {
        const modal = document.getElementById('plot-modal');
        if (!modal) return;
        
        // Tab switching
        const tabs = modal.querySelectorAll('.plot-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const chartType = tab.getAttribute('data-chart');
                this.switchChartTab(chartType);
            });
        });
        
        // Close events
        const closeBtn = modal.querySelector('.plot-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hidePlotModal());
        }
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hidePlotModal();
            }
        });
        
        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                this.hidePlotModal();
            }
        });
    },
    
    switchChartTab(chartType) {
        console.log(`🔄 [PLOT] Switching to ${chartType} tab`);
        
        // Update tab states
        const tabs = document.querySelectorAll('.plot-tab');
        tabs.forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-chart') === chartType);
        });
        
        // Update chart displays
        const charts = document.querySelectorAll('.plot-chart');
        charts.forEach(chart => {
            chart.classList.toggle('active', chart.id === `plot-chart-${chartType}`);
        });
        
        // Update action buttons to work with current chart type
        const previewBtn = document.getElementById('preview-btn');
        const downloadBtn = document.getElementById('download-btn');
        
        if (previewBtn) {
            previewBtn.onclick = () => {
                console.log(`🔘 [PLOT] Preview button clicked for ${chartType}`);
                window.PlottingManager.previewChart(chartType);
            };
        }
        if (downloadBtn) {
            downloadBtn.onclick = () => {
                console.log(`🔘 [PLOT] Download button clicked for ${chartType}`);
                window.PlottingManager.downloadChart(chartType);
            };
        }
    }
};

// Make global functions for onclick events
window.previewChart = function(chartType) {
    window.PlottingManager.previewChart(chartType);
};

window.downloadChart = function(chartType) {
    window.PlottingManager.downloadChart(chartType);
};



window.hidePlotModal = function() {
    window.PlottingManager.hidePlotModal();
};

console.log('✅ Plotting.js loaded - Sunburst chart integration ready');

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlottingManager;
}

// Initialize tab switching when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching is handled by setupModalEvents in PlottingManager
    console.log('✅ Plotting tab switching initialized');
}); 