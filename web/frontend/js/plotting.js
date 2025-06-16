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
            console.log(`🎨 [PLOT] Initializing plotting for result ${resultIndex}`);
            
            // Use EXACT same logic as downloadTableData() - no custom extraction
            const tableData = this.getProcessedTableData(resultIndex);
            if (!tableData) {
                showError('Unable to extract table data for plotting');
                return;
            }
            
            // Show modal and start plotting
            this.showPlotModal();
            await this.sendPlotRequest(tableData, resultIndex);
            
        } catch (error) {
            console.error('Error initializing plotting:', error);
            showError(`Failed to initialize plotting: ${error.message}`);
        }
    },
    
    // Get processed table data using EXACT same logic as downloadTableData()
    getProcessedTableData(resultIndex) {
        try {
            console.log(`📊 [PLOT] Getting processed table data for result index: ${resultIndex}`);
            
            // STEP 1: Get original table data (same as downloadTableData)
            const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
            if (!tableData) {
                console.error('No table data found for result index:', resultIndex);
                return null;
            }
            
            // STEP 2: Find SPECIFIC container for this exact resultIndex (same fix as downloadAsJSON)
            const specificContainerSelector = `div[data-result-index="${resultIndex}"]`;
            const allContainers = document.querySelectorAll(specificContainerSelector);
            
            console.log(`🔍 [PLOT CONTAINER] Looking for result index ${resultIndex}:`);
            console.log(`  - Found ${allContainers.length} elements with data-result-index="${resultIndex}"`);
            
            // Find the VISIBLE/ACTIVE main container (same logic as downloadAsJSON)
            let container = null;
            
            // CRITICAL: Filter out detached/invisible elements first  
            const visibleContainers = Array.from(allContainers).filter(elem => {
                // Check if element is attached to DOM and visible
                const isAttached = document.contains(elem);
                const isVisible = elem.offsetParent !== null || elem.style.display !== 'none';
                
                console.log(`    ${elem.tagName}.${elem.className}: attached=${isAttached}, visible=${isVisible}`);
                return isAttached && isVisible;
            });
            
            console.log(`    🔍 [PLOT] Filtered to ${visibleContainers.length} visible containers from ${allContainers.length} total`);
            
            for (const elem of visibleContainers) {
                const hasTableControls = elem.querySelector('.table-controls') !== null;
                const hasFlattening = elem.classList.contains('table-flatten-container');
                const isSimple = elem.classList.contains('table-simple-container');
                
                // For hierarchical tables, check button states to find the ACTIVE container
                let isActiveContainer = false;
                if (hasFlattening) {
                    const upBtn = elem.querySelector('.flatten-up');
                    const downBtn = elem.querySelector('.flatten-down');
                    const levelDisplay = elem.querySelector('.flatten-level-display');
                    
                    // Active container has functional buttons and valid level
                    const hasValidButtons = upBtn && downBtn && levelDisplay;
                    const levelAttr = levelDisplay?.getAttribute('data-current-level');
                    
                    console.log(`    ${elem.tagName}.${elem.className}: controls=${hasTableControls}, buttons=${hasValidButtons}, level=${levelAttr}`);
                    
                    if (hasValidButtons && levelAttr !== null) {
                        isActiveContainer = true;
                    }
                } else {
                    console.log(`    ${elem.tagName}.${elem.className}: controls=${hasTableControls}, simple=${isSimple}`);
                    isActiveContainer = hasTableControls || isSimple;
                }
                
                if (isActiveContainer) {
                    container = elem;
                    console.log(`    ✅ Selected as VISIBLE ACTIVE main container for plotting`);
                    break;
                }
            }
            
            if (!container) {
                console.error('❌ [PLOT] No main container found for result index:', resultIndex);
                return null;
            }
            
            // STEP 3: Apply processing (EXACT same as downloadTableData)
            let currentTableData = { ...tableData };
            
            // Apply current flatten level from THIS specific container only
            const levelDisplay = container.querySelector('.flatten-level-display');
            const currentLevel = levelDisplay ? parseInt(levelDisplay.getAttribute('data-current-level')) || 0 : 0;
            
            console.log(`🔍 [PLOT LEVEL] For result ${resultIndex}: level=${currentLevel}`);
            
            if (currentLevel > 0 && levelDisplay) {
                currentTableData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
                console.log(`🔄 [PLOT] Applied flatten level ${currentLevel}`);
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
            
            console.log(`✅ [PLOT] Processed table data successfully`);
            return currentTableData;
            
        } catch (error) {
            console.error('Error getting processed table data:', error);
            return null;
        }
    },
    
    // Create plot data schema using EXACT same logic as downloadAsJSON()
    createPlotDataSchema(tableData, resultIndex) {
        try {
            // Get the original backend data (same as downloadAsJSON)
            const originalTableData = window.FlattenManager.getTableDataFromResult(resultIndex);
            
            // Find the correct table container (same as downloadAsJSON)
            const container = document.querySelector(`div[data-result-index="${resultIndex}"].table-flatten-container, div[data-result-index="${resultIndex}"].table-simple-container`);
            const levelDisplay = container?.querySelector('.flatten-level-display');
            const currentFlattenLevel = levelDisplay ? parseInt(levelDisplay.getAttribute('data-current-level')) || 0 : 0;
            
            // Get current feature_rows (same as downloadAsJSON)
            const currentFeatureRows = tableData.feature_rows || [];
            
            // Get feature_cols (same as downloadAsJSON)
            const currentFeatureCols = window.TableManager.identifyCurrentFeatureCols(tableData, originalTableData, currentFeatureRows);
            
            console.log(`🔍 [PLOT] Feature cols calculation result: [${currentFeatureCols.join(', ')}]`);
            
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
                flatten_level_applied: currentFlattenLevel,
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
    async sendPlotRequest(processedTableData, resultIndex) {
        try {
            this.updateModalState('loading');
            
            console.log(`📤 [PLOT] Sending plot request to backend`);
            
            // Create plot data schema using EXACT same logic as downloadAsJSON
            const plotDataSchema = this.createPlotDataSchema(processedTableData, resultIndex);
            if (!plotDataSchema) {
                throw new Error('Failed to create plot data schema');
            }
            
            console.log(`📤 [PLOT] Request payload summary:`, {
                has_table_data: !!plotDataSchema,
                table_data_keys: plotDataSchema ? Object.keys(plotDataSchema) : 'null',
                final_columns_count: plotDataSchema?.final_columns?.length || 'missing',
                data_rows_count: plotDataSchema?.data_rows?.length || 'missing',
                data_row_sample_length: plotDataSchema?.data_rows?.[0]?.length || 'missing',
                feature_rows: plotDataSchema?.feature_rows || 'missing',
                feature_cols: plotDataSchema?.feature_cols || 'missing',
                row_count: plotDataSchema?.row_count || 'missing',
                col_count: plotDataSchema?.col_count || 'missing'
            });
            
            // CRITICAL DEBUG: Log the exact JSON being sent
            const requestPayload = {table_data: plotDataSchema};
            console.log(`📤 [PLOT] EXACT REQUEST PAYLOAD:`, requestPayload);
            console.log(`📤 [PLOT] REQUEST JSON STRING:`, JSON.stringify(requestPayload, null, 2));
            
            // 🔍 ENHANCED DEBUG FOR HEADER MATRIX ISSUE
            console.log(`📤 [PLOT] DETAILED HEADER MATRIX ANALYSIS:`);
            console.log(`  - header_matrix exists: ${!!plotDataSchema.header_matrix}`);
            console.log(`  - header_matrix length: ${plotDataSchema.header_matrix?.length || 'undefined'}`);
            console.log(`  - header_matrix type: ${typeof plotDataSchema.header_matrix}`);
            
            if (plotDataSchema.header_matrix && plotDataSchema.header_matrix.length > 0) {
                console.log(`  - header_matrix[0] exists: ${!!plotDataSchema.header_matrix[0]}`);
                console.log(`  - header_matrix[0] length: ${plotDataSchema.header_matrix[0]?.length || 'undefined'}`);
                console.log(`  - header_matrix[0] type: ${typeof plotDataSchema.header_matrix[0]}`);
                
                if (plotDataSchema.header_matrix[0] && plotDataSchema.header_matrix[0].length > 0) {
                    console.log(`  - header_matrix[0][0] sample:`, plotDataSchema.header_matrix[0][0]);
                    console.log(`  - header_matrix[0] all headers:`, plotDataSchema.header_matrix[0].map(h => ({
                        text: h.text,
                        colspan: h.colspan,
                        rowspan: h.rowspan,
                        position: h.position
                    })));
                }
            } else {
                console.log(`  - ❌ PROBLEM: header_matrix is empty or undefined!`);
            }
            
            console.log(`📤 [PLOT] HEADER MATRIX STRUCTURE:`, JSON.stringify(plotDataSchema.header_matrix, null, 2));
            console.log(`📤 [PLOT] TABLE METADATA:`);
            console.log(`  - has_multiindex: ${plotDataSchema.has_multiindex}`);
            console.log(`  - final_columns: [${plotDataSchema.final_columns?.join(', ') || 'undefined'}]`);
            console.log(`  - final_columns count: ${plotDataSchema.final_columns?.length || 0}`);
            console.log(`  - data_rows count: ${plotDataSchema.data_rows?.length || 0}`);
            console.log(`  - data_row[0] length: ${plotDataSchema.data_rows?.[0]?.length || 0}`);
            console.log(`  - feature_rows: [${plotDataSchema.feature_rows?.join(', ') || 'undefined'}]`);
            console.log(`  - feature_cols: [${plotDataSchema.feature_cols?.join(', ') || 'undefined'}]`);
            console.log(`  - flatten_level_applied: ${plotDataSchema.flatten_level_applied}`);
            
            // Validate critical fields before sending
            if (!plotDataSchema.final_columns || !plotDataSchema.data_rows) {
                throw new Error('Missing required fields: final_columns or data_rows');
            }
            
            if (plotDataSchema.data_rows.length === 0) {
                throw new Error('No data rows to plot');
            }
            
            if (plotDataSchema.final_columns.length === 0) {
                throw new Error('No columns defined');
            }
            
            // Log data consistency check
            const dataRowLength = plotDataSchema.data_rows[0]?.length || 0;
            const colCount = plotDataSchema.col_count || 0;
            console.log(`🔍 [PLOT] Data consistency check:`);
            console.log(`  - data_rows[0].length: ${dataRowLength}`);
            console.log(`  - col_count: ${colCount}`);
            console.log(`  - final_columns.length: ${plotDataSchema.final_columns.length}`);
            console.log(`  - Consistency: ${dataRowLength === colCount ? '✅ GOOD' : '❌ MISMATCH'}`);
            
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
            console.log(`📥 [PLOT] Received plot response:`, {
                success: result.success,
                plot_type: result.plot_type,
                data_points: result.data_points,
                has_plots: !!(result.plots?.column_first && result.plots?.row_first)
            });
            
            if (result.success) {
                this.currentPlotData = result;
                this.displayPlotResults(result);
            } else {
                this.showError(result.error || 'Failed to generate plots');
            }
            
        } catch (error) {
            console.error('Error sending plot request:', error);
            this.showError(`Failed to generate plots: ${error.message}`);
        }
    },
    
    // Display plot results in modal
    displayPlotResults(plotData) {
        try {
            this.updateModalState('success');
            
            console.log(`🎨 [PLOT] Displaying plot results`);
            
            // Store plot data for later use
            const plots = plotData.plots || {};
            
            // No need to update title elements since we removed the headers
            // The chart data is stored in this.currentPlotData for preview/download
            
            console.log(`✅ [PLOT] Successfully displayed plot results`);
            
        } catch (error) {
            console.error('Error displaying plot results:', error);
            this.showError('Error displaying chart results');
        }
    },
    
    // Preview chart in modal
    previewChart(chartType) {
        try {
            console.log(`👁️ [PLOT] Previewing ${chartType} chart`);
            
            if (!this.currentPlotData?.plots?.[chartType + '_first']) {
                showError('Chart data not available');
                return;
            }
            
            const chartData = this.currentPlotData.plots[chartType + '_first'];
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
            
            if (!this.currentPlotData?.plots?.[chartType + '_first']) {
                showError('Chart data not available');
                return;
            }
            
            const chartData = this.currentPlotData.plots[chartType + '_first'];
            const filename = `${chartType}_first_sunburst_chart.html`;
            
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
            
            showSuccess(`Downloaded ${chartType}-first chart as ${filename}`);
            console.log(`✅ [PLOT] Successfully downloaded ${filename}`);
            
        } catch (error) {
            console.error('Error downloading chart:', error);
            showError('Failed to download chart');
        }
    },
    
    // Download both charts
    downloadBothCharts() {
        try {
            console.log(`💾 [PLOT] Downloading both charts`);
            
            if (!this.currentPlotData?.plots) {
                showError('Chart data not available');
                return;
            }
            
            const plots = this.currentPlotData.plots;
            let downloadCount = 0;
            
            // Download column-first chart
            if (plots.column_first) {
                const blob1 = new Blob([plots.column_first.html_content], { type: 'text/html' });
                const url1 = URL.createObjectURL(blob1);
                const a1 = document.createElement('a');
                a1.href = url1;
                a1.download = 'column_first_sunburst_chart.html';
                document.body.appendChild(a1);
                a1.click();
                document.body.removeChild(a1);
                URL.revokeObjectURL(url1);
                downloadCount++;
            }
            
            // Download row-first chart with slight delay
            if (plots.row_first) {
                setTimeout(() => {
                    const blob2 = new Blob([plots.row_first.html_content], { type: 'text/html' });
                    const url2 = URL.createObjectURL(blob2);
                    const a2 = document.createElement('a');
                    a2.href = url2;
                    a2.download = 'row_first_sunburst_chart.html';
                    document.body.appendChild(a2);
                    a2.click();
                    document.body.removeChild(a2);
                    URL.revokeObjectURL(url2);
                }, 500);
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
            
            // Reset tabs
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
            previewBtn.onclick = () => this.previewChart(chartType);
        }
        if (downloadBtn) {
            downloadBtn.onclick = () => this.downloadChart(chartType);
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