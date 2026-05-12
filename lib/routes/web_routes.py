"""
Web interface routes for the Quantum Computing API
"""

import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

@router.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main web interface"""
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r", encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Quantum Computing API</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .method { font-weight: bold; color: #2c5282; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Quantum Computing API Service</h1>
                    <p>Your quantum computing API is running successfully!</p>
                    
                    <h2>📡 Available Endpoints</h2>
                    
                    <div class="endpoint">
                        <div class="method">GET /api/docs</div>
                        <p>Interactive API documentation (Swagger UI)</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST /api/circuit/execute</div>
                        <p>Execute custom quantum circuits</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST /api/qaoa/solve</div>
                        <p>Solve optimization problems using QAOA</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST /api/vqe/optimize</div>
                        <p>Find ground states using VQE</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST /api/grover/search</div>
                        <p>Search databases using Grover's algorithm</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST /api/shor/factor</div>
                        <p>Factor integers using Shor's algorithm</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">GET /api/health</div>
                        <p>Check service health and status</p>
                    </div>
                    
                    <h2>🔗 Quick Links</h2>
                    <ul>
                        <li><a href="/api/docs">📚 API Documentation</a></li>
                        <li><a href="/api/health">❤️ Health Check</a></li>
                        <li><a href="/api/simulators/status">🔧 Simulator Status</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error serving UI: {str(e)}</h1>", status_code=500)

@router.get("/api/")
async def api_root():
    """API root endpoint with available endpoints"""
    return {
        "message": "Quantum Computing Service API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "circuit": "/api/circuit/execute",
            "qaoa": "/api/qaoa/solve", 
            "vqe": "/api/vqe/optimize",
            "grover": "/api/grover/search",
            "shor": "/api/shor/factor",
            "qft": "/api/qft/transform",
            "jobs": "/api/jobs/{job_id}",
            "health": "/api/health"
        }
    }