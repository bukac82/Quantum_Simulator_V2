"""
Classical quantum algorithm routes (Grover, Shor, QFT) for the Quantum Computing API
"""

import torch
from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from api_models import GroverRequest, ShorRequest, QFTRequest, JobResponse
from api_utils import create_job_id, store_job_result, initialize_job_status

try:
    from algos.grover import GroverSearch
    from algos.shor import ShorsAlgorithm
    from algos.qft import QuantumFourierTransform
    from simulator import QuantumSimulator
except ImportError:
    GroverSearch = None
    ShorsAlgorithm = None
    QuantumFourierTransform = None
    QuantumSimulator = None

router = APIRouter(prefix="/api", tags=["algorithms"])

@router.post("/grover/search", response_model=JobResponse)
async def grover_search(request: GroverRequest, background_tasks: BackgroundTasks,
                       job_storage: dict):
    """Perform Grover's search algorithm"""
    if GroverSearch is None:
        raise HTTPException(status_code=503, detail="Grover algorithm not available")
    
    job_id = create_job_id()
    
    def run_grover():
        try:
            initialize_job_status(job_storage, job_id)
            
            grover = GroverSearch(request.search_array, request.target_value)
            result_index, result_value = grover.run()
            
            result = {
                "found_index": result_index,
                "found_value": result_value,
                "search_array": request.search_array,
                "target_value": request.target_value,
                "success": result_value == request.target_value,
                "search_space_size": len(request.search_array),
                "theoretical_speedup": f"O(√N) vs O(N) classical"
            }
            
            store_job_result(job_storage, job_id, result, progress=1.0)
            
        except Exception as e:
            store_job_result(job_storage, job_id, None, str(e))
    
    background_tasks.add_task(run_grover)
    
    return JobResponse(
        job_id=job_id,
        status="running",
        created_at=datetime.now().isoformat(),
        progress=0.0
    )

@router.post("/shor/factor", response_model=JobResponse)
async def shor_factor(request: ShorRequest, background_tasks: BackgroundTasks,
                      job_storage: dict):
    """Factor integer using Shor's algorithm"""
    if ShorsAlgorithm is None:
        raise HTTPException(status_code=503, detail="Shor's algorithm not available")
    
    job_id = create_job_id()
    
    def run_shor():
        try:
            initialize_job_status(job_storage, job_id)
            
            shor = ShorsAlgorithm(request.N, request.n_counting_qubits)
            factors = shor.factor()
            
            result = {
                "N": request.N,
                "factors": factors,
                "success": factors is not None and len(factors) == 2,
                "verification": factors[0] * factors[1] == request.N if factors and len(factors) == 2 else False,
                "n_counting_qubits": request.n_counting_qubits,
                "classical_difficulty": "Exponential for large N",
                "quantum_advantage": "Polynomial time complexity"
            }
            
            store_job_result(job_storage, job_id, result, progress=1.0)
            
        except Exception as e:
            store_job_result(job_storage, job_id, None, str(e))
    
    background_tasks.add_task(run_shor)
    
    return JobResponse(
        job_id=job_id,
        status="running",
        created_at=datetime.now().isoformat(),
        progress=0.0
    )

@router.post("/qft/transform")
async def quantum_fourier_transform(request: QFTRequest):
    """Apply Quantum Fourier Transform"""
    if not all([QuantumSimulator, QuantumFourierTransform]):
        raise HTTPException(status_code=503, detail="QFT modules not available")
    
    try:
        sim = QuantumSimulator(n_qubits=request.n_qubits)
        
        # Set input state if provided
        if request.input_state:
            if len(request.input_state) != 2**request.n_qubits:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Input state must have {2**request.n_qubits} amplitudes"
                )
            input_tensor = torch.tensor(request.input_state, dtype=torch.complex64)
            sim.set_state(input_tensor)
        else:
            # Create initial superposition
            sim.create_superposition_all()
        
        qft = QuantumFourierTransform(sim)
        
        # Apply QFT
        qubits = list(range(request.n_qubits))
        qft.qft(qubits)
        
        # Get results
        probabilities = sim.get_probabilities().numpy().tolist()
        measurements = sim.measure(shots=1000)
        final_state = sim.get_state().numpy()
        
        # Convert complex state
        state_vector_json = [{"real": float(x.real), "imag": float(x.imag)} for x in final_state]
        
        return {
            "status": "success",
            "probabilities": probabilities,
            "sample_measurements": measurements[:10],
            "n_qubits": request.n_qubits,
            "final_state": state_vector_json,
            "circuit_depth": sim.get_circuit_depth()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))