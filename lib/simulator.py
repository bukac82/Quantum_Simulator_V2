import torch
import numpy as np
from typing import List, Union, Optional
from lib.classes.gates import QuantumGates
from lib.classes.utils import QuantumUtils


class QuantumSimulator:
    """N-qubit quantum circuit simulator using PyTorch with memory-optimized linear operations"""
    
    def __init__(self, n_qubits: int = 2, device: str = 'cpu'):
        if not torch.cpu.is_available():
            raise RuntimeError("cpu is not available. This simulator requires cpu.")
        
        self.device = 'cpu'
        self.n_qubits = n_qubits
        self.state_size = 2 ** n_qubits
        self.gates = QuantumGates(device=self.device)
        self.reset()
        self.gate_sequence = []

    def reset(self):
        """Reset simulator to |00...0⟩ state"""
        self.state = torch.zeros(self.state_size, dtype=torch.complex64, device=self.device)
        self.state[0] = 1.0 + 0j
        self.gate_sequence = []

    def get_state(self) -> torch.Tensor:
        """Get current quantum state"""
        return self.state.clone()

    def set_state(self, state: torch.Tensor):
        """Set quantum state (with normalization)"""
        if state.shape != (self.state_size,):
            raise ValueError(f"State must have shape ({self.state_size},)")
        self.state = QuantumUtils.normalize_state(state.to(self.device))

    def get_probabilities(self) -> torch.Tensor:
        """Get measurement probabilities for all basis states"""
        return torch.abs(self.state) ** 2

    def _apply_single_qubit_gate_linear(self, gate: torch.Tensor, target_qubit: int):
        """Apply single-qubit gate using linear operations without full Kronecker product"""
        if target_qubit < 0 or target_qubit >= self.n_qubits:
            raise ValueError(f"Target qubit {target_qubit} out of range [0, {self.n_qubits-1}]")
        
        # Create new state vector
        new_state = torch.zeros_like(self.state)
        
        # Number of qubits before and after the target qubit
        qubits_before = target_qubit
        qubits_after = self.n_qubits - target_qubit - 1
        
        # Block size for the operation
        block_size = 2 ** qubits_after
        total_blocks = 2 ** qubits_before
        
        for block_idx in range(total_blocks):
            # Calculate base indices for this block
            base_0 = block_idx * (2 * block_size)  # |...0...⟩ states
            base_1 = base_0 + block_size            # |...1...⟩ states
            
            # Extract the relevant amplitudes
            amp_0 = self.state[base_0:base_0 + block_size]
            amp_1 = self.state[base_1:base_1 + block_size]
            
            # Apply the gate transformation
            new_amp_0 = gate[0, 0] * amp_0 + gate[0, 1] * amp_1
            new_amp_1 = gate[1, 0] * amp_0 + gate[1, 1] * amp_1
            
            # Update the new state
            new_state[base_0:base_0 + block_size] = new_amp_0
            new_state[base_1:base_1 + block_size] = new_amp_1
        
        self.state = new_state

    def _apply_two_qubit_gate_linear(self, gate_matrix: torch.Tensor, control: int, target: int):
        """Apply two-qubit gate using linear operations without full matrix construction"""
        if control == target:
            raise ValueError("Control and target qubits must be different")
        if control < 0 or control >= self.n_qubits or target < 0 or target >= self.n_qubits:
            raise ValueError(f"Qubit indices must be in range [0, {self.n_qubits-1}]")
        
        # Ensure control < target for consistent indexing
        if control > target:
            control, target = target, control
            # For CNOT and CZ gates, we need to adjust the matrix accordingly
            if gate_matrix.shape == (4, 4):
                # Swap control and target in the gate matrix
                # Original: |control,target⟩ -> reorder to |target,control⟩
                perm_matrix = torch.tensor([
                    [1, 0, 0, 0],  # |00⟩ -> |00⟩
                    [0, 0, 1, 0],  # |01⟩ -> |10⟩
                    [0, 1, 0, 0],  # |10⟩ -> |01⟩
                    [0, 0, 0, 1]   # |11⟩ -> |11⟩
                ], dtype=torch.complex64, device=self.device)
                gate_matrix = perm_matrix @ gate_matrix @ perm_matrix.T
        
        new_state = torch.zeros_like(self.state)
        
        # Calculate stride parameters
        control_stride = 2 ** (self.n_qubits - control - 1)
        target_stride = 2 ** (self.n_qubits - target - 1)
        
        # Iterate through all basis states
        for i in range(self.state_size):
            # Extract control and target bit values
            control_bit = (i >> (self.n_qubits - control - 1)) & 1
            target_bit = (i >> (self.n_qubits - target - 1)) & 1
            
            # Map to 2-qubit basis state index
            two_qubit_idx = control_bit * 2 + target_bit
            
            # Apply gate transformation
            for j in range(4):
                if abs(gate_matrix[j, two_qubit_idx]) > 1e-12:
                    # Decode output 2-qubit state
                    new_control_bit = j // 2
                    new_target_bit = j % 2
                    
                    # Calculate the output state index
                    new_i = i
                    # Update control bit
                    if control_bit != new_control_bit:
                        new_i ^= (1 << (self.n_qubits - control - 1))
                    # Update target bit
                    if target_bit != new_target_bit:
                        new_i ^= (1 << (self.n_qubits - target - 1))
                    
                    new_state[new_i] += gate_matrix[j, two_qubit_idx] * self.state[i]
        
        self.state = new_state

    def _create_cnot_matrix(self) -> torch.Tensor:
        """Create CNOT gate matrix"""
        return torch.tensor([
            [1, 0, 0, 0],
            [0, 1, 0, 0], 
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=torch.complex64, device=self.device)

    def _create_cz_matrix(self) -> torch.Tensor:
        """Create controlled-Z gate matrix"""
        return torch.tensor([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1]
        ], dtype=torch.complex64, device=self.device)

    def _apply_single_qubit_gate(self, gate: torch.Tensor, qubit: int, gate_name: str = None, param: float = None):
        """Apply single-qubit gate to specified qubit using linear operations"""
        self._apply_single_qubit_gate_linear(gate, qubit)
        
        if gate_name:
            if param is not None:
                self.gate_sequence.append((gate_name, qubit, param))
            else:
                self.gate_sequence.append((gate_name, qubit))

    def _apply_two_qubit_gate(self, gate_matrix: torch.Tensor, control: int, target: int, gate_name: str = None):
        """Apply two-qubit gate using linear operations"""
        self._apply_two_qubit_gate_linear(gate_matrix, control, target)
        
        if gate_name:
            self.gate_sequence.append((gate_name, (control, target)))

    # Single-qubit gate methods
    def x(self, qubit: int):
        """Apply Pauli-X gate"""
        self._apply_single_qubit_gate(self.gates.X, qubit, 'X')

    def y(self, qubit: int):
        """Apply Pauli-Y gate"""
        self._apply_single_qubit_gate(self.gates.Y, qubit, 'Y')

    def z(self, qubit: int):
        """Apply Pauli-Z gate"""
        self._apply_single_qubit_gate(self.gates.Z, qubit, 'Z')

    def h(self, qubit: int):
        """Apply Hadamard gate"""
        self._apply_single_qubit_gate(self.gates.H, qubit, 'H')

    def s(self, qubit: int):
        """Apply S gate (phase gate)"""
        self._apply_single_qubit_gate(self.gates.S, qubit, 'S')

    def t(self, qubit: int):
        """Apply T gate"""
        self._apply_single_qubit_gate(self.gates.T, qubit, 'T')

    # Rotation gates
    def rx(self, angle: float, qubit: int):
        """Apply rotation around X-axis"""
        self._apply_single_qubit_gate(self.gates.rx_matrix(angle), qubit, 'RX', angle)

    def ry(self, angle: float, qubit: int):
        """Apply rotation around Y-axis"""
        self._apply_single_qubit_gate(self.gates.ry_matrix(angle), qubit, 'RY', angle)

    def rz(self, angle: float, qubit: int):
        """Apply rotation around Z-axis"""
        self._apply_single_qubit_gate(self.gates.rz_matrix(angle), qubit, 'RZ', angle)

    # Two-qubit gates
    def cnot(self, control: int, target: int):
        """Apply CNOT gate"""
        cnot_matrix = self._create_cnot_matrix()
        self._apply_two_qubit_gate(cnot_matrix, control, target, 'CNOT')

    def cz(self, control: int, target: int):
        """Apply controlled-Z gate"""
        cz_matrix = self._create_cz_matrix()
        self._apply_two_qubit_gate(cz_matrix, control, target, 'CZ')

    # Measurement
    def measure(self, shots: int = 1) -> List[str]:
        """Perform measurement and return results"""
        probs = self.get_probabilities()
        outcomes = torch.multinomial(probs, shots, replacement=True)
        results = [f'{x:0{self.n_qubits}b}' for x in outcomes.tolist()]
        return results

    def measure_single_qubit(self, qubit: int, shots: int = 1) -> List[int]:
        """Measure single qubit and return 0/1 results"""
        probs = self.get_probabilities()
        prob_0 = sum(probs[i] for i in range(self.state_size) 
                    if not ((i >> qubit) & 1))
        prob_1 = 1 - prob_0
        
        outcomes = torch.multinomial(torch.tensor([prob_0, prob_1]), shots, replacement=True)
        return outcomes.tolist()

    def print_state(self, precision: int = 4):
        """Print current quantum state in readable format"""
        state_str = QuantumUtils.state_to_string(self.state, self.n_qubits, precision)
        print(f"Quantum State ({self.n_qubits} qubits): {state_str}")

    def print_probabilities(self, precision: int = 4):
        """Print measurement probabilities"""
        probs = self.get_probabilities()
        prob_np = QuantumUtils.tensor_to_numpy(probs)
        
        print(f"Measurement Probabilities ({self.n_qubits} qubits):")
        for i, prob in enumerate(prob_np):
            if prob > 10**(-precision):
                binary_str = f'{i:0{self.n_qubits}b}'
                print(f"  |{binary_str}⟩: {prob:.{precision}f}")

    def get_circuit_depth(self) -> int:
        """Get circuit depth (number of gates applied)"""
        return len(self.gate_sequence)

    def create_superposition_all(self):
        """Create equal superposition of all basis states"""
        for i in range(self.n_qubits):
            self.h(i)

    def create_bell_state(self, state_type: str = '00'):
        """Create Bell state (only for 2-qubit systems)"""
        if self.n_qubits != 2:
            raise ValueError("Bell states are only defined for 2-qubit systems")
        
        bell_state = QuantumUtils.create_bell_state(state_type, self.n_qubits, self.device)
        self.set_state(bell_state)

    def create_ghz_state(self):
        """Create GHZ state: (|00...0⟩ + |11...1⟩)/√2"""
        ghz_state = QuantumUtils.create_ghz_state(self.n_qubits, self.device)
        self.set_state(ghz_state)

    def get_memory_usage(self) -> dict:
        """Get memory usage statistics"""
        state_memory = self.state.element_size() * self.state.nelement()
        return {
            'state_vector_bytes': state_memory,
            'state_vector_mb': state_memory / (1024 * 1024),
            'state_size': self.state_size,
            'n_qubits': self.n_qubits
        }
