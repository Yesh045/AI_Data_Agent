// AI Analyst Dashboard - Frontend JavaScript

    let chartInstances = {};

// Initialize the dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
});

function setupEventListeners() {
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    // Send message on Enter key
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

async function initializeDashboard() {
    try {
        const response = await fetch('/init_dashboard');
        const data = await response.json();
        
        if (data.success) {
            renderDashboard(data.charts);
                    } else {
            showError('Failed to load dashboard: ' + data.error);
                }
            } catch (error) {
        console.error('Dashboard initialization error:', error);
        showError('Failed to connect to server');
    }
}

function renderDashboard(charts) {
    const loadingState = document.getElementById('loadingState');
    const chartsGrid = document.getElementById('chartsGrid');
    
    loadingState.style.display = 'none';
    chartsGrid.style.display = 'grid';
    
    chartsGrid.innerHTML = '';
    
    charts.forEach((chart, index) => {
        const chartElement = createChartElement(chart, index);
        chartsGrid.appendChild(chartElement);
    });
}

function createChartElement(chartData, index) {
    const container = document.createElement('div');
    
    if (chartData.type === 'metric') {
        container.className = 'metric-card';
        container.innerHTML = `
            <div class="metric-icon">${chartData.icon}</div>
            <div class="metric-value">${chartData.value}</div>
            <div class="metric-title">${chartData.title}</div>
        `;
    } else {
        container.className = 'chart-card';
        container.innerHTML = `
            <div class="chart-header">
                <div class="chart-icon">📊</div>
                <div class="chart-title">${chartData.title}</div>
                    </div>
            <div class="chart-content">
                <canvas id="chart-${index}"></canvas>
                </div>
            `;
        
        // Create chart after DOM element is added
        setTimeout(() => {
            createChart(`chart-${index}`, chartData);
        }, 100);
    }
    
    return container;
}

function createChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    let config;
    
    if (chartData.type === 'scatter') {
        // Scatter plot configuration
        config = {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Data Points',
                    data: chartData.labels.map((x, i) => ({
                        x: x,
                        y: chartData.data[i]
                    })),
                    backgroundColor: chartData.colors[0] || '#3b82f6',
                    borderColor: chartData.colors[0] || '#3b82f6',
                    borderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'X Axis'
                        },
                        grid: {
                            color: '#e2e8f0'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Y Axis'
                        },
                        grid: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        };
    } else {
        // Regular chart configuration
        config = {
            type: chartData.type,
                            data: {
                labels: chartData.labels || [],
                datasets: [{
                    data: chartData.data || [],
                    backgroundColor: chartData.colors || ['#3b82f6'],
                    borderColor: chartData.colors || ['#3b82f6'],
                    borderWidth: 2,
                    fill: chartData.type === 'line' ? false : true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: chartData.type === 'pie',
                        position: 'bottom'
                    }
                },
                scales: chartData.type !== 'pie' ? {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e2e8f0'
                        }
                    },
                    x: {
                        grid: {
                            color: '#e2e8f0'
                        }
                    }
                } : {}
            }
        };
    }
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    chartInstances[canvasId] = new Chart(ctx, config);
    }

    async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
    
        if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
        chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Show typing indicator
    const typingId = showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message })
        });
        
        const data = await response.json();
        hideTypingIndicator(typingId);
        
        if (data.success) {
            // Always show data table if available (this is the main response)
            if (data.data && data.data.length > 0) {
                addDataTable(data.data, data.summary || data.explanation);
            } else {
                // If no data, show the explanation
                addMessageToChat(data.explanation, 'ai');
            }
            
            // Add chart if requested - this will append to existing dashboard
            if (data.chart_data) {
                addChartToDashboard(data.chart_data);
                }
            } else {
            addMessageToChat('Sorry, I encountered an error: ' + data.error, 'ai');
            }
        } catch (error) {
        hideTypingIndicator(typingId);
            console.error('Chat error:', error);
        addMessageToChat('Sorry, I encountered a connection error. Please try again.', 'ai');
    }
}

function addMessageToChat(message, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const messageContent = document.createElement('div');
    messageContent.className = `message-${type}`;
    messageContent.textContent = message;
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

function addDataTable(data, summary) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-ai';
    
    // Add summary if provided
    if (summary) {
        const summaryDiv = document.createElement('div');
        summaryDiv.style.marginBottom = '0.5rem';
        summaryDiv.style.fontWeight = '500';
        summaryDiv.textContent = summary;
        messageContent.appendChild(summaryDiv);
    }
    
    const tableContainer = document.createElement('div');
    tableContainer.className = 'message-data';
    
    const table = document.createElement('table');
    table.className = 'data-table';
    
    // Create header
    const headerRow = document.createElement('tr');
    Object.keys(data[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    
    // Create data rows (limit to 10 rows for display)
    data.slice(0, 10).forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
    
    tableContainer.appendChild(table);
    messageContent.appendChild(tableContainer);
    
    if (data.length > 10) {
        const moreText = document.createElement('div');
        moreText.style.padding = '0.5rem';
        moreText.style.fontSize = '0.75rem';
        moreText.style.color = '#64748b';
        moreText.textContent = `... and ${data.length - 10} more rows`;
        messageContent.appendChild(moreText);
    }
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addChartToDashboard(chartData) {
    const chartsGrid = document.getElementById('chartsGrid');
    const chartElement = createChartElement(chartData, Date.now());
    chartsGrid.appendChild(chartElement);
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingId = 'typing-' + Date.now();
    
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span>AI is thinking...</span>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingId;
}

function hideTypingIndicator(typingId) {
    const typingElement = document.getElementById(typingId);
    if (typingElement) {
        typingElement.remove();
    }
}

function sendQuickMessage(message) {
    const chatInput = document.getElementById('chatInput');
    chatInput.value = message;
    sendMessage();
}

function showError(message) {
    const chatMessages = document.getElementById('chatMessages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message';
    
    const errorContent = document.createElement('div');
    errorContent.className = 'message-ai';
    errorContent.style.background = '#fef2f2';
    errorContent.style.color = '#dc2626';
    errorContent.style.border = '1px solid #fecaca';
    errorContent.textContent = message;
    
    errorDiv.appendChild(errorContent);
    chatMessages.appendChild(errorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}