#!/usr/bin/env python3
"""
Interactive Plotting System Test
================================

This script allows you to test the plotting system with any JSON file.
You can interactively enter file paths and see both column-first and row-first sunburst charts.
"""

import json
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.plotting import PlotGenerator

def display_banner():
    """Display the test banner"""
    print("=" * 70)
    print("🎯 INTERACTIVE PLOTTING SYSTEM TEST")
    print("=" * 70)
    print("📊 This tool tests sunburst chart generation from JSON files")
    print("🔄 Generates both column-first and row-first variants")
    print("📁 Enter JSON file paths to test with your data")
    print("💡 Type 'quit' or 'exit' to stop")
    print("=" * 70)

def load_and_validate_json(file_path):
    """Load and validate JSON file"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        # Load JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation
        required_fields = ['final_columns', 'data_rows', 'feature_rows', 'feature_cols']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"⚠️  Warning: Missing fields: {missing_fields}")
            print("📝 This might still work if it's a valid frontend JSON format")
        
        # Display basic info
        print(f"✅ Loaded JSON successfully")
        print(f"📊 Filename: {data.get('filename', 'Unknown')}")
        print(f"📋 Rows: {len(data.get('data_rows', []))}")
        print(f"📋 Columns: {len(data.get('final_columns', []))}")
        print(f"🏗️  Has hierarchy: {data.get('has_multiindex', False)}")
        print(f"🎯 Feature rows: {data.get('feature_rows', [])}")
        print(f"📈 Feature cols: {data.get('feature_cols', [])}")
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None

def test_plotting(json_data, file_path):
    """Test the plotting system with the loaded JSON data"""
    try:
        print(f"\n🔄 TESTING PLOTTING SYSTEM")
        print(f"📁 File: {os.path.basename(file_path)}")
        print("-" * 50)
        
        # Initialize plot generator
        plot_generator = PlotGenerator()
        
        # Generate plots
        print("🎨 Generating sunburst plots...")
        result = plot_generator.generate_plot(json_data)
        
        if result.get('success'):
            print("✅ SUCCESS: Plots generated successfully!")
            print(f"📊 Plot type: {result.get('plot_type')}")
            print(f"📈 Data points: {result.get('data_points')}")
            print(f"💬 Message: {result.get('message')}")
            
            # Display analysis
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"\n📊 ANALYSIS:")
                print(f"   🏷️  Categorical columns: {analysis.get('categorical_columns', [])}")
                print(f"   📏 Hierarchy levels: {analysis.get('hierarchy_levels', 0)}")
                print(f"   💰 Total value: {analysis.get('total_value', 0)}")
                print(f"   🔢 Unique categories: {analysis.get('unique_categories', {})}")
            
            # Display plots info
            plots = result.get('plots', {})
            if plots:
                print(f"\n🎯 GENERATED PLOTS:")
                
                # Column-first plot
                if 'column_first' in plots:
                    col_plot = plots['column_first']
                    print(f"   📊 Column-first: {col_plot.get('title', 'Untitled')}")
                    print(f"      📋 Hierarchy: {' → '.join(col_plot.get('hierarchy', []))}")
                    
                    # Save HTML file
                    output_file = f"interactive_test_column_{os.path.splitext(os.path.basename(file_path))[0]}.html"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(col_plot.get('html_content', ''))
                    print(f"      💾 Saved: {output_file}")
                
                # Row-first plot
                if 'row_first' in plots:
                    row_plot = plots['row_first']
                    print(f"   📊 Row-first: {row_plot.get('title', 'Untitled')}")
                    print(f"      📋 Hierarchy: {' → '.join(row_plot.get('hierarchy', []))}")
                    
                    # Save HTML file
                    output_file = f"interactive_test_row_{os.path.splitext(os.path.basename(file_path))[0]}.html"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(row_plot.get('html_content', ''))
                    print(f"      💾 Saved: {output_file}")
            
            print(f"\n🎉 Test completed successfully!")
            print(f"🌐 Open the generated HTML files in your browser to view the charts")
            
        else:
            print("❌ FAILED: Plot generation failed")
            print(f"💬 Error: {result.get('error', 'Unknown error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error during plotting test: {e}")
        return False

def interactive_menu():
    """Show interactive menu options"""
    print(f"\n📋 OPTIONS:")
    print(f"   1. Test with JSON file path")
    print(f"   2. Test with sample data")
    print(f"   3. Show recent HTML files")
    print(f"   4. Help")
    print(f"   5. Quit")
    
    choice = input("\n👉 Enter your choice (1-5): ").strip()
    return choice

def show_recent_html_files():
    """Show recently generated HTML files"""
    html_files = [f for f in os.listdir('.') if f.endswith('.html') and 'interactive_test' in f]
    
    if html_files:
        print(f"\n📁 RECENT HTML FILES:")
        for i, file in enumerate(html_files, 1):
            file_size = os.path.getsize(file)
            print(f"   {i}. {file} ({file_size:,} bytes)")
        print(f"\n💡 Open these files in your browser to view the charts")
    else:
        print(f"\n📁 No recent HTML files found")
        print(f"💡 Generate some plots first to see output files")

def create_sample_data():
    """Create sample data for testing"""
    sample_data = {
        "filename": "sample_test.xlsx",
        "has_multiindex": True,
        "header_matrix": [
            [
                {"text": "Category", "position": 0, "colspan": 1},
                {"text": "Type", "position": 1, "colspan": 1},
                {"text": "Year 2024", "position": 2, "colspan": 3}
            ],
            [
                {"text": "Q1", "position": 2, "colspan": 1},
                {"text": "Q2", "position": 3, "colspan": 1},
                {"text": "Q3", "position": 4, "colspan": 1}
            ]
        ],
        "final_columns": ["Category", "Type", "Q1", "Q2", "Q3"],
        "data_rows": [
            ["Sales", "Product A", 100, 150, 200],
            ["Sales", "Product B", 80, 120, 160],
            ["Marketing", "Campaign X", 50, 75, 100],
            ["Marketing", "Campaign Y", 60, 90, 120]
        ],
        "feature_rows": ["Category", "Type"],
        "feature_cols": ["Year 2024"]
    }
    
    # Save sample data
    sample_file = "sample_interactive_test.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Created sample data: {sample_file}")
    return sample_file

def show_help():
    """Show help information"""
    print(f"\n📚 HELP - How to use this tool:")
    print(f"=" * 50)
    print(f"1️⃣  FILE PATH FORMAT:")
    print(f"   • Absolute path: C:\\full\\path\\to\\file.json")
    print(f"   • Relative path: ./data/file.json")
    print(f"   • Current directory: filename.json")
    print(f"")
    print(f"2️⃣  SUPPORTED JSON FORMAT:")
    print(f"   • Must have: final_columns, data_rows, feature_rows, feature_cols")
    print(f"   • Optional: header_matrix (for hierarchical data)")
    print(f"   • Should be from frontend table download")
    print(f"")
    print(f"3️⃣  OUTPUT:")
    print(f"   • Generates both column-first and row-first charts")
    print(f"   • Saves HTML files in current directory")
    print(f"   • Files named: interactive_test_[type]_[filename].html")
    print(f"")
    print(f"4️⃣  TROUBLESHOOTING:")
    print(f"   • Check file exists and is readable")
    print(f"   • Verify JSON is valid (not corrupted)")
    print(f"   • Ensure data has both categorical and numeric columns")
    print(f"=" * 50)

def main():
    """Main interactive loop"""
    display_banner()
    
    while True:
        try:
            choice = interactive_menu()
            
            if choice in ['5', 'quit', 'exit', 'q']:
                print(f"\n👋 Goodbye! Thanks for testing the plotting system!")
                break
            
            elif choice == '1':
                # Test with user-provided JSON file
                file_path = input(f"\n📁 Enter JSON file path: ").strip()
                
                if not file_path:
                    print(f"❌ No file path provided")
                    continue
                
                print(f"\n📂 Loading: {file_path}")
                json_data = load_and_validate_json(file_path)
                
                if json_data:
                    test_plotting(json_data, file_path)
                
            elif choice == '2':
                # Test with sample data
                print(f"\n🧪 Creating sample data for testing...")
                sample_file = create_sample_data()
                
                json_data = load_and_validate_json(sample_file)
                if json_data:
                    test_plotting(json_data, sample_file)
                
            elif choice == '3':
                # Show recent HTML files
                show_recent_html_files()
                
            elif choice == '4':
                # Show help
                show_help()
                
            else:
                print(f"❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print(f"💡 Please try again or check your input")

if __name__ == "__main__":
    main() 