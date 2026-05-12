"""
Utility functions for quantum simulation and state manipulation.
"""

import torch
import numpy as np
import math
from typing import List, Tuple, Union


class QuantumUtils:
    """Utility functions for quantum state operations"""
    
    @staticmethod
    def tensor_to_numpy(tensor: Union[torch.Tensor, List, np.ndarray]) -> np.ndarray:
        """Convert tensor to numpy array, handling cpu tensors"""
        if isinstance(tensor, torch.Tensor):
            return tensor.cpu().detach().numpy()
        elif isinstance(tensor, (list, tuple)):
            return np.array([QuantumUtils.tensor_to_numpy(t) if isinstance(t, torch.Tensor) else t for t in tensor])
        else:
            return np.array(tensor)
    
    @staticmethod
    def normalize_state(state: torch.Tensor) -> torch.Tensor:
        """Normalize a quantum state vector"""
        norm = torch.sqrt(torch.sum(torch.abs(state)**2))
        if norm < 1e-12:
            raise ValueError("State vector has zero norm")
        return state / norm
    
    @staticmethod
    def is_normalized(state: torch.Tensor, tolerance: float = 1e-10) -> bool:
        """Check if state is normalized"""
        norm_squared = torch.sum(torch.abs(state)**2).item()
        return abs(norm_squared - 1.0) < tolerance
    
    @staticmethod
    def state_fidelity(state1: torch.Tensor, state2: torch.Tensor) -> float:
        """Calculate fidelity between two quantum states"""
        overlap = torch.abs(torch.vdot(state1, state2))**2
        return overlap.item()
    
    @staticmethod
    def permutation_matrix(n_qubits: int, permutation: List[int]) -> torch.Tensor:
        """Create permutation matrix for qubit reordering"""
        size = 2**n_qubits
        perm_matrix = torch.zeros((size, size), dtype=torch.complex64)
        
        for i in range(size):
            # Convert i to binary representation
            binary = [(i >> k) & 1 for k in range(n_qubits)]
            # Permute the bits
            permuted = [binary[permutation[k]] for k in range(n_qubits)]
            # Convert back to integer
            j = sum(bit * (2**k) for k, bit in enumerate(permuted))
            perm_matrix[j, i] = 1.0
            
        return perm_matrix
    
    @staticmethod
    def create_bell_state(state_type: str = '00', n_qubits: int = 2, device: str = 'cpu') -> torch.Tensor:
        """Create Bell states for 2-qubit systems"""
        if n_qubits != 2:
            raise ValueError("Bell states are only defined for 2 qubits")
            
        bell_states = {
            '00': torch.tensor([1, 0, 0, 1], dtype=torch.complex64) / math.sqrt(2),  # |Φ+⟩
            '01': torch.tensor([1, 0, 0, -1], dtype=torch.complex64) / math.sqrt(2), # |Φ-⟩
            '10': torch.tensor([0, 1, 1, 0], dtype=torch.complex64) / math.sqrt(2),  # |Ψ+⟩
            '11': torch.tensor([0, 1, -1, 0], dtype=torch.complex64) / math.sqrt(2)  # |Ψ-⟩
        }
        
        if state_type not in bell_states:
            raise ValueError("state_type must be '00', '01', '10', or '11'")
        
        return bell_states[state_type].to(device)
    
    @staticmethod
    def create_ghz_state(n_qubits: int, device: str = 'cpu') -> torch.Tensor:
        """Create GHZ state: (|00...0⟩ + |11...1⟩)/√2"""
        state_size = 2**n_qubits
        state = torch.zeros(state_size, dtype=torch.complex64, device=device)
        state[0] = 1.0 / math.sqrt(2)  # |00...0⟩
        state[-1] = 1.0 / math.sqrt(2)  # |11...1⟩
        return state
    
    @staticmethod
    def format_complex(z: complex, precision: int = 4) -> str:
        """Format complex number for display"""
        real_part = z.real
        imag_part = z.imag
        
        if abs(imag_part) < 10**(-precision):
            return f"{real_part:.{precision}f}"
        elif abs(real_part) < 10**(-precision):
            return f"{imag_part:.{precision}f}i"
        else:
            sign = "+" if imag_part >= 0 else "-"
            return f"({real_part:.{precision}f} {sign} {abs(imag_part):.{precision}f}i)"
    
    @staticmethod
    def state_to_string(state: torch.Tensor, n_qubits: int, precision: int = 4) -> str:
        """Convert quantum state to readable string representation"""
        state_np = QuantumUtils.tensor_to_numpy(state)
        state_size = 2**n_qubits
        
        terms = []
        for i in range(state_size):
            amplitude = state_np[i]
            if abs(amplitude) > 10**(-precision):
                binary_str = f'{i:0{n_qubits}b}'
                label = f'|{binary_str}⟩'
                formatted_amp = QuantumUtils.format_complex(complex(amplitude), precision)
                
                if len(terms) > 0 and not formatted_amp.startswith('(') and amplitude.real >= 0:
                    formatted_amp = "+" + formatted_amp
                terms.append(f"{formatted_amp} {label}")
        
        return " ".join(terms) if terms else "0"