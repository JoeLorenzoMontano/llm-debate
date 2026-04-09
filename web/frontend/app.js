/**
 * LLM Debate Web UI - Frontend JavaScript
 */

class DebateClient {
    constructor() {
        this.ws = null;
        this.clientId = this.generateClientId();
        this.transcript = [];
        this.isConnected = false;
        this.debateRunning = false;

        this.init();
    }

    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }

    init() {
        // Connect to WebSocket
        this.connectWebSocket();

        // Setup event listeners
        this.setupEventListeners();

        // Setup slider updates
        this.setupSliders();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;

        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);

            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
    }

    handleMessage(message) {
        console.log('Received message:', message);

        switch (message.type) {
            case 'connected':
                console.log('Connected to server:', message.data.message);
                break;

            case 'debate_start':
                this.onDebateStart(message.data);
                break;

            case 'turn_start':
                this.onTurnStart(message.data);
                break;

            case 'turn_complete':
                this.onTurnComplete(message.data);
                break;

            case 'debate_complete':
                this.onDebateComplete(message.data);
                break;

            case 'debate_stopped':
                this.onDebateStopped(message.data);
                break;

            case 'error':
                this.onError(message.data);
                break;

            case 'pong':
                console.log('Pong received');
                break;

            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    setupEventListeners() {
        const form = document.getElementById('debate-form');
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const exportBtn = document.getElementById('export-btn');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.startDebate();
        });

        stopBtn.addEventListener('click', () => {
            this.stopDebate();
        });

        exportBtn.addEventListener('click', () => {
            this.exportTranscript();
        });
    }

    setupSliders() {
        const maxRoundsSlider = document.getElementById('max_rounds');
        const roundsValue = document.getElementById('rounds-value');
        const timeoutSlider = document.getElementById('timeout');
        const timeoutValue = document.getElementById('timeout-value');

        maxRoundsSlider.addEventListener('input', (e) => {
            roundsValue.textContent = e.target.value;
        });

        timeoutSlider.addEventListener('input', (e) => {
            timeoutValue.textContent = e.target.value;
        });
    }

    updateConnectionStatus(connected) {
        const statusDiv = document.getElementById('connection-status');
        const dot = statusDiv.querySelector('.w-3');
        const text = statusDiv.querySelector('span');

        if (connected) {
            dot.className = 'w-3 h-3 rounded-full bg-green-500';
            text.textContent = 'Connected';
            text.className = 'text-sm text-green-400';
        } else {
            dot.className = 'w-3 h-3 rounded-full bg-red-500';
            text.textContent = 'Disconnected';
            text.className = 'text-sm text-red-400';
        }
    }

    startDebate() {
        if (!this.isConnected) {
            alert('Not connected to server. Please wait...');
            return;
        }

        if (this.debateRunning) {
            alert('A debate is already running');
            return;
        }

        // Get form values
        const config = {
            topic: document.getElementById('topic').value.trim(),
            mode: document.getElementById('mode').value,
            max_rounds: parseInt(document.getElementById('max_rounds').value),
            timeout: parseInt(document.getElementById('timeout').value),
            enable_convergence: document.getElementById('enable_convergence').checked,
            enable_actions: document.getElementById('enable_actions').checked,
            convergence_threshold: 0.85
        };

        if (!config.topic) {
            alert('Please enter a debate topic');
            return;
        }

        // Clear transcript
        this.transcript = [];
        const transcriptDiv = document.getElementById('transcript');
        transcriptDiv.innerHTML = '';

        // Send start message
        this.ws.send(JSON.stringify({
            type: 'start_debate',
            config: config
        }));

        // Update UI
        this.debateRunning = true;
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('status-bar').classList.remove('hidden');
        document.getElementById('export-btn').disabled = true;
    }

    stopDebate() {
        this.ws.send(JSON.stringify({ type: 'stop_debate' }));
        this.debateRunning = false;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
    }

    onDebateStart(data) {
        console.log('Debate started:', data);

        const statusText = document.getElementById('status-text');
        statusText.textContent = `Debate Started - ${data.mode}`;

        document.getElementById('total-rounds').textContent = data.max_rounds;
        document.getElementById('current-round').textContent = '0';

        // Add header to transcript
        this.addHeaderToTranscript(data);
    }

    onTurnStart(data) {
        console.log('Turn started:', data);

        document.getElementById('current-round').textContent = data.round;
        document.getElementById('status-text').textContent = `${data.cli.toUpperCase()} is responding...`;

        // Add turn indicator
        this.addTurnIndicator(data);
    }

    onTurnComplete(data) {
        console.log('Turn completed:', data);

        // Add to transcript
        this.transcript.push(data);

        // Add to UI
        this.addTurnToTranscript(data);

        // Scroll to bottom
        this.scrollToBottom();
    }

    onDebateComplete(data) {
        console.log('Debate completed:', data);

        this.debateRunning = false;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('export-btn').disabled = false;
        document.getElementById('status-text').textContent = `Completed - ${data.end_reason}`;

        if (data.converged) {
            const badge = document.getElementById('convergence-badge');
            badge.classList.remove('hidden');
            badge.textContent = `✓ Converged: ${data.convergence_reason}`;
        }

        // Add summary
        this.addSummaryToTranscript(data);
    }

    onDebateStopped(data) {
        console.log('Debate stopped:', data);

        this.debateRunning = false;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('status-text').textContent = 'Stopped by user';
    }

    onError(data) {
        console.error('Error:', data);
        alert(`Error: ${data.message}`);

        this.debateRunning = false;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
    }

    addHeaderToTranscript(data) {
        const transcriptDiv = document.getElementById('transcript');

        const header = document.createElement('div');
        header.className = 'bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white';
        header.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="text-2xl font-bold mb-2">${this.escapeHtml(data.topic)}</h3>
                    <div class="flex items-center space-x-4 text-sm">
                        <span><i class="fas fa-chess mr-1"></i> ${this.capitalize(data.mode)} Mode</span>
                        <span><i class="fas fa-redo mr-1"></i> Up to ${data.max_rounds} rounds</span>
                        ${data.convergence_enabled ? '<span><i class="fas fa-bullseye mr-1"></i> Convergence Enabled</span>' : ''}
                    </div>
                </div>
                <i class="fas fa-comments text-5xl opacity-20"></i>
            </div>
        `;

        transcriptDiv.appendChild(header);
    }

    addTurnIndicator(data) {
        const transcriptDiv = document.getElementById('transcript');

        const indicator = document.createElement('div');
        indicator.id = `turn-${data.round}-indicator`;
        indicator.className = 'flex items-center space-x-3 text-gray-400 text-sm my-4';
        indicator.innerHTML = `
            <i class="fas fa-circle-notch fa-spin text-blue-500"></i>
            <span>Round ${data.round} - ${data.cli.toUpperCase()} is thinking...</span>
        `;

        transcriptDiv.appendChild(indicator);
        this.scrollToBottom();
    }

    addTurnToTranscript(data) {
        const transcriptDiv = document.getElementById('transcript');

        // Remove indicator
        const indicator = document.getElementById(`turn-${data.round}-indicator`);
        if (indicator) {
            indicator.remove();
        }

        const turn = document.createElement('div');
        const isClaude = data.cli.toLowerCase() === 'claude';
        const bgColor = isClaude ? 'bg-blue-900/30' : 'bg-green-900/30';
        const borderColor = isClaude ? 'border-blue-500' : 'border-green-500';
        const iconColor = isClaude ? 'text-blue-500' : 'text-green-500';
        const icon = isClaude ? 'fa-robot' : 'fa-code';

        turn.className = `${bgColor} border-l-4 ${borderColor} rounded-lg p-6 hover:shadow-lg transition duration-200`;
        turn.innerHTML = `
            <div class="flex items-start space-x-4">
                <div class="flex-shrink-0">
                    <i class="fas ${icon} ${iconColor} text-2xl"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-3">
                        <h4 class="text-lg font-bold ${iconColor}">${data.cli.toUpperCase()}</h4>
                        <span class="text-xs text-gray-400">
                            Round ${data.round} • ${data.execution_time.toFixed(2)}s
                        </span>
                    </div>
                    <div class="prose prose-invert max-w-none">
                        ${this.formatResponse(data.response)}
                    </div>
                    ${data.actions && data.actions.length > 0 ? this.formatActions(data.actions) : ''}
                </div>
            </div>
        `;

        transcriptDiv.appendChild(turn);
    }

    addSummaryToTranscript(data) {
        const transcriptDiv = document.getElementById('transcript');

        const summary = document.createElement('div');
        summary.className = 'bg-gray-800 border-2 border-gray-700 rounded-lg p-6 mt-6';
        summary.innerHTML = `
            <h3 class="text-xl font-bold mb-4 flex items-center">
                <i class="fas fa-flag-checkered mr-2 text-yellow-500"></i>
                Debate Summary
            </h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span class="text-gray-400">Total Rounds:</span>
                    <span class="font-semibold ml-2">${data.total_rounds}</span>
                </div>
                <div>
                    <span class="text-gray-400">End Reason:</span>
                    <span class="font-semibold ml-2">${data.end_reason}</span>
                </div>
                ${data.converged ? `
                <div class="col-span-2">
                    <span class="text-gray-400">Convergence:</span>
                    <span class="font-semibold ml-2 text-green-400">✓ ${data.convergence_reason}</span>
                </div>
                ` : ''}
            </div>
        `;

        transcriptDiv.appendChild(summary);
    }

    formatResponse(text) {
        // Basic markdown-like formatting
        text = this.escapeHtml(text);

        // Code blocks
        text = text.replace(/```([^`]+)```/g, '<pre class="bg-gray-900 p-3 rounded mt-2 mb-2 overflow-x-auto"><code>$1</code></pre>');

        // Inline code
        text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-900 px-2 py-1 rounded text-sm">$1</code>');

        // Bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Convert newlines to <br>
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    formatActions(actions) {
        if (!actions || actions.length === 0) return '';

        let html = '<div class="mt-4 p-3 bg-gray-900/50 rounded border border-gray-700">';
        html += '<div class="text-sm font-semibold text-yellow-400 mb-2"><i class="fas fa-bolt mr-1"></i> Actions Taken:</div>';
        html += '<ul class="text-sm space-y-1">';

        actions.forEach(action => {
            html += `<li class="text-gray-300"><i class="fas fa-check-circle text-green-500 mr-1"></i> ${action.action_type}</li>`;
        });

        html += '</ul></div>';
        return html;
    }

    exportTranscript() {
        if (this.transcript.length === 0) {
            alert('No transcript to export');
            return;
        }

        let markdown = `# LLM Debate Transcript\n\n`;
        markdown += `**Generated:** ${new Date().toISOString()}\n\n`;
        markdown += `---\n\n`;

        this.transcript.forEach(turn => {
            markdown += `## Round ${turn.round} - ${turn.cli.toUpperCase()}\n\n`;
            markdown += `${turn.response}\n\n`;
            markdown += `*Execution time: ${turn.execution_time.toFixed(2)}s*\n\n`;
            markdown += `---\n\n`;
        });

        // Download
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `debate-${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
    }

    scrollToBottom() {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.debateClient = new DebateClient();
});
