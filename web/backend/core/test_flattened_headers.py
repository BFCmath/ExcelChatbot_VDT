"""
Test script for the flattened headers functionality.
Tests the acronym generation and header flattening with various examples.
"""

import pandas as pd
import sys
import os

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.postprocess import TablePostProcessor

def test_acronym_generation():
    """Test the acronym generation function with various inputs."""
    processor = TablePostProcessor()
    
    test_cases = [
        ("chi phí", "cp"),
        ("Chi Phí", "CP"),  # Case preserved
        ("cấp 1", "c1"),
        ("Cấp 1", "C1"),  # Case preserved
        ("năm 2024", "n2024"),
        ("Năm 2024", "N2024"),  # Case preserved
        ("học kì 1", "hk1"),
        ("Học Kì 1", "HK1"),  # Case preserved
        ("tên", "t"),
        ("Tên", "T"),  # Case preserved
        ("quý 1", "q1"),
        ("tháng 12", "t12"),
        ("doanh thu năm 2023", "dtn2023"),
        ("Header", "H"),  # Case preserved
        ("123", "123"),
        ("a1b2c3", "a123"),  # First letter + numbers
        ("test case", "tc"),
        ("Test Case", "TC"),  # Case preserved
    ]
    
    print("="*60)
    print("TESTING ACRONYM GENERATION")
    print("="*60)
    
    for input_text, expected in test_cases:
        result = processor.create_acronym(input_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{input_text}' -> Output: '{result}' (Expected: '{expected}')")
    
    print()

def test_flattened_headers():
    """Test the flattened headers creation with a sample MultiIndex DataFrame."""
    
    print("="*60)
    print("TESTING FLATTENED HEADERS")
    print("="*60)
    
    # Create a sample MultiIndex DataFrame similar to the user's example
    level1 = ['Chi Phí', 'Chi Phí', 'Chi Phí', 'Chi Phí', 'Tên', 'Tên']
    level2 = ['Cấp 1', 'Cấp 1', 'Cấp 2', 'Cấp 2', 'Header', 'Header']
    level3 = ['Học kì 1', 'Học kì 2', 'Học kì 1', 'Học kì 2', 'Header', 'Header']
    
    columns = pd.MultiIndex.from_arrays([level1, level2, level3], names=['Level1', 'Level2', 'Level3'])
    
    # Create sample data
    data = [
        [100, 150, 200, 250, 'Nguyễn Văn A', 'Male'],
        [120, 170, 220, 270, 'Trần Thị B', 'Female'],
        [110, 160, 210, 260, 'Lê Văn C', 'Male'],
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    print("Original DataFrame structure:")
    print("Columns:", df.columns.tolist())
    print()
    
    # Test the flattened headers creation
    processor = TablePostProcessor()
    flattened_headers = processor.create_flattened_headers(df.columns)
    
    print("Flattened Headers:")
    for i, header in enumerate(flattened_headers):
        print(f"  Column {i}: '{header}'")
    print()
    
    # Test the full table extraction
    try:
        table_structures = processor.extract_hierarchical_table_info(df)
        
        print("Normal Table Info:")
        print(f"  Has MultiIndex: {table_structures['normal_table']['has_multiindex']}")
        print(f"  Header Matrix Levels: {len(table_structures['normal_table']['header_matrix'])}")
        print(f"  Final Columns: {table_structures['normal_table']['final_columns']}")
        print()
        
        print("Flattened Table Info:")
        print(f"  Has MultiIndex: {table_structures['flattened_table']['has_multiindex']}")
        print(f"  Header Matrix Levels: {len(table_structures['flattened_table']['header_matrix'])}")
        print(f"  Final Columns: {table_structures['flattened_table']['final_columns']}")
        print()
    except Exception as e:
        print(f"Error in table extraction: {e}")
        print("Continuing with header comparison...")
        print()
    
    print("Expected flattened format based on user's requirements:")
    print("  Level 1: Chi Phí")
    print("    Level 2: Cấp 1")
    print("      Level 3: Học kì 1, Học kì 2")
    print("    Level 2: Cấp 2")
    print("      Level 3: Học kì 1, Học kì 2")
    print("  Should become: CP C1 Học kì 1, CP C1 Học kì 2, CP C2 Học kì 1, CP C2 Học kì 2")
    print("  (Note: Only intermediate levels get acronyms, final level stays as-is, case preserved)")
    print()
    
    # Show actual flattened result for Chi Phí columns
    chi_phi_columns = [header for header in flattened_headers if 'CP' in header or 'cp' in header.lower()]
    print("Actual flattened Chi Phí columns:", chi_phi_columns)
    
    # Show vertical merge result for Tên columns  
    ten_columns = [header for header in flattened_headers if 'Tên' in header or 'tên' in header.lower()]
    print("Actual flattened Tên columns:", ten_columns)
    
    # Verify expected results
    expected_headers = [
        "CP C1 Học kì 1",
        "CP C1 Học kì 2", 
        "CP C2 Học kì 1",
        "CP C2 Học kì 2",
        "Tên",
        "Tên"
    ]
    
    print("\n✓ Expected vs Actual Results:")
    for i, (expected, actual) in enumerate(zip(expected_headers, flattened_headers)):
        status = "✓" if expected == actual else "✗"
        print(f"  {i+1}. Expected: '{expected}' | Actual: '{actual}' {status}")

def test_simple_columns():
    """Test with simple (non-MultiIndex) columns."""
    
    print("="*60)
    print("TESTING SIMPLE COLUMNS")
    print("="*60)
    
    # Create a simple DataFrame
    df_simple = pd.DataFrame({
        'Name': ['John', 'Jane'],
        'Age': [25, 30],
        'City': ['NY', 'LA']
    })
    
    processor = TablePostProcessor()
    table_structures = processor.extract_hierarchical_table_info(df_simple)
    
    print("Simple DataFrame columns:", df_simple.columns.tolist())
    print("Normal table final columns:", table_structures['normal_table']['final_columns'])
    print("Flattened table final columns:", table_structures['flattened_table']['final_columns'])
    print("Should be identical for simple columns: ", 
          table_structures['normal_table']['final_columns'] == table_structures['flattened_table']['final_columns'])
    print()

if __name__ == "__main__":
    print("FLATTENED HEADERS FUNCTIONALITY TEST")
    print("="*60)
    print()
    
    # Run all tests
    test_acronym_generation()
    test_flattened_headers()  
    test_simple_columns()
    
    print("="*60)
    print("TEST COMPLETED")
    print("="*60) 