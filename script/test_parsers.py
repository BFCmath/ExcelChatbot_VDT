"""
Test script to validate parser updates for new prompt formats.
"""

def test_decomposer_parser():
    """Test the decomposer parser with the new format."""
    from llm import parse_decomposer_output
    
    # Test data that matches the new decomposer prompt output format
    test_output = """
### Thinking
Câu truy vấn là: "cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè".
Các keyword chính được xác định: "cà phê đen", "việt nam", "giá", "tháng hè".

1. **Keyword: "cà phê đen"**
   Kiểm tra trong: `Row Hierarchy`.
   Phát hiện: "cà phê đen" nằm dưới `Feature Row` "Cà phê".
   Kết luận: Đây là một `Row Keyword`.

### Row Keywords
- cà phê đen
- việt nam

### Col Keywords
- tháng hè
"""
    
    print("🧪 Testing Decomposer Parser")
    print("=" * 50)
    
    result = parse_decomposer_output(test_output)
    
    print("Input:", test_output)
    print("\nParsed Result:")
    print(f"Row Keywords: {result['row_keywords']}")
    print(f"Col Keywords: {result['col_keywords']}")
    
    # Expected results
    expected_row = ['cà phê đen', 'việt nam']
    expected_col = ['tháng hè']
    
    assert result['row_keywords'] == expected_row, f"Expected {expected_row}, got {result['row_keywords']}"
    assert result['col_keywords'] == expected_col, f"Expected {expected_col}, got {result['col_keywords']}"
    
    print("✅ Decomposer parser test PASSED!")
    return True


def test_separator_parser():
    """Test the separator parser with the new format."""
    from multifile import MultiFileProcessor
    
    # Create a processor instance to test the parser
    processor = MultiFileProcessor()
    
    # Test data that matches the new separator prompt output format
    test_output = """
### Thinking
The user query asks for the wholesale price of black coffee. The query doesn't specify a year. File 'example2.xlsx' contains coffee export prices for 2023, including wholesale. File 'example4.xlsx' contains coffee export prices for 2024, also including wholesale. Both files are potentially relevant due to the unspecified time. Therefore, the query should be directed to both files to cover all possibilities.

### Separated Query
example2.xlsx - Cà phê đen có giá sĩ khoảng bao nhiêu
example4.xlsx - Cà phê đen có giá sĩ khoảng bao nhiêu
"""
    
    print("\n🧪 Testing Separator Parser")
    print("=" * 50)
    
    result = processor.parse_separator_response(test_output)
    
    print("Input:", test_output)
    print("\nParsed Result:")
    for i, assignment in enumerate(result, 1):
        print(f"{i}. File: {assignment['file']}")
        print(f"   Query: {assignment['query']}")
        print(f"   Reasoning: {assignment['reasoning']}")
    
    # Expected results
    expected_assignments = [
        {'file': 'example2.xlsx', 'query': 'Cà phê đen có giá sĩ khoảng bao nhiêu', 'reasoning': 'From query separator analysis'},
        {'file': 'example4.xlsx', 'query': 'Cà phê đen có giá sĩ khoảng bao nhiêu', 'reasoning': 'From query separator analysis'}
    ]
    
    assert len(result) == len(expected_assignments), f"Expected {len(expected_assignments)} assignments, got {len(result)}"
    
    for i, (actual, expected) in enumerate(zip(result, expected_assignments)):
        assert actual['file'] == expected['file'], f"Assignment {i}: Expected file {expected['file']}, got {actual['file']}"
        assert actual['query'] == expected['query'], f"Assignment {i}: Expected query {expected['query']}, got {actual['query']}"
    
    print("✅ Separator parser test PASSED!")
    return True


def test_reporter_functionality():
    """Test the reporter functionality."""
    from reporter import reporter
    
    print("\n🧪 Testing Reporter Functionality")
    print("=" * 50)
    
    # Test single query report
    test_query = "test query for reporting"
    test_result = {
        'row_selection': 'test row selection',
        'col_selection': 'test col selection'
    }
    test_file_info = {
        'filename': 'test.xlsx',
        'feature_rows': ['row1', 'row2'],
        'feature_cols': ['col1', 'col2']
    }
    
    report_id = reporter.save_single_query_report(test_query, test_result, test_file_info, "test")
    print(f"✅ Single query report saved with ID: {report_id}")
    
    # Test summary report
    test_summary = "This is a test summary for validation"
    test_metadata = {
        'feature_rows': ['row1', 'row2'],
        'feature_cols': ['col1', 'col2'],
        'df_shape': (10, 5)
    }
    
    summary_report_id = reporter.save_summary_report("test_file.xlsx", test_metadata, test_summary)
    print(f"✅ Summary report saved with ID: {summary_report_id}")
    
    # Test recent reports display
    print("\n📊 Recent reports:")
    reporter.display_recent_reports_summary(limit=3)
    
    return True


def main():
    """Run all parser tests."""
    print("🚀 TESTING PARSER UPDATES")
    print("=" * 60)
    
    try:
        # Test parsers
        test_decomposer_parser()
        test_separator_parser()
        test_reporter_functionality()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Decomposer parser working correctly")
        print("✅ Separator parser working correctly") 
        print("✅ Reporter functionality working correctly")
        print("✅ Ready to use updated prompts and reporting system")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 