"""
Health check module for container monitoring.
"""
import threading
import http.server
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthStatus:
    def __init__(self):
        self.status = "starting"
        self.last_check_time = None
        self.error = None

    def update(self, status: str, error: str = None):
        self.status = status
        self.error = error

health_status = HealthStatus()

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            response = {
                "status": health_status.status,
                "last_check_time": health_status.last_check_time,
                "error": health_status.error
            }
            
            self.send_response(200 if health_status.status == "healthy" else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server(port: int = 8080):
    """Start the health check server in a separate thread."""
    server = http.server.HTTPServer(("", port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(json.dumps({
        "level": "INFO",
        "message": "Health check server started",
        "port": port
    }))
    return server

def update_health_status(status: str = "healthy", error: str = None):
    """Update the health status."""
    health_status.update(status, error)
    logger.debug(json.dumps({
        "level": "DEBUG",
        "message": "Health status updated",
        "status": status,
        "error": error
    })) 