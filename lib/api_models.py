"""
Pydantic models for the Quantum Computing API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class QuantumGate(BaseModel):
    gate: str
    qubits: List[int]
    params: Optional[Dict[str, float]] = None

class CircuitRequest(BaseModel):
    n_qubits: int = Field(ge=1, le=10, description="Number of qubits in the circuit")
    gates: List[QuantumGate] = Field(description="List of quantum gates to apply")
    shots: int = Field(default=1000, ge=1, le=10000, description="Number of measurement shots")

class StateRequest(BaseModel):
    n_qubits: int = Field(ge=1, le=10)
    circuit_id: Optional[str] = None

class QAOARequest(BaseModel):
    graph_edges: List[List[int]] = Field(description="Graph edges as list of [source, target] pairs")
    n_qubits: int = Field(ge=2, le=8, description="Number of qubits/vertices")
    n_layers: int = Field(default=2, ge=1, le=10, description="QAOA depth (p layers)")
    shots: int = Field(default=1000, ge=1, le=10000)
    mixer_type: str = Field(default="standard", description="Mixer type: standard, xy, ring, asymmetric")
    use_warm_start: bool = Field(default=False, description="Use classical warm start")

class VQERequest(BaseModel):
    n_qubits: int = Field(ge=1, le=8)
    hamiltonian_terms: List[Dict[str, Any]] = Field(description="Hamiltonian terms as list of dictionaries")
    ansatz_type: str = Field(default="hardware_efficient", description="Type of ansatz circuit")
    ansatz_depth: int = Field(default=2, ge=1, le=5, description="Ansatz circuit depth")
    shots: int = Field(default=1000, ge=1, le=10000)

class GroverRequest(BaseModel):
    search_array: List[Any] = Field(description="Array to search through")
    target_value: Any = Field(description="Target value to find")

class ShorRequest(BaseModel):
    N: int = Field(ge=4, le=21, description="Integer to factor")
    n_counting_qubits: int = Field(default=4, ge=3, le=8, description="Number of counting qubits")

class QFTRequest(BaseModel):
    n_qubits: int = Field(ge=1, le=6, description="Number of qubits for QFT")
    input_state: Optional[List[float]] = Field(default=None, description="Optional input state amplitudes")

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[float] = None

class SimulatorStatus(BaseModel):
    n_qubits: int
    circuit_depth: int
    memory_usage_mb: float
    current_state: str