// ================= VQE Functions =================

async function runVQE() {
    try {
        showMessage('Starting VQE optimization...', 'info');
        
        // Parse Hamiltonian terms
        const termsText = document.getElementById('hamiltonianTerms').value.trim();
        let hamiltonianTerms;
        try {
            hamiltonianTerms = JSON.parse(termsText);
        } catch (e) {
            throw new Error('Invalid JSON format for Hamiltonian terms');
        }
        
        if (!Array.isArray(hamiltonianTerms) || !hamiltonianTerms.every(term => 
            term.hasOwnProperty('pauli_ops') && 
            term.hasOwnProperty('coefficient') && 
            term.hasOwnProperty('qubits')
        )) {
            throw new Error('Hamiltonian terms must have pauli_ops, coefficient, and qubits fields');
        }
        
        const request = {
            n_qubits: parseInt(document.getElementById('vqeQubits').value),
            hamiltonian_terms: hamiltonianTerms,
            ansatz_type: "hardware_efficient",
            ansatz_depth: parseInt(document.getElementById('ansatzDepth').value),
            shots: parseInt(document.getElementById('vqeShots').value)
        };
        
        const response = await fetch('/api/vqe/optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        activeJobs[result.job_id] = 'vqe';
        
        showMessage('VQE job submitted successfully', 'success');
        pollJobResults(result.job_id, 'vqe');
        
    } catch (error) {
        showMessage(`Error running VQE: ${error.message}`, 'error');
    }
}

function displayVQEResults(result) {
    const resultsDiv = document.getElementById('vqeResults');
    const contentDiv = document.getElementById('vqeResultContent');
    
    let html = `
        <div class="result-metric">
            <span class="metric-label">Ground State Energy:</span>
            <span class="metric-value">${result.energy.toFixed(6)}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Converged:</span>
            <span class="metric-value">${result.converged ? 'Yes' : 'No'}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Iterations:</span>
            <span class="metric-value">${result.iterations}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Ansatz Type:</span>
            <span class="metric-value">${result.ansatz_info.type}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Ansatz Depth:</span>
            <span class="metric-value">${result.ansatz_info.depth}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Parameters:</span>
            <span class="metric-value">${result.ansatz_info.n_parameters}</span>
        </div>
    `;
    
    // Optimal parameters display
    if (result.optimal_params && result.optimal_params.length > 0) {
        html += `
            <div class="solution-display">
                <strong>Optimal Parameters:</strong><br>
                ${result.optimal_params.map((param, i) => `θ${i}: ${param.toFixed(4)}`).join(', ')}
            </div>
        `;
    }
    
    // Hamiltonian info
    if (result.hamiltonian_info) {
        html += `
            <div class="cut-visualization">
                <strong>Hamiltonian Terms (${result.hamiltonian_info.n_terms}):</strong><br>
                ${result.hamiltonian_info.terms.slice(0, 3).join('<br>')}
                ${result.hamiltonian_info.terms.length > 3 ? '<br>...' : ''}
            </div>
        `;
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

function loadPresetHamiltonian() {
    const numQubits = parseInt(document.getElementById('vqeQubits').value);
    let preset;
    
    if (numQubits === 2) {
        // H2 molecule Hamiltonian
        preset = [
            {"pauli_ops": ["I"], "coefficient": -1.0523732, "qubits": [0]},
            {"pauli_ops": ["Z"], "coefficient": -0.39793742, "qubits": [0]},
            {"pauli_ops": ["Z"], "coefficient": -0.39793742, "qubits": [1]},
            {"pauli_ops": ["Z", "Z"], "coefficient": -0.01128010, "qubits": [0, 1]},
            {"pauli_ops": ["X", "X"], "coefficient": 0.18093119, "qubits": [0, 1]}
        ];
    } else {
        // Generic Ising model
        preset = [];
        for (let i = 0; i < numQubits; i++) {
            preset.push({"pauli_ops": ["Z"], "coefficient": -1.0, "qubits": [i]});
        }
        for (let i = 0; i < numQubits - 1; i++) {
            preset.push({"pauli_ops": ["Z", "Z"], "coefficient": -0.5, "qubits": [i, i + 1]});
        }
    }
    
    document.getElementById('hamiltonianTerms').value = JSON.stringify(preset, null, 2);
    showMessage('Preset Hamiltonian loaded', 'success');
}