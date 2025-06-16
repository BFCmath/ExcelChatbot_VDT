// Table Rendering Module
console.log('🚀 Loading table.js...');

// Create hierarchical HTML table
function createHierarchicalHtmlTable(tableInfo, filename) {
    if (!tableInfo || !tableInfo.data_rows || tableInfo.data_rows.length === 0) {
        return '<p class="no-data">No data to display</p>';
    }

    const { has_multiindex, header_matrix, final_columns, data_rows, row_count, col_count } = tableInfo;
    
    let html = '<div class="table-container">';
    html += `<div class="table-info">Showing ${row_count} rows × ${col_count} columns`;
    if (row_count > 100) {
        html += ` (first 100 rows displayed)`;
    }
    html += '</div>';
    
    // Wrap the table in a table-wrapper for horizontal scrolling
    html += '<div class="table-wrapper">';
    html += '<table class="data-table hierarchical-table">';
    
    // Generate header section with proper rowspan and colspan
    html += '<thead>';
    
    if (has_multiindex && header_matrix && header_matrix.length > 1) {
        // Multi-level headers with merged cells (both rowspan and colspan)
        // Track cells that should be skipped due to rowspan from previous levels
        const skipMatrix = Array(header_matrix.length).fill(null).map(() => Array(col_count).fill(false));
        
        header_matrix.forEach((level, levelIndex) => {
            html += '<tr class="header-level-' + levelIndex + '">';
            
            let currentPosition = 0;
            level.forEach(header => {
                // Skip positions that are covered by rowspan from previous levels
                while (currentPosition < col_count && skipMatrix[levelIndex][currentPosition]) {
                    currentPosition++;
                }
                
                if (currentPosition >= col_count) return;
                
                // Only render cells that should be displayed (not hidden by spanning)
                const colspanAttr = header.colspan > 1 ? ` colspan="${header.colspan}"` : '';
                const rowspanAttr = header.rowspan > 1 ? ` rowspan="${header.rowspan}"` : '';
                const headerText = header.text || '';
                
                // Determine header class based on level and spanning
                let levelClass = 'sub-level-header';
                if (levelIndex === 0) {
                    levelClass = 'top-level-header';
                }
                if (header.rowspan > 1) {
                    levelClass += ' vertical-span';
                }
                if (header.colspan > 1) {
                    levelClass += ' horizontal-span';
                }
                
                html += `<th class="${levelClass}"${colspanAttr}${rowspanAttr}>${window.Utils.escapeHtml(headerText)}</th>`;
                
                // Mark positions as occupied due to this cell's span
                for (let r = levelIndex; r < levelIndex + header.rowspan && r < skipMatrix.length; r++) {
                    for (let c = currentPosition; c < currentPosition + header.colspan && c < col_count; c++) {
                        if (r > levelIndex) { // Don't mark the current cell as skipped
                            skipMatrix[r][c] = true;
                        }
                    }
                }
                
                currentPosition += header.colspan;
            });
            
            html += '</tr>';
        });
    } else {
        // Simple single-level headers
        html += '<tr>';
        final_columns.forEach(col => {
            html += `<th>${window.Utils.escapeHtml(col)}</th>`;
        });
        html += '</tr>';
    }
    
    html += '</thead>';
    
    // Generate body section
    html += '<tbody>';
    const maxRows = Math.min(data_rows.length, 100);
    
    for (let i = 0; i < maxRows; i++) {
        const row = data_rows[i];
        html += '<tr>';
        
        row.forEach((cell, colIndex) => {
            const cellValue = window.Utils.formatCellValue(cell);
            html += `<td>${cellValue}</td>`;
        });
        
        html += '</tr>';
    }
    
    html += '</tbody>';
    html += '</table>';
    html += '</div>'; // Close table-wrapper
    html += '</div>'; // Close table-container
    
    return html;
}

