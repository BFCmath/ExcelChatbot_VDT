"""
Query Reporting Module

This module handles saving query results, including both single-file and multi-file queries,
to structured report files for analysis and tracking.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path


class QueryReporter:
    """Handles reporting and saving of query results to files."""
    
    def __init__(self, report_dir="../report"):
        """
        Initialize the QueryReporter.
        
        Args:
            report_dir (str): Directory to save reports in
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of reports
        (self.report_dir / "single_queries").mkdir(exist_ok=True)
        (self.report_dir / "multi_queries").mkdir(exist_ok=True)
        (self.report_dir / "summaries").mkdir(exist_ok=True)
        (self.report_dir / "metadata").mkdir(exist_ok=True)
    
    def generate_report_id(self):
        """Generate a unique report ID based on timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    
    def save_single_query_report(self, query, result, file_info=None, mode="single"):
        """
        Save a single query report.
        
        Args:
            query (str): The natural language query
            result (dict): The processing result
            file_info (dict): Information about the file processed
            mode (str): Processing mode ("single" or "splitter")
        """
        report_id = self.generate_report_id()
        report_data = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "mode": mode,
            "file_info": file_info,
            "result": result
        }
        
        # Save JSON report
        json_file = self.report_dir / "single_queries" / f"query_{report_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Save readable text report
        txt_file = self.report_dir / "single_queries" / f"query_{report_id}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(self._format_single_query_report(report_data))
        
        print(f"📄 Single query report saved: {report_id}")
        return report_id
    
    def save_multi_query_report(self, original_query, assignments, results):
        """
        Save a multi-file query report.
        
        Args:
            original_query (str): The original natural language query
            assignments (list): List of file assignments from query separator
            results (dict): Results from processing each file
        """
        report_id = self.generate_report_id()
        report_data = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "original_query": original_query,
            "assignments": assignments,
            "results": results,
            "files_processed": len(results),
            "total_assignments": len(assignments)
        }
        
        # Save JSON report
        json_file = self.report_dir / "multi_queries" / f"multi_query_{report_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Save readable text report
        txt_file = self.report_dir / "multi_queries" / f"multi_query_{report_id}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(self._format_multi_query_report(report_data))
        
        # Save DataFrame results to Excel if available
        self._save_dataframes_to_excel(report_id, results)
        
        print(f"📄 Multi-query report saved: {report_id}")
        return report_id
    
    def save_summary_report(self, filename, metadata, summary):
        """
        Save a file summary report.
        
        Args:
            filename (str): Name of the file
            metadata (dict): File metadata
            summary (str): Generated summary
        """
        report_id = self.generate_report_id()
        report_data = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "metadata": metadata,
            "summary": summary
        }
        
        # Save JSON report
        json_file = self.report_dir / "summaries" / f"summary_{report_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Save readable text report
        txt_file = self.report_dir / "summaries" / f"summary_{report_id}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(self._format_summary_report(report_data))
        
        print(f"📄 Summary report saved: {report_id}")
        return report_id
    
    def _format_single_query_report(self, report_data):
        """Format single query report as readable text."""
        text = f"""
SINGLE QUERY REPORT
{'='*60}
Report ID: {report_data['report_id']}
Timestamp: {report_data['timestamp']}
Mode: {report_data['mode']}

QUERY
{'='*60}
{report_data['query']}

FILE INFORMATION
{'='*60}
"""
        if report_data.get('file_info'):
            text += f"File: {report_data['file_info'].get('filename', 'N/A')}\n"
            text += f"Feature Rows: {report_data['file_info'].get('feature_rows', 'N/A')}\n"
            text += f"Feature Cols: {report_data['file_info'].get('feature_cols', 'N/A')}\n"
        else:
            text += "No file information available\n"
        
        text += f"""
PROCESSING RESULT
{'='*60}
"""
        if isinstance(report_data['result'], dict):
            if 'row_selection' in report_data['result']:
                text += f"Row Selection:\n{report_data['result']['row_selection']}\n\n"
            if 'col_selection' in report_data['result']:
                text += f"Column Selection:\n{report_data['result']['col_selection']}\n\n"
        else:
            text += f"{report_data['result']}\n"
        
        return text
    
    def _format_multi_query_report(self, report_data):
        """Format multi-query report as readable text."""
        text = f"""
MULTI-FILE QUERY REPORT
{'='*60}
Report ID: {report_data['report_id']}
Timestamp: {report_data['timestamp']}
Files Processed: {report_data['files_processed']}
Total Assignments: {report_data['total_assignments']}

ORIGINAL QUERY
{'='*60}
{report_data['original_query']}

