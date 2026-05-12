// ================= Main Application and Shared Functions =================

// Global variables
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

// ================= Utility Functions =================

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

// Auto-refresh jobs periodically
setInterval(refreshJobs, 30000); // Refresh every 30 seconds