// Format simple table data (legacy support)
function formatTableData(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return 'No data found.';
    }
    
    // Convert simple array data to table format for legacy support
    // This is a fallback for simple data structures
    const tableInfo = {
        has_multiindex: false,
        header_matrix: [[{
            text: 'Data',
            colspan: 1,
            position: 0
        }]],
        final_columns: ['Data'],
        data_rows: data.map(item => [item]),
        row_count: data.length,
        col_count: 1
    };
    
    return createHierarchicalHtmlTable(tableInfo, 'data');
}

// Setup table flatten controls event handlers
function setupTableToggleEvents(container) {
    const tableContainers = container.querySelectorAll('.table-flatten-container, .table-simple-container');
    
    tableContainers.forEach(tableContainer => {
        setupNaNRowToggle(tableContainer);
        setupFeatureColToggle(tableContainer);
        setupTableDownloadEvents(tableContainer);
    });
    
    const flattenContainers = container.querySelectorAll('.table-flatten-container');
    
    flattenContainers.forEach(flattenContainer => {
        const upBtn = flattenContainer.querySelector('.flatten-up');
        const downBtn = flattenContainer.querySelector('.flatten-down');
        const levelDisplay = flattenContainer.querySelector('.flatten-level-display');
        const tableView = flattenContainer.querySelector('.dynamic-table-view');
        const maxLevels = parseInt(flattenContainer.getAttribute('data-max-levels'));
        const resultIndex = parseInt(flattenContainer.getAttribute('data-result-index'));
        
        // Get the original table data
        const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
        
        if (!tableData) return;
        
        // Get initial flatten level from HTML (set in messages.js)
        // This ensures consistency between HTML and JavaScript
        let currentLevel = parseInt(levelDisplay.getAttribute('data-current-level')) || Math.max(maxLevels - 1, 0);
        
        function updateTable() {
            // 🔍 DEBUG: Log level change for this specific table
            console.log(`🔄 [LEVEL CHANGE] Result ${resultIndex}: Changed to level ${currentLevel}`);
            console.log(`📋 [LEVEL CHANGE] Table filename: ${tableData.filename}`);
            console.log(`📊 [LEVEL CHANGE] Original header matrix: ${tableData.header_matrix ? tableData.header_matrix.length : 0} levels`);
            if (tableData.header_matrix) {
                tableData.header_matrix.forEach((level, idx) => {
                    console.log(`  Level ${idx}: [${level.map(h => `"${h.text}"(${h.colspan}c,${h.rowspan}r)`).join(', ')}]`);
                });
            }
            
            let flattenedData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
            
            // 🔍 DEBUG: Log flattened result header
            console.log(`📊 [LEVEL CHANGE] Flattened header matrix: ${flattenedData.header_matrix ? flattenedData.header_matrix.length : 0} levels`);
            console.log(`📋 [LEVEL CHANGE] Flattened columns: [${flattenedData.final_columns?.join(', ') || 'none'}]`);
            
            // Check feature column toggle state
            const featureColCheckbox = flattenContainer.querySelector('.feature-col-checkbox');
            const showAllFeatureCols = featureColCheckbox ? featureColCheckbox.checked : false;
            
            // Apply feature column filtering if needed
            if (!showAllFeatureCols) {
                flattenedData = window.FlattenManager.filterTableDataByRedundantColumns(flattenedData, true);
            }
            
            // Check NaN row toggle state
            const nanRowCheckbox = flattenContainer.querySelector('.nan-row-checkbox');
            const showNaNRows = nanRowCheckbox ? nanRowCheckbox.checked : false;
            
            // Apply NaN row filtering if needed
            if (!showNaNRows) {
                flattenedData = window.FlattenManager.filterTableDataByNaNRows(flattenedData, true);
            }
            
            const newTableHtml = createHierarchicalHtmlTable(flattenedData, tableData.filename || 'Table');
            tableView.innerHTML = newTableHtml;
            
            // Update info text with hidden counts
            const tableContainer = tableView.querySelector('.table-container');
            if (tableContainer) {
                const infoDiv = tableContainer.querySelector('.table-info');
                if (infoDiv) {
                    let additionalInfo = [];
                    
                    if (!showNaNRows && flattenedData.nan_rows_hidden) {
                        additionalInfo.push(`${flattenedData.nan_rows_hidden} NaN rows hidden`);
                    }
                    
                    if (!showAllFeatureCols && flattenedData.redundant_columns_hidden) {
                        additionalInfo.push(`${flattenedData.redundant_columns_hidden} redundant feature rows hidden`);
                    }
                    
                    if (additionalInfo.length > 0) {
                        infoDiv.innerHTML += ` (${additionalInfo.join(', ')})`;
                    }
                }
            }
            
            // Update button states
            upBtn.disabled = currentLevel >= maxLevels;
            downBtn.disabled = currentLevel <= 0;
            
            // Update display text - but keep it hidden as per UI design
            levelDisplay.textContent = currentLevel === 0 ? 'Hierarchical' : `Flatten L${currentLevel}`;
            levelDisplay.setAttribute('data-current-level', currentLevel);
            
            // 🔍 DEBUG: Confirm level update
            console.log(`✅ [LEVEL CHANGE] Result ${resultIndex}: Level updated to ${currentLevel}, display text: "${levelDisplay.textContent}"`);
            console.log(`🔘 [LEVEL CHANGE] Button states: UP disabled=${upBtn.disabled}, DOWN disabled=${downBtn.disabled}`);
        }
        
        upBtn.addEventListener('click', function() {
            if (currentLevel < maxLevels) {
                currentLevel += 1;
                updateTable();
            }
        });
        
        downBtn.addEventListener('click', function() {
            if (currentLevel > 0) {
                currentLevel -= 1;
                updateTable();
            }
        });
        
        // Initialize button states and set initial level display
        upBtn.disabled = currentLevel >= maxLevels;
        downBtn.disabled = currentLevel <= 0;
        levelDisplay.textContent = currentLevel === 0 ? 'Hierarchical' : `Flatten L${currentLevel}`;
        levelDisplay.setAttribute('data-current-level', currentLevel);
        
        // Initial table setup with default flatten level
        updateTable();
    });
}

