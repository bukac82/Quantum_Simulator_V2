from typing import List, Union, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator import QuantumSimulator
from .hamiltonian import Hamiltonian  # Relative import within package
import numpy as np

class HardwareEfficientAnsatz:
    """Parameterized circuits optimized for NISQ hardware"""
    def __init__(self, n_qubits: int, depth: int, rotation_gates=['RY', 'RZ']):
        self.n_qubits = n_qubits
        self.depth = depth
        self.rotation_gates = rotation_gates
        self.n_parameters = self._count_parameters()
    
    def _count_parameters(self) -> int:
        """Count total number of parameters"""
        return self.depth * self.n_qubits * len(self.rotation_gates)
    
    def apply_circuit(self, simulator: QuantumSimulator, parameters: List[float]):
        """Apply ansatz with given parameters"""
        if len(parameters) != self.n_parameters:
            raise ValueError(f"Expected {self.n_parameters} parameters, got {len(parameters)}")
        
        param_idx = 0
        for layer in range(self.depth):
            # Rotation layer
            for qubit in range(self.n_qubits):
                for gate_type in self.rotation_gates:
                    angle = parameters[param_idx]
                    if gate_type == 'RY':
                        simulator.ry(angle, qubit)
                    elif gate_type == 'RZ':
                        simulator.rz(angle, qubit)
                    elif gate_type == 'RX':
                        simulator.rx(angle, qubit)
                    param_idx += 1
            
            # Entangling layer (skip on last layer)
            if layer < self.depth - 1:
                for qubit in range(self.n_qubits - 1):
                    simulator.cnot(qubit, qubit + 1)

class QAOAAnsatz:
    """QAOA-specific ansatz with cost and mixer layers"""
    def __init__(self, cost_hamiltonian: Hamiltonian, n_layers: int):
        self.cost_hamiltonian = cost_hamiltonian
        self.n_layers = n_layers
        self.n_parameters = 2 * n_layers  # β and γ parameters
    
    def apply_circuit(self, simulator: QuantumSimulator, parameters: List[float]):
        """Apply QAOA ansatz: alternating cost and mixer layers"""
        if len(parameters) != self.n_parameters:
            raise ValueError(f"Expected {self.n_parameters} parameters, got {len(parameters)}")
        
        # Initial superposition
        for qubit in range(simulator.n_qubits):
            simulator.h(qubit)
        
        for layer in range(self.n_layers):
            gamma = parameters[2 * layer]      # Cost parameter
            beta = parameters[2 * layer + 1]   # Mixer parameter
            
            # Cost layer: e^(-iγH_C)
            self._apply_cost_layer(simulator, gamma)
            
            # Mixer layer: e^(-iβH_M) where H_M = Σ Xᵢ
            self._apply_mixer_layer(simulator, beta)
    
    def _apply_cost_layer(self, simulator: QuantumSimulator, gamma: float):
        """Apply cost Hamiltonian evolution e^(-iγH_C)"""
        for term in self.cost_hamiltonian.terms:
            self._apply_pauli_evolution(simulator, term, gamma)
    
    def _apply_mixer_layer(self, simulator: QuantumSimulator, beta: float):
        """Apply mixer Hamiltonian evolution e^(-iβΣXᵢ)"""
        for qubit in range(simulator.n_qubits):
            simulator.rx(2 * beta, qubit)  # RX(2β) = e^(-iβX)
    
    def _apply_pauli_evolution(self, simulator: QuantumSimulator, 
                              pauli_term, angle: float):
        """Apply evolution under a Pauli string"""
        # For ZZ terms (most common in optimization problems)
        if len(pauli_term.pauli_ops) == 2 and all(op == 'Z' for op in pauli_term.pauli_ops):
            q1, q2 = pauli_term.qubits
            # e^(-iγZZ) decomposition
            simulator.cnot(q1, q2)
            simulator.rz(2 * angle * pauli_term.coefficient, q2)
            simulator.cnot(q1, q2)
        else:
            # General case: transform to Z basis, apply rotation, transform back
            for i, (op, qubit) in enumerate(zip(pauli_term.pauli_ops, pauli_term.qubits)):
                if op == 'X':
                    simulator.ry(-np.pi/2, qubit)
                elif op == 'Y':
                    simulator.rx(np.pi/2, qubit)
            
            # Apply controlled rotations (simplified for two-qubit case)
            if len(pauli_term.qubits) == 2:
                q1, q2 = pauli_term.qubits
                simulator.cnot(q1, q2)
                simulator.rz(2 * angle * pauli_term.coefficient, q2)
                simulator.cnot(q1, q2)
            
            # Transform back
            for i, (op, qubit) in enumerate(zip(pauli_term.pauli_ops, pauli_term.qubits)):
                if op == 'X':
                    simulator.ry(np.pi/2, qubit)
                elif op == 'Y':
                    simulator.rx(-np.pi/2, qubit)

# ----------------------------------------------------------------------------------------------------------------
