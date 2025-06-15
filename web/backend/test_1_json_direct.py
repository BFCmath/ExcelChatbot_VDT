#!/usr/bin/env python3
"""
Test the 1.json file directly with the plotting system
"""

import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.plotting import PlotGenerator

def test_1_json():
    """Test the 1.json file directly"""
    
    # Load the 1.json file
    with open('../../1.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("🧪 TESTING 1.JSON WITH PLOTTING SYSTEM")
    print("=" * 60)
    
    # Display data structure info
    print(f"📊 Filename: {data.get('filename')}")
    print(f"📋 final_columns length: {len(data.get('final_columns', []))}")
    print(f"📋 data_rows[0] length: {len(data.get('data_rows', [[]])[0])}")
    print(f"📋 col_count: {data.get('col_count')}")
    print(f"📋 row_count: {data.get('row_count')}")
    print(f"🏗️  has_multiindex: {data.get('has_multiindex')}")
    print(f"📈 feature_rows: {data.get('feature_rows')}")
    print(f"📈 feature_cols: {data.get('feature_cols')}")
    
    print(f"\n🔍 DETAILED STRUCTURE:")
    print(f"  final_columns: {data.get('final_columns')}")
    print(f"  data_rows[0]: {data.get('data_rows', [[]])[0]}")
    print(f"  header_matrix levels: {len(data.get('header_matrix', []))}")
    
    # Test with plotting system
    print(f"\n🎨 TESTING WITH PLOTTING SYSTEM:")
    plot_generator = PlotGenerator()
    result = plot_generator.generate_plot(data)
    
    print(f"✅ Success: {result.get('success')}")
    if result.get('success'):
        print(f"📊 Plot type: {result.get('plot_type')}")
        print(f"📈 Data points: {result.get('data_points')}")
        print(f"💬 Message: {result.get('message')}")
        
        # Save HTML files
        plots = result.get('plots', {})
        if 'column_first' in plots:
            with open('test_1_json_column.html', 'w', encoding='utf-8') as f:
                f.write(plots['column_first']['html_content'])
            print(f"💾 Saved: test_1_json_column.html")
            
        if 'row_first' in plots:
            with open('test_1_json_row.html', 'w', encoding='utf-8') as f:
                f.write(plots['row_first']['html_content'])
            print(f"💾 Saved: test_1_json_row.html")
    else:
        print(f"❌ Error: {result.get('error')}")
        print(f"📋 Full result: {result}")

if __name__ == "__main__":
    test_1_json() 