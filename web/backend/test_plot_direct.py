from core.plotting import PlotGenerator
import json

# More realistic sample data structure (similar to what frontend sends)
sample_data = {
    'filename': 'test.xlsx',
    'final_columns': ['Category', 'Type', 'Q1', 'Q2', 'Q3', 'Q4'],
    'data_rows': [
        ['Sales', 'Product A', '100', '150', '200', '250'],
        ['Sales', 'Product B', '80', '120', '160', '200'],
        ['Marketing', 'Product A', '50', '75', '100', '125'],
        ['Marketing', 'Product B', '40', '60', '80', '100']
    ],
    'feature_rows': ['Category', 'Type'],
    'feature_cols': ['Q1', 'Q2', 'Q3', 'Q4'],
    'has_multiindex': True,
    'header_matrix': [
        [
            {'text': 'Category', 'position': 0, 'colspan': 1, 'rowspan': 2},
            {'text': 'Type', 'position': 1, 'colspan': 1, 'rowspan': 2},
            {'text': '2023', 'position': 2, 'colspan': 4, 'rowspan': 1}
        ],
        [
            {'text': 'Q1', 'position': 2, 'colspan': 1, 'rowspan': 1},
            {'text': 'Q2', 'position': 3, 'colspan': 1, 'rowspan': 1},
            {'text': 'Q3', 'position': 4, 'colspan': 1, 'rowspan': 1},
            {'text': 'Q4', 'position': 5, 'colspan': 1, 'rowspan': 1}
        ]
    ]
}

print("Testing PlotGenerator with realistic data...")
generator = PlotGenerator()
result = generator.generate_plot(sample_data)
print('Success:', result.get('success', False))
print('Error:', result.get('error', 'None'))
print('Plot type:', result.get('plot_type', 'None'))
print('Data points:', result.get('data_points', 'None'))

if result.get('success'):
    print('Analysis:', result.get('analysis', {}))
    plots = result.get('plots', {})
    print('Column-first plot available:', 'column_first' in plots)
    print('Row-first plot available:', 'row_first' in plots)
else:
    print('Full result:', result) 