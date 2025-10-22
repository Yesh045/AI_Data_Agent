document.addEventListener('DOMContentLoaded', () => {
    const dataSourceBtn = document.getElementById('data-source-btn');
    const dropdownContent = document.getElementById('dropdown-content');
    const connectionStatus = document.getElementById('connection-status');
    const connectSampleDbBtn = document.getElementById('connect-sample-db');
    const csvUploadInput = document.getElementById('csv-upload');
    const excelUploadInput = document.getElementById('excel-upload');
    
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');
    const resultsSection = document.getElementById('results-section');
    const downloadBtn = document.getElementById('download-charts-btn');
    
    let chartInstances = {};

    // Dropdown toggle
    dataSourceBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownContent.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.data-source-container')) {
            dropdownContent.classList.remove('show');
        }
    });

    // Connection logic
    const connectDataSource = async (sourceType, file = null) => {
        updateConnectionStatus('Connecting...', 'connecting');
        let body = { source_type: sourceType };

        if (file) {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = async () => {
                body.file_data = reader.result.split(',')[1];
                body.file_name = file.name;
                await sendConnectionRequest(body);
            };
            reader.onerror = () => updateConnectionStatus('Failed to read file.', 'error');
        } else {
            await sendConnectionRequest(body);
        }
    };

    const sendConnectionRequest = async (body) => {
        try {
            const response = await fetch('/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();

            if (data.status === 'success') {
                updateConnectionStatus(data.message, 'success');
                unlockApp(data.schema);
                dropdownContent.classList.remove('show');
            } else {
                updateConnectionStatus(data.message, 'error');
            }
        } catch (error) {
            updateConnectionStatus('Connection failed.', 'error');
        }
    };

    const unlockApp = (schema) => {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.placeholder = 'Ask anything about your data...';
        appendChatMessage(`<p><strong>✅ Connected!</strong></p><p>Ask me anything about your data.</p>`, 'bot-message');
    };

    const updateConnectionStatus = (message, statusClass) => {
        connectionStatus.textContent = `Status: ${message}`;
        connectionStatus.className = 'connection-status';
        if (statusClass) connectionStatus.classList.add(statusClass);
    };
    
    connectSampleDbBtn.addEventListener('click', () => connectDataSource('sample_db'));
    csvUploadInput.addEventListener('change', (e) => connectDataSource('file', e.target.files[0]));
    excelUploadInput.addEventListener('change', (e) => connectDataSource('file', e.target.files[0]));
    
    // Chat logic
    const sendMessage = async () => {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        appendChatMessage(prompt, 'user-message');
        userInput.value = '';
        appendChatMessage('<p>🤔 Analyzing...</p>', 'bot-message', true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt }),
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error('Error:', error);
            updateChat({ analysis: { summary: 'Sorry, an error occurred.' } });
        }
    };
    
    const updateUI = (data) => {
        updateChat(data);
        updateResults(data);
    };

    const updateChat = (data) => {
        const loadingMessage = chatBox.querySelector('.loading');
        const chatHtml = data.analysis?.summary || "Done.";
        
        if (loadingMessage) {
            loadingMessage.innerHTML = `<p>${chatHtml}</p>`;
            loadingMessage.classList.remove('loading');
        } else {
            appendChatMessage(`<p>${chatHtml}</p>`, 'bot-message');
        }
    };

    const updateResults = (data) => {
        resultsSection.innerHTML = '';
        Object.values(chartInstances).forEach(chart => chart.destroy());
        chartInstances = {};
        
        // Reset charts
        for (let i = 1; i <= 4; i++) {
            document.getElementById(`chart${i}`).style.display = 'none';
            document.getElementById(`chart${i}-placeholder`).style.display = 'flex';
            document.getElementById(`chart${i}-placeholder`).textContent = '';
            document.getElementById(`chart${i}-title`).textContent = '';
            document.getElementById(`chart${i}-badge`).textContent = '';
        }
        downloadBtn.style.display = 'none';

        // Show SQL
        if (data.sql_query) {
            const details = document.createElement('details');
            details.innerHTML = `<summary>📝 SQL Query</summary><pre>${data.sql_query}</pre>`;
            details.style.cssText = 'background:#f8f9fa;padding:15px;border-radius:8px;margin-bottom:20px;';
            resultsSection.appendChild(details);
        }
        
        // Show table
        if (data.results && data.results.length > 0) {
            resultsSection.innerHTML += createTable(data.results);
        }

        // Render charts
        if (data.analysis?.charts && data.analysis.charts.length > 0) {
            console.log(`📊 Rendering ${data.analysis.charts.length} charts`);
            data.analysis.charts.forEach((chartData, index) => {
                if (index < 4) {
                    renderSmartChart(index + 1, chartData, data.results);
                }
            });
            downloadBtn.style.display = 'block';
        }
    };

    // INTELLIGENT CHART RENDERING
    const renderSmartChart = (chartNum, chartData, rawData) => {
        const canvas = document.getElementById(`chart${chartNum}`);
        const placeholder = document.getElementById(`chart${chartNum}-placeholder`);
        const titleEl = document.getElementById(`chart${chartNum}-title`);
        const badgeEl = document.getElementById(`chart${chartNum}-badge`);
        
        try {
            const config = chartData.config;
            const xCol = config.data.labels[0];
            const yCol = config.data.datasets[0].data[0];
            const chartType = config.type;
            
            console.log(`Chart ${chartNum}: ${chartType.toUpperCase()} - ${xCol} vs ${yCol}`);
            
            // Smart data preparation
            let chartLabels, chartValues;
            
            if (yCol === 'count') {
                // Count occurrences
                const counts = {};
                rawData.forEach(row => {
                    const key = String(row[xCol] || 'Unknown');
                    counts[key] = (counts[key] || 0) + 1;
                });
                chartLabels = Object.keys(counts);
                chartValues = Object.values(counts);
            } else {
                // Aggregate by grouping
                const grouped = {};
                rawData.forEach(row => {
                    const key = String(row[xCol] || 'Unknown');
                    const val = parseFloat(row[yCol]) || 0;
                    grouped[key] = (grouped[key] || 0) + val;
                });
                chartLabels = Object.keys(grouped);
                chartValues = Object.values(grouped);
            }
            
            // Limit data points for readability
            if (chartLabels.length > 20 && chartType !== 'line') {
                const sorted = chartLabels.map((label, i) => ({label, value: chartValues[i]}))
                    .sort((a, b) => b.value - a.value)
                    .slice(0, 15);
                chartLabels = sorted.map(d => d.label);
                chartValues = sorted.map(d => d.value);
            }
            
            config.data.labels = chartLabels;
            config.data.datasets[0].data = chartValues;
            
            if (!config.options) config.options = {};
            config.options.responsive = true;
            config.options.maintainAspectRatio = false;
            
            // Show chart
            placeholder.style.display = 'none';
            canvas.style.display = 'block';
            titleEl.textContent = chartData.title;
            badgeEl.textContent = chartType.toUpperCase();
            
            chartInstances[chartNum] = new Chart(canvas.getContext('2d'), config);
            console.log(`✅ Chart ${chartNum} rendered`);
            
        } catch (error) {
            console.error(`Chart ${chartNum} error:`, error);
            placeholder.textContent = `Error: ${error.message}`;
            placeholder.style.display = 'flex';
        }
    };
    
    const createTable = (data) => {
        const headers = Object.keys(data[0]);
        let table = '<div class="table-wrapper"><table class="results-table"><thead><tr>';
        headers.forEach(h => table += `<th>${h}</th>`);
        table += '</tr></thead><tbody>';
        data.slice(0, 50).forEach(row => {
            table += '<tr>';
            headers.forEach(h => table += `<td>${row[h] ?? 'N/A'}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table></div>';
        if (data.length > 50) table += `<p class="truncation-notice">Showing 50 of ${data.length} rows</p>`;
        return table;
    };

    const appendChatMessage = (content, className, isLoading = false) => {
        const div = document.createElement('div');
        div.className = `message ${className}`;
        if (isLoading) div.classList.add('loading');
        div.innerHTML = content;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    };
    
    downloadBtn.addEventListener('click', () => {
        Object.values(chartInstances).forEach((chart, i) => {
            const link = document.createElement('a');
            link.href = chart.toBase64Image();
            link.download = `chart_${i+1}.png`;
            link.click();
        });
    });
    
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});