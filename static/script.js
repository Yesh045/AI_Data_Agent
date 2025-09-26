document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');
    const insightBox = document.getElementById('insight-box');
    const downloadBtn = document.getElementById('download-chart-btn');
    
    let chartInstance = null;

    const sendMessage = async () => {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        appendChatMessage(prompt, 'user-message');
        userInput.value = '';
        appendChatMessage('<p>Thinking...</p>', 'bot-message', true);

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
            const errorData = { analysis: { summary: 'Sorry, a technical error occurred. Please check the server console.' } };
            updateChat(errorData);
        }
    };
    
    const updateUI = (data) => {
        updateChat(data);
        updateInsights(data);
    };

    const updateChat = (data) => {
        const loadingMessage = chatBox.querySelector('.loading');
        let chatHtml = '';

        if (data.analysis && data.analysis.summary) {
            chatHtml += `<p>${data.analysis.summary}</p>`;
        }
        
        if (data.results && data.results.length > 0) {
            chatHtml += createTable(data.results);
        }

        if (loadingMessage) {
            if (chatHtml.trim() === '') {
                loadingMessage.innerHTML = "<p>I've processed your request. See the insights panel for details.</p>";
            } else {
                loadingMessage.innerHTML = chatHtml;
            }
            loadingMessage.classList.remove('loading');
        }
    };

    const updateInsights = (data) => {
        insightBox.innerHTML = '';
        downloadBtn.style.display = 'none';

        if (data.sql_query) {
            const details = document.createElement('details');
            details.innerHTML = `<summary>Show SQL Query</summary><pre>${data.sql_query}</pre>`;
            insightBox.appendChild(details);
        }

        if (data.analysis && data.analysis.chart_config) {
            const canvas = document.createElement('canvas');
            canvas.id = 'botChart';
            insightBox.appendChild(canvas);
            renderChart(data.analysis.chart_config, data.results);
            downloadBtn.style.display = 'block';
        } else if (!data.sql_query) {
             insightBox.innerHTML = '<p>No analysis to display for this conversation.</p>';
        }
    };

    // *** THIS IS THE NEW, SMARTER CHARTING LOGIC ***
    const renderChart = (config, data) => {
        console.log("Attempting to render chart with this config:", config);
        const ctx = document.getElementById('botChart').getContext('2d');
        if (chartInstance) {
            chartInstance.destroy();
        }

        try {
            // Robustly get the column names from the AI's blueprint
            const labelKey = config.data.labels;
            const dataKey = config.data.datasets[0].data;

            if (!labelKey || !dataKey) {
                throw new Error("AI blueprint is missing label or data key.");
            }

            // Map the actual data using the column names
            const labels = data.map(row => row[labelKey]);
            const chartData = data.map(row => row[dataKey]);

            // Update the config with the real data
            config.data.labels = labels;
            config.data.datasets[0].data = chartData;

            // Set a default color if the AI doesn't provide one
            if (!config.data.datasets[0].backgroundColor) {
                config.data.datasets[0].backgroundColor = 'rgba(0, 122, 255, 0.6)';
            }

            console.log("Final chart.js config:", config);
            chartInstance = new Chart(ctx, config);

        } catch (error) {
            console.error("Failed to build chart from AI blueprint:", error);
            insightBox.innerHTML += `<p style="color: red;">Error: I failed to plot the visualization correctly.</p>`;
        }
    };
    
    const downloadChart = () => {
        if (!chartInstance) return;
        const link = document.createElement('a');
        link.href = chartInstance.toBase64Image('image/png', 1.0);
        link.download = 'ai_data_agent_chart.png';
        link.click();
    };

    const createTable = (data) => {
        const headers = Object.keys(data[0]);
        let table = '<div class="table-wrapper">';
        table += '<table><thead><tr>';
        headers.forEach(h => table += `<th>${h}</th>`);
        table += '</tr></thead><tbody>';
        data.forEach(row => {
            table += '<tr>';
            headers.forEach(h => table += `<td>${row[h]}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table></div>';
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

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    downloadBtn.addEventListener('click', downloadChart);
});