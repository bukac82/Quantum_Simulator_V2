import torch
import math
import numpy as np
from typing import List, Optional, Tuple
from simulator import QuantumSimulator
from algos.qpe import QuantumPhaseEstimation
import random
from math import gcd


class ShorsAlgorithm:
    """
    Shor's algorithm for integer factorization using quantum period finding
    """
    
    def __init__(self, N: int, n_counting_qubits: int = 8):
        """
        Initialize Shor's algorithm
        
        Args:
            N: Integer to factor
            n_counting_qubits: Number of counting qubits for phase estimation
        """
        self.N = N
        self.n_counting_qubits = n_counting_qubits
        
        # Calculate required qubits: counting qubits + work qubits for modular exponentiation
        self.n_work_qubits = math.ceil(math.log2(N)) + 2  # Extra qubits for computation
        self.total_qubits = n_counting_qubits + self.n_work_qubits
        
        self.sim = QuantumSimulator(n_qubits=self.total_qubits)
        self.qpe = QuantumPhaseEstimation(self.sim)
        
        # Qubit assignments
        self.counting_qubits = list(range(n_counting_qubits))
        self.work_qubits = list(range(n_counting_qubits, self.total_qubits))
        
    def factor(self, max_attempts: int = 10) -> Optional[Tuple[int, int]]:
        """
        Factor the integer N using Shor's algorithm
        
        Args:
            max_attempts: Maximum number of attempts before giving up
            
        Returns:
            Tuple of (factor1, factor2) if successful, None otherwise
        """
        print(f"\n[Shor's Algorithm] Factoring N = {self.N}")
        
        # Step 1: Classical preprocessing
        if self._is_even(self.N):
            return (2, self.N // 2)
        
        if self._is_perfect_power(self.N):
            return self._find_perfect_power_factors()
        
        # Step 2: Quantum period finding
        for attempt in range(max_attempts):
            print(f"\n--- Attempt {attempt + 1} ---")
            
            # Choose random a coprime to N
            a = self._choose_random_a()
            if a is None:
                continue
                
            print(f"Chosen a = {a}")
            
            # Check if we got lucky with gcd
            g = gcd(a, self.N)
            if g > 1:
                print(f"Found factor by GCD: {g}")
                return (g, self.N // g)
            
            # Quantum period finding
            period = self._quantum_period_finding(a)
            if period is None:
                print("Quantum period finding failed")
                continue
                
            print(f"Found period r = {period}")
            
            # Classical post-processing
            factors = self._classical_post_processing(a, period)
            if factors:
                return factors
        
        print("Shor's algorithm failed to find factors")
        return None
    
    def _is_even(self, n: int) -> bool:
        """Check if number is even"""
        return n % 2 == 0
    
    def _is_perfect_power(self, n: int) -> bool:
        """Check if n is a perfect power (n = b^k for k > 1)"""
        for k in range(2, int(math.log2(n)) + 1):
            b = round(n ** (1/k))
            if b ** k == n:
                return True
        return False
    
    def _find_perfect_power_factors(self) -> Tuple[int, int]:
        """Find factors if N is a perfect power"""
        for k in range(2, int(math.log2(self.N)) + 1):
            b = round(self.N ** (1/k))
            if b ** k == self.N:
                return (b, b ** (k-1))
        return None
    
    def _choose_random_a(self) -> Optional[int]:
        """Choose random a coprime to N"""
        max_attempts = 100
        for _ in range(max_attempts):
            a = random.randint(2, self.N - 1)
            if gcd(a, self.N) == 1:
                return a
        return None
    
    def _quantum_period_finding(self, a: int) -> Optional[int]:
        """
        Quantum period finding using phase estimation
        
        Args:
            a: Base for modular exponentiation
            
        Returns:
            Period r such that a^r ≡ 1 (mod N), or None if failed
        """
        print(f"[Quantum Period Finding] Finding period of a^x mod N where a = {a}, N = {self.N}")
        
        # Reset simulator
        self.sim.reset()
        
        # Prepare initial state |1⟩ in work register
        self.sim.x(self.work_qubits[0])  # Start with |1⟩
        
        # Create superposition in counting register
        for qubit in self.counting_qubits:
            self.sim.h(qubit)
        
        # Apply controlled modular exponentiation
        self._controlled_modular_exponentiation(a)
        
        # Apply inverse QFT to counting register
        self.qpe.qft.inverse_qft(self.counting_qubits)
        
        # Measure counting register
        results = self.sim.measure(shots=1000)
        
        # Analyze results to find period
        return self._analyze_period_results(results, a)
    
    def _controlled_modular_exponentiation(self, a: int):
        """
        Exact permutation of the wavefunction to implement |j⟩|1⟩ → |j⟩|a^j mod N⟩.
        Works for small N, directly modifies the quantum state vector.
        """
        new_state = torch.zeros_like(self.sim.state)
        work_mask = (1 << self.n_work_qubits) - 1  # mask for low bits

        for idx in range(self.sim.state_size):
            amp = self.sim.state[idx]
            if amp.abs() == 0:
                continue

            j = idx >> self.n_work_qubits  # portion representing |j⟩
            x = idx & work_mask            # work register bits

            if x == 0:
                new_x = 0
            else:
                a_pow_j = pow(a, j, self.N)
                new_x = (a_pow_j * x) % self.N

            new_idx = (j << self.n_work_qubits) | new_x
            new_state[new_idx] += amp

        self.sim.state = new_state

    
    def _analyze_period_results(self, results: List[str], a: int) -> Optional[int]:
        """
        Analyze quantum measurement results to extract the period
        
        Args:
            results: List of measurement outcomes
            a: Base used in modular exponentiation
            
        Returns:
            Period r, or None if analysis failed
        """
        print("[Period Analysis] Analyzing measurement results")
        
        # Count measurement outcomes in counting register
        counts = {}
        for result in results:
            # Extract counting register bits
            counting_result = result[:self.n_counting_qubits]
            counts[counting_result] = counts.get(counting_result, 0) + 1
        
        # Find most frequent outcomes
        sorted_outcomes = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Top measurement outcomes:")
        for outcome, count in sorted_outcomes[:5]:
            decimal = int(outcome, 2)
            print(f"  |{outcome}⟩ → {decimal} (count: {count})")
        
        # Try to extract period from top outcomes
        for outcome, count in sorted_outcomes[:3]:
            decimal_value = int(outcome, 2)
            if decimal_value == 0:
                continue
                
            # Phase estimation gives us s/r where s is measured value
            # and r is the period we want to find
            period = self._extract_period_from_phase(decimal_value, 2**self.n_counting_qubits)
            
            if period and self._verify_period(a, period):
                return period
        
        return None
    
    def _extract_period_from_phase(self, measured_value: int, total_outcomes: int) -> Optional[int]:
        """
        Extract period from measured phase using continued fractions
        
        Args:
            measured_value: Measured decimal value
            total_outcomes: Total possible outcomes (2^n_counting_qubits)
            
        Returns:
            Estimated period
        """
        if measured_value == 0:
            return None
        
        # Use continued fractions to find period
        phase = measured_value / total_outcomes
        
        # Simple approach: try small denominators
        for r in range(1, min(self.N, 100)):  # Limit search space
            if abs(phase - round(phase * r) / r) < 1 / (2 * total_outcomes):
                return r
        
        # Alternative: use built-in fraction approximation
        from fractions import Fraction
        frac = Fraction(measured_value, total_outcomes).limit_denominator(self.N)
        return frac.denominator
    
    def _verify_period(self, a: int, r: int) -> bool:
        """
        Verify that r is indeed the period (a^r ≡ 1 mod N)
        
        Args:
            a: Base
            r: Candidate period
            
        Returns:
            True if r is the correct period
        """
        if r <= 0:
            return False
        return pow(a, r, self.N) == 1
    
    def _classical_post_processing(self, a: int, r: int) -> Optional[Tuple[int, int]]:
        """
        Classical post-processing to extract factors from the period
        
        Args:
            a: Base used in period finding
            r: Found period
            
        Returns:
            Tuple of factors, or None if failed
        """
        print(f"[Classical Post-processing] a = {a}, r = {r}")
        
        # Check if period is even
        if r % 2 != 0:
            print("Period is odd, cannot proceed")
            return None
        
        # Check if a^(r/2) ≡ -1 (mod N)
        half_power = pow(a, r // 2, self.N)
        if half_power == self.N - 1:  # This is -1 mod N
            print("a^(r/2) ≡ -1 (mod N), cannot proceed")
            return None
        
        # Compute potential factors
        factor1 = gcd(half_power - 1, self.N)
        factor2 = gcd(half_power + 1, self.N)
        
        print(f"a^(r/2) = {half_power}")
        print(f"gcd({half_power} - 1, {self.N}) = {factor1}")
        print(f"gcd({half_power} + 1, {self.N}) = {factor2}")
        
        # Check if we found non-trivial factors
        if 1 < factor1 < self.N:
            return (factor1, self.N // factor1)
        elif 1 < factor2 < self.N:
            return (factor2, self.N // factor2)
        else:
            print("No non-trivial factors found")
            return None
    
    def demonstrate_small_example(self):
        """Demonstrate with a small example"""
        print(f"\n[Demonstration] Factoring N = {self.N}")
        print(f"Using {self.n_counting_qubits} counting qubits and {self.n_work_qubits} work qubits")
        
        factors = self.factor()
        
        if factors:
            f1, f2 = factors
            print(f"\n[Success] Found factors: {self.N} = {f1} × {f2}")
            print(f"Verification: {f1} × {f2} = {f1 * f2}")
        else:
            print(f"\n[Failed] Could not factor {self.N}")
        
        return factors