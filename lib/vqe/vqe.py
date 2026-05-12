from vqe.hamiltonian import Hamiltonian
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator import QuantumSimulator
from classes.plotter import QuantumPlotter


class VariationalQuantumEigensolver:
    """VQE algorithm implementation with proper type handling"""
    
    def __init__(self, hamiltonian: Hamiltonian, ansatz, optimizer):
        self.hamiltonian = hamiltonian
        self.ansatz = ansatz
        self.optimizer = optimizer
        self.simulator = None
        self.history = {'energies': [], 'parameters': []}
        
    def cost_function(self, parameters: np.ndarray, shots: int = 1000) -> float:
        """Cost function: ⟨ψ(θ)|H|ψ(θ)⟩"""
        try:
            # Reset simulator
            self.simulator.reset()
            
            # Prepare ansatz state |ψ(θ)⟩
            self.ansatz.apply_circuit(self.simulator, parameters.tolist())
            
            # Measure expectation value ⟨ψ(θ)|H|ψ(θ)⟩
            energy = self.hamiltonian.expectation_value(self.simulator, shots)
            
            # Store history with proper types
            self.history['energies'].append(float(energy))
            self.history['parameters'].append(parameters.copy().tolist())
            
            return float(energy)  # Ensure Python float
            
        except Exception as e:
            print(f"Error in cost function: {e}")
            return float('inf')

    def plot_results(self, result, simulator, plotter):
        """Plot VQE results using QuantumPlotter"""
        # Plot convergence
        conv_fig = plotter.plot_vqe_convergence(result['history'])
        
        # Prepare final state and plot
        simulator.reset()
        self.ansatz.apply_circuit(simulator, result['optimal_params'])
        
        # Plot final state
        prob_fig = plotter.plot_state_probabilities(simulator)
        amp_fig = plotter.plot_state_amplitudes(simulator)
        
        # Plot circuit
        circuit_fig = plotter.plot_quantum_circuit(simulator.gate_sequence, simulator.n_qubits)
        
        return {
            'convergence': conv_fig,
            'probabilities': prob_fig,
            'amplitudes': amp_fig,
            'circuit': circuit_fig
        }

    def run(self, initial_params: np.ndarray, n_qubits: int, shots: int = 1000) -> dict:
        """Run VQE optimization with proper type conversion"""
        self.simulator = QuantumSimulator(n_qubits=n_qubits)
        self.history = {'energies': [], 'parameters': []}
        
        # Define cost function with shots
        def objective(params):
            return self.cost_function(params, shots)
        
        # Classical optimization loop
        from scipy.optimize import minimize
        result = minimize(
            objective,
            initial_params,
            method='COBYLA',  # Good for noisy optimization
            options={'maxiter': 100}
        )
        
        # Convert all results to proper Python types
        return {
            'energy': float(result.fun),
            'optimal_params': result.x.tolist(),  # Convert to list
            'converged': bool(result.success),
            'iterations': int(result.nfev),
            'history': {
                'energies': [float(e) for e in self.history['energies']],
                'parameters': [[float(p) for p in params] for params in self.history['parameters']]
            }
        }