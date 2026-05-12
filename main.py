"""
Main demonstration script for the 2-qubit Quantum Simulator
This script showcases various quantum operations, circuits, and visualizations.
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
import math
import time
from typing import List, Tuple

# Import our quantum simulator and plotter classes
# Updated imports to match your library structure
from simul import QuantumSimulator2Q
from lib.classes.plotter import QuantumPlotter
from lib.classes.gates import QuantumGates
from lib.classes.utils import QuantumUtils


def demo_basic_operations():
    """Demonstrate basic single-qubit operations"""
    print("=" * 60)
    print("DEMO 1: Basic Single-Qubit Operations")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    # Start with |00⟩ state
    print("\n1.1 Initial state |00⟩:")
    sim.print_state()
    
    # Apply Hadamard to first qubit
    print("\n1.2 After H(0) - creating superposition on qubit 0:")
    sim.h(0)
    sim.print_state()
    
    # Apply X gate to second qubit
    print("\n1.3 After X(1) - flipping qubit 1:")
    sim.x(1)
    sim.print_state()
    
    # Plot the state
    try:
        fig1 = plotter.plot_state_amplitudes(sim)
        fig2 = plotter.plot_state_probabilities(sim)
        plt.show()
    except AttributeError as e:
        print(f"Plotting methods not available: {e}")
        print("Current state probabilities:", sim.get_probabilities().tolist())
    
    return sim, plotter


def demo_bell_states():
    """Demonstrate creation of all four Bell states"""
    print("\n" + "=" * 60)
    print("DEMO 2: Bell States Creation")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    bell_states = [
        ("Φ+", [("H", 0), ("CNOT", (0, 1))]),
        ("Φ-", [("H", 0), ("Z", 0), ("CNOT", (0, 1))]),
        ("Ψ+", [("H", 0), ("X", 1), ("CNOT", (0, 1))]),
        ("Ψ-", [("H", 0), ("Z", 0), ("X", 1), ("CNOT", (0, 1))])
    ]
    
    for name, circuit in bell_states:
        print(f"\n2.{bell_states.index((name, circuit)) + 1} Bell State |{name}⟩:")
        sim.reset()
        
        # Apply gates
        for gate_info in circuit:
            if gate_info[0] == "H":
                sim.h(gate_info[1])
            elif gate_info[0] == "X":
                sim.x(gate_info[1])
            elif gate_info[0] == "Z":
                sim.z(gate_info[1])
            elif gate_info[0] == "CNOT":
                sim.cnot(gate_info[1][0], gate_info[1][1])
        
        sim.print_state()
        print(f"Concurrence (entanglement measure): {sim.get_concurrence():.4f}")
        
        # Try to plot circuit diagram if method exists
        try:
            fig = plotter.plot_quantum_circuit(circuit, figsize=(10, 3))
            plt.title(f"Bell State |{name}⟩ Circuit")
            plt.show()
        except AttributeError:
            print(f"Circuit diagram for |{name}⟩: {' → '.join([str(gate) for gate in circuit])}")
        
        # Try to plot entanglement measure if method exists
        try:
            fig_ent = plotter.plot_entanglement_measure(sim)
            plt.show()
        except AttributeError:
            pass


def demo_rotation_gates():
    """Demonstrate rotation gates and their effects"""
    print("\n" + "=" * 60)
    print("DEMO 3: Rotation Gates")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    # Test different rotation angles
    angles = [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi]
    
    print("\n3.1 RY rotation on qubit 0:")
    states_evolution = []
    labels = []
    
    for i, angle in enumerate(angles):
        sim.reset()
        sim.ry(angle, 0)
        states_evolution.append(sim.get_state().clone())
        labels.append(f'RY({angle:.2f})')
        
        print(f"  Angle {angle:.2f} ({angle*180/math.pi:.0f}°):")
        sim.print_state()
    
    # Try to plot state evolution if method exists
    try:
        fig = plotter.plot_state_evolution(states_evolution, labels)
        plt.show()
    except AttributeError:
        print("State evolution plotting not available")
    
    # Show Bloch sphere for different rotations if method exists
    try:
        for i, angle in enumerate([0, math.pi/4, math.pi/2]):
            sim.reset()
            sim.ry(angle, 0)
            fig = plotter.plot_bloch_sphere_projection(sim, qubit=0)
            plt.title(f'Bloch Sphere - RY({angle:.2f}) on Qubit 0')
            plt.show()
    except AttributeError:
        print("Bloch sphere plotting not available")


def demo_measurement_statistics():
    """Demonstrate measurement statistics over multiple runs"""
    print("\n" + "=" * 60)
    print("DEMO 4: Measurement Statistics")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    # Create a superposition state
    sim.reset()
    sim.h(0)  # Equal superposition on qubit 0
    sim.h(1)  # Equal superposition on qubit 1
    
    print("\n4.1 Initial state (both qubits in superposition):")
    sim.print_state()
    print("Theoretical probabilities:", sim.get_probabilities().tolist())
    
    # Use the built-in multiple measurement method
    num_shots = 1000
    print(f"\n4.2 Performing {num_shots} measurements...")
    
    # Reset state and use measure_multiple to avoid state collapse
    sim.reset()
    sim.h(0)
    sim.h(1)
    results = sim.measure_multiple(shots=num_shots)
    
    # Convert binary string results to integers for counting
    int_results = [int(result, 2) for result in results]
    
    # Try to plot histogram if method exists
    try:
        fig = plotter.plot_measurement_histogram(int_results)
        plt.show()
    except AttributeError:
        print("Histogram plotting not available")
    
    # Calculate and display statistics
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for result in int_results:
        counts[result] += 1
    
    print("\n4.3 Measurement Statistics:")
    state_names = ['|00⟩', '|01⟩', '|10⟩', '|11⟩']
    for i, name in enumerate(state_names):
        observed_prob = counts[i] / num_shots
        theoretical_prob = 0.25  # Equal superposition
        print(f"  {name}: {counts[i]:4d} ({observed_prob:.3f}) - Theoretical: {theoretical_prob:.3f}")


def demo_quantum_algorithms():
    """Demonstrate simple quantum algorithms"""
    print("\n" + "=" * 60)
    print("DEMO 5: Quantum Algorithms")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    # 5.1 Quantum Teleportation (simplified version)
    print("\n5.1 Quantum Teleportation Protocol (simplified):")
    
    # Step 1: Create entangled pair (Bell state)
    sim.reset()
    sim.h(0)
    sim.cnot(0, 1)
    print("  Step 1 - Created entangled pair:")
    sim.print_state()
    print(f"  Entanglement (concurrence): {sim.get_concurrence():.4f}")
    
    # Step 2: Apply some operation to "teleport"
    sim.z(0)  # Apply Z gate to first qubit
    print("  Step 2 - After applying Z to qubit 0:")
    sim.print_state()
    
    # Step 3: Measure and correct (simplified)
    sim.cnot(0, 1)
    sim.h(0)
    print("  Step 3 - After correction operations:")
    sim.print_state()
    
    # 5.2 Grover's algorithm inspired circuit
    print("\n5.2 Grover-inspired quantum search:")
    
    sim.reset()
    # Initialize in uniform superposition
    sim.h(0)
    sim.h(1)
    print("  Initial superposition:")
    sim.print_state()
    
    # Oracle (mark state |11⟩)
    sim.cz(0, 1)  # Phase flip |11⟩
    print("  After oracle (marking |11⟩):")
    sim.print_state()
    
    # Diffusion operator (simplified)
    sim.h(0)
    sim.h(1)
    sim.x(0)
    sim.x(1)
    sim.cz(0, 1)
    sim.x(0)
    sim.x(1)
    sim.h(0)
    sim.h(1)
    print("  After diffusion operator:")
    sim.print_state()
    
    # Try to plot final probabilities if method exists
    try:
        fig = plotter.plot_state_probabilities(sim)
        plt.title("Grover-inspired Algorithm Result")
        plt.show()
    except AttributeError:
        print("  Final probabilities:", sim.get_probabilities().tolist())


def demo_expectation_values():
    """Demonstrate expectation value calculations"""
    print("\n" + "=" * 60)
    print("DEMO 6: Expectation Values")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    gates = QuantumGates(device=sim.device)
    
    # Create a test state
    sim.reset()
    sim.ry(math.pi/3, 0)  # Rotate qubit 0
    sim.rx(math.pi/4, 1)  # Rotate qubit 1
    
    print("\n6.1 Test state:")
    sim.print_state()
    
    # Calculate various expectation values
    print("\n6.2 Expectation values:")
    
    # Single qubit observables
    I = torch.eye(2, dtype=torch.complex64, device=sim.device)
    Z_I = torch.kron(gates.Z, I)  # Z on qubit 0
    I_Z = torch.kron(I, gates.Z)  # Z on qubit 1
    X_I = torch.kron(gates.X, I)  # X on qubit 0
    I_X = torch.kron(I, gates.X)  # X on qubit 1
    
    # Two-qubit observables
    Z_Z = torch.kron(gates.Z, gates.Z)  # Z⊗Z
    X_X = torch.kron(gates.X, gates.X)  # X⊗X
    
    observables = [
        ("⟨Z₀⊗I₁⟩", Z_I),
        ("⟨I₀⊗Z₁⟩", I_Z),
        ("⟨X₀⊗I₁⟩", X_I),
        ("⟨I₀⊗X₁⟩", I_X),
        ("⟨Z₀⊗Z₁⟩", Z_Z),
        ("⟨X₀⊗X₁⟩", X_X)
    ]
    
    for name, observable in observables:
        expectation = sim.expectation_value(observable)
        print(f"  {name} = {expectation:.4f}")


def demo_complex_circuits():
    """Demonstrate complex quantum circuits"""
    print("\n" + "=" * 60)
    print("DEMO 7: Complex Quantum Circuits")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    # Circuit 1: Quantum Fourier Transform (2-qubit version)
    print("\n7.1 2-Qubit Quantum Fourier Transform:")
    
    sim.reset()
    sim.x(0)  # Start with |01⟩ state
    print("  Input state |01⟩:")
    sim.print_state()
    
    # QFT circuit
    sim.h(0)
    sim.rz(math.pi/2, 0)  # Controlled phase (simplified)
    sim.h(1)
    sim.swap()  # Swap qubits (bit reversal)
    
    print("  After 2-qubit QFT:")
    sim.print_state()
    
    # Show circuit sequence
    print("  Gate sequence:", sim.get_gate_sequence())
    
    # Try to plot circuit if method exists
    try:
        qft_circuit = [
            ("H", 0),
            ("RZ", 0, math.pi/2),
            ("H", 1),
            ("SWAP", (0, 1))
        ]
        fig = plotter.plot_quantum_circuit(qft_circuit, figsize=(12, 4))
        plt.title("2-Qubit Quantum Fourier Transform")
        plt.show()
    except AttributeError:
        print("  Circuit plotting not available")
    
    # Circuit 2: Parameterized quantum circuit
    print("\n7.2 Parameterized Quantum Circuit:")
    
    params = [math.pi/4, math.pi/3, math.pi/6, math.pi/2]
    param_names = ['θ₁', 'θ₂', 'θ₃', 'θ₄']
    
    sim.reset()
    sim.ry(params[0], 0)
    sim.ry(params[1], 1)
    sim.cnot(0, 1)
    sim.rz(params[2], 0)
    sim.rz(params[3], 1)
    sim.cnot(1, 0)
    sim.ry(-params[0]/2, 0)
    sim.ry(-params[1]/2, 1)
    
    print(f"  Parameters: {[f'{name}={val:.3f}' for name, val in zip(param_names, params)]}")
    sim.print_state()
    print(f"  Entanglement measure: {sim.get_concurrence():.4f}")
    
    # Try to plot final state if method exists
    try:
        fig = plotter.plot_state_amplitudes(sim, figsize=(12, 6))
        plt.suptitle("Parameterized Quantum Circuit Result")
        plt.show()
    except AttributeError:
        print("  State amplitude plotting not available")


def demo_state_operations():
    """Demonstrate state manipulation and comparison operations"""
    print("\n" + "=" * 60)
    print("DEMO 8: State Operations")
    print("=" * 60)
    
    sim1 = QuantumSimulator2Q()
    sim2 = QuantumSimulator2Q()
    
    # Create two different states
    sim1.reset()
    sim1.h(0)
    sim1.cnot(0, 1)  # Bell state
    
    sim2.reset()
    sim2.h(0)
    sim2.h(1)  # Product superposition state
    
    print("\n8.1 State 1 (Bell state):")
    sim1.print_state()
    print(f"  Concurrence: {sim1.get_concurrence():.4f}")
    
    print("\n8.2 State 2 (Product superposition):")
    sim2.print_state()
    print(f"  Concurrence: {sim2.get_concurrence():.4f}")
    
    # Calculate fidelity between states
    fidelity = sim1.get_fidelity_with(sim2.get_state())
    print(f"\n8.3 Fidelity between states: {fidelity:.4f}")
    
    # Test state copying
    sim3 = sim1.copy()
    print(f"\n8.4 Fidelity with copied state: {sim1.get_fidelity_with(sim3.get_state()):.4f}")
    
    # Demonstrate custom state setting
    print("\n8.5 Setting custom normalized state:")
    custom_state = torch.tensor([0.5, 0.5, 0.5, 0.5], dtype=torch.complex64)
    sim3.set_state(custom_state)
    sim3.print_state()
    print(f"  Probabilities sum: {sim3.get_probabilities().sum():.6f}")


def interactive_demo():
    """Interactive demonstration allowing user to build circuits"""
    print("\n" + "=" * 60)
    print("DEMO 9: Interactive Circuit Builder")
    print("=" * 60)
    
    sim = QuantumSimulator2Q()
    plotter = QuantumPlotter()
    
    print("\nInteractive Quantum Circuit Builder")
    print("Available gates: H, X, Y, Z, S, T, RX, RY, RZ, CNOT, CZ, SWAP")
    print("Commands:")
    print("  'state' - show current state")
    print("  'probs' - show probabilities")
    print("  'reset' - reset to |00⟩")
    print("  'measure [qubit]' - measure qubit(s)")
    print("  'concur' - show entanglement measure")
    print("  'gates' - show applied gate sequence")
    print("  'quit' - exit")
    print("\nGate format examples:")
    print("  'H 0' - Hadamard on qubit 0")
    print("  'RY 1 1.57' - RY rotation on qubit 1 with angle 1.57")
    print("  'CNOT 0 1' - CNOT with control=0, target=1")
    
    circuit_history = []
    
    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            
            if not command:
                continue
                
            cmd = command[0].upper()
            
            if cmd == 'QUIT':
                break
            elif cmd == 'RESET':
                sim.reset()
                circuit_history = []
                print("Circuit reset to |00⟩")
            elif cmd == 'STATE':
                sim.print_state()
            elif cmd == 'PROBS':
                probs = sim.get_probabilities()
                state_names = ['|00⟩', '|01⟩', '|10⟩', '|11⟩']
                for i, name in enumerate(state_names):
                    print(f"  {name}: {probs[i]:.6f}")
            elif cmd == 'CONCUR':
                print(f"Concurrence (entanglement): {sim.get_concurrence():.6f}")
            elif cmd == 'GATES':
                if sim.get_gate_sequence():
                    print("Applied gates:", sim.get_gate_sequence())
                else:
                    print("No gates applied yet")
            elif cmd == 'MEASURE':
                if len(command) > 1:
                    qubit = int(command[1])
                    result = sim.measure(qubit)
                    print(f"Measured qubit {qubit}: {result}")
                else:
                    result = sim.measure()
                    print(f"Measured both qubits: {result:02b}")
            elif cmd in ['H', 'X', 'Y', 'Z', 'S', 'T']:
                qubit = int(command[1])
                getattr(sim, cmd.lower())(qubit)
                circuit_history.append((cmd, qubit))
                print(f"Applied {cmd} to qubit {qubit}")
            elif cmd in ['RX', 'RY', 'RZ']:
                qubit = int(command[1])
                angle = float(command[2])
                getattr(sim, cmd.lower())(angle, qubit)
                circuit_history.append((cmd, qubit, angle))
                print(f"Applied {cmd}({angle:.3f}) to qubit {qubit}")
            elif cmd == 'CNOT':
                control, target = int(command[1]), int(command[2])
                sim.cnot(control, target)
                circuit_history.append(("CNOT", (control, target)))
                print(f"Applied CNOT with control={control}, target={target}")
            elif cmd == 'CZ':
                q1, q2 = int(command[1]), int(command[2])
                sim.cz(q1, q2)
                circuit_history.append(("CZ", (q1, q2)))
                print(f"Applied CZ between qubits {q1} and {q2}")
            elif cmd == 'SWAP':
                sim.swap()
                circuit_history.append(("SWAP", (0, 1)))
                print("Applied SWAP between qubits 0 and 1")
            else:
                print("Unknown command. Try 'H 0', 'CNOT 0 1', 'state', 'probs', etc.")
                
        except (IndexError, ValueError) as e:
            print(f"Invalid command format: {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    
    print("Interactive demo ended.")


def run_all_demos():
    """Run all demonstrations"""
    print("🌊 2-QUBIT QUANTUM SIMULATOR DEMONSTRATION 🌊")
    print("This comprehensive demo showcases quantum computing concepts")
    print("using a custom PyTorch-based 2-qubit quantum simulator.\n")
    
    # Check device availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    try:
        # Run all demos in sequence
        demo_basic_operations()
        input("\nPress Enter to continue to Bell States demo...")
        
        demo_bell_states()
        input("\nPress Enter to continue to Rotation Gates demo...")
        
        demo_rotation_gates()
        input("\nPress Enter to continue to Measurement Statistics demo...")
        
        demo_measurement_statistics()
        input("\nPress Enter to continue to Quantum Algorithms demo...")
        
        demo_quantum_algorithms()
        input("\nPress Enter to continue to Expectation Values demo...")
        
        demo_expectation_values()
        input("\nPress Enter to continue to Complex Circuits demo...")
        
        demo_complex_circuits()
        input("\nPress Enter to continue to State Operations demo...")
        
        demo_state_operations()
        input("\nPress Enter to start Interactive demo (or Ctrl+C to skip)...")
        
        interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except ImportError as e:
        print(f"\nImport error: {e}")
        print("Please make sure all required files are in the correct locations:")
        print("- simulator.py")
        print("- classes/plotter.py")
        print("- classes/gates.py") 
        print("- classes/utils.py")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check that all dependencies are installed and files are accessible.")


if __name__ == "__main__":
    # Check if matplotlib backend supports interactive plots
    import matplotlib
    print(f"Using matplotlib backend: {matplotlib.get_backend()}")
    
    # Set random seed for reproducible results
    torch.manual_seed(42)
    np.random.seed(42)
    
    # Run the complete demonstration
    run_all_demos()
