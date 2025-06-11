#!/usr/bin/env python3
"""
Simple HTTP server to serve the Excel Chatbot frontend.
"""
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 3000

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files with proper MIME types."""
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    """Start the HTTP server."""
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        with socketserver.TCPServer(("", PORT), HTTPRequestHandler) as httpd:
            print(f"🚀 Excel Chatbot Frontend Server")
            print(f"📂 Serving files from: {os.getcwd()}")
            print(f"🌐 Server running at: http://localhost:{PORT}")
            print(f"📱 Open the URL above in your browser")
            print()
            print("💡 Make sure the backend server is running on port 5001!")
            print("   cd ../backend && python -m uvicorn app:app --reload --port 5001")
            print()
            print("⏹️  Press Ctrl+C to stop the server")
            print("-" * 60)
            
            # Try to open the browser automatically
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🎉 Browser opened automatically!")
            except Exception:
                print("⚠️  Could not open browser automatically")
            
            print()
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use!")
            print("   Try closing other applications or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 