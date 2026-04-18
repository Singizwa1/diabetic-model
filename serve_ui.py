#!/usr/bin/env python
"""
Simple HTTP Server for Diabetes Risk Prediction UI
Serves the HTML interface and handles CORS for API communication
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
HANDLER = http.server.SimpleHTTPRequestHandler

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers"""
    
    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    # Change to the script directory
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print("=" * 70)
        print("🏥 DIABETES RISK PREDICTION - WEB UI SERVER")
        print("=" * 70)
        print()
        print(f"📡 Web Server Running on: http://localhost:{PORT}")
        print()
        print("🌐 Open in Browser: http://localhost:8080")
        print()
        print("⚠️  Make sure FastAPI is also running on: http://127.0.0.1:8000")
        print()
        print("Press CTRL+C to stop the server")
        print()
        print("=" * 70)
        httpd.serve_forever()
