import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import torch


class QuantumPlotter:
    """A plotting class for visualizing quantum states and circuits"""
    
    def __init__(self):
        self.plt = plt
        self.patches = patches
        self.FancyBboxPatch = FancyBboxPatch
    
    def _tensor_to_numpy(self, tensor):
        """Convert tensor to numpy array, handling CUDA tensors"""
        if isinstance(tensor, torch.Tensor):
            return tensor.cpu().detach().numpy()
        elif isinstance(tensor, (list, tuple)):
            return np.array([self._tensor_to_numpy(t) if isinstance(t, torch.Tensor) else t for t in tensor])
        else:
            return np.array(tensor)
    
    def plot_state_amplitudes(self, simulator, figsize=(12, 6)):
        """Plot the real and imaginary parts of state amplitudes"""
        state = simulator.get_state()
        n_qubits = simulator.n_qubits
        n_states = 2**n_qubits
        state_labels = [f'|{i:0{n_qubits}b}⟩' for i in range(n_states)]
        
        # Convert to numpy and extract real/imaginary parts
        state_np = self._tensor_to_numpy(state)
        real_parts = state_np.real
        imag_parts = state_np.imag
        
        fig, (ax1, ax2) = self.plt.subplots(1, 2, figsize=figsize)
        
        # Real parts
        bars1 = ax1.bar(range(n_states), real_parts, color='blue', alpha=0.7)
        ax1.set_title('Real Parts of Amplitudes')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlabel('Basis State')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Set x-axis labels
        if n_states <= 16:
            ax1.set_xticks(range(n_states))
            ax1.set_xticklabels(state_labels, rotation=45 if n_states > 8 else 0)
        else:
            # For large systems, show fewer labels
            step = max(1, n_states // 16)
            ticks = range(0, n_states, step)
            ax1.set_xticks(ticks)
            ax1.set_xticklabels([state_labels[i] for i in ticks], rotation=45)
        
        # Imaginary parts
        bars2 = ax2.bar(range(n_states), imag_parts, color='red', alpha=0.7)
        ax2.set_title('Imaginary Parts of Amplitudes')
        ax2.set_ylabel('Amplitude')
        ax2.set_xlabel('Basis State')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Set x-axis labels
        if n_states <= 16:
            ax2.set_xticks(range(n_states))
            ax2.set_xticklabels(state_labels, rotation=45 if n_states > 8 else 0)
        else:
            ax2.set_xticks(ticks)
            ax2.set_xticklabels([state_labels[i] for i in ticks], rotation=45)
        
        # Add value labels on bars (only for significant values)
        for i, (bar, val) in enumerate(zip(bars1, real_parts)):
            if abs(val) > 1e-3:  # Only show significant values
                ax1.text(bar.get_x() + bar.get_width()/2, val + 0.01 if val >= 0 else val - 0.03,
                        f'{val:.3f}', ha='center', va='bottom' if val >= 0 else 'top', fontsize=8)
        
        for i, (bar, val) in enumerate(zip(bars2, imag_parts)):
            if abs(val) > 1e-3:
                ax2.text(bar.get_x() + bar.get_width()/2, val + 0.01 if val >= 0 else val - 0.03,
                        f'{val:.3f}', ha='center', va='bottom' if val >= 0 else 'top', fontsize=8)
        
        self.plt.tight_layout()
        return fig
    
    def plot_state_probabilities(self, simulator, figsize=(10, 6)):
        """Plot measurement probabilities"""
        probabilities = simulator.get_probabilities()
        n_qubits = simulator.n_qubits
        n_states = 2**n_qubits
        state_labels = [f'|{i:0{n_qubits}b}⟩' for i in range(n_states)]
        
        # Convert probabilities to numpy
        prob_np = self._tensor_to_numpy(probabilities)
        
        fig, ax = self.plt.subplots(figsize=figsize)
        
        bars = ax.bar(range(n_states), prob_np, color='green', alpha=0.7)
        ax.set_title(f'Measurement Probabilities ({n_qubits} qubits)')
        ax.set_ylabel('Probability')
        ax.set_xlabel('Basis State')
        ax.set_ylim(0, max(1, np.max(prob_np) * 1.1))
        ax.grid(True, alpha=0.3)
        
        # Set x-axis labels
        if n_states <= 16:
            ax.set_xticks(range(n_states))
            ax.set_xticklabels(state_labels, rotation=45 if n_states > 8 else 0)
        else:
            # For large systems, show fewer labels
            step = max(1, n_states // 16)
            ticks = range(0, n_states, step)
            ax.set_xticks(ticks)
            ax.set_xticklabels([state_labels[i] for i in ticks], rotation=45)
        
        # Add probability labels on bars (only for significant probabilities)
        for i, (bar, prob) in enumerate(zip(bars, prob_np)):
            if prob > 1e-3:  # Only show significant probabilities
                ax.text(bar.get_x() + bar.get_width()/2, prob + max(prob_np)*0.01,
                       f'{prob:.3f}', ha='center', va='bottom', fontsize=8)
        
        self.plt.tight_layout()
        return fig
    
    def plot_bloch_sphere_projection(self, simulator, qubit=0, figsize=(5, 5)):
        """Plot Bloch sphere representation for a single qubit (marginal state)"""
        # Calculate single qubit density matrix
        state = simulator.get_state()
        state_np = self._tensor_to_numpy(state)
        n_qubits = simulator.n_qubits
        
        if qubit >= n_qubits:
            raise ValueError(f"Qubit {qubit} out of range for {n_qubits}-qubit system")
        
        # Calculate reduced density matrix for the specified qubit
        n_states = 2**n_qubits
        rho = np.zeros((2, 2), dtype=complex)
        
        for i in range(n_states):
            for j in range(n_states):
                # Check if states i and j differ only in the specified qubit
                bit_i = (i >> (n_qubits - qubit - 1)) & 1
                bit_j = (j >> (n_qubits - qubit - 1)) & 1
                
                # Remove the specified qubit from both states
                other_bits_i = (i & ~(1 << (n_qubits - qubit - 1)))
                other_bits_j = (j & ~(1 << (n_qubits - qubit - 1)))
                
                if other_bits_i == other_bits_j:
                    rho[bit_i, bit_j] += state_np[i] * np.conj(state_np[j])
        
        # Calculate Bloch vector components
        pauli_x = np.array([[0, 1], [1, 0]])
        pauli_y = np.array([[0, -1j], [1j, 0]])
        pauli_z = np.array([[1, 0], [0, -1]])
        
        x = np.real(np.trace(pauli_x @ rho))
        y = np.real(np.trace(pauli_y @ rho))
        z = np.real(np.trace(pauli_z @ rho))
        
        # Create 3D plot
        fig = self.plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        # Remove background panes and grid
        ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        ax.grid(False)
        ax.set_axis_off()

        # Draw Bloch sphere surface
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 40)
        sphere_x = np.outer(np.cos(u), np.sin(v))
        sphere_y = np.outer(np.sin(u), np.sin(v))
        sphere_z = np.outer(np.ones(np.size(u)), np.cos(v))
        
        # Sphere surface with light pinkish color and transparency
        ax.plot_surface(sphere_x, sphere_y, sphere_z, rstride=1, cstride=1,
                        color='#f7eef0', alpha=0.2, linewidth=0)
        
        # Wireframe to match the image
        ax.plot_wireframe(sphere_x, sphere_y, sphere_z, color='gray', alpha=0.15, linewidth=0.5)

        # Draw coordinate axes (lines through the origin)
        ax.plot([-1, 1], [0, 0], [0, 0], 'k-', alpha=0.3, linewidth=1)
        ax.plot([0, 0], [-1, 1], [0, 0], 'k-', alpha=0.3, linewidth=1)
        ax.plot([0, 0], [0, 0], [-1, 1], 'k-', alpha=0.3, linewidth=1)

        # Draw equator
        u_eq = np.linspace(0, 2 * np.pi, 100)
        ax.plot(np.cos(u_eq), np.sin(u_eq), np.zeros(100), color='k', alpha=0.3, linewidth=1)
        
        # Draw x-z and y-z circles
        ax.plot(np.cos(u_eq), np.zeros(100), np.sin(u_eq), color='k', alpha=0.3, linewidth=1)
        ax.plot(np.zeros(100), np.cos(u_eq), np.sin(u_eq), color='k', alpha=0.3, linewidth=1)

        # Label axes
        ax.text(1.25, 0, 0, '$x$', fontsize=16, ha='center', va='center')
        ax.text(0, 1.25, 0, '$y$', fontsize=16, ha='center', va='center')
        ax.text(0, 0, 1.15, '$|0\\rangle$', fontsize=16, ha='center', va='center')
        ax.text(0, 0, -1.25, '$|1\\rangle$', fontsize=16, ha='center', va='center')
        
        # Normalize the vector if norm > 1 due to floating point
        norm = np.sqrt(x**2 + y**2 + z**2)
        if norm > 1.0:
            x, y, z = x/norm, y/norm, z/norm
            
        # Draw state vector (thick pinkish-red arrow)
        arrow_color = '#dc267f' # Matches the pinkish red in the image
        ax.quiver(0, 0, 0, x, y, z, color=arrow_color, arrow_length_ratio=0.15, linewidth=4)
        
        # Set limits
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        
        # Make the plot exactly square so the sphere is perfectly round
        try:
            ax.set_box_aspect([1, 1, 1])
        except AttributeError:
            pass # For older matplotlib versions

        ax.set_title(f'Bloch Representation\nqubit {qubit}', fontsize=16, pad=10)
        self.plt.tight_layout()
        
        return fig
    
    def plot_quantum_circuit(self, gates_sequence, n_qubits, figsize=None):
        """
        Plot a quantum circuit diagram
        gates_sequence: list of tuples (gate_name, qubit(s), parameters)
        n_qubits: number of qubits in the circuit
        """
        if figsize is None:
            width = max(12, len(gates_sequence) * 1.2)
            height = max(4, n_qubits * 1.5)
            figsize = (width, height)
        
        fig, ax = self.plt.subplots(figsize=figsize)
        
        # Circuit parameters
        qubit_spacing = 1.0
        gate_spacing = 1.0
        qubit_positions = [n_qubits - 1 - i for i in range(n_qubits)]  # Top to bottom: q0, q1, q2, ...
        
        # Draw qubit lines
        max_gates = len(gates_sequence) + 1
        for i, y_pos in enumerate(qubit_positions):
            ax.plot([0, max_gates * gate_spacing], [y_pos, y_pos], 'k-', linewidth=2)
            ax.text(-0.3, y_pos, f'q{i}', fontsize=12, ha='right', va='center')
        
        # Draw gates
        for gate_idx, gate_info in enumerate(gates_sequence):
            x_pos = (gate_idx + 1) * gate_spacing
            
            if len(gate_info) == 2:
                gate_name, qubit = gate_info
                params = None
            else:
                gate_name, qubit, params = gate_info
            
            if gate_name.upper() == 'CNOT':
                # Special handling for CNOT
                control, target = qubit  # qubit is a tuple for CNOT
                control_y = qubit_positions[control]
                target_y = qubit_positions[target]
                
                # Draw control dot
                ax.scatter([x_pos], [control_y], s=100, c='black', zorder=5)
                
                # Draw target circle
                circle = self.plt.Circle((x_pos, target_y), 0.15, fill=False, 
                                       color='black', linewidth=2, zorder=5)
                ax.add_patch(circle)
                
                # Draw plus sign in target
                ax.plot([x_pos-0.08, x_pos+0.08], [target_y, target_y], 'k-', linewidth=2)
                ax.plot([x_pos, x_pos], [target_y-0.08, target_y+0.08], 'k-', linewidth=2)
                
                # Draw connecting line
                ax.plot([x_pos, x_pos], [min(control_y, target_y), max(control_y, target_y)], 
                       'k-', linewidth=2)
                
            elif gate_name.upper() in ['CZ', 'SWAP']:
                # Two-qubit gates with symmetric representation
                if len(qubit) == 2:
                    q1, q2 = qubit
                    y1, y2 = qubit_positions[q1], qubit_positions[q2]
                    
                    if gate_name.upper() == 'CZ':
                        # Both qubits get control dots
                        ax.scatter([x_pos, x_pos], [y1, y2], s=100, c='black', zorder=5)
                    else:  # SWAP
                        # Draw X symbols
                        for y in [y1, y2]:
                            ax.plot([x_pos-0.1, x_pos+0.1], [y-0.1, y+0.1], 'k-', linewidth=3)
                            ax.plot([x_pos-0.1, x_pos+0.1], [y+0.1, y-0.1], 'k-', linewidth=3)
                    
                    # Draw connecting line
                    ax.plot([x_pos, x_pos], [min(y1, y2), max(y1, y2)], 'k-', linewidth=2)
            
            else:
                # Single qubit gates
                if isinstance(qubit, (list, tuple)):
                    qubit = qubit[0]  # Take first qubit if multiple provided
                
                y_pos = qubit_positions[qubit]
                
                # Gate box
                if gate_name.upper() in ['RX', 'RY', 'RZ'] and params is not None:
                    gate_text = f'{gate_name.upper()}\n({params:.2f})'
                    box_height = 0.35
                else:
                    gate_text = gate_name.upper()
                    box_height = 0.25
                
                box = self.FancyBboxPatch((x_pos-0.2, y_pos-box_height/2), 0.4, box_height,
                                        boxstyle="round,pad=0.02", 
                                        facecolor='lightblue', 
                                        edgecolor='black', linewidth=1.5)
                ax.add_patch(box)
                
                # Gate label
                ax.text(x_pos, y_pos, gate_text, ha='center', va='center', 
                       fontsize=10, fontweight='bold')
        
        # Formatting
        ax.set_xlim(-0.5, max_gates * gate_spacing + 0.5)
        ax.set_ylim(-0.5, n_qubits - 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'Quantum Circuit ({n_qubits} qubits)', fontsize=14, fontweight='bold')
        
        return fig
    
    def plot_measurement_histogram(self, results, figsize=(10, 6)):
        """Plot histogram of measurement results from multiple runs"""
        if not results:
            return None
            
        # Determine number of qubits from first result
        n_qubits = len(results[0]) if isinstance(results[0], str) else len(f'{results[0]:b}')
        n_states = 2**n_qubits
        state_labels = [f'{i:0{n_qubits}b}' for i in range(n_states)]
        
        # Count occurrences
        counts = {label: 0 for label in state_labels}
        for result in results:
            if isinstance(result, int):
                binary_str = f'{result:0{n_qubits}b}'
                counts[binary_str] += 1
            else:
                counts[result] += 1
        
        fig, ax = self.plt.subplots(figsize=figsize)
        
        labels = list(counts.keys())
        values = list(counts.values())
        
        bars = ax.bar(range(len(labels)), values, color='purple', alpha=0.7)
        ax.set_title(f'Measurement Results ({sum(values)} shots)')
        ax.set_xlabel('Measurement Outcome')
        ax.set_ylabel('Count')
        ax.grid(True, alpha=0.3)
        
        # Set x-axis labels
        if n_states <= 16:
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45 if n_states > 8 else 0)
        else:
            # For large systems, show fewer labels
            step = max(1, len(labels) // 16)
            ticks = range(0, len(labels), step)
            ax.set_xticks(ticks)
            ax.set_xticklabels([labels[i] for i in ticks], rotation=45)
        
        # Add count labels on bars (only for significant counts)
        max_count = max(values) if values else 0
        for i, (bar, count) in enumerate(zip(bars, values)):
            if count > max_count * 0.05:  # Only show labels for bars > 5% of max
                ax.text(bar.get_x() + bar.get_width()/2, count + max_count*0.01,
                       str(count), ha='center', va='bottom', fontsize=8)
        
        self.plt.tight_layout()
        return fig
    
    def plot_state_evolution(self, states_history, labels=None, figsize=(12, 8)):
        """
        Plot the evolution of quantum state probabilities over time
        states_history: list of quantum states at different time steps
        labels: list of labels for each time step
        """
        if labels is None:
            labels = [f'Step {i}' for i in range(len(states_history))]
        
        n_qubits = int(np.log2(len(states_history[0])))
        state_labels = [f'|{i:0{n_qubits}b}⟩' for i in range(2**n_qubits)]
        
        # Extract probabilities for each state at each time step
        prob_evolution = []
        for state in states_history:
            if hasattr(state, 'get_probabilities'):
                probs = self._tensor_to_numpy(state.get_probabilities())
            else:
                # Assume it's already a tensor/array of probabilities
                state_np = self._tensor_to_numpy(state)
                probs = np.abs(state_np)**2 if not np.all(np.abs(state_np)**2 == state_np) else state_np
            prob_evolution.append(probs)
        
        prob_evolution = np.array(prob_evolution).T
        
        fig, ax = self.plt.subplots(figsize=figsize)
        
        # Plot evolution for each basis state (only show significant ones)
        colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(state_labels))))
        significant_states = []
        
        for i, state_label in enumerate(state_labels):
            max_prob = np.max(prob_evolution[i])
            if max_prob > 0.01:  # Only plot states with significant probability
                ax.plot(range(len(labels)), prob_evolution[i], 
                       marker='o', color=colors[len(significant_states) % len(colors)], 
                       label=state_label, linewidth=2)
                significant_states.append(i)
        
        ax.set_xlabel('Evolution Step')
        ax.set_ylabel('Probability')
        ax.set_title('Quantum State Evolution')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45)
        ax.set_ylim(0, 1)
        
        self.plt.tight_layout()
        return fig
    
    def plot_entanglement_measure(self, simulator, figsize=(8, 6)):
        """Plot entanglement measure (concurrence) for the 2-qubit state"""
        if simulator.n_qubits != 2:
            print("Entanglement measure visualization only available for 2-qubit systems")
            return None
            
        state = simulator.get_state()
        state_np = self._tensor_to_numpy(state)
        
        # Calculate density matrix
        rho = np.outer(state_np, np.conj(state_np))
        
        # Calculate concurrence (measure of entanglement)
        # For 2-qubit pure states: C = 2|α00*α11 - α01*α10|
        alpha_00, alpha_01, alpha_10, alpha_11 = state_np
        concurrence = 2 * abs(alpha_00 * alpha_11 - alpha_01 * alpha_10)
        
        # Create visualization
        fig, (ax1, ax2) = self.plt.subplots(1, 2, figsize=figsize)
        
        # Concurrence meter
        ax1.bar(['Concurrence'], [concurrence], color='purple', alpha=0.7, width=0.5)
        ax1.set_ylim(0, 1)
        ax1.set_title('Entanglement Measure')
        ax1.set_ylabel('Concurrence')
        ax1.grid(True, alpha=0.3)
        ax1.text(0, concurrence + 0.05, f'{concurrence:.3f}', 
                ha='center', va='bottom', fontweight='bold')
        
        # Entanglement classification
        if concurrence < 0.1:
            classification = "Separable"
            color = 'green'
        elif concurrence < 0.7:
            classification = "Partially Entangled"
            color = 'orange'
        else:
            classification = "Highly Entangled"
            color = 'red'
        
        ax2.pie([concurrence, 1-concurrence], labels=[classification, 'Not Entangled'], 
               colors=[color, 'lightgray'], startangle=90)
        ax2.set_title('Entanglement Classification')
        
        self.plt.tight_layout()
        return fig
    
    def show_all_plots(self):
        """Display all generated plots"""
        self.plt.show()
    
    def save_plot(self, fig, filename, dpi=300):
        """Save a plot to file"""
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Plot saved as {filename}")
        
    def plot_vqe_convergence(self, history, figsize=(10, 6)):
        """Plot VQE energy convergence during optimization"""
        energies = history['energies']
        
        fig, ax = self.plt.subplots(figsize=figsize)
        ax.plot(energies, 'b-o', linewidth=2, markersize=4)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Energy')
        ax.set_title('VQE Energy Convergence')
        ax.grid(True, alpha=0.3)
        
        # Add final energy annotation
        if energies:
            ax.annotate(f'Final: {energies[-1]:.6f}', 
                    xy=(len(energies)-1, energies[-1]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        self.plt.tight_layout()
        return fig

    def plot_qaoa_results(self, solution_counts, graph_edges, n_qubits, figsize=(12, 8)):
        """Plot QAOA results including solution distribution and cut analysis"""
        fig, ((ax1, ax2), (ax3, ax4)) = self.plt.subplots(2, 2, figsize=figsize)
        
        # 1. Solution frequency histogram
        solutions = list(solution_counts.keys())
        counts = list(solution_counts.values())
        
        bars = ax1.bar(range(len(solutions)), counts, color='purple', alpha=0.7)
        ax1.set_title('Solution Frequencies')
        ax1.set_xlabel('Solution Index')
        ax1.set_ylabel('Count')
        ax1.grid(True, alpha=0.3)
        
        # Set x-axis labels
        if len(solutions) <= 16:
            ax1.set_xticks(range(len(solutions)))
            ax1.set_xticklabels(solutions, rotation=45)
        else:
            # For many solutions, show fewer labels
            step = max(1, len(solutions) // 10)
            ticks = range(0, len(solutions), step)
            ax1.set_xticks(ticks)
            ax1.set_xticklabels([solutions[i] for i in ticks], rotation=45)
        
        # Add count labels for top solutions
        max_count = max(counts) if counts else 0
        for i, (bar, count) in enumerate(zip(bars, counts)):
            if count > max_count * 0.1:  # Only label significant bars
                ax1.text(bar.get_x() + bar.get_width()/2, count + max_count*0.01,
                        str(count), ha='center', va='bottom', fontsize=8)
        
        # 2. Cut size analysis
        cut_sizes = []
        for solution in solutions:
            cut_size = self._calculate_cut_size(solution, graph_edges)
            cut_sizes.append(cut_size)
        
        scatter = ax2.scatter(cut_sizes, counts, c=cut_sizes, cmap='viridis', s=100, alpha=0.7)
        ax2.set_xlabel('Cut Size')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Cut Size vs Frequency')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax2, label='Cut Size')
        
        # 3. Cut size distribution
        if cut_sizes:
            unique_cuts = list(set(cut_sizes))
            cut_counts = [cut_sizes.count(cut) for cut in unique_cuts]
            
            ax3.bar(unique_cuts, cut_counts, color='orange', alpha=0.7)
            ax3.set_xlabel('Cut Size')
            ax3.set_ylabel('Number of Solutions')
            ax3.set_title('Cut Size Distribution')
            ax3.grid(True, alpha=0.3)
        
        # 4. Graph visualization
        self._plot_graph_with_cut(ax4, graph_edges, n_qubits, solutions[0] if solutions else None)
        
        self.plt.tight_layout()
        return fig

    def _calculate_cut_size(self, solution_string, edges):
        """Helper method to calculate cut size"""
        cut_size = 0
        for i, j in edges:
            if i < len(solution_string) and j < len(solution_string):
                if solution_string[i] != solution_string[j]:
                    cut_size += 1
        return cut_size

    def _plot_graph_with_cut(self, ax, edges, n_qubits, solution=None):
        """Plot graph with highlighted cut edges"""
        try:
            import networkx as nx
        except ImportError:
            ax.text(0.5, 0.5, 'NetworkX not available\nfor graph visualization', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Graph Visualization (NetworkX required)')
            return
        
        # Create graph
        G = nx.Graph()
        G.add_nodes_from(range(n_qubits))
        G.add_edges_from(edges)
        
        # Position nodes in a circle
        pos = nx.circular_layout(G)
        
        # Draw nodes
        if solution and len(solution) == n_qubits:
            node_colors = ['red' if solution[i] == '1' else 'lightblue' for i in range(n_qubits)]
        else:
            node_colors = 'lightblue'
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, ax=ax)
        nx.draw_networkx_labels(G, pos, ax=ax)
        
        # Draw edges
        if solution and len(solution) == n_qubits:
            cut_edges = [(i, j) for i, j in edges if i < len(solution) and j < len(solution) and solution[i] != solution[j]]
            uncut_edges = [(i, j) for i, j in edges if i < len(solution) and j < len(solution) and solution[i] == solution[j]]
            
            if cut_edges:
                nx.draw_networkx_edges(G, pos, edgelist=cut_edges, edge_color='red', 
                                    width=2, ax=ax)
            if uncut_edges:
                nx.draw_networkx_edges(G, pos, edgelist=uncut_edges, edge_color='gray', 
                                    width=1, ax=ax)
        else:
            nx.draw_networkx_edges(G, pos, ax=ax)
        
        ax.set_title('Graph with Cut Visualization')
        ax.axis('off')