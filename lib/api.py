"""
Enhanced Quantum Computing API Service - Modular Version
A comprehensive REST API service for quantum computing operations using FastAPI
"""

import uvicorn
from fastapi import Depends
from lib.config import create_app, check_imports, job_storage, active_simulators

# Check quantum module availability
check_imports()

# Create the FastAPI app
app = create_app()

# Import route modules and register them with dependencies
from routes.web_routes import router as web_router
app.include_router(web_router)

# Circuit execution endpoint
from routes.circuit_routes import execute_circuit
from api_models import CircuitRequest, JobResponse
from fastapi import BackgroundTasks

@app.post("/api/circuit/execute", response_model=JobResponse, tags=["circuit"])
async def execute_circuit_endpoint(
    request: CircuitRequest, 
    background_tasks: BackgroundTasks
):
    return await execute_circuit(request, background_tasks, job_storage, active_simulators)

# QAOA endpoint
from routes.qaoa_routes import solve_qaoa
from api_models import QAOARequest

@app.post("/api/qaoa/solve", response_model=JobResponse, tags=["qaoa"])
async def solve_qaoa_endpoint(
    request: QAOARequest,
    background_tasks: BackgroundTasks
):
    return await solve_qaoa(request, background_tasks, job_storage)

# VQE endpoint
from routes.vqe_routes import optimize_vqe
from api_models import VQERequest

@app.post("/api/vqe/optimize", response_model=JobResponse, tags=["vqe"])
async def optimize_vqe_endpoint(
    request: VQERequest,
    background_tasks: BackgroundTasks
):
    return await optimize_vqe(request, background_tasks, job_storage)

# Algorithm endpoints
from routes.algorithm_routes import grover_search, shor_factor, quantum_fourier_transform
from api_models import GroverRequest, ShorRequest, QFTRequest

@app.post("/api/grover/search", response_model=JobResponse, tags=["algorithms"])
async def grover_search_endpoint(
    request: GroverRequest,
    background_tasks: BackgroundTasks
):
    return await grover_search(request, background_tasks, job_storage)

@app.post("/api/shor/factor", response_model=JobResponse, tags=["algorithms"])
async def shor_factor_endpoint(
    request: ShorRequest,
    background_tasks: BackgroundTasks
):
    return await shor_factor(request, background_tasks, job_storage)

@app.post("/api/qft/transform", tags=["algorithms"])
async def qft_transform_endpoint(request: QFTRequest):
    return await quantum_fourier_transform(request)

# Job management endpoints
from routes.job_routes import get_job_status, list_jobs, delete_job, cleanup_jobs

@app.get("/api/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
async def get_job_status_endpoint(job_id: str):
    return await get_job_status(job_id, job_storage)

@app.get("/api/jobs", tags=["jobs"])
async def list_jobs_endpoint():
    return await list_jobs(job_storage)

@app.delete("/api/jobs/{job_id}", tags=["jobs"])
async def delete_job_endpoint(job_id: str):
    return await delete_job(job_id, job_storage, active_simulators)

@app.post("/api/jobs/cleanup", tags=["jobs"])
async def cleanup_jobs_endpoint():
    return await cleanup_jobs(job_storage, active_simulators)

# System status endpoints
from routes.system_routes import health_check, get_simulators_status

@app.get("/api/health", tags=["system"])
async def health_check_endpoint():
    return await health_check(job_storage, active_simulators)

@app.get("/api/simulators/status", tags=["system"])
async def get_simulators_status_endpoint():
    return await get_simulators_status(active_simulators)

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",  # Changed from 0.0.0.0 to 127.0.0.1
        port=5050,
        reload=True,
        log_level="info"
    )