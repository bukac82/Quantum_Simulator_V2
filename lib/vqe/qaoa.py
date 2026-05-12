from .hamiltonian import Hamiltonian, PauliString
from .ansatz import QAOAAnsatz
from .vqe import VariationalQuantumEigensolver
from typing import List, Tuple, Optional
import numpy as np
from collections import Counter
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator import QuantumSimulator
from classes.plotter import QuantumPlotter

class QuantumApproximateOptimization:
    """QAOA algorithm for combinatorial optimization - Enhanced with practical fixes"""
    
    def __init__(self, n_layers: int, optimizer=None, mixer_type: str = 'standard', 
                 use_warm_start: bool = False, adaptive_initialization: bool = True):
        self.n_layers = n_layers
        self.optimizer = optimizer
        self.history = {'energies': [], 'parameters': []}
        
        # Enhancement parameters
        self.mixer_type = mixer_type  # 'standard', 'xy', 'ring', 'asymmetric'
        self.use_warm_start = use_warm_start
        self.adaptive_initialization = adaptive_initialization
        
    def solve_max_cut(self, graph_edges: List[Tuple[int, int]], n_qubits: int, shots: int = 1000) -> dict:
        """Solve Max-Cut problem using QAOA - Enhanced Version with practical fixes"""
        
        # Create Max-Cut Hamiltonian: H = Σ 0.5(1 - ZᵢZⱼ) for edges (i,j)
        # We implement H = -0.5 Σ ZᵢZⱼ (dropping constant term)
        pauli_terms = []
        
        for i, j in graph_edges:
            # Add -0.5 * ZᵢZⱼ term
            pauli_terms.append(PauliString(['Z', 'Z'], -0.5, [i, j]))
        
        hamiltonian = Hamiltonian(pauli_terms)
        
        # Get classical warm start if enabled
        warm_start_solution = None
        if self.use_warm_start:
            warm_start_solution = self._classical_greedy_maxcut(graph_edges, n_qubits)
        
        # Enhanced cost function with improved initialization and mixer
        def cost_function(parameters):
            simulator = QuantumSimulator(n_qubits=n_qubits)
            self._apply_qaoa_circuit(simulator, parameters, graph_edges, warm_start_solution)
            return hamiltonian.expectation_value(simulator, shots)
        
        # Enhanced optimization with multiple strategies
        best_result = None
        best_energy = float('inf')
        
        # Determine number of trials based on problem complexity
        n_trials = max(5, min(10, len(graph_edges)))
        
        for trial in range(n_trials):
            initial_params = self._get_initial_parameters(trial, graph_edges, n_qubits)
            
            # Enhanced optimization settings
            from scipy.optimize import minimize
            
            # Use different optimizers for different trials
            if trial < 3:
                method = 'COBYLA'
                options = {
                    'maxiter': 400,  # More iterations
                    'tol': 1e-8,     # Tighter tolerance
                    'rhobeg': 0.1    # Smaller initial step size
                }
            else:
                method = 'SLSQP'
                options = {
                    'maxiter': 300,
                    'ftol': 1e-8
                }
            
            try:
                result = minimize(
                    cost_function,
                    initial_params,
                    method=method,
                    options=options
                )
                
                if result.fun < best_energy:
                    best_energy = result.fun
                    best_result = result
                    print(f"Trial {trial} ({method}): New best energy = {result.fun:.6f}")
                    
            except Exception as e:
                print(f"Trial {trial} failed: {e}")
                continue
        
        if best_result is None:
            raise RuntimeError("All optimization trials failed")
        
        # Get final state and solution using best parameters
        simulator = QuantumSimulator(n_qubits=n_qubits)
        self._apply_qaoa_circuit(simulator, best_result.x, graph_edges, warm_start_solution)
        measurements = simulator.measure(shots=shots)
        simulator.reset()

        counts = Counter(measurements)
        
        # Calculate actual cut values for all measured solutions
        solution_analysis = {}
        for solution, count in counts.items():
            cut_size = self._calculate_cut_size(solution, graph_edges)
            solution_analysis[solution] = {
                'count': count,
                'cut_size': cut_size,
                'probability': count / shots
            }
        
        # Find solution with maximum cut size (not just most frequent)
        best_cut_solution = max(solution_analysis.keys(), 
                              key=lambda x: solution_analysis[x]['cut_size'])
        best_cut_size = solution_analysis[best_cut_solution]['cut_size']
        
        # Also get most frequent solution
        most_frequent_solution = counts.most_common(1)[0][0]
        
        # Calculate approximation ratio
        max_possible_cut = self._get_max_cut_size(graph_edges, n_qubits)
        approximation_ratio = best_cut_size / max_possible_cut if max_possible_cut > 0 else 0
        
        # Calculate probability of measuring optimal solutions
        optimal_solutions = [sol for sol, analysis in solution_analysis.items() 
                           if analysis['cut_size'] == max_possible_cut]
        optimal_probability = sum(solution_analysis[sol]['probability'] 
                                for sol in optimal_solutions)
        
        # Calculate trivial solution probability for analysis
        all_zero = '0' * n_qubits
        all_one = '1' * n_qubits
        trivial_probability = (solution_analysis.get(all_zero, {}).get('probability', 0) + 
                             solution_analysis.get(all_one, {}).get('probability', 0))
        
        return {
            'best_cut_size': best_cut_size,
            'best_cut_solution': best_cut_solution,
            'most_frequent_solution': most_frequent_solution,
            'most_frequent_cut_size': solution_analysis[most_frequent_solution]['cut_size'],
            'optimal_params': best_result.x,
            'solution_counts': dict(counts.most_common(10)),
            'solution_analysis': solution_analysis,
            'converged': best_result.success,
            'iterations': best_result.nfev,
            'final_energy': best_result.fun,
            'qaoa_layers': self.n_layers,
            'max_possible_cut': max_possible_cut,
            'approximation_ratio': approximation_ratio,
            'optimal_probability': optimal_probability,
            'optimal_solutions': optimal_solutions,
            # Enhanced analysis
            'trivial_probability': trivial_probability,
            'mixer_type': self.mixer_type,
            'used_warm_start': self.use_warm_start
        }
    
    def _apply_qaoa_circuit(self, simulator, parameters, graph_edges, warm_start_solution=None):
        """Apply the complete QAOA circuit with enhancements"""
        
        # Enhanced initialization
        if warm_start_solution is not None:
            # Warm start: initialize to classical solution
            for qubit in range(simulator.n_qubits):
                if warm_start_solution[qubit] == 1:
                    simulator.x(qubit)
            
            # Add small superposition around the classical solution
            for qubit in range(simulator.n_qubits):
                simulator.ry(0.2, qubit)  # Small rotation for exploration
        else:
            # Standard initialization: uniform superposition
            for qubit in range(simulator.n_qubits):
                simulator.h(qubit)
        
        # Apply QAOA layers
        for layer in range(self.n_layers):
            gamma = parameters[2 * layer]
            beta = parameters[2 * layer + 1]
            
            # Apply cost layer: e^(-iγH_C)
            self._apply_cost_layer(simulator, gamma, graph_edges)
            
            # Apply enhanced mixer layer: e^(-iβH_M)
            self._apply_mixer_layer(simulator, beta)
    
    def _apply_cost_layer(self, simulator, gamma, graph_edges):
        """Apply the cost Hamiltonian layer"""
        for i, j in graph_edges:
            # Apply e^(-iγ(-0.5)Z_i⊗Z_j) = e^(i(γ/2)Z_i⊗Z_j)
            simulator.rz(gamma, i)
            simulator.rz(gamma, j)
            simulator.cnot(i, j)
            simulator.rz(-gamma, j)
            simulator.cnot(i, j)
    
    def _apply_mixer_layer(self, simulator, beta):
        """Apply enhanced mixer layer based on mixer_type"""
        
        if self.mixer_type == 'standard':
            # Standard X mixer: Σ X_i
            for qubit in range(simulator.n_qubits):
                simulator.rx(2 * beta, qubit)
        
        elif self.mixer_type == 'xy':
            # XY mixer - promotes more diverse transitions
            for qubit in range(simulator.n_qubits):
                simulator.rx(2 * beta, qubit)
                simulator.ry(beta * 0.5, qubit)  # Add Y component
        
        elif self.mixer_type == 'ring':
            # Ring mixer - couples neighboring qubits
            for qubit in range(simulator.n_qubits):
                simulator.rx(2 * beta, qubit)
            # Add coupling terms
            for qubit in range(simulator.n_qubits - 1):
                simulator.cnot(qubit, qubit + 1)
                simulator.rz(beta * 0.1, qubit + 1)
                simulator.cnot(qubit, qubit + 1)
            # Connect last to first for ring topology
            if simulator.n_qubits > 2:
                simulator.cnot(simulator.n_qubits - 1, 0)
                simulator.rz(beta * 0.1, 0)
                simulator.cnot(simulator.n_qubits - 1, 0)
        
        elif self.mixer_type == 'asymmetric':
            # Asymmetric mixer - different rotation for each qubit
            for qubit in range(simulator.n_qubits):
                angle = 2 * beta * (1 + 0.2 * np.sin(qubit + 1))
                simulator.rx(angle, qubit)
        
        else:
            raise ValueError(f"Unknown mixer type: {self.mixer_type}")
    
    def _get_initial_parameters(self, trial: int, graph_edges: List[Tuple[int, int]], n_qubits: int) -> np.ndarray:
        """Get initial parameters with enhanced strategies"""
        
        if not self.adaptive_initialization:
            # Simple random initialization
            return np.random.uniform(0, np.pi, 2 * self.n_layers)
        
        # Enhanced initialization strategies
        if trial == 0:
            # QAOA theory-inspired initialization
            gamma_params = [np.pi/4] * self.n_layers
            beta_params = [np.pi/8] * self.n_layers
            initial_params = []
            for i in range(self.n_layers):
                initial_params.extend([gamma_params[i], beta_params[i]])
            return np.array(initial_params)
        
        elif trial == 1:
            # Small perturbations around theory values
            gamma_params = [np.pi/4 + np.random.uniform(-0.2, 0.2) for _ in range(self.n_layers)]
            beta_params = [np.pi/8 + np.random.uniform(-0.2, 0.2) for _ in range(self.n_layers)]
            initial_params = []
            for i in range(self.n_layers):
                initial_params.extend([gamma_params[i], beta_params[i]])
            return np.array(initial_params)
        
        elif trial == 2:
            # Graph-structure aware initialization
            edge_density = len(graph_edges) / (n_qubits * (n_qubits - 1) / 2)
            
            if edge_density < 0.3:  # Sparse graph
                gamma_base = np.pi/3
                beta_base = np.pi/6
            elif edge_density > 0.7:  # Dense graph
                gamma_base = np.pi/6
                beta_base = np.pi/12
            else:  # Medium density
                gamma_base = np.pi/4
                beta_base = np.pi/8
            
            gammas = np.random.uniform(gamma_base * 0.7, gamma_base * 1.3, self.n_layers)
            betas = np.random.uniform(beta_base * 0.7, beta_base * 1.3, self.n_layers)
            
            initial_params = []
            for g, b in zip(gammas, betas):
                initial_params.extend([g, b])
            return np.array(initial_params)
        
        elif trial == 3:
            # Layered initialization (different parameters for different layers)
            initial_params = []
            for layer in range(self.n_layers):
                # Deeper layers get smaller parameters
                decay_factor = 0.8 ** layer
                gamma = (np.pi/4) * decay_factor * np.random.uniform(0.5, 1.5)
                beta = (np.pi/8) * decay_factor * np.random.uniform(0.5, 1.5)
                initial_params.extend([gamma, beta])
            return np.array(initial_params)
        
        else:
            # Random with bias toward smaller values (for warm start)
            if self.use_warm_start:
                # Smaller parameters for fine-tuning around warm start
                return np.random.uniform(0, np.pi/2, 2 * self.n_layers)
            else:
                # Broader random search
                return np.random.uniform(0, np.pi, 2 * self.n_layers)
    
    def _classical_greedy_maxcut(self, edges: List[Tuple[int, int]], n_qubits: int) -> List[int]:
        """Simple greedy algorithm for Max-Cut warm start"""
        # Start with random assignment
        assignment = [np.random.randint(0, 2) for _ in range(n_qubits)]
        
        # Greedily flip bits to improve cut
        improved = True
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for qubit in range(n_qubits):
                # Calculate current cut size
                current_cut = self._calculate_cut_size(''.join(map(str, assignment)), edges)
                
                # Try flipping this qubit
                assignment[qubit] = 1 - assignment[qubit]
                new_cut = self._calculate_cut_size(''.join(map(str, assignment)), edges)
                
                if new_cut > current_cut:
                    improved = True
                    print(f"Greedy improvement: qubit {qubit} flipped, cut: {current_cut} → {new_cut}")
                else:
                    assignment[qubit] = 1 - assignment[qubit]  # Flip back
        
        final_cut = self._calculate_cut_size(''.join(map(str, assignment)), edges)
        print(f"Classical greedy solution: {''.join(map(str, assignment))} (cut size: {final_cut})")
        
        return assignment
    
    def _calculate_cut_size(self, solution_string: str, edges: List[Tuple[int, int]]) -> int:
        """Calculate the number of edges cut by a given solution"""
        cut_size = 0
        
        for i, j in edges:
            # solution_string[i] gives the bit value for qubit i
            if i < len(solution_string) and j < len(solution_string):
                if solution_string[i] != solution_string[j]:
                    cut_size += 1
                
        return cut_size
    
    def _get_max_cut_size(self, graph_edges: List[Tuple[int, int]], n_qubits: int) -> int:
        """Calculate the maximum possible cut size by brute force"""
        max_cut = 0
        
        for i in range(2**n_qubits):
            solution = f"{i:0{n_qubits}b}"
            cut_size = self._calculate_cut_size(solution, graph_edges)
            max_cut = max(max_cut, cut_size)
            
        return max_cut
    
    def analyze_max_cut_solutions(self, graph_edges: List[Tuple[int, int]], n_qubits: int):
        """Analyze all possible solutions for Max-Cut problem"""
        print(f"\nAnalyzing all possible solutions for Max-Cut:")
        print(f"Graph edges: {graph_edges}")
        print(f"Solution format: bit string where bit i represents qubit i")
        print("-" * 60)
        
        max_cut = 0
        optimal_solutions = []
        
        for i in range(2**n_qubits):
            solution = f"{i:0{n_qubits}b}"
            cut_size = self._calculate_cut_size(solution, graph_edges)
            
            print(f"Solution {solution}: cut size = {cut_size}")
            
            if cut_size > max_cut:
                max_cut = cut_size
                optimal_solutions = [solution]
            elif cut_size == max_cut:
                optimal_solutions.append(solution)
        
        print(f"\nMaximum cut size: {max_cut}")
        print(f"Optimal solutions: {optimal_solutions}")
        
        # Enhanced analysis
        edge_density = len(graph_edges) / (n_qubits * (n_qubits - 1) / 2) if n_qubits > 1 else 0
        print(f"Graph density: {edge_density:.3f}")
        print(f"Expected QAOA difficulty: {'Easy' if edge_density < 0.3 else 'Hard' if edge_density > 0.7 else 'Medium'}")
        
        return max_cut, optimal_solutions
    
    def plot_results(self, result, graph_edges, n_qubits, plotter):
        """Plot QAOA-specific results with enhanced analysis"""
        # Plot QAOA-specific results
        qaoa_fig = plotter.plot_qaoa_results(
            result['solution_counts'], 
            graph_edges, 
            n_qubits
        )
        
        # Create simulator with optimal parameters to plot circuit and state
        from simulator import QuantumSimulator
        from .ansatz import QAOAAnsatz
        from .hamiltonian import Hamiltonian, PauliString
        
        # Recreate the ansatz to show circuit
        pauli_terms = [PauliString(['Z', 'Z'], -0.5, [i, j]) for i, j in graph_edges]
        hamiltonian = Hamiltonian(pauli_terms)
        
        simulator = QuantumSimulator(n_qubits=n_qubits)
        
        # Apply the enhanced circuit
        warm_start = self._classical_greedy_maxcut(graph_edges, n_qubits) if self.use_warm_start else None
        self._apply_qaoa_circuit(simulator, result['optimal_params'], graph_edges, warm_start)
        
        # Plot state and circuit (pass n_qubits to circuit plotting)
        prob_fig = plotter.plot_state_probabilities(simulator)
        circuit_fig = plotter.plot_quantum_circuit(simulator.gate_sequence, n_qubits)
        
        # Print enhanced analysis
        print(f"\n🔍 Enhanced QAOA Analysis:")
        print(f"Mixer type: {result.get('mixer_type', 'standard')}")
        print(f"Used warm start: {result.get('used_warm_start', False)}")  
        print(f"Approximation ratio: {result['approximation_ratio']:.3f}")
        print(f"Trivial solution probability: {result.get('trivial_probability', 0):.3f}")
        
        return {
            'qaoa_analysis': qaoa_fig,
            'probabilities': prob_fig,
            'circuit': circuit_fig
        }