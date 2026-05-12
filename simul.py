import torch
import torch.nn as nn
import numpy as np
from typing import Union, List
import math

class QuantumSimulator2Q:
    """A 2-qubit quantum simulator using PyTorch"""
    
    def __init__(self, device='cuda'):
        self.device = device
        self.n_qubits = 2
        self.state_size = 2**self.n_qubits  # 4 states for 2 qubits
        
        # Initialize to |00⟩ state
        self.state = torch.zeros(self.state_size, dtype=torch.complex64, device=device)
        self.state[0] = 1.0 + 0j
        
        # Define Pauli matrices
        self.I = torch.tensor([[1, 0], [0, 1]], dtype=torch.complex64, device=device)
        self.X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64, device=device)
        self.Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64, device=device)
        self.Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64, device=device)
        self.H = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex64, device=device) / math.sqrt(2)
        
        # S and T gates - Fixed to use proper complex values
        self.S = torch.tensor([[1, 0], [0, 1j]], dtype=torch.complex64, device=device)
        # T gate: e^(iπ/4) = cos(π/4) + i*sin(π/4) = 1/√2 + i/√2
        t_phase = complex(math.cos(math.pi/4), math.sin(math.pi/4))
        self.T = torch.tensor([[1, 0], [0, t_phase]], dtype=torch.complex64, device=device)
    
    def reset(self):
        """Reset to |00⟩ state"""
        self.state = torch.zeros(self.state_size, dtype=torch.complex64, device=self.device)
        self.state[0] = 1.0 + 0j
    
    def get_state(self):
        """Get current quantum state"""
        return self.state.clone()
    
    def set_state(self, state: torch.Tensor):
        """Set quantum state (must be normalized)"""
        if state.shape != (self.state_size,):
            raise ValueError(f"State must have shape ({self.state_size},)")
        
        # Normalize the state
        norm = torch.sqrt(torch.sum(torch.abs(state)**2))
        self.state = state / norm
    
    def get_probabilities(self):
        """Get measurement probabilities for each basis state"""
        return torch.abs(self.state)**2
    
    def _single_qubit_gate(self, gate: torch.Tensor, qubit: int):
        """Apply single qubit gate to specified qubit (0 or 1)"""
        if qubit == 0:
            # Gate on qubit 0: gate ⊗ I
            full_gate = torch.kron(gate, self.I)
        elif qubit == 1:
            # Gate on qubit 1: I ⊗ gate
            full_gate = torch.kron(self.I, gate)
        else:
            raise ValueError("Qubit must be 0 or 1")
        
        self.state = full_gate @ self.state
    
    def _two_qubit_gate(self, gate: torch.Tensor):
        """Apply 2-qubit gate to both qubits"""
        if gate.shape != (4, 4):
            raise ValueError("Two-qubit gate must be 4x4")
        
        self.state = gate @ self.state
    
    # Single qubit gates
    def x(self, qubit: int):
        """Apply Pauli-X (NOT) gate"""
        self._single_qubit_gate(self.X, qubit)
    
    def y(self, qubit: int):
        """Apply Pauli-Y gate"""
        self._single_qubit_gate(self.Y, qubit)
    
    def z(self, qubit: int):
        """Apply Pauli-Z gate"""
        self._single_qubit_gate(self.Z, qubit)
    
    def h(self, qubit: int):
        """Apply Hadamard gate"""
        self._single_qubit_gate(self.H, qubit)
    
    def s(self, qubit: int):
        """Apply S gate"""
        self._single_qubit_gate(self.S, qubit)
    
    def t(self, qubit: int):
        """Apply T gate"""
        self._single_qubit_gate(self.T, qubit)
    
    def rx(self, angle: float, qubit: int):
        """Apply rotation around X axis"""
        cos_half = math.cos(angle / 2)
        sin_half = math.sin(angle / 2)
        rx_gate = torch.tensor([
            [cos_half, -1j * sin_half],
            [-1j * sin_half, cos_half]
        ], dtype=torch.complex64, device=self.device)
        self._single_qubit_gate(rx_gate, qubit)
    
    def ry(self, angle: float, qubit: int):
        """Apply rotation around Y axis"""
        cos_half = math.cos(angle / 2)
        sin_half = math.sin(angle / 2)
        ry_gate = torch.tensor([
            [cos_half, -sin_half],
            [sin_half, cos_half]
        ], dtype=torch.complex64, device=self.device)
        self._single_qubit_gate(ry_gate, qubit)
    
    def rz(self, angle: float, qubit: int):
        """Apply rotation around Z axis"""
        # Fixed: Use Python complex() instead of torch.exp() with complex input
        exp_neg = complex(math.cos(-angle/2), math.sin(-angle/2))
        exp_pos = complex(math.cos(angle/2), math.sin(angle/2))
        rz_gate = torch.tensor([
            [exp_neg, 0],
            [0, exp_pos]
        ], dtype=torch.complex64, device=self.device)
        self._single_qubit_gate(rz_gate, qubit)
    
    # Two-qubit gates
    def cnot(self, control: int, target: int):
        """Apply CNOT gate"""
        if control == target:
            raise ValueError("Control and target must be different")
        
        if control == 0 and target == 1:
            # Control on qubit 0, target on qubit 1
            cnot_gate = torch.tensor([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]
            ], dtype=torch.complex64, device=self.device)
        else:  # control == 1 and target == 0
            # Control on qubit 1, target on qubit 0
            cnot_gate = torch.tensor([
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
                [0, 1, 0, 0]
            ], dtype=torch.complex64, device=self.device)
        
        self._two_qubit_gate(cnot_gate)
    
    def cz(self, control: int, target: int):
        """Apply controlled-Z gate"""
        if control == target:
            raise ValueError("Control and target must be different")
        
        cz_gate = torch.tensor([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1]
        ], dtype=torch.complex64, device=self.device)
        
        self._two_qubit_gate(cz_gate)
    
    def swap(self):
        """Apply SWAP gate between the two qubits"""
        swap_gate = torch.tensor([
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ], dtype=torch.complex64, device=self.device)
        
        self._two_qubit_gate(swap_gate)
    
    def measure(self, qubit: int = None):
        """
        Measure qubit(s) and return result
        If qubit is None, measure both qubits
        Returns: measurement result(s) and post-measurement state
        """
        probabilities = self.get_probabilities()
        
        if qubit is None:
            # Measure both qubits
            outcome = torch.multinomial(probabilities, 1).item()
            # Collapse to measured state
            self.state = torch.zeros_like(self.state)
            self.state[outcome] = 1.0 + 0j
            return outcome
        else:
            # Measure single qubit
            if qubit == 0:
                # Probability of measuring 0 on qubit 0 (states |00⟩ and |01⟩)
                prob_0 = probabilities[0] + probabilities[1]
            else:  # qubit == 1
                # Probability of measuring 0 on qubit 1 (states |00⟩ and |10⟩)
                prob_0 = probabilities[0] + probabilities[2]
            
            # Sample measurement outcome
            outcome = 0 if torch.rand(1).item() < prob_0 else 1
            
            # Collapse state based on measurement
            if qubit == 0:
                if outcome == 0:
                    # Measured 0 on qubit 0
                    self.state[2:] = 0  # Zero out |10⟩ and |11⟩
                    norm = torch.sqrt(prob_0)
                    if norm > 0:
                        self.state[:2] /= norm
                else:
                    # Measured 1 on qubit 0
                    self.state[:2] = 0  # Zero out |00⟩ and |01⟩
                    norm = torch.sqrt(1 - prob_0)
                    if norm > 0:
                        self.state[2:] /= norm
            else:  # qubit == 1
                if outcome == 0:
                    # Measured 0 on qubit 1
                    self.state[1] = 0  # Zero out |01⟩
                    self.state[3] = 0  # Zero out |11⟩
                    norm = torch.sqrt(prob_0)
                    if norm > 0:
                        self.state[0] /= norm
                        self.state[2] /= norm
                else:
                    # Measured 1 on qubit 1
                    self.state[0] = 0  # Zero out |00⟩
                    self.state[2] = 0  # Zero out |10⟩
                    norm = torch.sqrt(1 - prob_0)
                    if norm > 0:
                        self.state[1] /= norm
                        self.state[3] /= norm
            
            return outcome
    
    def expectation_value(self, observable: torch.Tensor):
        """Calculate expectation value of an observable"""
        if observable.shape != (4, 4):
            raise ValueError("Observable must be 4x4 for 2-qubit system")
        
        return torch.real(torch.conj(self.state) @ observable @ self.state).item()
    
    def print_state(self):
        """Print current quantum state in readable format"""
        state_labels = ['|00⟩', '|01⟩', '|10⟩', '|11⟩']
        print("Quantum State:")
        for i, (amplitude, label) in enumerate(zip(self.state, state_labels)):
            if torch.abs(amplitude) > 1e-10:  # Only show non-zero amplitudes
                real_part = torch.real(amplitude).item()
                imag_part = torch.imag(amplitude).item()
                
                if abs(imag_part) < 1e-10:
                    print(f"  {real_part:.4f} {label}")
                elif abs(real_part) < 1e-10:
                    print(f"  {imag_part:.4f}i {label}")
                else:
                    sign = "+" if imag_part >= 0 else "-"
                    print(f"  ({real_part:.4f} {sign} {abs(imag_part):.4f}i) {label}")
