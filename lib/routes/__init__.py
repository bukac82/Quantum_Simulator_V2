"""
Routes package for the Quantum Computing API
"""

from .web_routes import router as web_router
from .circuit_routes import execute_circuit
from .qaoa_routes import solve_qaoa
from .vqe_routes import optimize_vqe
from .algorithm_routes import grover_search, shor_factor, quantum_fourier_transform
from .job_routes import get_job_status, list_jobs, delete_job, cleanup_jobs
from .system_routes import health_check, get_simulators_status

__all__ = [
    'web_router',
    'execute_circuit',
    'solve_qaoa', 
    'optimize_vqe',
    'grover_search',
    'shor_factor',
    'quantum_fourier_transform',
    'get_job_status',
    'list_jobs',
    'delete_job',
    'cleanup_jobs',
    'health_check',
    'get_simulators_status'
]