document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');
    
    // Get references to our dashboard panels
    const insightBox = document.getElementById('insight-box');
    const downloadBtn = document.getElementById('download-chart-btn');
    const suggestionChips = document.querySelectorAll('.chip');
    
    let chartInstance = null;

    const sendMessage = async (prompt) => {
        if (!prompt || prompt.trim() === '') return;

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
            updateInsights(errorData);
        }
    };
    
    const updateUI = (data) => {
        updateChat(data);
        updateInsights(data);
    };

    const updateChat = (data) => {
        const loadingMessage = chatBox.querySelector('.loading');
        let chatHtml = '';

        if (data.chat_response) {
            chatHtml = `<p>${data.chat_response}</p>`;
        } else if (data.analysis && data.analysis.summary) {
            chatHtml = `<p>${data.analysis.summary}</p>`;
        } else {
            chatHtml = `<p>I've updated the insights panel with your results.</p>`;
        }

        if (loadingMessage) {
            loadingMessage.innerHTML = chatHtml;
            loadingMessage.classList.remove('loading');
        } else {
            appendChatMessage(chatHtml, 'bot-message');
        }
    };

    const updateInsights = (data) => {
        // Always clear the panel and hide the button first for a fresh slate
        insightBox.innerHTML = '';
        downloadBtn.style.display = 'none';

        if (data.sql) {
            const details = document.createElement('details');
            details.innerHTML = `<summary>Show SQL Query</summary><pre>${data.sql}</pre>`;
            insightBox.appendChild(details);
        }

        if (data.analysis && data.analysis.chart_config) {
            const canvas = document.createElement('canvas');
            canvas.id = 'botChart';
            insightBox.appendChild(canvas);
            renderChart(data.analysis.chart_config, data.results);
            downloadBtn.style.display = 'block'; // Show the download button only if a chart exists
        } else if (data.results && data.results.length > 0) {
            insightBox.innerHTML += createTable(data.results);
        } else if (!data.sql && !data.chat_response) {
             insightBox.innerHTML = '<p>No analysis to display. Ask a question!</p>';
        }
    };

    const renderChart = (config, data) => {
        const ctx = document.getElementById('botChart').getContext('2d');
        if (chartInstance) {
            chartInstance.destroy();
        }

        config.data.datasets.forEach(dataset => {
            const dataKey = dataset.data[0];
            dataset.data = data.map(row => row[dataKey]);
        });
        
        const labelKey = config.data.labels[0];
        config.data.labels = data.map(row => row[labelKey]);

        chartInstance = new Chart(ctx, config);
    };
    
    const downloadChart = () => {
        if (!chartInstance) return;
        const link = document.createElement('a');
        link.href = chartInstance.toBase64Image();
        link.download = 'ai_data_agent_chart.png';
        link.click();
    };

    const createTable = (data) => {
        const headers = Object.keys(data[0]);
        let table = '<table><thead><tr>';
        headers.forEach(h => table += `<th>${h}</th>`);
        table += '</tr></thead><tbody>';
        data.forEach(row => {
            table += '<tr>';
            headers.forEach(h => table += `<td>${row[h]}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table>';
        return table;
    };

    const appendChatMessage = (content, className, isLoading = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        if (isLoading) { messageDiv.classList.add('loading'); }

        if (className === 'bot-message') {
            messageDiv.innerHTML = content;
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            messageDiv.appendChild(p);
        }
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    sendBtn.addEventListener('click', () => sendMessage(userInput.value));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(userInput.value);
    });
    downloadBtn.addEventListener('click', downloadChart);
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.textContent;
            userInput.value = prompt;
            sendMessage(prompt);
        });
    });
});