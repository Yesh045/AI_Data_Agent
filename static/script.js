document.addEventListener('DOMContentLoaded', () => {
    // --- Get all UI elements ---
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

    // --- Dropdown Toggle ---
    dataSourceBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownContent.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.data-source-container')) {
            dropdownContent.classList.remove('show');
        }
    });

    // --- Connection Logic ---
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
            updateConnectionStatus('Backend connection failed.', 'error');
        }
    };

    const unlockApp = (schema) => {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.placeholder = 'Ask a question about your data...';
        appendChatMessage(`<p><strong>Connection successful!</strong><br>Schema: <code>${schema}</code>. How can I help?</p>`, 'bot-message');
    };

    const updateConnectionStatus = (message, statusClass) => {
        connectionStatus.textContent = `Status: ${message}`;
        connectionStatus.className = 'connection-status';
        if (statusClass) connectionStatus.classList.add(statusClass);
    };
    
    connectSampleDbBtn.addEventListener('click', () => connectDataSource('sample_db'));
    csvUploadInput.addEventListener('change', (e) => connectDataSource('file', e.target.files[0]));
    excelUploadInput.addEventListener('change', (e) => connectDataSource('file', e.target.files[0]));
    
    // --- Core Chat & Analysis Logic ---
    const sendMessage = async () => {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        appendChatMessage(prompt, 'user-message');
        userInput.value = '';
        appendChatMessage('<p>Analyzing...</p>', 'bot-message', true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error('Error:', error);
            updateChat({ analysis: { summary: 'Sorry, a technical error occurred.' } });
        }
    };
    
    const updateUI = (data) => {
        updateChat(data);
        updateResults(data);
    };

    const updateChat = (data) => {
        const loadingMessage = chatBox.querySelector('.loading');
        let chatHtml = (data.analysis && data.analysis.summary) ? `<p>${data.analysis.summary}</p>` : "<p>Analysis complete.</p>";
        if (loadingMessage) {
            loadingMessage.innerHTML = chatHtml;
            loadingMessage.classList.remove('loading');
        } else {
            appendChatMessage(chatHtml, 'bot-message');
        }
    };

    const updateResults = (data) => {
        resultsSection.innerHTML = '';
        Object.values(chartInstances).forEach(chart => chart.destroy());
        chartInstances = {};
        
        // Reset all chart placeholders
        for (let i = 1; i <= 4; i++) {
            document.getElementById(`chart${i}`).style.display = 'none';
            const placeholder = document.getElementById(`chart${i}-placeholder`);
            placeholder.style.display = 'flex';
            placeholder.textContent = 'Waiting for data...';
            document.getElementById(`chart${i}-title`).textContent = '';
            document.getElementById(`chart${i}-badge`).textContent = '';
        }
        downloadBtn.style.display = 'none';

        if (data.sql_query) {
            const details = document.createElement('details');
            details.innerHTML = `<summary>Show Generated SQL Query</summary><pre>${data.sql_query}</pre>`;
            details.style.cssText = 'background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ddd;';
            resultsSection.appendChild(details);
        }
        
        if (data.results && data.results.length > 0) {
            resultsSection.innerHTML += createTable(data.results);
        }

        if (data.analysis && data.analysis.charts && data.analysis.charts.length > 0) {
            console.log('Rendering charts:', data.analysis.charts.length);
            data.analysis.charts.slice(0, 4).forEach((chartData, index) => {
                renderChart(index + 1, chartData, data.results);
            });
            downloadBtn.style.display = 'block';
        }
    };

    // THE CRITICAL FIX: Properly aggregate data before charting
    const aggregateDataForChart = (data, labelKey, dataKey) => {
        console.log(`Aggregating data: labelKey=${labelKey}, dataKey=${dataKey}`);
        
        // If dataKey is 'count', we need to count occurrences
        if (dataKey.toLowerCase() === 'count') {
            const counts = {};
            data.forEach(row => {
                const label = row[labelKey];
                counts[label] = (counts[label] || 0) + 1;
            });
            return {
                labels: Object.keys(counts),
                values: Object.values(counts)
            };
        }
        
        // If we already have aggregated data (e.g., from GROUP BY)
        if (data.length < 50 && data.every(row => row[dataKey] !== undefined)) {
            const aggregated = {};
            data.forEach(row => {
                const label = String(row[labelKey]);
                const value = parseFloat(row[dataKey]) || 0;
                aggregated[label] = (aggregated[label] || 0) + value;
            });
            return {
                labels: Object.keys(aggregated),
                values: Object.values(aggregated)
            };
        }
        
        // For large datasets, group and sum
        const grouped = {};
        data.forEach(row => {
            const label = String(row[labelKey]);
            const value = parseFloat(row[dataKey]) || 0;
            if (!grouped[label]) {
                grouped[label] = 0;
            }
            grouped[label] += value;
        });
        
        return {
            labels: Object.keys(grouped),
            values: Object.values(grouped)
        };
    };

    const renderChart = (chartNum, chartData, data) => {
        const canvas = document.getElementById(`chart${chartNum}`);
        const placeholder = document.getElementById(`chart${chartNum}-placeholder`);
        const titleEl = document.getElementById(`chart${chartNum}-title`);
        const badgeEl = document.getElementById(`chart${chartNum}-badge`);
        
        try {
            const config = chartData.config;
            
            // Extract the column names from the config
            const labelKey = config.data.labels[0];
            const dataKey = config.data.datasets[0].data[0];
            
            console.log(`Chart ${chartNum}: labelKey=${labelKey}, dataKey=${dataKey}`);
            
            // Aggregate the data properly
            const aggregated = aggregateDataForChart(data, labelKey, dataKey);
            
            console.log(`Aggregated labels:`, aggregated.labels);
            console.log(`Aggregated values:`, aggregated.values);
            
            // Update the config with aggregated data
            config.data.labels = aggregated.labels;
            config.data.datasets[0].data = aggregated.values;
            
            // Ensure options are set
            if (!config.options) config.options = {};
            config.options.responsive = true;
            config.options.maintainAspectRatio = false;
            
            // Show the canvas and hide placeholder
            placeholder.style.display = 'none';
            canvas.style.display = 'block';
            
            // Update title and badge
            titleEl.textContent = chartData.title || `Chart ${chartNum}`;
            badgeEl.textContent = config.type.toUpperCase();
            
            // Create the chart
            chartInstances[chartNum] = new Chart(canvas.getContext('2d'), config);
            console.log(`Chart ${chartNum} rendered successfully`);
            
        } catch (error) {
            console.error(`Chart ${chartNum} Error:`, error);
            placeholder.textContent = 'Failed to render chart: ' + error.message;
            placeholder.style.display = 'flex';
            canvas.style.display = 'none';
        }
    };
    
    const createTable = (data) => {
        const headers = Object.keys(data[0]);
        let table = '<div class="table-wrapper"><table class="results-table"><thead><tr>';
        headers.forEach(h => table += `<th>${h.replace(/`/g, '')}</th>`);
        table += '</tr></thead><tbody>';
        data.slice(0, 50).forEach(row => {
            table += '<tr>';
            headers.forEach(h => table += `<td>${row[h]}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table></div>';
        if (data.length > 50) {
            table += `<p style="text-align: center; color: #888; margin-top: 10px;"><em>Showing first 50 rows of ${data.length} total rows</em></p>`;
        }
        return table;
    };

    const appendChatMessage = (content, className, isLoading = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        if (isLoading) { messageDiv.classList.add('loading'); }
        messageDiv.innerHTML = content;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };
    
    // Download all charts functionality
    downloadBtn.addEventListener('click', () => {
        Object.keys(chartInstances).forEach((chartNum) => {
            const chart = chartInstances[chartNum];
            if (chart) {
                const link = document.createElement('a');
                link.href = chart.toBase64Image('image/png', 1.0);
                link.download = `chart_${chartNum}_${Date.now()}.png`;
                link.click();
            }
        });
    });
    
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});