// ================= Circuit Designer Functions =================

let circuit = [];
let currentJob = null;
let draggedGate = null;
let pendingGateData = null;
let numQubits = 2;
let circuitDepth = 10;

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
    executeCircuit();
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
    executeCircuit();
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
                    
                    const top = Math.min(controlRect.top, targetRect.top) - containerRect.top + (controlRect.height / 2);
                    const height = Math.abs(targetRect.top - controlRect.top);
                    const left = controlRect.left - containerRect.left + (controlRect.width / 2) - 1;
                    
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
        executeCircuit();
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
            document.getElementById('currentState').textContent = '|00...0⟩';
            document.getElementById('measurementProbabilities').innerHTML = '';
            document.getElementById('measurementHistogram').style.display = 'none';
            document.getElementById('pythonCodeDisplay').style.display = 'none';
            if(document.getElementById('blochSpheresDisplay')) {
                document.getElementById('blochSpheresDisplay').style.display = 'none';
            }
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
    
    if (result.python_code) {
        document.getElementById('pythonCodeContent').textContent = result.python_code;
        document.getElementById('pythonCodeDisplay').style.display = 'block';
    }
    
    if (result.bloch_vectors && result.bloch_vectors.length > 0) {
        const container = document.getElementById('blochSpheresImages');
        container.innerHTML = '';
        
        result.bloch_vectors.forEach((vector, idx) => {
            const plotDiv = document.createElement('div');
            plotDiv.id = `bloch-sphere-${idx}`;
            plotDiv.style.width = '300px';
            plotDiv.style.height = '300px';
            container.appendChild(plotDiv);
            
            // Generate sphere surface
            const u = []; const v = [];
            for(let i=0; i<=20; i++) {
                u.push((i * 2 * Math.PI) / 20);
                v.push((i * Math.PI) / 20);
            }
            const x = []; const y = []; const z = [];
            for(let i=0; i<u.length; i++) {
                x[i] = []; y[i] = []; z[i] = [];
                for(let j=0; j<v.length; j++) {
                    x[i][j] = Math.cos(u[i]) * Math.sin(v[j]);
                    y[i][j] = Math.sin(u[i]) * Math.sin(v[j]);
                    z[i][j] = Math.cos(v[j]);
                }
            }

            const sphere = {
                type: 'surface',
                x: x, y: y, z: z,
                opacity: 0.1,
                colorscale: [[0, '#f7eef0'], [1, '#f7eef0']],
                showscale: false,
                hoverinfo: 'skip'
            };

            // Equator
            const eqX = [], eqY = [], eqZ = [];
            for(let i=0; i<=40; i++) {
                const angle = (i * 2 * Math.PI) / 40;
                eqX.push(Math.cos(angle)); eqY.push(Math.sin(angle)); eqZ.push(0);
            }
            const equator = {
                type: 'scatter3d', mode: 'lines',
                x: eqX, y: eqY, z: eqZ,
                line: {color: 'rgba(0,0,0,0.2)', width: 2},
                hoverinfo: 'skip'
            };

            // Axes lines
            const axes = {
                type: 'scatter3d', mode: 'lines',
                x: [-1, 1, null, 0, 0, null, 0, 0],
                y: [0, 0, null, -1, 1, null, 0, 0],
                z: [0, 0, null, 0, 0, null, -1, 1],
                line: {color: 'rgba(0,0,0,0.15)', width: 2},
                hoverinfo: 'skip'
            };

            // Vector
            const vecX = [0, vector[0]];
            const vecY = [0, vector[1]];
            const vecZ = [0, vector[2]];
            const stateVector = {
                type: 'scatter3d', mode: 'lines+markers',
                x: vecX, y: vecY, z: vecZ,
                line: {color: '#dc267f', width: 6},
                marker: {size: [0, 6], color: '#dc267f'},
                name: 'State',
                hoverinfo: 'x+y+z'
            };

            // Labels
            const labels = {
                type: 'scatter3d', mode: 'text',
                x: [1.2, 0, 0, 0],
                y: [0, 1.2, 0, 0],
                z: [0, 0, 1.2, -1.2],
                text: ['x', 'y', '|0⟩', '|1⟩'],
                textfont: {size: 14, color: '#94a3b8'},
                hoverinfo: 'skip'
            };

            const layout = {
                title: { text: `Qubit ${idx}`, font: {color: '#e2e8f0'} },
                margin: {l: 0, r: 0, b: 0, t: 40},
                scene: {
                    xaxis: {visible: false, range: [-1.3, 1.3]},
                    yaxis: {visible: false, range: [-1.3, 1.3]},
                    zaxis: {visible: false, range: [-1.3, 1.3]},
                    camera: { eye: {x: 1.3, y: 1.3, z: 1.3} },
                    aspectmode: 'cube'
                },
                showlegend: false,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)'
            };

            Plotly.newPlot(plotDiv.id, [sphere, equator, axes, stateVector, labels], layout, {displayModeBar: false});
        });
        
        document.getElementById('blochSpheresDisplay').style.display = 'block';
    } else {
        document.getElementById('blochSpheresDisplay').style.display = 'none';
    }
}

function copyPythonCode() {
    const code = document.getElementById('pythonCodeContent').textContent;
    navigator.clipboard.writeText(code).then(() => {
        showMessage('Python code copied to clipboard', 'success');
    }).catch(err => {
        showMessage('Failed to copy code', 'error');
    });
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

// Circuit-specific keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.getElementById('rotationPopup').style.display = 'none';
        document.getElementById('twoQubitPopup').style.display = 'none';
        pendingGateData = null;
    }
});

document.getElementById('rotationAngle')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        confirmRotation();
    }
});