// Setup NaN row toggle functionality
function setupNaNRowToggle(container) {
    const nanRowCheckbox = container.querySelector('.nan-row-checkbox');
    if (!nanRowCheckbox) return;
    
    const resultIndex = parseInt(container.getAttribute('data-result-index'));
    const tableView = container.querySelector('.dynamic-table-view');
    
    if (!tableView) return;
    
    // Get the original table data
    const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
    if (!tableData) return;
    
    function updateTable() {
        const showNaNRows = nanRowCheckbox.checked;
        
        // Get current flatten level (if applicable)
        let currentLevel = 0;
        const levelDisplay = container.querySelector('.flatten-level-display');
        if (levelDisplay) {
            currentLevel = parseInt(levelDisplay.getAttribute('data-current-level')) || 0;
        }
        
        // Get flattened table data
        let displayTableData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
        
        // Check feature column toggle state
        const featureColCheckbox = container.querySelector('.feature-col-checkbox');
        const showAllFeatureCols = featureColCheckbox ? featureColCheckbox.checked : false;
        
        // Apply feature column filtering if needed
        if (!showAllFeatureCols) {
            displayTableData = window.FlattenManager.filterTableDataByRedundantColumns(displayTableData, true);
        }
        
        // Apply NaN row filtering
        if (!showNaNRows) {
            displayTableData = window.FlattenManager.filterTableDataByNaNRows(displayTableData, true);
        }
        
        // Update table HTML
        const newTableHtml = createHierarchicalHtmlTable(displayTableData, tableData.filename || 'Table');
        tableView.innerHTML = newTableHtml;
        
        // Update info text with hidden counts
        const tableContainer = tableView.querySelector('.table-container');
        if (tableContainer) {
            const infoDiv = tableContainer.querySelector('.table-info');
            if (infoDiv) {
                let additionalInfo = [];
                
                if (!showNaNRows && displayTableData.nan_rows_hidden) {
                    additionalInfo.push(`${displayTableData.nan_rows_hidden} NaN rows hidden`);
                }
                
                if (!showAllFeatureCols && displayTableData.redundant_columns_hidden) {
                    additionalInfo.push(`${displayTableData.redundant_columns_hidden} redundant feature rows hidden`);
                }
                
                if (additionalInfo.length > 0) {
                    infoDiv.innerHTML += ` (${additionalInfo.join(', ')})`;
                }
            }
        }
    }
    
    // Add event listener for NaN row toggle
    nanRowCheckbox.addEventListener('change', updateTable);
    
    // Initialize with NaN rows hidden (checkbox unchecked by default)
    updateTable();
}

