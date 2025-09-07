import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="frontend", **kwargs)

def serve_frontend(port=8000):
    """Serve the frontend on the specified port"""
    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"Frontend server running at http://localhost:{port}")
        print("Open your browser and navigate to the URL above")
        httpd.serve_forever()

if __name__ == "__main__":
    serve_frontend()