"""
API utilities with NumPy serialization support
"""

import uuid
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Union


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization
    
    Args:
        obj: Object that may contain NumPy types
        
    Returns:
        Object with NumPy types converted to native Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, set):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def create_job_id() -> str:
    """Generate a unique job ID"""
    return str(uuid.uuid4())


def initialize_job_status(job_storage: Dict, job_id: str) -> None:
    """Initialize job status in storage"""
    job_storage[job_id] = {
        "job_id": job_id,
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "progress": 0.0,
        "result": None,
        "error": None
    }


def store_job_result(job_storage: Dict, job_id: str, result: Any = None, 
                    error: str = None, progress: float = 1.0) -> None:
    """
    Store job result with automatic NumPy type conversion
    
    Args:
        job_storage: Job storage dictionary
        job_id: Job identifier
        result: Job result (will be converted from NumPy types)
        error: Error message if job failed
        progress: Job progress (0.0 to 1.0)
    """
    if job_id not in job_storage:
        initialize_job_status(job_storage, job_id)
    
    if error:
        job_storage[job_id].update({
            "status": "failed",
            "error": str(error),
            "progress": progress,
            "completed_at": datetime.now().isoformat()
        })
    else:
        # Convert NumPy types before storing
        converted_result = convert_numpy_types(result) if result is not None else None
        
        job_storage[job_id].update({
            "status": "completed",
            "result": converted_result,
            "progress": progress,
            "completed_at": datetime.now().isoformat()
        })


def validate_and_convert_request(request_data: Dict) -> Dict:
    """
    Validate and convert request data, ensuring proper types
    
    Args:
        request_data: Raw request data
        
    Returns:
        Validated and converted request data
    """
    converted_data = convert_numpy_types(request_data)
    return converted_data


def safe_serialize_response(data: Any) -> Any:
    """
    Safely serialize response data by converting NumPy types
    
    Args:
        data: Response data that may contain NumPy types
        
    Returns:
        Serialization-safe data
    """
    try:
        return convert_numpy_types(data)
    except Exception as e:
        print(f"Warning: Could not convert some data types: {e}")
        return data


# Additional utility functions for quantum computing results

def format_measurement_results(measurements: List[str], shots: int) -> Dict:
    """Format measurement results for API response"""
    from collections import Counter
    
    counts = Counter(measurements)
    probabilities = {state: count/shots for state, count in counts.items()}
    
    return {
        "measurements": measurements,
        "counts": dict(counts),
        "probabilities": probabilities,
        "total_shots": int(shots)
    }


def format_optimization_result(result: Dict, algorithm_type: str) -> Dict:
    """Format optimization algorithm results for API response"""
    formatted_result = {
        "algorithm": str(algorithm_type),
        "success": bool(result.get("converged", False)),
        "iterations": int(result.get("iterations", 0)),
        "timestamp": datetime.now().isoformat()
    }
    
    # Add algorithm-specific fields
    if algorithm_type.lower() == "vqe":
        formatted_result.update({
            "ground_state_energy": float(result.get("energy", 0.0)),
            "optimal_parameters": [float(x) for x in result.get("optimal_params", [])]
        })
    elif algorithm_type.lower() == "qaoa":
        formatted_result.update({
            "best_solution": str(result.get("best_cut_solution", "")),
            "best_value": int(result.get("best_cut_size", 0)),
            "approximation_ratio": float(result.get("approximation_ratio", 0.0))
        })
    
    return convert_numpy_types(formatted_result)


def validate_hamiltonian_terms(terms: List[Dict]) -> List[Dict]:
    """Validate and convert Hamiltonian terms"""
    validated_terms = []
    
    for term in terms:
        if not all(key in term for key in ["pauli_ops", "coefficient", "qubits"]):
            raise ValueError("Each Hamiltonian term must have 'pauli_ops', 'coefficient', and 'qubits' fields")
        
        validated_term = {
            "pauli_ops": [str(op) for op in term["pauli_ops"]],
            "coefficient": float(term["coefficient"]),
            "qubits": [int(q) for q in term["qubits"]]
        }
        validated_terms.append(validated_term)
    
    return validated_terms


def validate_graph_edges(edges: List[List[int]], n_qubits: int) -> List[List[int]]:
    """Validate and convert graph edges for QAOA"""
    validated_edges = []
    
    for edge in edges:
        if len(edge) != 2:
            raise ValueError("Each edge must have exactly 2 vertices")
        
        i, j = int(edge[0]), int(edge[1])
        
        if i < 0 or i >= n_qubits or j < 0 or j >= n_qubits:
            raise ValueError(f"Edge vertices must be in range [0, {n_qubits-1}]")
        
        if i == j:
            raise ValueError("Self-loops are not allowed")
        
        validated_edges.append([i, j])
    
    return validated_edges