// Setup feature column toggle functionality
function setupFeatureColToggle(container) {
    const featureColCheckbox = container.querySelector('.feature-col-checkbox');
    if (!featureColCheckbox) return;
    
    const resultIndex = parseInt(container.getAttribute('data-result-index'));
    const tableView = container.querySelector('.dynamic-table-view');
    
    if (!tableView) return;
    
    // Get the original table data
    const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
    if (!tableData) return;
    
    function updateTable() {
        const showAllFeatureCols = featureColCheckbox.checked;
        
        // Get current flatten level (if applicable)
        let currentLevel = 0;
        const levelDisplay = container.querySelector('.flatten-level-display');
        if (levelDisplay) {
            currentLevel = parseInt(levelDisplay.getAttribute('data-current-level')) || 0;
        }
        
        // Get flattened table data
        let displayTableData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
        
        // Apply feature column filtering if needed
        if (!showAllFeatureCols) {
            displayTableData = window.FlattenManager.filterTableDataByRedundantColumns(displayTableData, true);
        }
        
        // Check NaN row toggle state
        const nanRowCheckbox = container.querySelector('.nan-row-checkbox');
        const showNaNRows = nanRowCheckbox ? nanRowCheckbox.checked : false;
        
        // Apply NaN row filtering
        if (!showNaNRows) {
            displayTableData = window.FlattenManager.filterTableDataByNaNRows(displayTableData, true);
        }
        
        // Update table HTML
        const newTableHtml = createHierarchicalHtmlTable(displayTableData, tableData.filename || 'Table');
        tableView.innerHTML = newTableHtml;
        
        // Update info text with hidden counts
        const tableContainer = tableView.querySelector('.table-container');
        if (tableContainer) {
            const infoDiv = tableContainer.querySelector('.table-info');
            if (infoDiv) {
                let additionalInfo = [];
                
                if (!showNaNRows && displayTableData.nan_rows_hidden) {
                    additionalInfo.push(`${displayTableData.nan_rows_hidden} NaN rows hidden`);
                }
                
                if (!showAllFeatureCols && displayTableData.redundant_columns_hidden) {
                    additionalInfo.push(`${displayTableData.redundant_columns_hidden} redundant feature rows hidden`);
                }
                
                if (additionalInfo.length > 0) {
                    infoDiv.innerHTML += ` (${additionalInfo.join(', ')})`;
                }
            }
        }
    }
    
    // Add event listener for feature column toggle
    featureColCheckbox.addEventListener('change', updateTable);
    
    // Initialize with redundant feature columns hidden (checkbox unchecked by default)
    updateTable();
}

// Setup table download functionality
function setupTableDownloadEvents(container) {
    const downloadBtn = container.querySelector('.table-download-btn');
    if (!downloadBtn) return;
    
    const resultIndex = parseInt(container.getAttribute('data-result-index'));
    
    if (!downloadBtn) return;
    
    downloadBtn.addEventListener('click', function() {
        downloadTableData(resultIndex);
    });
}

