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