import numpy as np
from typing import List, Union, Optional

class PauliString:
    """Represents a Pauli string like 'XYZ' with coefficient"""
    def __init__(self, pauli_ops: List[str], coefficient: float, qubits: List[int]):
        self.pauli_ops = pauli_ops  # ['X', 'Y', 'Z']
        self.coefficient = coefficient
        self.qubits = qubits
        
    def __str__(self):
        return f"{self.coefficient} * {''.join([f'{op}_{q}' for op, q in zip(self.pauli_ops, self.qubits)])}"

class Hamiltonian:
    """Represents H = Σ αᵢ Pᵢ where Pᵢ are Pauli strings"""
    def __init__(self, pauli_terms: List[PauliString]):
        self.terms = pauli_terms
    
    def expectation_value(self, simulator, shots: int = 1000) -> float:
        """Calculate ⟨ψ|H|ψ⟩ by measuring each Pauli term"""
        # Import here to avoid circular import
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        total = 0.0
        
        for term in self.terms:
            # Save current state
            original_state = simulator.get_state().clone()
            
            # Measure this Pauli term
            exp_val = self._measure_pauli_string(simulator, term, shots)
            total += term.coefficient * exp_val
            
            # Restore state for next measurement
            simulator.set_state(original_state)
            
        return total
    
    def _measure_pauli_string(self, simulator, pauli_string: PauliString, shots: int = 1000) -> float:
        """Measure ⟨ψ|P|ψ⟩ for Pauli string P"""
        
        # Change basis for measurement
        for i, pauli_op in enumerate(pauli_string.pauli_ops):
            qubit = pauli_string.qubits[i]
            if pauli_op == 'X':
                simulator.ry(-np.pi/2, qubit)  # Rotate to X basis
            elif pauli_op == 'Y':
                simulator.rx(np.pi/2, qubit)   # Rotate to Y basis
            # Z basis needs no rotation
        
        # Measure and calculate expectation value
        measurements = simulator.measure(shots=shots)
        expectation = self._calculate_expectation_from_measurements(
            measurements, pauli_string
        )
        return expectation
    
    def _calculate_expectation_from_measurements(self, measurements: List[str], 
                                               pauli_string: PauliString) -> float:
        """Calculate expectation value from measurement results"""
        total = 0.0
        
        for measurement in measurements:
            # Calculate parity for the measured qubits
            parity = 1
            for qubit in pauli_string.qubits:
                if measurement[-(qubit+1)] == '1':  # Reverse indexing
                    parity *= -1
            total += parity
        
        return total / len(measurements)
    
    # ----------------------------------------------------------------------------------------------------------------
