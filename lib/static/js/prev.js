// Global variables (keeping your existing ones)
let circuit = [];
let currentJob = null;
let draggedGate = null;
let pendingGateData = null;
let numQubits = 2;
let circuitDepth = 10;
let activeJobs = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    updateCircuit();
    showTab('circuit'); // Start with circuit tab
    refreshJobs();
});

// ================= Tab Management =================

function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// ================= QAOA Functions =================

async function runQAOA() {
    try {
        showMessage('Starting QAOA optimization...', 'info');
        
        // Parse graph edges
        const edgesText = document.getElementById('graphEdges').value.trim();
        let graphEdges;
        try {
            graphEdges = JSON.parse(edgesText);
        } catch (e) {
            throw new Error('Invalid JSON format for graph edges');
        }
        
        if (!Array.isArray(graphEdges) || !graphEdges.every(edge => 
            Array.isArray(edge) && edge.length === 2 && 
            typeof edge[0] === 'number' && typeof edge[1] === 'number'
        )) {
            throw new Error('Graph edges must be an array of [source, target] pairs');
        }
        
        const request = {
            graph_edges: graphEdges,
            n_qubits: parseInt(document.getElementById('qaoaQubits').value),
            n_layers: parseInt(document.getElementById('qaoaLayers').value),
            shots: parseInt(document.getElementById('qaoaShots').value),
            mixer_type: document.getElementById('mixerType').value,
            use_warm_start: document.getElementById('useWarmStart').checked
        };
        
        const response = await fetch('/api/qaoa/solve', {
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
        activeJobs[result.job_id] = 'qaoa';
        
        showMessage('QAOA job submitted successfully', 'success');
        pollJobResults(result.job_id, 'qaoa');
        
    } catch (error) {
        showMessage(`Error running QAOA: ${error.message}`, 'error');
    }
}

function displayQAOAResults(result) {
    const resultsDiv = document.getElementById('qaoaResults');
    const contentDiv = document.getElementById('qaoaResultContent');
    
    let html = `
        <div class="result-metric">
            <span class="metric-label">Best Cut Size:</span>
            <span class="metric-value">${result.best_cut_size}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Maximum Possible:</span>
            <span class="metric-value">${result.max_possible_cut}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Approximation Ratio:</span>
            <span class="metric-value">${(result.approximation_ratio * 100).toFixed(1)}%</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">QAOA Layers:</span>
            <span class="metric-value">${result.qaoa_layers}</span>
        </div>
        <div class="result-metric">
            <span class="metric-label">Converged:</span>
            <span class="metric-value">${result.converged ? 'Yes' : 'No'}</span>
        </div>
    `;
    
    // Best solution display
    html += `
        <div class="solution-display">
            <strong>Best Solution:</strong> ${result.best_cut_solution}<br>
            <strong>Most Frequent:</strong> ${result.most_frequent_solution}
        </div>
    `;
    
    // Solution counts visualization
    if (result.solution_counts) {
        html += '<h5>Top Solutions:</h5>';
        Object.entries(result.solution_counts).slice(0, 5).forEach(([solution, count]) => {
            const percentage = ((count / Object.values(result.solution_counts).reduce((a, b) => a + b, 0)) * 100).toFixed(1);
            html += `
                <div class="measurement-bar">
                    <div class="measurement-label">${solution}</div>
                    <div class="measurement-fill" style="width: ${percentage}%">${count} (${percentage}%)</div>
                </div>
            `;
        });
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

function generateRandomGraph() {
    const numQubits = parseInt(document.getElementById('qaoaQubits').value);
    const edges = [];
    
    // Generate a random connected graph
    for (let i = 0; i < numQubits - 1; i++) {
        edges.push([i, i + 1]);
    }
    
    // Add random additional edges
    const numAdditionalEdges = Math.floor(Math.random() * numQubits);
    for (let i = 0; i < numAdditionalEdges; i++) {
        const source = Math.floor(Math.random() * numQubits);
        const target = Math.floor(Math.random() * numQubits);
        if (source !== target && !edges.some(e => 
            (e[0] === source && e[1] === target) || (e[0] === target && e[1] === source)
        )) {
            edges.push([source, target]);
        }
    }
    
    document.getElementById('graphEdges').value = JSON.stringify(edges);
    showMessage(`Generated random graph with ${edges.length} edges`, 'success');
}

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

// ================= Algorithm Functions =================

async function runGrover() {
    try {
        showMessage('Running Grover search...', 'info');
        
        const searchArray = JSON.parse(document.getElementById('groverArray').value);
        const targetValue = document.getElementById('groverTarget').value;
        
        const request = {
            search_array: searchArray,
            target_value: targetValue
        };
        
        const response = await fetch('/api/grover/search', {
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
        activeJobs[result.job_id] = 'grover';
        
        showMessage('Grover search job submitted', 'success');
        pollJobResults(result.job_id, 'algorithm');
        
    } catch (error) {
        showMessage(`Error running Grover: ${error.message}`, 'error');
    }
}

async function runShor() {
    try {
        showMessage('Running Shor factoring...', 'info');
        
        const request = {
            N: parseInt(document.getElementById('shorN').value),
            n_counting_qubits: parseInt(document.getElementById('shorCountingQubits').value)
        };
        
        const response = await fetch('/api/shor/factor', {
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
        activeJobs[result.job_id] = 'shor';
        
        showMessage('Shor factoring job submitted', 'success');
        pollJobResults(result.job_id, 'algorithm');
        
    } catch (error) {
        showMessage(`Error running Shor: ${error.message}`, 'error');
    }
}

async function runQFT() {
    try {
        showMessage('Running Quantum Fourier Transform...', 'info');
        
        const request = {
            n_qubits: parseInt(document.getElementById('qftQubits').value)
        };
        
        const response = await fetch('/api/qft/transform', {
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
        displayAlgorithmResults(result, 'QFT');
        showMessage('QFT completed successfully', 'success');
        
    } catch (error) {
        showMessage(`Error running QFT: ${error.message}`, 'error');
    }
}

function displayAlgorithmResults(result, algorithmType) {
    const resultsDiv = document.getElementById('algorithmResults');
    const contentDiv = document.getElementById('algorithmResultContent');
    
    let html = `<h5>${algorithmType} Results:</h5>`;
    
    if (algorithmType === 'Grover') {
        html += `
            <div class="result-metric">
                <span class="metric-label">Found Index:</span>
                <span class="metric-value">${result.found_index}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Found Value:</span>
                <span class="metric-value">${result.found_value}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Success:</span>
                <span class="metric-value">${result.success ? 'Yes' : 'No'}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Search Space Size:</span>
                <span class="metric-value">${result.search_space_size}</span>
            </div>
        `;
    } else if (algorithmType === 'Shor') {
        html += `
            <div class="result-metric">
                <span class="metric-label">Number to Factor:</span>
                <span class="metric-value">${result.N}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Factors:</span>
                <span class="metric-value">${result.factors ? result.factors.join(' × ') : 'Not found'}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Success:</span>
                <span class="metric-value">${result.success ? 'Yes' : 'No'}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Verification:</span>
                <span class="metric-value">${result.verification ? 'Correct' : 'Failed'}</span>
            </div>
        `;
    } else if (algorithmType === 'QFT') {
        html += `
            <div class="result-metric">
                <span class="metric-label">Qubits:</span>
                <span class="metric-value">${result.n_qubits}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Circuit Depth:</span>
                <span class="metric-value">${result.circuit_depth}</span>
            </div>
        `;
        
        // Show sample measurements
        if (result.sample_measurements && result.sample_measurements.length > 0) {
            html += `
                <div class="solution-display">
                    <strong>Sample Measurements:</strong><br>
                    ${result.sample_measurements.slice(0, 5).join(', ')}
                </div>
            `;
        }
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// ================= Job Management =================

async function refreshJobs() {
    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();
        
        const statusDiv = document.getElementById('jobStatus');
        let html = `
            <div class="result-metric">
                <span class="metric-label">Total Jobs:</span>
                <span class="metric-value">${data.total}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Running:</span>
                <span class="metric-value">${data.running}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Completed:</span>
                <span class="metric-value">${data.completed}</span>
            </div>
            <div class="result-metric">
                <span class="metric-label">Failed:</span>
                <span class="metric-value">${data.failed}</span>
            </div>
        `;
        
        if (data.jobs && data.jobs.length > 0) {
            html += '<h5>Recent Jobs:</h5>';
            data.jobs.slice(0, 5).forEach(job => {
                html += `
                    <div class="job-item ${job.status}">
                        <div>
                            <div class="job-id">${job.job_id}</div>
                            <div>Created: ${new Date(job.created_at).toLocaleTimeString()}</div>
                        </div>
                        <div class="job-status status-${job.status}">${job.status.toUpperCase()}</div>
                    </div>
                `;
            });
        }
        
        statusDiv.innerHTML = html;
        
    } catch (error) {
        showMessage(`Error refreshing jobs: ${error.message}`, 'error');
    }
}

async function cleanupJobs() {
    try {
        const response = await fetch('/api/jobs/cleanup', { method: 'POST' });
        const result = await response.json();
        
        showMessage(result.message, 'success');
        refreshJobs();
        
    } catch (error) {
        showMessage(`Error cleaning up jobs: ${error.message}`, 'error');
    }
}

// ================= Enhanced Job Polling =================

async function pollJobResults(jobId, jobType) {
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        const job = await response.json();
        
        if (job.status === 'completed') {
            delete activeJobs[jobId];
            
            // Display results based on job type
            if (jobType === 'qaoa') {
                displayQAOAResults(job.result);
                showMessage('QAOA optimization completed successfully', 'success');
            } else if (jobType === 'vqe') {
                displayVQEResults(job.result);
                showMessage('VQE optimization completed successfully', 'success');
            } else if (jobType === 'grover') {
                displayAlgorithmResults(job.result, 'Grover');
                showMessage('Grover search completed successfully', 'success');
            } else if (jobType === 'shor') {
                displayAlgorithmResults(job.result, 'Shor');
                showMessage('Shor factoring completed successfully', 'success');
            } else if (jobType === 'circuit') {
                displayResults(job.result);
                showMessage('Circuit executed successfully', 'success');
            }
            
            refreshJobs();
            
        } else if (job.status === 'failed') {
            delete activeJobs[jobId];
            showMessage(`Job failed: ${job.error}`, 'error');
            refreshJobs();
            
        } else if (job.status === 'running') {
            // Show progress if available
            if (job.progress) {
                updateJobProgress(jobId, job.progress);
            }
            
            // Continue polling
            setTimeout(() => pollJobResults(jobId, jobType), 2000);
        }
    } catch (error) {
        showMessage(`Error polling results: ${error.message}`, 'error');
    }
}

function updateJobProgress(jobId, progress) {
    // You can implement a progress bar here if needed
    console.log(`Job ${jobId}: ${(progress * 100).toFixed(1)}% complete`);
}

// ================= Keep all your existing circuit functions =================

function updateCircuit() {
    numQubits = parseInt(document.getElementById('numQubits').value);
    circuitDepth = parseInt(document.getElementById('circuitDepth').value);
    
    const circuitGrid = document.getElementById('circuitGrid');
    circuitGrid.innerHTML = '';
    
    circuit = Array(numQubits).fill().map(() => Array(circuitDepth).fill(null));
    
    for (let qubit = 0; qubit < numQubits; qubit++) {
        const qubitLine = document.createElement('div');
        qubitLine.className = 'qubit-line';
        
        const qubitLabel = document.createElement('div');
        qubitLabel.className = 'qubit-label';
        qubitLabel.textContent = `q${qubit}`;
        qubitLine.appendChild(qubitLabel);
        
        for (let slot = 0; slot < circuitDepth; slot++) {
            const gateSlot = document.createElement('div');
            gateSlot.className = 'gate-slot';
            gateSlot.dataset.qubit = qubit;
            gateSlot.dataset.slot = slot;
            qubitLine.appendChild(gateSlot);
        }
        
        circuitGrid.appendChild(qubitLine);
    }
    
    showMessage('Circuit updated successfully', 'success');
}

function clearCircuit() {
    circuit = Array(numQubits).fill().map(() => Array(circuitDepth).fill(null));
    updateCircuitDisplay();
    showMessage('Circuit cleared', 'info');
}

function setupDragAndDrop() {
    document.addEventListener('dragstart', function(e) {
        if (e.target.classList.contains('gate-item')) {
            draggedGate = {
                type: e.target.dataset.gate,
                element: e.target
            };
            e.dataTransfer.effectAllowed = 'copy';
            e.target.style.opacity = '0.5';
        }
    });
    
    document.addEventListener('dragend', function(e) {
        if (e.target.classList.contains('gate-item')) {
            e.target.style.opacity = '1';
            draggedGate = null;
        }
    });
    
    document.addEventListener('dragover', function(e) {
        if (e.target.classList.contains('gate-slot')) {
            e.preventDefault();
            e.target.classList.add('drop-zone');
        }
    });
    
    document.addEventListener('dragleave', function(e) {
        if (e.target.classList.contains('gate-slot')) {
            e.target.classList.remove('drop-zone');
        }
    });
    
    document.addEventListener('drop', function(e) {
        if (e.target.classList.contains('gate-slot') && draggedGate) {
            e.preventDefault();
            e.target.classList.remove('drop-zone');
            
            const qubit = parseInt(e.target.dataset.qubit);
            const slot = parseInt(e.target.dataset.slot);
            
            handleGateDrop(draggedGate.type, qubit, slot);
        }
    });
}

function handleGateDrop(gateType, qubit, slot) {
    if (['RX', 'RY', 'RZ'].includes(gateType)) {
        pendingGateData = { type: gateType, qubit: qubit, slot: slot };
        showRotationPopup();
    } else if (['CNOT', 'CZ'].includes(gateType)) {
        pendingGateData = { type: gateType, controlQubit: qubit, slot: slot };
        showTwoQubitPopup(qubit);
    } else {
        placeGate(gateType, [qubit], slot);
    }
}

function showRotationPopup() {
    document.getElementById('rotationPopup').style.display = 'flex';
    document.getElementById('rotationAngle').focus();
}

function showTwoQubitPopup(controlQubit) {
    const targetSelect = document.getElementById('targetQubit');
    targetSelect.innerHTML = '';
    
    for (let i = 0; i < numQubits; i++) {
        if (i !== controlQubit) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `q${i}`;
            targetSelect.appendChild(option);
        }
    }
    
    document.getElementById('twoQubitPopup').style.display = 'flex';
}

function confirmRotation() {
    const angle = parseFloat(document.getElementById('rotationAngle').value);
    if (isNaN(angle)) {
        showMessage('Please enter a valid angle', 'error');
        return;
    }
    
    const { type, qubit, slot } = pendingGateData;
    placeGate(type, [qubit], slot, { angle: angle });
    
    document.getElementById('rotationPopup').style.display = 'none';
    pendingGateData = null;
}

function cancelRotation() {
    document.getElementById('rotationPopup').style.display = 'none';
    pendingGateData = null;
}

function confirmTwoQubit() {
    const targetQubit = parseInt(document.getElementById('targetQubit').value);
    const { type, controlQubit, slot } = pendingGateData;
    
    placeGate(type, [controlQubit, targetQubit], slot);
    
    document.getElementById('twoQubitPopup').style.display = 'none';
    pendingGateData = null;
}

function cancelTwoQubit() {
    document.getElementById('twoQubitPopup').style.display = 'none';
    pendingGateData = null;
}

function placeGate(gateType, qubits, slot, params = null) {
    for (let qubit of qubits) {
        if (circuit[qubit][slot] !== null) {
            showMessage('Gate slot already occupied', 'error');
            return;
        }
    }
    
    const gate = {
        gate: gateType,
        qubits: qubits,
        params: params
    };
    
    for (let qubit of qubits) {
        circuit[qubit][slot] = gate;
    }
    
    updateCircuitDisplay();
    showMessage(`${gateType} gate placed successfully`, 'success');
}

function updateCircuitDisplay() {
    document.querySelectorAll('.gate-slot').forEach(slot => {
        slot.innerHTML = '';
        slot.classList.remove('occupied');
    });
    
    for (let qubit = 0; qubit < numQubits; qubit++) {
        for (let slot = 0; slot < circuitDepth; slot++) {
            const gate = circuit[qubit][slot];
            if (gate) {
                const slotElement = document.querySelector(`.gate-slot[data-qubit="${qubit}"][data-slot="${slot}"]`);
                renderGate(gate, slotElement, qubit);
            }
        }
    }
    
    drawTwoQubitConnections();
}

function renderGate(gate, slotElement, currentQubit) {
    slotElement.classList.add('occupied');
    
    if (gate.qubits.length === 1) {
        const gateDiv = document.createElement('div');
        gateDiv.className = `placed-gate single-qubit ${gate.gate.startsWith('R') ? 'rotation' : ''}`;
        gateDiv.textContent = gate.gate;
        
        if (gate.params && gate.params.angle !== undefined) {
            const angleInput = document.createElement('input');
            angleInput.className = 'angle-input';
            angleInput.type = 'number';
            angleInput.step = '0.01';
            angleInput.value = gate.params.angle.toFixed(2);
            angleInput.addEventListener('change', function() {
                gate.params.angle = parseFloat(this.value);
            });
            gateDiv.appendChild(angleInput);
        }
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-gate';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => removeGate(currentQubit, parseInt(slotElement.dataset.slot));
        gateDiv.appendChild(removeBtn);
        
        slotElement.appendChild(gateDiv);
    } else if (gate.qubits.length === 2) {
        const isControl = currentQubit === gate.qubits[0];
        const gateDiv = document.createElement('div');
        gateDiv.className = 'placed-gate two-qubit';
        
        if (isControl) {
            gateDiv.innerHTML = '<div class="control-dot"></div>';
        } else {
            if (gate.gate === 'CNOT') {
                gateDiv.innerHTML = '<div class="target-circle"><div class="target-plus"></div></div>';
            } else if (gate.gate === 'CZ') {
                gateDiv.innerHTML = '<div class="control-dot"></div>';
            }
        }
        
        if (isControl) {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-gate';
            removeBtn.textContent = '×';
            removeBtn.onclick = () => removeGate(currentQubit, parseInt(slotElement.dataset.slot));
            gateDiv.appendChild(removeBtn);
        }
        
        slotElement.appendChild(gateDiv);
    }
}

function drawTwoQubitConnections() {
    document.querySelectorAll('.cnot-connection').forEach(conn => conn.remove());
    
    for (let qubit = 0; qubit < numQubits; qubit++) {
        for (let slot = 0; slot < circuitDepth; slot++) {
            const gate = circuit[qubit][slot];
            if (gate && gate.qubits.length === 2 && qubit === gate.qubits[0]) {
                const controlQubit = gate.qubits[0];
                const targetQubit = gate.qubits[1];
                
                const controlSlot = document.querySelector(`.gate-slot[data-qubit="${controlQubit}"][data-slot="${slot}"]`);
                const targetSlot = document.querySelector(`.gate-slot[data-qubit="${targetQubit}"][data-slot="${slot}"]`);
                
                if (controlSlot && targetSlot) {
                    const connection = document.createElement('div');
                    connection.className = 'cnot-connection';
                    
                    const controlRect = controlSlot.getBoundingClientRect();
                    const targetRect = targetSlot.getBoundingClientRect();
                    const containerRect = document.getElementById('circuitGrid').getBoundingClientRect();
                    
                    const top = Math.min(controlRect.top, targetRect.top) - containerRect.top + 30;
                    const height = Math.abs(targetRect.top - controlRect.top);
                    const left = controlRect.left - containerRect.left + 28;
                    
                    connection.style.top = `${top}px`;
                    connection.style.left = `${left}px`;
                    connection.style.height = `${height}px`;
                    
                    document.getElementById('circuitGrid').appendChild(connection);
                }
            }
        }
    }
}

function removeGate(qubit, slot) {
    const gate = circuit[qubit][slot];
    if (gate) {
        for (let q of gate.qubits) {
            circuit[q][slot] = null;
        }
        updateCircuitDisplay();
        showMessage('Gate removed', 'info');
    }
}

async function executeCircuit() {
    try {
        showMessage('Executing circuit...', 'info');
        
        const gates = [];
        const processedSlots = new Set();
        
        for (let qubit = 0; qubit < numQubits; qubit++) {
            for (let slot = 0; slot < circuitDepth; slot++) {
                const gate = circuit[qubit][slot];
                const slotKey = `${slot}-${gate?.qubits?.join('-') || qubit}`;
                
                if (gate && !processedSlots.has(slotKey)) {
                    gates.push({
                        gate: gate.gate,
                        qubits: gate.qubits,
                        params: gate.params
                    });
                    processedSlots.add(slotKey);
                }
            }
        }
        
        if (gates.length === 0) {
            showMessage('No gates in circuit to execute', 'error');
            return;
        }
        
        const response = await fetch('/api/circuit/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                n_qubits: numQubits,
                gates: gates,
                shots: parseInt(document.getElementById('measurementShots').value)
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentJob = result.job_id;
        activeJobs[result.job_id] = 'circuit';
        
        pollJobResults(result.job_id, 'circuit');
        
    } catch (error) {
        showMessage(`Error executing circuit: ${error.message}`, 'error');
    }
}

function displayResults(result) {
    if (result.state_vector) {
        const stateString = formatStateVector(result.state_vector);
        document.getElementById('currentState').textContent = stateString;
    }
    
    if (result.probabilities) {
        displayProbabilities(result.probabilities);
    }
    
    if (result.measurements) {
        displayMeasurementHistogram(result.measurements);
    }
}

function formatStateVector(stateVector) {
    let terms = [];
    const threshold = 0.001;
    
    for (let i = 0; i < stateVector.length; i++) {
        const amplitude = stateVector[i];
        const real = amplitude.real || 0;
        const imag = amplitude.imag || 0;
        const magnitude = Math.sqrt(real * real + imag * imag);
        
        if (magnitude > threshold) {
            const binaryState = i.toString(2).padStart(numQubits, '0');
            
            let amplitudeStr = '';
            const realSignificant = Math.abs(real) > threshold;
            const imagSignificant = Math.abs(imag) > threshold;
            
            if (realSignificant && imagSignificant) {
                const imagPart = imag >= 0 ? `+${imag.toFixed(3)}i` : `${imag.toFixed(3)}i`;
                amplitudeStr = `(${real.toFixed(3)}${imagPart})`;
            } else if (realSignificant) {
                amplitudeStr = real.toFixed(3);
            } else if (imagSignificant) {
                amplitudeStr = `${imag.toFixed(3)}i`;
            }
            
            terms.push({ amplitude: amplitudeStr, state: binaryState, isPositive: real >= 0 && imag >= 0 });
        }
    }
    
    if (terms.length === 0) return '|00...0⟩';
    
    let stateString = '';
    for (let i = 0; i < terms.length; i++) {
        const term = terms[i];
        
        if (i === 0) {
            stateString = `${term.amplitude}|${term.state}⟩`;
        } else {
            if (term.amplitude.startsWith('-')) {
                stateString += ` ${term.amplitude}|${term.state}⟩`;
            } else {
                stateString += ` + ${term.amplitude}|${term.state}⟩`;
            }
        }
    }
    
    return stateString;
}

function displayProbabilities(probabilities) {
    const container = document.getElementById('measurementProbabilities');
    container.innerHTML = '';
    
    for (let i = 0; i < probabilities.length; i++) {
        if (probabilities[i] > 0.001) {
            const binaryState = i.toString(2).padStart(numQubits, '0');
            const percentage = (probabilities[i] * 100).toFixed(1);
            
            const barDiv = document.createElement('div');
            barDiv.className = 'probability-bar';
            
            barDiv.innerHTML = `
                <div class="probability-label">|${binaryState}⟩</div>
                <div class="probability-fill" style="width: ${percentage}%">${percentage}%</div>
            `;
            
            container.appendChild(barDiv);
        }
    }
}

function displayMeasurementHistogram(measurements) {
    const histogram = {};
    measurements.forEach(measurement => {
        histogram[measurement] = (histogram[measurement] || 0) + 1;
    });
    
    const container = document.getElementById('histogramBars');
    container.innerHTML = '';
    
    const total = measurements.length;
    
    Object.entries(histogram).forEach(([state, count]) => {
        const percentage = ((count / total) * 100).toFixed(1);
        
        const barDiv = document.createElement('div');
        barDiv.className = 'measurement-bar';
        
        barDiv.innerHTML = `
            <div class="measurement-label">${state}</div>
            <div class="measurement-fill" style="width: ${percentage}%">${count} (${percentage}%)</div>
        `;
        
        container.appendChild(barDiv);
    });
    
    document.getElementById('measurementHistogram').style.display = 'block';
}

function performMeasurement() {
    if (!currentJob) {
        showMessage('Please execute a circuit first', 'error');
        return;
    }
    
    showMessage('Performing measurement...', 'info');
}

function addMeasurement() {
    let lastColumn = -1;
    for (let slot = circuitDepth - 1; slot >= 0; slot--) {
        for (let qubit = 0; qubit < numQubits; qubit++) {
            if (circuit[qubit][slot] !== null) {
                lastColumn = slot;
                break;
            }
        }
        if (lastColumn !== -1) break;
    }
    
    const measurementColumn = Math.min(lastColumn + 1, circuitDepth - 1);
    
    for (let qubit = 0; qubit < numQubits; qubit++) {
        if (circuit[qubit][measurementColumn] === null) {
            placeGate('M', [qubit], measurementColumn);
        }
    }
}

function showMessage(message, type = 'info') {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.textContent = message;
    
    messagesContainer.appendChild(messageDiv);
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.getElementById('rotationPopup').style.display = 'none';
        document.getElementById('twoQubitPopup').style.display = 'none';
        pendingGateData = null;
    }
});

document.getElementById('rotationAngle').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        confirmRotation();
    }
});

// Auto-refresh jobs periodically
setInterval(refreshJobs, 30000); // Refresh every 30 seconds