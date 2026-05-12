"""
QAOA algorithm routes for the Quantum Computing API
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from api_models import QAOARequest, JobResponse
from api_utils import create_job_id, store_job_result, convert_numpy_types, initialize_job_status

try:
    from vqe.qaoa import QuantumApproximateOptimization
except ImportError:
    QuantumApproximateOptimization = None

router = APIRouter(prefix="/api/qaoa", tags=["qaoa"])

@router.post("/solve", response_model=JobResponse)
async def solve_qaoa(request: QAOARequest, background_tasks: BackgroundTasks,
                     job_storage: dict):
    """Solve Max-Cut problem using QAOA"""
    if QuantumApproximateOptimization is None:
        raise HTTPException(status_code=503, detail="QAOA module not available")
    
    job_id = create_job_id()
    
    def run_qaoa():
        try:
            initialize_job_status(job_storage, job_id)
            
            qaoa = QuantumApproximateOptimization(
                n_layers=request.n_layers,
                mixer_type=request.mixer_type,
                use_warm_start=request.use_warm_start,
                adaptive_initialization=True
            )
            
            # Convert edge format
            edges = [(edge[0], edge[1]) for edge in request.graph_edges]
            
            job_storage[job_id]["progress"] = 0.3
            
            result = qaoa.solve_max_cut(
                graph_edges=edges,
                n_qubits=request.n_qubits,
                shots=request.shots
            )
            
            # Add analysis
            max_cut, optimal_solutions = qaoa.analyze_max_cut_solutions(edges, request.n_qubits)
            result["theoretical_analysis"] = {
                "max_possible_cut": max_cut,
                "optimal_solutions": optimal_solutions,
                "num_optimal_solutions": len(optimal_solutions)
            }
            
            store_job_result(job_storage, job_id, convert_numpy_types(result), progress=1.0)
            
        except Exception as e:
            store_job_result(job_storage, job_id, None, str(e))
    
    background_tasks.add_task(run_qaoa)
    
    return JobResponse(
        job_id=job_id,
        status="running", 
        created_at=datetime.now().isoformat(),
        progress=0.0
    )