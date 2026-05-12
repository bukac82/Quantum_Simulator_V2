"""
VQE algorithm routes for the Quantum Computing API - Fixed NumPy serialization
"""

import numpy as np
from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from api_models import VQERequest, JobResponse
from api_utils import create_job_id, store_job_result, initialize_job_status

try:
    from vqe.ansatz import HardwareEfficientAnsatz
    from vqe.hamiltonian import Hamiltonian, PauliString
    from vqe.vqe import VariationalQuantumEigensolver
except ImportError:
    HardwareEfficientAnsatz = None
    Hamiltonian = None
    PauliString = None
    VariationalQuantumEigensolver = None

router = APIRouter(prefix="/api/vqe", tags=["vqe"])

def convert_numpy_types(obj):
    """Recursively convert NumPy types to native Python types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

@router.post("/optimize", response_model=JobResponse)
async def optimize_vqe(request: VQERequest, background_tasks: BackgroundTasks,
                       job_storage: dict):
    """Run VQE optimization"""
    if not all([HardwareEfficientAnsatz, Hamiltonian, PauliString, VariationalQuantumEigensolver]):
        raise HTTPException(status_code=503, detail="VQE modules not available")
    
    job_id = create_job_id()
    
    def run_vqe():
        try:
            initialize_job_status(job_storage, job_id)
            
            # Create Hamiltonian from terms
            pauli_terms = []
            for term in request.hamiltonian_terms:
                pauli_string = PauliString(
                    pauli_ops=term["pauli_ops"],
                    coefficient=float(term["coefficient"]),  # Ensure float
                    qubits=[int(q) for q in term["qubits"]]   # Ensure int list
                )
                pauli_terms.append(pauli_string)
            
            hamiltonian = Hamiltonian(pauli_terms)
            
            job_storage[job_id]["progress"] = 0.3
            
            # Create ansatz
            if request.ansatz_type == "hardware_efficient":
                ansatz = HardwareEfficientAnsatz(
                    n_qubits=int(request.n_qubits),
                    depth=int(request.ansatz_depth)
                )
            else:
                raise ValueError(f"Unsupported ansatz type: {request.ansatz_type}")
            
            # Run VQE
            vqe = VariationalQuantumEigensolver(hamiltonian, ansatz, None)
            initial_params = np.random.uniform(0, 2*np.pi, ansatz.n_parameters)
            
            job_storage[job_id]["progress"] = 0.5
            
            result = vqe.run(
                initial_params=initial_params,
                n_qubits=int(request.n_qubits),
                shots=int(request.shots)
            )
            
            # Enhanced result with ansatz info - Convert all NumPy types
            enhanced_result = {
                "energy": float(result["energy"]),
                "optimal_params": [float(x) for x in result["optimal_params"]],
                "converged": bool(result["converged"]),
                "iterations": int(result["iterations"]),
                "ansatz_info": {
                    "type": str(request.ansatz_type),
                    "depth": int(request.ansatz_depth),
                    "n_parameters": int(ansatz.n_parameters)
                },
                "hamiltonian_info": {
                    "n_terms": int(len(pauli_terms)),
                    "terms": [str(term) for term in pauli_terms[:5]]  # Limit to first 5 terms
                }
            }
            
            # Apply recursive NumPy conversion to be extra safe
            enhanced_result = convert_numpy_types(enhanced_result)
            
            store_job_result(job_storage, job_id, enhanced_result, progress=1.0)
            
        except Exception as e:
            print(f"VQE error: {e}")
            store_job_result(job_storage, job_id, None, str(e))
    
    background_tasks.add_task(run_vqe)
    
    return JobResponse(
        job_id=job_id,
        status="running",
        created_at=datetime.now().isoformat(),
        progress=0.0
    )