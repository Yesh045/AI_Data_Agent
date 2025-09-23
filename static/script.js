document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');

    const sendMessage = async () => {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        // Display user message
        appendMessage(prompt, 'user-message');
        userInput.value = '';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: prompt }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Display bot response (SQL and results)
            let botHtml = `<p>Here is the SQL I generated:</p><pre>${data.sql}</pre>`;
            
            if (data.results && data.results.length > 0) {
                 botHtml += `<p>And here are the results:</p>${createTable(data.results)}`;
            } else {
                 botHtml += `<p>The query ran successfully but returned no data.</p>`;
            }

            appendMessage(botHtml, 'bot-message');

        } catch (error) {
            console.error('Error:', error);
            appendMessage('Sorry, something went wrong. Please check the console for details.', 'bot-message');
        }
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

    const appendMessage = (content, className) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
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

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});


    
