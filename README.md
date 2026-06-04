# 🌌 Quantum Circuit Simulator V2

A comprehensive, production-ready quantum circuit simulator built with PyTorch. Simulate quantum algorithms, visualize quantum states, and explore variational quantum computing—all on your classical computer.

<div align="center">

![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-1.9+-red.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

**[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Examples](#-examples) • [Documentation](#-documentation)**

</div>

---

## 🚀 Features

- ⚡ **N-Qubit Simulation** - Scalable quantum state vectors with memory-optimized operations
- 🎯 **Complete Gate Library** - Pauli, Hadamard, rotations, and multi-qubit gates
- 🧮 **Advanced Algorithms** - VQE, QAOA, QFT, and Quantum Phase Estimation
- 📊 **Rich Visualization** - State amplitudes, Bloch spheres, circuit diagrams, and more
- 🔧 **API Server** - Built-in FastAPI interface for remote access
- 📚 **Educational** - Extensive examples, exercises, and documentation
- ⚙️ **Performance Optimized** - Efficient state vector manipulation and measurements

---

## 📋 What's Inside

| Component | Description |
|-----------|-------------|
| **Simulator** | Core quantum state vector engine with 20+ quantum gates |
| **Variational Algorithms** | VQE and QAOA with customizable ansätze and Hamiltonians |
| **Quantum Transforms** | Quantum Fourier Transform (QFT) and Phase Estimation (QPE) |
| **Visualization** | Comprehensive plotting tools for states and circuits |
| **REST API** | FastAPI server for programmatic access |
| **Examples** | 50+ runnable examples covering basics to advanced topics |

---

## 💻 Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

```bash
# Clone the repository
git clone https://github.com/bukac82/Quantum_Simulator_V2.git
cd Quantum_Simulator_V2

# Install dependencies
pip install -r requirements.txt
# or with conda
conda env create -f environment.yml
conda activate quantum-sim
```

### Verify Installation

```python
from simulator import QuantumSimulator
sim = QuantumSimulator(n_qubits=2)
sim.print_state()  # Should print |00⟩
print("✓ Installation successful!")
```

---

## ⚡ Quick Start

### 1. Your First Quantum Circuit

```python
from simulator import QuantumSimulator
from classes.plotter import QuantumPlotter

# Create a 2-qubit simulator
sim = QuantumSimulator(n_qubits=2)
plotter = QuantumPlotter()

# Build a simple circuit
sim.h(0)           # Hadamard on qubit 0 → superposition
sim.cnot(0, 1)     # CNOT: entangle qubits 0 and 1

# Inspect the quantum state
sim.print_state()           # View state in bra-ket notation
sim.print_probabilities()   # View measurement probabilities

# Measure the system
results = sim.measure(shots=1000)
print(f"Measurement results: {results[:10]}")
```

**Expected Output:**
```
State: 0.7071|00⟩ + 0.7071|11⟩    # Bell state
Probabilities: |00⟩: 0.500, |11⟩: 0.500
```

### 2. Create Quantum States

```python
# Bell state (maximally entangled)
sim.reset()
sim.h(0)
sim.cnot(0, 1)
print("Bell state created: (|00⟩ + |11⟩)/√2")

# GHZ state (N-qubit entanglement)
sim_3 = QuantumSimulator(n_qubits=3)
sim_3.create_ghz_state()
print("GHZ state: (|000⟩ + |111⟩)/√2")

# Superposition state
sim_4 = QuantumSimulator(n_qubits=4)
for i in range(4):
    sim_4.h(i)
print("Equal superposition over 16 states")
```

### 3. Measure & Visualize

```python
# Visualize state amplitudes
amp_fig = plotter.plot_state_amplitudes(sim)
prob_fig = plotter.plot_state_probabilities(sim)

# Measurement histogram
results = sim.measure(shots=1000)
hist_fig = plotter.plot_measurement_histogram(results)

# Save plots
plotter.save_plot(amp_fig, 'state_amplitudes.png', dpi=300)
```

---

## 🎓 Examples

### Example 1: Bell States & Entanglement

```python
from simulator import QuantumSimulator

def create_bell_states():
    """Create and analyze all four Bell states"""
    bell_states = {
        'Φ⁺': lambda sim: [sim.h(0), sim.cnot(0, 1)],
        'Φ⁻': lambda sim: [sim.h(0), sim.z(0), sim.cnot(0, 1)],
        'Ψ⁺': lambda sim: [sim.h(0), sim.x(1), sim.cnot(0, 1)],
        'Ψ⁻': lambda sim: [sim.h(0), sim.x(1), sim.z(0), sim.cnot(0, 1)]
    }
    
    for name, prep in bell_states.items():
        sim = QuantumSimulator(n_qubits=2)
        prep(sim)
        print(f"\n{name} Bell State:")
        sim.print_state()
        
create_bell_states()
```

### Example 2: Variational Quantum Eigensolver (VQE)

Find the ground state energy of a quantum system:

```python
from vqe.vqe import VariationalQuantumEigensolver
from vqe.hamiltonian import Hamiltonian, PauliString
from vqe.ansatz import HardwareEfficientAnsatz
import numpy as np

# Define Hamiltonian: H = 0.5*Z₀ + 0.5*Z₁ - 0.25*Z₀Z₁
hamiltonian = Hamiltonian([
    PauliString(['Z'], 0.5, [0]),
    PauliString(['Z'], 0.5, [1]),
    PauliString(['Z', 'Z'], -0.25, [0, 1])
])

# Create ansatz with 2 layers
ansatz = HardwareEfficientAnsatz(n_qubits=2, depth=2)

# Run VQE
vqe = VariationalQuantumEigensolver(hamiltonian, ansatz, None)
initial_params = np.random.uniform(0, 2*np.pi, ansatz.n_parameters)
result = vqe.run(initial_params, n_qubits=2)

print(f"Ground state energy: {result['energy']:.6f}")
print(f"Converged: {result['converged']}")
```

### Example 3: Quantum Approximate Optimization (QAOA)

Solve Max-Cut problems:

```python
from vqe.qaoa import QuantumApproximateOptimization

# Define graph for Max-Cut problem
graph_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]  # 4-cycle
n_qubits = 4

# Create QAOA solver
qaoa = QuantumApproximateOptimization(
    n_layers=2,
    mixer_type='standard',
    use_warm_start=True,
    adaptive_initialization=True
)

# Solve
result = qaoa.solve_max_cut(graph_edges, n_qubits, shots=1000)

print(f"Best cut size: {result['best_cut_size']}")
print(f"Approximation ratio: {result['approximation_ratio']:.3f}")
print(f"Best solution: {result['best_cut_solution']}")
```

### Example 4: Grover's Search Algorithm

```python
def grovers_algorithm(target_item: int, n_qubits: int):
    """Find target_item in unsorted database using Grover's algorithm"""
    from simulator import QuantumSimulator
    import numpy as np
    
    sim = QuantumSimulator(n_qubits=n_qubits)
    N = 2**n_qubits
    iterations = int(np.pi * np.sqrt(N) / 4)
    
    # Initialize superposition
    for qubit in range(n_qubits):
        sim.h(qubit)
    
    # Grover iterations
    for _ in range(iterations):
        # Oracle + Diffusion operator
        # (Implementation details omitted for brevity)
        pass
    
    # Measure
    results = sim.measure(shots=1000)
    success_rate = sum(1 for r in results if int(r, 2) == target_item) / 1000
    
    return success_rate

# Search for item 7 in 3-qubit (8-item) database
success = grovers_algorithm(target_item=7, n_qubits=3)
print(f"Success rate: {success:.1%}")
```

---

## 📊 Simulator vs Real Quantum Computers

| Aspect | This Simulator | Real Quantum Computer |
|--------|-------|-------------------|
| **State Access** | ��� Full state vector | ❌ No direct access |
| **Gate Fidelity** | ✅ 100% perfect | ❌ 99.9% single-qubit |
| **Coherence Time** | ✅ Infinite | ❌ ~100 μs |
| **Scalability** | ⚠️ ~20-25 qubits max | 🚀 Potential thousands |
| **Cost** | 💰 Free | 💰💰💰 Very expensive |
| **Noise** | ❌ None | ✅ Realistic errors |
| **Use Case** | 📚 Learning, R&D | 🔬 Production research |

**Best for this simulator:**
- Algorithm development
- Education & learning
- Proof of concepts (< 20 qubits)
- Debugging and analysis

---

## 🛠️ API Reference

### QuantumSimulator

#### Initialization
```python
sim = QuantumSimulator(n_qubits=4, device='cpu')
```

#### State Management
```python
sim.reset()                    # Reset to |0000⟩
state = sim.get_state()       # Get current state vector
sim.set_state(custom_state)   # Set custom state
probs = sim.get_probabilities()  # Get |ψᵢ|²
```

#### Single-Qubit Gates
```python
sim.h(0)              # Hadamard
sim.x(0), sim.y(0), sim.z(0)  # Pauli gates
sim.s(0), sim.t(0)    # Phase gates
sim.rx(angle, 0)      # X-rotation
sim.ry(angle, 0)      # Y-rotation
sim.rz(angle, 0)      # Z-rotation
```

#### Multi-Qubit Gates
```python
sim.cnot(0, 1)        # Controlled-NOT
sim.cz(0, 1)          # Controlled-Z
```

#### Measurement
```python
results = sim.measure(shots=1000)           # Full measurement
single = sim.measure_single_qubit(0, shots=1000)  # Single qubit
```

#### Utilities
```python
sim.print_state()                    # Display state
sim.print_probabilities()            # Display probabilities
depth = sim.get_circuit_depth()      # Gate count
usage = sim.get_memory_usage()       # Memory stats
```

### QuantumPlotter

```python
from classes.plotter import QuantumPlotter

plotter = QuantumPlotter()

# Visualizations
plotter.plot_state_amplitudes(sim)
plotter.plot_state_probabilities(sim)
plotter.plot_bloch_sphere_projection(sim, qubit=0)
plotter.plot_measurement_histogram(results)
plotter.plot_quantum_circuit(gate_sequence, n_qubits)

# Save/Show
plotter.save_plot(fig, 'output.png', dpi=300)
plotter.show_all_plots()
```

---

## ⚙️ Performance & Scaling

### Memory Requirements

| Qubits | State Size | Memory | Feasibility |
|--------|-----------|--------|-------------|
| 10 | 1,024 | 8 KB | ✅ Instant |
| 15 | 32,768 | 256 KB | ✅ Very fast |
| 20 | 1,048,576 | 8 MB | ✅ Good |
| 25 | 33.5M | 256 MB | ⚠️ Noticeable |
| 30 | 1.07B | 8 GB | ❌ Requires HPC |

### Optimization Tips

```python
# 1. Batch measurements
results = sim.measure(shots=10000)  # Better than individual calls

# 2. Reuse simulator instances
sim.reset()  # Faster than creating new

# 3. Monitor memory
if sim.get_memory_usage()['state_vector_mb'] > 1000:
    print("Warning: High memory usage")

# 4. Use CPU for small systems
sim = QuantumSimulator(n_qubits=10, device='cpu')
```

---

## 🚀 Running the API Server

Start the FastAPI server for remote access:

```bash
# Install uvicorn
pip install uvicorn

# Run server (port 5050)
uvicorn lib.api:app --host 127.0.0.1 --port 5050 --reload

# API will be available at http://localhost:5050
# Swagger docs at http://localhost:5050/docs
```

---

## 📚 Documentation

For comprehensive documentation, see:

- **[Quantum Gates](docs/GATES.md)** - Complete gate reference
- **[Algorithms](docs/ALGORITHMS.md)** - VQE, QAOA, QFT, QPE
- **[Visualization](docs/VISUALIZATION.md)** - Plotting guide
- **[API Docs](docs/API.md)** - Full API reference
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
pytest tests/ -v  # Verbose output
pytest tests/ --cov=  # With coverage
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-thing`)
3. **Commit** changes (`git commit -am 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-thing`)
5. **Create** a Pull Request

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/Quantum_Simulator_V2.git
cd Quantum_Simulator_V2
pip install -e ".[dev]"
```

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- PyTorch for the computational backbone
- Quantum computing community for inspiration
- Contributors and users providing feedback

---

## 📞 Support & Feedback

- 📖 **Documentation**: Check the docs/ folder
- 🐛 **Issues**: [Report bugs](https://github.com/bukac82/Quantum_Simulator_V2/issues)
- 💡 **Discussions**: [Start a discussion](https://github.com/bukac82/Quantum_Simulator_V2/discussions)
- 📧 **Contact**: Open an issue for questions

---

## 🗺️ Roadmap

- [ ] GPU acceleration support
- [ ] Noise models for realistic simulation
- [ ] Additional variational ansätze
- [ ] Advanced error correction codes
- [ ] Web-based interactive simulator
- [ ] Integration with IBM Qiskit
- [ ] Performance benchmarks suite

---

## 📈 Project Stats

![Stars](https://img.shields.io/github/stars/bukac82/Quantum_Simulator_V2?style=social)
![Forks](https://img.shields.io/github/forks/bukac82/Quantum_Simulator_V2?style=social)
![Issues](https://img.shields.io/github/issues/bukac82/Quantum_Simulator_V2)

---

<div align="center">

**Made with ❤️ by the Quantum Computing Community**

[⬆ back to top](#-quantum-circuit-simulator-v2)

</div>
