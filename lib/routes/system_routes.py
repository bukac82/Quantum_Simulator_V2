"""
System status and health check routes for the Quantum Computing API
"""

from fastapi import APIRouter
from datetime import datetime

try:
    from simulator import QuantumSimulator
except ImportError:
    QuantumSimulator = None

router = APIRouter(prefix="/api", tags=["system"])

@router.get("/health")
async def health_check(job_storage: dict, active_simulators: dict):
    """Comprehensive health check endpoint"""
    try:
        if QuantumSimulator:
            # Test quantum simulator creation
            test_sim = QuantumSimulator(n_qubits=2)
            test_sim.h(0)
            test_sim.cnot(0, 1)
            test_probabilities = test_sim.get_probabilities()
            simulator_health = "healthy"
        else:
            simulator_health = "error: QuantumSimulator not available"
    except Exception as e:
        simulator_health = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "active_jobs": len([j for j in job_storage.values() if j["status"] == "running"]),
        "total_jobs": len(job_storage),
        "active_simulators": len(active_simulators),
        "simulator_health": simulator_health,
        "memory_usage": {
            "active_simulators": len(active_simulators),
            "job_storage_size": len(job_storage)
        }
    }

@router.get("/simulators/status")
async def get_simulators_status(active_simulators: dict):
    """Get status of all active simulators"""
    simulators_status = {}
    
    for job_id, sim in active_simulators.items():
        try:
            memory_info = sim.get_memory_usage()
            simulators_status[job_id] = {
                "n_qubits": sim.n_qubits,
                "circuit_depth": sim.get_circuit_depth(),
                "memory_usage_mb": memory_info["state_vector_mb"],
                "state_size": memory_info["state_size"]
            }
        except Exception as e:
            simulators_status[job_id] = {"error": str(e)}
    
    return {
        "active_simulators": simulators_status,
        "total_active": len(active_simulators)
    }