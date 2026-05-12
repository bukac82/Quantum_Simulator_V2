import torch
import math
import numpy as np
from typing import List, Optional, Callable, Tuple
from simulator import QuantumSimulator


class QuantumFourierTransform:
    """Quantum Fourier Transform implementation"""
    
    def __init__(self, simulator: QuantumSimulator):
        self.sim = simulator
        self.device = simulator.device
    
    def qft(self, qubits: List[int], inverse: bool = False):
        """
        Apply Quantum Fourier Transform to specified qubits
        
        Args:
            qubits: List of qubit indices to apply QFT to
            inverse: If True, apply inverse QFT
        """
        n = len(qubits)
        
        if inverse:
            # Inverse QFT: reverse the order and conjugate rotations
            qubits = qubits[::-1]
        
        for i in range(n):
            qubit = qubits[i]
            
            # Apply Hadamard gate
            self.sim.h(qubit)
            
            # Apply controlled rotation gates
            for j in range(i + 1, n):
                control = qubits[j]
                k = j - i
                angle = 2 * math.pi / (2**(k + 1))
                
                if inverse:
                    angle = -angle
                
                self._controlled_phase_rotation(control, qubit, angle)
        
        if not inverse:
            # For forward QFT, reverse the qubit order at the end
            self._swap_qubits(qubits)
    
    def inverse_qft(self, qubits: List[int]):
        """Apply inverse Quantum Fourier Transform"""
        self.qft(qubits, inverse=True)
    
    def _controlled_phase_rotation(self, control: int, target: int, angle: float):
        """Apply controlled phase rotation gate"""
        # Create controlled phase rotation matrix
        phase = complex(math.cos(angle), math.sin(angle))
        cp_matrix = torch.tensor([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, phase]
        ], dtype=torch.complex64, device=self.device)
        
        self.sim._apply_two_qubit_gate(cp_matrix, control, target, f'CP({angle:.3f})')
    
    def _swap_qubits(self, qubits: List[int]):
        """Swap qubits to reverse their order"""
        n = len(qubits)
        for i in range(n // 2):
            self._swap_gate(qubits[i], qubits[n - 1 - i])
    
    def _swap_gate(self, qubit1: int, qubit2: int):
        """Apply SWAP gate between two qubits using three CNOTs"""
        self.sim.cnot(qubit1, qubit2)
        self.sim.cnot(qubit2, qubit1)
        self.sim.cnot(qubit1, qubit2)