// Download table data in multiple formats
function downloadTableData(resultIndex) {
    const tableData = window.FlattenManager.getTableDataFromResult(resultIndex);
    if (!tableData) {
        console.error('No table data found for result index:', resultIndex);
        return;
    }
    
    // Get current table state (with any active filters and flattening)
    // Use specific selector to find the correct table container
    const container = document.querySelector(`div[data-result-index="${resultIndex}"].table-flatten-container, div[data-result-index="${resultIndex}"].table-simple-container`);
    if (!container) {
        console.error('Table container not found for result index:', resultIndex);
        return;
    }
    
    let currentTableData = { ...tableData };
    
    // Apply current flatten level if it's a hierarchical table
    const levelDisplay = container.querySelector('.flatten-level-display');
    if (levelDisplay) {
        const currentLevel = parseInt(levelDisplay.getAttribute('data-current-level')) || 0;
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
    
    // Show download options modal
    showDownloadModal(currentTableData, resultIndex);
}

// Show download options modal
function showDownloadModal(tableData, resultIndex) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Download Table</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <p>Download table data with current flattening and filters applied:</p>
                <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 20px;">
                    <button class="btn btn-primary download-json-btn">
                        <i class="fas fa-file-code"></i> Download as JSON
                    </button>
                </div>
                <div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 0.85rem; color: #888;">
                    <i class="fas fa-info-circle" style="color: #10a37f; margin-right: 6px;"></i>
                    Export includes flattened column names and applied filters
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Event listeners for modal
    const closeBtn = modal.querySelector('.close');
    const jsonBtn = modal.querySelector('.download-json-btn');
    
    function closeModal() {
        document.body.removeChild(modal);
    }
    
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeModal();
    });
    
    jsonBtn.addEventListener('click', function() {
        downloadAsJSON(tableData, resultIndex);  // tableData is actually the currentTableData passed from downloadTableData()
        closeModal();
    });
}

