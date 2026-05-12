from simulator import QuantumSimulator
from classes.gates import QuantumGates
import torch
import math


class GroverSearch:
    def __init__(self, arr, target_value):
        self.arr = arr
        self.target_value = target_value
        self.n_qubits = math.ceil(math.log2(len(arr)))
        self.N = 2 ** self.n_qubits
        
        # Pad the array so its length = 2^n_qubits
        if len(self.arr) < self.N:
            self.arr += [None] * (self.N - len(self.arr))
        
        self.simulator = QuantumSimulator(n_qubits=self.n_qubits)

    def initialize(self):
        print(f"\n[Initialization] Creating superposition for N = {self.N}")
        self.simulator.reset()
        self.simulator.create_superposition_all()
        # self.simulator.print_state()

    def oracle(self):
        print(f"\n[Oracle] Flipping sign of states where arr[i] == {self.target_value}")
        
        # Apply oracle by flipping the phase of target states
        # We'll use Z gates controlled by the binary representation of target indices
        target_indices = []
        for i in range(self.N):
            if self.arr[i] == self.target_value:
                print(f"  Marking index {i} (|{i:0{self.n_qubits}b}⟩)")
                target_indices.append(i)
        
        # For each target index, apply a multi-controlled Z gate
        for index in target_indices:
            self._apply_oracle_for_index(index)
        
        # self.simulator.print_state()

    def _apply_oracle_for_index(self, target_index):
        """Apply oracle operation for a specific index using quantum gates"""
        # Convert index to binary representation
        binary = f'{target_index:0{self.n_qubits}b}'
        
        # We need to flip qubits that are 0 in the binary representation,
        # then apply multi-controlled Z, then flip back
        flip_qubits = []
        for i, bit in enumerate(binary):    # reversed because qubit 0 is rightmost
            if bit == '0':
                flip_qubits.append(i)
                self.simulator.x(i)  # Flip to make it 1
        
        # Apply multi-controlled Z gate
        self._apply_multi_controlled_z()
        
        # Flip back the qubits we flipped
        for qubit in flip_qubits:
            self.simulator.x(qubit)

    def _apply_multi_controlled_z(self):
        """Apply a Z gate controlled by all qubits"""
        if self.n_qubits == 1:
            self.simulator.z(0)
        elif self.n_qubits == 2:
            self.simulator.cz(0, 1)
        else:
            # For more than 2 qubits, we need to implement multi-controlled Z
            # This is a simplified approach - in practice, you'd use ancilla qubits
            # or decompose into multiple 2-qubit gates
            self._apply_multi_controlled_z_decomposed()

    def _apply_multi_controlled_z_decomposed(self):
        """Decompose multi-controlled Z into 2-qubit gates"""
        # For simplicity, we'll use a direct state manipulation approach
        # This could be optimized with proper gate decomposition
        current_state = self.simulator.get_state()
        
        # Find the all-ones state and flip its phase
        all_ones_index = (1 << self.n_qubits) - 1  # 2^n - 1
        current_state[all_ones_index] *= -1
        
        self.simulator.set_state(current_state)

    def apply_diffusion(self):
        """Apply diffusion operator using individual gates"""
        print(f"\n[Diffusion] Inverting about the mean")
        
        # Step 1: Apply H gates to all qubits
        for i in range(self.n_qubits):
            self.simulator.h(i)
        
        # Step 2: Apply oracle for |00...0⟩ state (flip phase of all-zero state)
        self._apply_zero_state_oracle()
        
        # Step 3: Apply H gates to all qubits again
        for i in range(self.n_qubits):
            self.simulator.h(i)
        
        # self.simulator.print_state()

    def _apply_zero_state_oracle(self):
        """Apply oracle that flips the phase of |00...0⟩ state"""
        # Flip all qubits (X gates), apply multi-controlled Z, then flip back
        for i in range(self.n_qubits):
            self.simulator.x(i)
        
        # Apply multi-controlled Z
        self._apply_multi_controlled_z()
        
        # Flip back
        for i in range(self.n_qubits):
            self.simulator.x(i)

    def run(self):
        print("\n[Grover Search Started]")
        self.initialize()
        
        iterations = int(math.floor((math.pi / 4) * math.sqrt(self.N)))
        print(f"[Iterations] Grover will run for {iterations} iterations")
        
        for i in range(iterations):
            print(f"\n--- Iteration {i + 1} ---")
            self.oracle()
            self.apply_diffusion()
        
        result = self.simulator.measure(shots=1)
        result_index = int(result[0], 2)
        print(f"\n[Measurement] Final result: |{result[0]}⟩ → Index = {result_index} → Value = {self.arr[result_index]}")
        return result_index, self.arr[result_index]
