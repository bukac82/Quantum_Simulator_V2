import torch
import math
import numpy as np
from typing import List, Optional, Callable, Tuple
from simulator import QuantumSimulator
from algos.qft import QuantumFourierTransform

class QuantumPhaseEstimation:
    """Quantum Phase Estimation algorithm implementation"""
    
    def __init__(self, simulator: QuantumSimulator):
        self.sim = simulator
        self.device = simulator.device
        self.qft = QuantumFourierTransform(simulator)
    
    def estimate_phase(self, 
                      unitary_power_func: Callable[[int, int], None],
                      eigenstate_qubits: List[int],
                      counting_qubits: List[int],
                      prepare_eigenstate_func: Optional[Callable[[], None]] = None) -> List[str]:
        """
        Perform quantum phase estimation
        
        Args:
            unitary_power_func: Function that applies U^(2^k) to eigenstate qubits
                               Takes (power_of_2, target_qubit) as arguments
            eigenstate_qubits: Qubits containing the eigenstate
            counting_qubits: Qubits used for phase estimation (measurement qubits)
            prepare_eigenstate_func: Optional function to prepare eigenstate
        
        Returns:
            List of measurement results as binary strings
        """
        n_counting = len(counting_qubits)
        
        # Step 1: Prepare eigenstate (if preparation function provided)
        if prepare_eigenstate_func:
            prepare_eigenstate_func()
        
        # Step 2: Initialize counting qubits in superposition
        for qubit in counting_qubits:
            self.sim.h(qubit)
        
        # Step 3: Apply controlled unitary operations
        for i, control_qubit in enumerate(counting_qubits):
            power = 2 ** (n_counting - 1 - i)  # Powers: 2^(n-1), 2^(n-2), ..., 2^1, 2^0
            
            # Apply controlled U^(2^k) operations
            for target_qubit in eigenstate_qubits:
                self._controlled_unitary_power(control_qubit, target_qubit, 
                                             unitary_power_func, power)
        
        # Step 4: Apply inverse QFT to counting qubits
        self.qft.inverse_qft(counting_qubits)
        
        # Step 5: Measure counting qubits
        results = self.sim.measure(shots=1000)
        
        return results
    
    def _controlled_unitary_power(self, control: int, target: int, 
                                unitary_power_func: Callable[[int, int], None], 
                                power: int):
        """Apply controlled version of U^power"""
        # This is a simplified implementation
        # In practice, you'd need to implement controlled versions of your unitary
        # For demonstration, we'll use a controlled phase rotation
        angle = 2 * math.pi * power / (2**4)  # Example phase
        self.qft._controlled_phase_rotation(control, target, angle)
    
    def estimate_eigenphase(self, 
                           phase: float,
                           n_counting_qubits: int = 4,
                           eigenstate_qubit: int = None) -> Tuple[float, List[str]]:
        """
        Estimate phase of a simple phase gate eigenstate
        
        Args:
            phase: True phase to estimate (for demonstration)
            n_counting_qubits: Number of counting qubits for precision
            eigenstate_qubit: Qubit containing eigenstate (if None, uses last qubit)
        
        Returns:
            Tuple of (estimated_phase, measurement_results)
        """
        if eigenstate_qubit is None:
            eigenstate_qubit = self.sim.n_qubits - 1
        
        counting_qubits = list(range(n_counting_qubits))
        
        # Prepare |1⟩ eigenstate of phase gate
        self.sim.x(eigenstate_qubit)
        
        # Create unitary power function for phase gate
        def phase_power_func(power: int, target: int):
            total_phase = phase * power
            self.sim.rz(total_phase, target)
        
        def prepare_eigenstate():
            self.sim.x(eigenstate_qubit)
        
        # Perform phase estimation
        results = self.estimate_phase(
            unitary_power_func=phase_power_func,
            eigenstate_qubits=[eigenstate_qubit],
            counting_qubits=counting_qubits,
            prepare_eigenstate_func=None  # Already prepared above
        )
        
        # Analyze results to get estimated phase
        estimated_phase = self._analyze_phase_estimation_results(results, n_counting_qubits)
        
        return estimated_phase, results
    
    def _analyze_phase_estimation_results(self, results: List[str], n_counting_qubits: int) -> float:
        """Analyze measurement results to extract estimated phase"""
        # Count occurrences of each measurement outcome
        counts = {}
        for result in results:
            # Extract counting qubits measurement (first n_counting_qubits bits)
            counting_result = result[:n_counting_qubits]
            counts[counting_result] = counts.get(counting_result, 0) + 1
        
        # Find most frequent outcome
        most_frequent = max(counts.keys(), key=lambda x: counts[x])
        
        # Convert binary string to decimal and normalize
        decimal_value = int(most_frequent, 2)
        estimated_phase = decimal_value / (2 ** n_counting_qubits)
        
        return estimated_phase