QUERY ASSIGNMENTS
{'='*60}
"""
        for i, assignment in enumerate(report_data['assignments'], 1):
            text += f"{i}. File: {assignment['file']}\n"
            text += f"   Query: {assignment['query']}\n"
            text += f"   Reasoning: {assignment.get('reasoning', 'N/A')}\n\n"
        
        text += f"""
PROCESSING RESULTS
{'='*60}
"""
        for filename, result in report_data['results'].items():
            text += f"\n📄 {filename}:\n"
            text += f"   Query: {result.get('query', 'N/A')}\n"
            if 'dataframe' in result:
                df = result['dataframe']
                if hasattr(df, 'shape'):
                    text += f"   Results: {df.shape[0]} rows × {df.shape[1]} columns\n"
                else:
                    text += f"   Results: {df}\n"
            else:
                text += "   Results: No data available\n"
            
            if 'error' in result:
                text += f"   Error: {result['error']}\n"
        
        return text
    
    def _format_summary_report(self, report_data):
        """Format summary report as readable text."""
        text = f"""
FILE SUMMARY REPORT
{'='*60}
Report ID: {report_data['report_id']}
Timestamp: {report_data['timestamp']}
Filename: {report_data['filename']}

GENERATED SUMMARY
{'='*60}
{report_data['summary']}

METADATA DETAILS
{'='*60}
"""
        metadata = report_data['metadata']
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if key not in ['row_structure', 'col_structure']:  # Skip large structures
                    text += f"{key}: {value}\n"
        
        return text
    
    def _save_dataframes_to_excel(self, report_id, results):
        """Save DataFrame results to Excel file."""
        excel_file = self.report_dir / "multi_queries" / f"data_{report_id}.xlsx"
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for filename, result in results.items():
                    if 'dataframe' in result and hasattr(result['dataframe'], 'to_excel'):
                        # Clean filename for sheet name (Excel has restrictions)
                        sheet_name = filename.replace('.xlsx', '').replace('.', '_')[:31]
                        result['dataframe'].to_excel(writer, sheet_name=sheet_name, index=True)
            
            print(f"📊 Data saved to Excel: data_{report_id}.xlsx")
        except Exception as e:
            print(f"Warning: Could not save DataFrame to Excel: {e}")
    
    def get_recent_reports(self, limit=10, report_type="all"):
        """
        Get recent reports.
        
        Args:
            limit (int): Number of reports to return
            report_type (str): Type of reports ("single", "multi", "summaries", "all")
        """
        reports = []
        
        if report_type in ["single", "all"]:
            single_dir = self.report_dir / "single_queries"
            if single_dir.exists():
                for file in sorted(single_dir.glob("query_*.json"), reverse=True)[:limit]:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['type'] = 'single'
                        reports.append(data)
        
        if report_type in ["multi", "all"]:
            multi_dir = self.report_dir / "multi_queries"
            if multi_dir.exists():
                for file in sorted(multi_dir.glob("multi_query_*.json"), reverse=True)[:limit]:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['type'] = 'multi'
                        reports.append(data)
        
        if report_type in ["summaries", "all"]:
            summaries_dir = self.report_dir / "summaries"
            if summaries_dir.exists():
                for file in sorted(summaries_dir.glob("summary_*.json"), reverse=True)[:limit]:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['type'] = 'summary'
                        reports.append(data)
        
        # Sort all reports by timestamp
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        return reports[:limit]
    
    def display_recent_reports_summary(self, limit=5):
        """Display a summary of recent reports."""
        reports = self.get_recent_reports(limit)
        
        print(f"\n📊 RECENT REPORTS (Last {len(reports)})")
        print("="*60)
        
        for report in reports:
            timestamp = datetime.fromisoformat(report['timestamp']).strftime("%Y-%m-%d %H:%M")
            report_type = report['type'].upper()
            
            if report['type'] == 'single':
                query = report.get('query', 'N/A')[:50] + "..." if len(report.get('query', '')) > 50 else report.get('query', 'N/A')
                print(f"[{timestamp}] {report_type} - {query}")
            elif report['type'] == 'multi':
                query = report.get('original_query', 'N/A')[:50] + "..." if len(report.get('original_query', '')) > 50 else report.get('original_query', 'N/A')
                files_count = report.get('files_processed', 0)
                print(f"[{timestamp}] {report_type} - {query} ({files_count} files)")
            elif report['type'] == 'summary':
                filename = report.get('filename', 'N/A')
                print(f"[{timestamp}] {report_type} - {filename}")


# Global reporter instance
reporter = QueryReporter() 