// Download as JSON format for plotting (SIMPLIFIED VERSION)
function downloadAsJSON(tableData, resultIndex) {
    const filename = (tableData.filename || 'table').replace(/\.[^/.]+$/, '') + '_plotting_data.json';
    
    // Get the original backend data 
    const originalTableData = window.FlattenManager.getTableDataFromResult(resultIndex);
    
    // Find the SPECIFIC table container for this exact resultIndex
    // CRITICAL: Must be the exact container, not influenced by other tables on the page
    const specificContainerSelector = `div[data-result-index="${resultIndex}"]`;
    const allContainers = document.querySelectorAll(specificContainerSelector);
    
    console.log(`🔍 [CONTAINER DEBUG] Looking for result index ${resultIndex} (type: ${typeof resultIndex}):`);
    console.log(`  - Found ${allContainers.length} elements with data-result-index="${resultIndex}"`);
    
    // 🔍 CRITICAL: Show ALL table containers in DOM to detect pollution
    const allTableContainers = document.querySelectorAll('.table-flatten-container, .table-simple-container');
    console.log(`🌍 [DOM STATE] Total table containers in DOM: ${allTableContainers.length}`);
    allTableContainers.forEach((container, index) => {
        const elemResultIndex = container.getAttribute('data-result-index');
        const levelDisplay = container.querySelector('.flatten-level-display');
        const level = levelDisplay ? levelDisplay.getAttribute('data-current-level') : 'none';
        const visible = container.offsetParent !== null;
        console.log(`  Container ${index}: resultIndex=${elemResultIndex}, level=${level}, visible=${visible}, class=${container.className}`);
    });
    
    // Find the VISIBLE/ACTIVE main container (not detached/duplicate containers)
    let container = null;
    let levelDisplay = null;
    let currentFlattenLevel = 0;
    
    // CRITICAL: Filter out detached/invisible elements first
    const visibleContainers = Array.from(allContainers).filter(elem => {
        // Check if element is attached to DOM and visible
        const isAttached = document.contains(elem);
        const isVisible = elem.offsetParent !== null || elem.style.display !== 'none';
        
        // Additional verification: Check if this element actually belongs to the right table
        const elemResultIndex = parseInt(elem.getAttribute('data-result-index'));
        const resultIndexMatch = elemResultIndex === resultIndex;
        
        console.log(`    ${elem.tagName}.${elem.className}: attached=${isAttached}, visible=${isVisible}, resultIndex=${elemResultIndex}, match=${resultIndexMatch}`);
        return isAttached && isVisible && resultIndexMatch;
    });
    
    console.log(`    🔍 Filtered to ${visibleContainers.length} visible containers from ${allContainers.length} total`);
    
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
            const buttonsResponsive = upBtn && !upBtn.disabled !== !downBtn.disabled; // At least one should be enabled
            
            console.log(`    ${elem.tagName}.${elem.className}: controls=${hasTableControls}, buttons=${hasValidButtons}, level=${levelAttr}, responsive=${buttonsResponsive}`);
            
            if (hasValidButtons && levelAttr !== null) {
                isActiveContainer = true;
            }
        } else {
            console.log(`    ${elem.tagName}.${elem.className}: controls=${hasTableControls}, simple=${isSimple}`);
            isActiveContainer = hasTableControls || isSimple;
        }
        
        if (isActiveContainer) {
            container = elem;
            
            // 🔍 CRITICAL DEBUG: Show full container details
            const containerLevelDisplay = container.querySelector('.flatten-level-display');
            const containerLevel = containerLevelDisplay ? containerLevelDisplay.getAttribute('data-current-level') : 'none';
            const containerParent = container.parentElement;
            const containerIndex = Array.from(document.querySelectorAll('.table-flatten-container, .table-simple-container')).indexOf(container);
            
            console.log(`    ✅ Selected as VISIBLE ACTIVE main container:`);
            console.log(`       🏷️ Result Index: ${resultIndex}`);
            console.log(`       📊 Container Level: ${containerLevel}`);
            console.log(`       📍 Container Index in DOM: ${containerIndex}`);
            console.log(`       🔗 Parent: ${containerParent?.className || 'none'}`);
            console.log(`       📂 Container ID/classes: ${container.className}`);
            
            break;
        }
    }
    
    if (!container) {
        console.error(`❌ [CONTAINER] No active main container found for result index ${resultIndex}`);
        currentFlattenLevel = 0;
    } else {
        console.log(`✅ [CONTAINER] Using ACTIVE container: ${container.className}`);
        
        // Get level display from THIS specific ACTIVE container only
        levelDisplay = container.querySelector('.flatten-level-display');
        currentFlattenLevel = levelDisplay ? parseInt(levelDisplay.getAttribute('data-current-level')) || 0 : 0;
        
        console.log(`🔍 [LEVEL DEBUG] For result ${resultIndex}:`);
        console.log(`  - Level display found: ${levelDisplay ? 'Yes' : 'No'}`);
        console.log(`  - Level attribute: ${levelDisplay?.getAttribute('data-current-level') || 'N/A'}`);
        console.log(`  - Calculated level: ${currentFlattenLevel}`);
        
        // VERIFY by checking button states
        if (container.classList.contains('table-flatten-container')) {
            const upBtn = container.querySelector('.flatten-up');
            const downBtn = container.querySelector('.flatten-down');
            console.log(`  - UP button disabled: ${upBtn?.disabled} (level >= max: ${currentFlattenLevel >= parseInt(container.getAttribute('data-max-levels') || '0')})`);
            console.log(`  - DOWN button disabled: ${downBtn?.disabled} (level <= 0: ${currentFlattenLevel <= 0})`);
        }
    }
    
    // Debug logging for multi-table download issue
    console.log(`🔍 [DOWNLOAD DEBUG] Result Index: ${resultIndex}`);
    console.log(`🔍 [DOWNLOAD DEBUG] Container found: ${container ? 'Yes' : 'No'}`);
    console.log(`🔍 [DOWNLOAD DEBUG] Container class: ${container?.className || 'N/A'}`);
    console.log(`🔍 [DOWNLOAD DEBUG] Level display found: ${levelDisplay ? 'Yes' : 'No'}`);
    console.log(`🔍 [DOWNLOAD DEBUG] Level display attribute: ${levelDisplay?.getAttribute('data-current-level') || 'N/A'}`);
    console.log(`🔍 [DOWNLOAD DEBUG] Calculated flatten level: ${currentFlattenLevel}`);
    
    // Debug: Show all elements with this result index
    const allElementsWithIndex = document.querySelectorAll(`[data-result-index="${resultIndex}"]`);
    console.log(`🔍 [DOWNLOAD DEBUG] All elements with result-index ${resultIndex}:`, allElementsWithIndex.length);
    allElementsWithIndex.forEach((el, i) => {
        console.log(`  ${i}: ${el.tagName}.${el.className} - ${el.getAttribute('data-current-level') || 'no-level'}`);
    });
    
    // Get current feature_rows (after redundant filtering)
    const currentFeatureRows = tableData.feature_rows || [];
    
    // Get feature_cols for current flattened table (descendants of original feature_cols)
    const currentFeatureCols = identifyCurrentFeatureCols(tableData, originalTableData, currentFeatureRows);
    
    // Create simplified plotting data structure
    const plotDataSchema = {
        filename: tableData.filename,
        has_multiindex: tableData.has_multiindex,
        header_matrix: tableData.header_matrix,       // Current header structure
        final_columns: tableData.final_columns,       // Current column names
        data_rows: tableData.data_rows,               // Current filtered data
        row_count: tableData.row_count,
        col_count: tableData.col_count,
        
        // CRITICAL FOR PLOTTING:
        feature_rows: currentFeatureRows,             // Filtered feature rows (grouping columns)
        feature_cols: currentFeatureCols,             // Data columns in flattened table
        
        export_timestamp: new Date().toISOString(),
        flatten_level_applied: currentFlattenLevel,
        filters_applied: {
            nan_rows_hidden: tableData.nan_rows_hidden || 0,
            redundant_columns_hidden: tableData.redundant_columns_hidden || 0
        }
    };
    
    // 🔍 ENHANCED DEBUG FOR HEADER MATRIX DOWNLOAD ISSUE
    console.log(`💾 [DOWNLOAD] DETAILED HEADER MATRIX ANALYSIS:`);
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
    
    console.log(`💾 [DOWNLOAD] HEADER MATRIX STRUCTURE:`, JSON.stringify(plotDataSchema.header_matrix, null, 2));
    console.log(`💾 [DOWNLOAD] TABLE METADATA:`);
    console.log(`  - has_multiindex: ${plotDataSchema.has_multiindex}`);
    console.log(`  - final_columns: [${plotDataSchema.final_columns?.join(', ') || 'undefined'}]`);
    console.log(`  - final_columns count: ${plotDataSchema.final_columns?.length || 0}`);
    console.log(`  - data_rows count: ${plotDataSchema.data_rows?.length || 0}`);
    console.log(`  - data_row[0] length: ${plotDataSchema.data_rows?.[0]?.length || 0}`);
    console.log(`  - feature_rows: [${plotDataSchema.feature_rows?.join(', ') || 'undefined'}]`);
    console.log(`  - feature_cols: [${plotDataSchema.feature_cols?.join(', ') || 'undefined'}]`);
    console.log(`  - flatten_level_applied: ${plotDataSchema.flatten_level_applied}`);
    
    window.Utils.saveJsonToFile(plotDataSchema, filename);
    console.log(`📊 Plotting data saved to: ${filename}`);
    console.log(`📈 Result Index: ${resultIndex}`);
    console.log(`📈 Flatten level: ${currentFlattenLevel}`);
    console.log(`🎯 Feature rows: [${currentFeatureRows.join(', ')}]`);
    console.log(`📊 Feature cols: [${currentFeatureCols.join(', ')}]`);
    console.log(`🔍 Container found: ${container ? 'Yes' : 'No'} (${container?.className || 'N/A'})`);
}

