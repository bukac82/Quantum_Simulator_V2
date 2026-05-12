"""
Configuration and dependencies for the Quantum Computing API
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Global storage for jobs and simulators
job_storage = {}
active_simulators = {}

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Quantum Computing Service API",
        description="A comprehensive quantum computing API service with web interface",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Enable CORS for web frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files (for the web UI)
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app

def check_imports():
    """Check and report on quantum module imports"""
    try:
        # Import your quantum modules
        from simulator import QuantumSimulator
        from vqe.ansatz import HardwareEfficientAnsatz, QAOAAnsatz
        from vqe.hamiltonian import Hamiltonian, PauliString
        from vqe.qaoa import QuantumApproximateOptimization
        from vqe.vqe import VariationalQuantumEigensolver
        from algos.grover import GroverSearch
        from algos.qft import QuantumFourierTransform
        from algos.qpe import QuantumPhaseEstimation
        from algos.shor import ShorsAlgorithm
        from classes.plotter import QuantumPlotter
        print("✅ All quantum modules imported successfully")
        return True
    except ImportError as e:
        print(f"⚠️ Warning: Some quantum modules could not be imported: {e}")
        print("🔧 API will run with limited functionality")
        return False