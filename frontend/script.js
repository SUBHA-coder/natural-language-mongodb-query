document.addEventListener('DOMContentLoaded', function() {
    const setupDbButton = document.getElementById('setup-db');
    const importCsvButton = document.getElementById('import-csv');
    const setupMessage = document.getElementById('setup-message');
    const importMessage = document.getElementById('import-message');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const queryDisplay = document.getElementById('query-display');
    
    // Setup sample database
    setupDbButton.addEventListener('click', async function() {
        setupMessage.textContent = 'Setting up sample database...';
        setupMessage.style.backgroundColor = '#e0f7fa';
        
        try {
            const response = await fetch('/api/setup', { method: 'POST' });
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON, got: ${text.substring(0, 120)}...`);
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Setup failed');
            }
            setupMessage.textContent = data.message;
            setupMessage.style.backgroundColor = '#e8f5e9';
        } catch (error) {
            console.error('Error:', error);
            setupMessage.textContent = 'Failed to setup database: ' + error.message;
            setupMessage.style.backgroundColor = '#ffebee';
        }
    });

    // Import CSVs from /csv folder
    importCsvButton.addEventListener('click', async function() {
        importMessage.textContent = 'Importing CSV files from /csv ...';
        importMessage.style.backgroundColor = '#e0f7fa';

        try {
            const response = await fetch('/api/import-csv', { method: 'POST' });
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON, got: ${text.substring(0, 120)}...`);
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'CSV import failed');
            }
            importMessage.textContent = `CSV import completed: ${JSON.stringify(data.imported)}`;
            importMessage.style.backgroundColor = '#e8f5e9';
        } catch (error) {
            console.error('Error:', error);
            importMessage.textContent = 'Failed to import CSV: ' + error.message;
            importMessage.style.backgroundColor = '#ffebee';
        }
    });
    
    // Send user query
    async function sendQuery() {
        const question = userInput.value.trim();
        if (!question) return;
        
        // Add user message to chat
        addMessage(question, 'user');
        userInput.value = '';
        
        // Show loading message
        const loadingMsgId = addMessage('Processing your question...', 'system');
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON, got: ${text.substring(0, 120)}...`);
            }
            const data = await response.json();
            
            // Remove loading message
            removeMessage(loadingMsgId);
            
            if (!response.ok || data.error) {
                addMessage(`Error: ${data.error}`, 'error');
                return;
            }
            
            // Display the MongoDB query
            if (data.query) {
                queryDisplay.textContent = JSON.stringify(data.query, null, 2);
            }
            
            // Display the result
            let resultMessage = '';
            
            if (Array.isArray(data.result)) {
                if (data.result.length === 0) {
                    resultMessage = 'No results found for your query.';
                } else {
                    resultMessage = formatResults(data.result);
                }
            } else if (typeof data.result === 'number') {
                resultMessage = `Result: ${data.result}`;
            } else {
                resultMessage = JSON.stringify(data.result, null, 2);
            }
            
            addMessage(resultMessage, 'system');
            
        } catch (error) {
            console.error('Error:', error);
            removeMessage(loadingMsgId);
            addMessage(`Error processing your query: ${error.message}`, 'error');
        }
    }
    
    // Handle send button click
    sendButton.addEventListener('click', sendQuery);
    
    // Handle Enter key press
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendQuery();
        }
    });
    
    // Add message to chat
    function addMessage(text, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        const id = Date.now().toString();
        messageElement.id = id;
        
        if (type === 'user') {
            messageElement.textContent = text;
        } else {
            if (text.startsWith('<table>')) {
                messageElement.innerHTML = text;
            } else {
                messageElement.textContent = text;
            }
        }
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }
    
    // Remove message from chat
    function removeMessage(id) {
        const messageElement = document.getElementById(id);
        if (messageElement) {
            messageElement.remove();
        }
    }
    
    // Format results as table or list
    function formatResults(results) {
        if (!results || results.length === 0) return 'No results found.';
        
        // Check if results are simple enough for a table
        if (typeof results[0] === 'object' && !Array.isArray(results[0])) {
            // Get all unique keys
            const keys = new Set();
            results.forEach(item => {
                Object.keys(item).forEach(key => keys.add(key));
            });
            
            // Create table
            let table = '<table><tr>';
            keys.forEach(key => {
                table += `<th>${key}</th>`;
            });
            table += '</tr>';
            
            // Add data rows
            results.forEach(item => {
                table += '<tr>';
                keys.forEach(key => {
                    let value = item[key] !== undefined ? item[key] : '';
                    if (typeof value === 'object') {
                        value = JSON.stringify(value);
                    }
                    table += `<td>${value}</td>`;
                });
                table += '</tr>';
            });
            
            table += '</table>';
            return table;
        } else {
            // Fallback to JSON string
            return JSON.stringify(results, null, 2);
        }
    }
});