// Identify feature_cols in the current flattened table
function identifyCurrentFeatureCols(currentTableData, originalTableData, currentFeatureRows) {
    const isHierarchical = currentTableData.has_multiindex;
    const currentColumns = currentTableData.final_columns || [];
    const featureRowsCount = currentFeatureRows.length;
    
    console.log(`🔍 Identifying feature cols:`);
    console.log(`  - Original feature_cols: [${originalTableData?.feature_cols?.join(', ') || 'MISSING'}]`);
    console.log(`  - Current columns: [${currentColumns.join(', ')}]`);
    console.log(`  - Feature rows count: ${featureRowsCount}`);
    console.log(`  - Is hierarchical: ${isHierarchical}`);
    
    // Remove early return - calculate feature_cols even if original is missing
    if (!originalTableData || !originalTableData.feature_cols || originalTableData.feature_cols.length === 0) {
        console.warn(`🔧 Original feature_cols missing, using fallback calculation`);
        
        if (isHierarchical) {
            // Fallback for hierarchical: Find data headers from header matrix
            const parentHeaders = findTopLevelDataParents(currentTableData, originalTableData);
            console.log(`  - Fallback hierarchical feature_cols: [${parentHeaders.join(', ')}]`);
            return parentHeaders;
        } else {
            // Fallback for flattened: Assume all columns after feature rows are data columns
            const dataColumns = currentColumns.slice(featureRowsCount);
            console.log(`  - Fallback flattened feature_cols: [${dataColumns.join(', ')}]`);
            return dataColumns;
        }
    }
    
    if (isHierarchical) {
        // LEVEL 0 (Hierarchical): Return top-level parent headers that span data columns
        const parentHeaders = findTopLevelDataParents(currentTableData, originalTableData);
        console.log(`  - Top-level data parents: [${parentHeaders.join(', ')}]`);
        return parentHeaders;
    } else {
        // LEVEL 1+ (Flattened): Return actual data column names (after feature rows)
        const dataColumns = currentColumns.slice(featureRowsCount);
        console.log(`  - Data columns (flattened): [${dataColumns.join(', ')}]`);
        return dataColumns;
    }
}

