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
        
        // Set default flatten level to max(maxLevels - 2, 0) to save space
        // This shows a nearly flattened view by default
        let currentLevel = Math.max(maxLevels - 1, 0);
        
        function updateTable() {
            let flattenedData = window.FlattenManager.createFlattenedTableData(tableData, currentLevel);
            
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

// Export table functions
window.TableManager = {
    createHierarchicalHtmlTable,
    formatTableData,
    setupTableToggleEvents,
    setupNaNRowToggle,
    setupFeatureColToggle,
    debugHeaders: function(resultIndex, level) {
        return window.FlattenManager.debugHeaders(resultIndex, level);
    }
};

console.log('✅ Table.js loaded'); 