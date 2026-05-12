"""
Quantum gate definitions and operations for 2-qubit systems.
"""

import torch
import math
from typing import Tuple


class QuantumGates:
    """Collection of quantum gate matrices and operations for n-qubit systems"""
    
    def __init__(self, device: str = 'cpu'):
        if not torch.cpu.is_available():
            raise RuntimeError("cpu is not available. This simulator requires cpu.")
        
        self.device = 'cpu'
        self._initialize_single_qubit_gates()
    
    def _initialize_single_qubit_gates(self):
        """Initialize standard single-qubit gate matrices"""
        # Pauli matrices
        self.I = torch.tensor([[1, 0], [0, 1]], dtype=torch.complex64, device=self.device)
        self.X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64, device=self.device)
        self.Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64, device=self.device)
        self.Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64, device=self.device)
        
        # Hadamard gate
        self.H = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex64, device=self.device) / math.sqrt(2)
        
        # Phase gates
        self.S = torch.tensor([[1, 0], [0, 1j]], dtype=torch.complex64, device=self.device)
        t_phase = complex(math.cos(math.pi/4), math.sin(math.pi/4))
        self.T = torch.tensor([[1, 0], [0, t_phase]], dtype=torch.complex64, device=self.device)
    
    def get_single_qubit_gate(self, gate_name: str) -> torch.Tensor:
        """Get single qubit gate matrix by name"""
        gate_map = {
            'I': self.I, 'X': self.X, 'Y': self.Y, 'Z': self.Z,
            'H': self.H, 'S': self.S, 'T': self.T
        }
        
        if gate_name.upper() not in gate_map:
            raise ValueError(f"Unknown gate: {gate_name}")
        
        return gate_map[gate_name.upper()]
    
    def rx_matrix(self, angle: float) -> torch.Tensor:
        """Generate RX rotation matrix"""
        cos_half = math.cos(angle / 2)
        sin_half = math.sin(angle / 2)
        return torch.tensor([
            [cos_half, -1j * sin_half],
            [-1j * sin_half, cos_half]
        ], dtype=torch.complex64, device=self.device)
    
    def ry_matrix(self, angle: float) -> torch.Tensor:
        """Generate RY rotation matrix"""
        cos_half = math.cos(angle / 2)
        sin_half = math.sin(angle / 2)
        return torch.tensor([
            [cos_half, -sin_half],
            [sin_half, cos_half]
        ], dtype=torch.complex64, device=self.device)
    
    def rz_matrix(self, angle: float) -> torch.Tensor:
        """Generate RZ rotation matrix"""
        exp_neg = complex(math.cos(-angle/2), math.sin(-angle/2))
        exp_pos = complex(math.cos(angle/2), math.sin(angle/2))
        return torch.tensor([
            [exp_neg, 0],
            [0, exp_pos]
        ], dtype=torch.complex64, device=self.device)