// Find top-level parent headers that span data columns (not feature rows)
function findTopLevelDataParents(currentTableData, originalTableData) {
    const headerMatrix = currentTableData.header_matrix;
    if (!headerMatrix || headerMatrix.length === 0) {
        return [];
    }
    
    const topLevel = headerMatrix[0] || [];
    const dataParents = [];
    const originalFeatureRows = originalTableData?.feature_rows || [];
    
    for (const header of topLevel) {
        // A header is a data column if it's not a feature row header
        // Remove the incorrect colspan > 1 requirement - single data columns also have colspan = 1
        const isFeatureRowHeader = originalFeatureRows.includes(header.text);
        
        if (!isFeatureRowHeader) {
            // This is a data column header (either single or spanning multiple columns)
            dataParents.push(header.text);
        }
    }
    
    console.log(`  - Top level headers: [${topLevel.map(h => `"${h.text}"(${h.colspan}c,${h.rowspan}r)`).join(', ')}]`);
    console.log(`  - Feature rows: [${originalFeatureRows.join(', ')}]`);
    console.log(`  - Data parent headers: [${dataParents.join(', ')}]`);
    
    return dataParents;
}



// Setup plotting events for table
function setupTablePlottingEvents(container) {
    // Find all plot buttons within the container (since container might be messageContent)
    const plotBtns = container.querySelectorAll('.plot-table-btn');
    
    plotBtns.forEach(plotBtn => {
        plotBtn.addEventListener('click', function() {
            // Get the result index from the button's own data attribute
            const resultIndex = plotBtn.getAttribute('data-result-index');
            console.log(`🎯 [TABLE] Plot button clicked for result ${resultIndex}`);
            
            // Check if PlottingManager is available
            if (window.PlottingManager) {
                window.PlottingManager.initializePlotting(resultIndex);
            } else {
                console.error('PlottingManager not available');
                showError('Plotting functionality not loaded');
            }
        });
    });
    
    if (plotBtns.length === 0) {
        console.warn('No plot buttons found in container');
    } else {
        console.log(`✅ [TABLE] Set up ${plotBtns.length} plot button(s)`);
    }
}

// Export table functions
window.TableManager = {
    createHierarchicalHtmlTable,
    formatTableData,
    setupTableToggleEvents,
    setupNaNRowToggle,
    setupFeatureColToggle,
    setupTableDownloadEvents,
    setupTablePlottingEvents,
    downloadTableData,
    downloadAsJSON,
    identifyCurrentFeatureCols,
    findTopLevelDataParents,
    debugHeaders: function(resultIndex, level) {
        return window.FlattenManager.debugHeaders(resultIndex, level);
    }
};

console.log('✅ Table.js loaded'); 