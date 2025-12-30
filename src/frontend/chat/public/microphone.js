/**
 * Microphone Recording for Chainlit STT Integration
 *
 * This script adds voice recording capabilities to the Chainlit chat interface,
 * enabling users to record audio that gets transcribed by the on-prem STT service.
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        maxRecordingTime: 120000, // 2 minutes max
        audioMimeType: 'audio/webm;codecs=opus',
        fallbackMimeType: 'audio/webm',
        sttEndpoint: '/api/stt/transcribe',
        inputSelector: 'textarea[data-testid="stChatInput"], textarea.cl-chat-input, input[type="text"].cl-input',
        submitButtonSelector: 'button[data-testid="stChatSubmitButton"], button.cl-send-button',
    };

    // State
    let mediaRecorder = null;
    let audioChunks = [];
    let recordingStartTime = null;
    let recordingTimer = null;
    let micButton = null;
    let isRecording = false;

    /**
     * Initialize the microphone functionality when DOM is ready
     */
    function init() {
        // Wait for Chainlit UI to load
        const observer = new MutationObserver((mutations, obs) => {
            const inputArea = document.querySelector(CONFIG.inputSelector);
            if (inputArea && !document.getElementById('mic-record-btn')) {
                createMicrophoneButton();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });

        // Also try immediately in case UI is already loaded
        setTimeout(createMicrophoneButton, 1000);
    }

    /**
     * Create and insert the microphone button
     */
    function createMicrophoneButton() {
        // Find the input container
        const inputArea = document.querySelector(CONFIG.inputSelector);
        if (!inputArea) {
            console.log('Chainlit input area not found, will retry...');
            return;
        }

        // Check if button already exists
        if (document.getElementById('mic-record-btn')) {
            return;
        }

        // Find the input container (parent of the textarea)
        const inputContainer = inputArea.closest('div');
        if (!inputContainer) {
            return;
        }

        // Create the microphone button
        micButton = document.createElement('button');
        micButton.id = 'mic-record-btn';
        micButton.type = 'button';
        micButton.className = 'mic-button';
        micButton.setAttribute('aria-label', 'Record voice message');
        micButton.setAttribute('title', 'Click to record voice message');
        micButton.innerHTML = getMicIcon();

        micButton.addEventListener('click', toggleRecording);

        // Create container for the button
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'mic-button-container';
        buttonContainer.appendChild(micButton);

        // Insert button near the input
        inputContainer.parentElement.insertBefore(buttonContainer, inputContainer.nextSibling);

        // Add styles
        injectStyles();

        console.log('Microphone button added to Chainlit UI');
    }

    /**
     * Get the microphone icon SVG
     */
    function getMicIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" x2="12" y1="19" y2="22"></line>
        </svg>`;
    }

    /**
     * Get the stop icon SVG
     */
    function getStopIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2"></rect>
        </svg>`;
    }

    /**
     * Toggle recording state
     */
    async function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    }

    /**
     * Start audio recording
     */
    async function startRecording() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                }
            });

            // Determine supported MIME type
            let mimeType = CONFIG.audioMimeType;
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = CONFIG.fallbackMimeType;
            }
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/mp4';
            }

            // Create media recorder
            mediaRecorder = new MediaRecorder(stream, { mimeType });
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                // Process the recording
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                await processRecording(audioBlob, mimeType);
            };

            // Start recording
            mediaRecorder.start(100); // Collect data every 100ms
            isRecording = true;
            recordingStartTime = Date.now();

            // Update UI
            updateButtonState(true);
            startRecordingTimer();

            // Set max recording time
            recordingTimer = setTimeout(() => {
                if (isRecording) {
                    showNotification('Maximum recording time reached (2 minutes)', 'warning');
                    stopRecording();
                }
            }, CONFIG.maxRecordingTime);

            console.log('Recording started');

        } catch (err) {
            console.error('Failed to start recording:', err);
            showNotification('Could not access microphone. Please check permissions.', 'error');
        }
    }

    /**
     * Stop audio recording
     */
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }

        isRecording = false;
        updateButtonState(false);
        stopRecordingTimer();

        if (recordingTimer) {
            clearTimeout(recordingTimer);
            recordingTimer = null;
        }

        console.log('Recording stopped');
    }

    /**
     * Process the recorded audio
     */
    async function processRecording(audioBlob, mimeType) {
        showNotification('Transcribing...', 'info');

        try {
            // Create form data
            const formData = new FormData();

            // Determine file extension
            let extension = '.webm';
            if (mimeType.includes('mp4')) extension = '.m4a';
            else if (mimeType.includes('ogg')) extension = '.ogg';

            formData.append('audio', audioBlob, `recording${extension}`);
            formData.append('role', getUserRole());
            formData.append('language', 'nl');
            formData.append('enable_correction', 'true');
            formData.append('conservative_mode', 'true');
            formData.append('conversation_context', JSON.stringify(getConversationContext()));

            // Send to STT endpoint
            const response = await fetch(CONFIG.sttEndpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`STT request failed: ${response.status}`);
            }

            const result = await response.json();
            const text = result.corrected_text || result.draft_text || '';

            if (text) {
                // Insert transcribed text into input
                insertTextIntoInput(text, result.was_corrected);

                if (result.was_corrected) {
                    showNotification('Transcribed and corrected', 'success');
                } else {
                    showNotification('Transcribed', 'success');
                }
            } else {
                showNotification('No speech detected', 'warning');
            }

        } catch (err) {
            console.error('Transcription failed:', err);
            showNotification('Transcription failed. Please try again.', 'error');
        }
    }

    /**
     * Insert transcribed text into the Chainlit input
     */
    function insertTextIntoInput(text, wasCorrected) {
        const input = document.querySelector(CONFIG.inputSelector);
        if (!input) {
            console.error('Could not find input to insert text');
            return;
        }

        // Get current value and append
        const currentValue = input.value || '';
        const newValue = currentValue ? `${currentValue} ${text}` : text;

        // Set value (works for both textarea and input)
        input.value = newValue;

        // Trigger input event to notify Chainlit
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        // Focus the input
        input.focus();

        // Add visual indicator
        if (wasCorrected) {
            input.classList.add('stt-corrected');
            setTimeout(() => input.classList.remove('stt-corrected'), 3000);
        } else {
            input.classList.add('stt-transcribed');
            setTimeout(() => input.classList.remove('stt-transcribed'), 3000);
        }
    }

    /**
     * Update button state based on recording status
     */
    function updateButtonState(recording) {
        if (!micButton) return;

        if (recording) {
            micButton.innerHTML = getStopIcon();
            micButton.classList.add('recording');
            micButton.setAttribute('title', 'Click to stop recording');
        } else {
            micButton.innerHTML = getMicIcon();
            micButton.classList.remove('recording');
            micButton.setAttribute('title', 'Click to record voice message');
        }
    }

    /**
     * Start the recording timer display
     */
    function startRecordingTimer() {
        if (!micButton) return;

        const timerSpan = document.createElement('span');
        timerSpan.id = 'recording-timer';
        timerSpan.className = 'recording-timer';
        timerSpan.textContent = '0:00';
        micButton.parentElement.appendChild(timerSpan);

        // Update timer every second
        const updateTimer = setInterval(() => {
            if (!isRecording) {
                clearInterval(updateTimer);
                return;
            }

            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerSpan.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    /**
     * Stop the recording timer display
     */
    function stopRecordingTimer() {
        const timerSpan = document.getElementById('recording-timer');
        if (timerSpan) {
            timerSpan.remove();
        }
    }

    /**
     * Get the current user role from the page
     */
    function getUserRole() {
        // Try to find role badge
        const roleBadge = document.querySelector('.role-badge');
        if (roleBadge) {
            if (roleBadge.classList.contains('role-badge-gp')) return 'gp';
            if (roleBadge.classList.contains('role-badge-patient')) return 'patient';
            if (roleBadge.classList.contains('role-badge-admin')) return 'admin';
        }
        return 'gp'; // Default
    }

    /**
     * Get conversation context from the chat history
     */
    function getConversationContext() {
        // Try to extract recent messages from the chat
        const messages = [];
        const messageElements = document.querySelectorAll('.cl-message, [data-testid="stChatMessage"]');

        messageElements.forEach((el, index) => {
            if (index >= 5) return; // Limit to last 5 messages

            const content = el.textContent || '';
            const isUser = el.classList.contains('user') || el.getAttribute('data-author') === 'user';

            messages.push({
                role: isUser ? 'user' : 'assistant',
                content: content.substring(0, 500),
            });
        });

        return messages.reverse(); // Chronological order
    }

    /**
     * Show a notification to the user
     */
    function showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.getElementById('stt-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.id = 'stt-notification';
        notification.className = `stt-notification stt-notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Inject CSS styles for the microphone button
     */
    function injectStyles() {
        if (document.getElementById('mic-button-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'mic-button-styles';
        styles.textContent = `
            .mic-button-container {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-left: 8px;
            }

            .mic-button {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: 2px solid #1976d2;
                background-color: white;
                color: #1976d2;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .mic-button:hover {
                background-color: #e3f2fd;
                transform: scale(1.05);
            }

            .mic-button.recording {
                background-color: #f44336;
                border-color: #f44336;
                color: white;
                animation: pulse-recording 1s infinite;
            }

            @keyframes pulse-recording {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }

            .recording-timer {
                font-size: 14px;
                font-weight: 600;
                color: #f44336;
                min-width: 40px;
            }

            .stt-transcribed {
                border-color: #4caf50 !important;
                box-shadow: 0 0 4px rgba(76, 175, 80, 0.5) !important;
            }

            .stt-corrected {
                border-color: #2196f3 !important;
                box-shadow: 0 0 4px rgba(33, 150, 243, 0.5) !important;
            }

            .stt-notification {
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                z-index: 10000;
                animation: slide-up 0.3s ease;
            }

            .stt-notification-info {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 1px solid #1976d2;
            }

            .stt-notification-success {
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 1px solid #4caf50;
            }

            .stt-notification-warning {
                background-color: #fff3e0;
                color: #e65100;
                border: 1px solid #ff9800;
            }

            .stt-notification-error {
                background-color: #ffebee;
                color: #c62828;
                border: 1px solid #f44336;
            }

            .stt-notification.fade-out {
                animation: fade-out 0.3s ease forwards;
            }

            @keyframes slide-up {
                from {
                    opacity: 0;
                    transform: translateX(-50%) translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(-50%) translateY(0);
                }
            }

            @keyframes fade-out {
                to {
                    opacity: 0;
                    transform: translateX(-50%) translateY(-20px);
                }
            }

            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .mic-button {
                    background-color: #1e1e1e;
                    border-color: #90caf9;
                    color: #90caf9;
                }

                .mic-button:hover {
                    background-color: #333;
                }

                .mic-button.recording {
                    background-color: #d32f2f;
                    border-color: #d32f2f;
                    color: white;
                }

                .stt-notification-info {
                    background-color: #1e3a5f;
                    color: #90caf9;
                }

                .stt-notification-success {
                    background-color: #1b3a1b;
                    color: #81c784;
                }

                .stt-notification-warning {
                    background-color: #3d2e0a;
                    color: #ffb74d;
                }

                .stt-notification-error {
                    background-color: #3d1a1a;
                    color: #ef9a9a;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also try after a delay in case Chainlit loads dynamically
    setTimeout(init, 2000);
    setTimeout(init, 5000);

})();
