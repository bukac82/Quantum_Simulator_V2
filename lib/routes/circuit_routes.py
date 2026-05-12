"""
Circuit execution routes for the Quantum Computing API
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from api_models import CircuitRequest, JobResponse
from api_utils import create_job_id, store_job_result, convert_numpy_types, initialize_job_status

try:
    from simulator import QuantumSimulator
    from classes.plotter import QuantumPlotter
except ImportError:
    QuantumSimulator = None
    QuantumPlotter = None
    
import io
import base64

router = APIRouter(prefix="/api/circuit", tags=["circuit"])

@router.post("/execute", response_model=JobResponse)
async def execute_circuit(request: CircuitRequest, background_tasks: BackgroundTasks, 
                         job_storage: dict, active_simulators: dict):
    """Execute a custom quantum circuit"""
    if QuantumSimulator is None:
        raise HTTPException(status_code=503, detail="Quantum simulator not available")
    
    job_id = create_job_id()
    
    def run_circuit():
        try:
            initialize_job_status(job_storage, job_id)
            
            sim = QuantumSimulator(n_qubits=request.n_qubits)
            total_gates = len(request.gates)
            
            # Generate Python code equivalent
            py_code = [
                "from lib.simulator import QuantumSimulator",
                "",
                f"sim = QuantumSimulator(n_qubits={request.n_qubits})"
            ]
            
            # Apply gates with progress tracking
            for i, gate_op in enumerate(request.gates):
                gate_name = gate_op.gate.upper()
                qubits = gate_op.qubits
                params = gate_op.params or {}
                
                # Progress update
                progress = 0.1 + (0.7 * (i + 1) / total_gates)
                job_storage[job_id]["progress"] = progress
                
                # Apply gate based on type
                if gate_name == "H" and len(qubits) == 1:
                    sim.h(qubits[0])
                    py_code.append(f"sim.h({qubits[0]})")
                elif gate_name == "X" and len(qubits) == 1:
                    sim.x(qubits[0])
                    py_code.append(f"sim.x({qubits[0]})")
                elif gate_name == "Y" and len(qubits) == 1:
                    sim.y(qubits[0])
                    py_code.append(f"sim.y({qubits[0]})")
                elif gate_name == "Z" and len(qubits) == 1:
                    sim.z(qubits[0])
                    py_code.append(f"sim.z({qubits[0]})")
                elif gate_name == "S" and len(qubits) == 1:
                    sim.s(qubits[0])
                    py_code.append(f"sim.s({qubits[0]})")
                elif gate_name == "T" and len(qubits) == 1:
                    sim.t(qubits[0])
                    py_code.append(f"sim.t({qubits[0]})")
                elif gate_name == "CNOT" and len(qubits) == 2:
                    sim.cnot(qubits[0], qubits[1])
                    py_code.append(f"sim.cnot({qubits[0]}, {qubits[1]})")
                elif gate_name == "CZ" and len(qubits) == 2:
                    sim.cz(qubits[0], qubits[1])
                    py_code.append(f"sim.cz({qubits[0]}, {qubits[1]})")
                elif gate_name == "RX" and len(qubits) == 1:
                    angle = params.get("angle", 0)
                    sim.rx(angle, qubits[0])
                    py_code.append(f"sim.rx({angle}, {qubits[0]})")
                elif gate_name == "RY" and len(qubits) == 1:
                    angle = params.get("angle", 0)
                    sim.ry(angle, qubits[0])
                    py_code.append(f"sim.ry({angle}, {qubits[0]})")
                elif gate_name == "RZ" and len(qubits) == 1:
                    angle = params.get("angle", 0)
                    sim.rz(angle, qubits[0])
                    py_code.append(f"sim.rz({angle}, {qubits[0]})")
                else:
                    raise ValueError(f"Unsupported gate: {gate_name} with {len(qubits)} qubits")
            
            # Progress: measurements
            job_storage[job_id]["progress"] = 0.9
            
            # Get results
            measurements = sim.measure(shots=request.shots)
            probabilities = sim.get_probabilities().numpy().tolist()
            state_vector = sim.get_state().numpy()
            
            # Convert complex state vector for JSON
            state_vector_json = [{"real": float(x.real), "imag": float(x.imag)} for x in state_vector]
            
            py_code.extend([
                "",
                f"measurements = sim.measure(shots={request.shots})",
                "probabilities = sim.get_probabilities()",
                "state_vector = sim.get_state()",
                "",
                "print('Measurements:', measurements)",
                "print('Probabilities:', probabilities)"
            ])
            
            # Calculate bloch vectors for interactive 3D rendering
            bloch_vectors = []
            import numpy as np
            
            try:
                state_np = sim.get_state().numpy()
                n_qubits = request.n_qubits
                n_states = 2**n_qubits
                
                pauli_x = np.array([[0, 1], [1, 0]])
                pauli_y = np.array([[0, -1j], [1j, 0]])
                pauli_z = np.array([[1, 0], [0, -1]])
                
                for q in range(n_qubits):
                    rho = np.zeros((2, 2), dtype=complex)
                    for i in range(n_states):
                        for j in range(n_states):
                            bit_i = (i >> (n_qubits - q - 1)) & 1
                            bit_j = (j >> (n_qubits - q - 1)) & 1
                            other_bits_i = (i & ~(1 << (n_qubits - q - 1)))
                            other_bits_j = (j & ~(1 << (n_qubits - q - 1)))
                            if other_bits_i == other_bits_j:
                                rho[bit_i, bit_j] += state_np[i] * np.conj(state_np[j])
                    
                    x = float(np.real(np.trace(pauli_x @ rho)))
                    y = float(np.real(np.trace(pauli_y @ rho)))
                    z = float(np.real(np.trace(pauli_z @ rho)))
                    
                    norm = np.sqrt(x**2 + y**2 + z**2)
                    if norm > 1.0:
                        x, y, z = x/norm, y/norm, z/norm
                        
                    bloch_vectors.append([x, y, z])
            except Exception as e:
                print(f"Error computing bloch vectors: {e}")
            
            result = {
                "measurements": measurements,
                "probabilities": probabilities,
                "state_vector": state_vector_json,
                "bloch_vectors": bloch_vectors,
                "circuit_depth": sim.get_circuit_depth(),
                "gate_sequence": sim.gate_sequence,
                "n_qubits": request.n_qubits,
                "shots": request.shots,
                "memory_usage": sim.get_memory_usage(),
                "python_code": "\n".join(py_code)
            }
            
            # Store simulator for potential future use
            active_simulators[job_id] = sim
            
            store_job_result(job_storage, job_id, convert_numpy_types(result), progress=1.0)
            
        except Exception as e:
            store_job_result(job_storage, job_id, None, str(e))
    
    background_tasks.add_task(run_circuit)
    
    return JobResponse(
        job_id=job_id,
        status="running",
        created_at=datetime.now().isoformat(),
        progress=0.0
    )