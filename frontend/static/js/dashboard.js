document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-btn');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdVal = document.getElementById('threshold-val');
    const historyList = document.getElementById('history-list');
    const statusPulse = document.getElementById('status-pulse');
    const statusText = document.getElementById('status-text');
    const overlay = document.getElementById('overlay');
    const detectionMsg = document.getElementById('detection-msg');
    const resetHistoryBtn = document.getElementById('reset-history-btn');
    const calibProgress = document.getElementById('calib-progress');
    const stabilityStatus = document.getElementById('stability-status');
    const videoFeed = document.getElementById('video-feed');

    let isRunning = false;

    // Enhanced Status Polling
    async function pollSystemStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            // 1. Update Detection State
            const serverRunning = data.status === 'Active';
            if (serverRunning !== isRunning) {
                isRunning = serverRunning;
                updateUIState();
            }

            // 2. Update Calibration & Stability
            if (calibProgress) {
                calibProgress.style.width = `${data.calibration}%`;
            }
            
            if (stabilityStatus) {
                const isSteady = data.is_steady;
                stabilityStatus.innerText = isSteady ? 'Steady' : 'Moving';
                stabilityStatus.style.backgroundColor = isSteady ? 'rgba(76, 201, 240, 0.2)' : 'rgba(247, 37, 133, 0.2)';
                stabilityStatus.style.color = isSteady ? '#4cc9f0' : '#f72585';
            }

        } catch (err) {
            console.error('Status poll failed:', err);
        }
    }

    // Reset History Handler
    if (resetHistoryBtn) {
        resetHistoryBtn.addEventListener('click', async () => {
            if (!confirm('Clear all alert history for your presentation?')) return;
            
            try {
                await fetch('/api/reset_history', { method: 'DELETE' });
                fetchAlerts(); 
            } catch (err) {
                console.error('Failed to reset history:', err);
            }
        });
    }

    // Update UI based on state
    function updateUIState() {
        if (isRunning) {
            toggleBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Detection';
            toggleBtn.classList.remove('primary-btn');
            toggleBtn.classList.add('secondary-btn');
            statusPulse.classList.add('active');
            statusText.innerText = 'System Active';
            overlay.style.borderColor = 'var(--success)';
            detectionMsg.innerText = 'Monitoring Environment...';
            detectionMsg.style.color = 'var(--success)';
            
            videoFeed.src = '/video_feed?t=' + new Date().getTime();
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-play"></i> Start Detection';
            toggleBtn.classList.remove('secondary-btn');
            toggleBtn.classList.add('primary-btn');
            statusPulse.classList.remove('active');
            statusText.innerText = 'System Paused';
            overlay.style.borderColor = 'var(--text-dim)';
            detectionMsg.innerText = 'Detection Paused';
            detectionMsg.style.color = 'var(--text-dim)';
            
            videoFeed.src = '';
        }
    }

    // Toggle Button Handler
    toggleBtn.addEventListener('click', async () => {
        isRunning = !isRunning;
        await updateSettings();
        updateUIState();
    });

    // Slider Handler
    thresholdSlider.addEventListener('input', (e) => {
        thresholdVal.innerText = parseFloat(e.target.value).toFixed(2);
    });

    thresholdSlider.addEventListener('change', async () => {
        await updateSettings();
    });

    // Update Settings API
    async function updateSettings() {
        try {
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    threshold: parseFloat(thresholdSlider.value),
                    is_running: isRunning
                })
            });
        } catch (err) {
            console.error('Failed to update settings:', err);
        }
    }

    // Fetch Alerts
    async function fetchAlerts() {
        try {
            const res = await fetch('/api/alerts');
            const alerts = await res.json();
            
            if (alerts.length === 0) {
                historyList.innerHTML = '<div class="empty-state">No alerts logged yet.</div>';
                return;
            }

            historyList.innerHTML = alerts.map(alert => `
                <div class="history-item">
                    <div class="time">${alert.timestamp}</div>
                    <div class="details">
                        <span>${alert.type} Detected</span>
                        <span class="conf">${(parseFloat(alert.confidence) * 100).toFixed(0)}% 🔥</span>
                    </div>
                </div>
            `).join('');

            const latest = alerts[0];
            if (latest) {
                const latestTime = new Date(latest.timestamp).getTime();
                const now = new Date().getTime();
                if (now - latestTime < 10000) {
                    triggerVisualAlert();
                }
            }

        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        }
    }

    function triggerVisualAlert() {
        overlay.style.borderColor = 'var(--primary)';
        detectionMsg.innerText = '🚨 FIRE DETECTED!';
        detectionMsg.style.color = 'var(--primary)';
        
        setTimeout(() => {
            if (isRunning) {
                overlay.style.borderColor = 'var(--success)';
                detectionMsg.innerText = 'Monitoring Environment...';
                detectionMsg.style.color = 'var(--success)';
            }
        }, 5000);
    }

    // Periodic tasks
    setInterval(pollSystemStatus, 1000);
    setInterval(fetchAlerts, 1000); // Super-fast for presentation
    
    pollSystemStatus();
    fetchAlerts();
});
