// MD Pilot Next - Revolutionary Health Navigation System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all systems
    initializeNavigation();
    initializeSignalScanner();
    initializeTrajectoryPredictor();
    initializeCoPilot();
    initializeFlightRecorder();
    initializeWeatherSystem();
    initializeKnowledgeNavigator();
    initializeMissionControl();
    initializeSystemEffects();
    
    // Start system animations
    startSystemAnimations();
});

// Navigation System
function initializeNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    const panels = document.querySelectorAll('.feature-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetPanel = this.dataset.panel;
            
            // Update active states
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(targetPanel).classList.add('active');
            
            // Play transition sound (in production)
            playSystemSound('panel-switch');
            
            // Initialize panel-specific features
            initializePanelFeatures(targetPanel);
        });
    });
}

// Health Signal Scanner
function initializeSignalScanner() {
    // Animate signal points
    const signalPoints = document.querySelectorAll('.signal-point');
    
    signalPoints.forEach(point => {
        // Add hover interactions
        point.addEventListener('mouseenter', function() {
            this.style.filter = 'brightness(1.5) drop-shadow(0 0 20px currentColor)';
        });
        
        point.addEventListener('mouseleave', function() {
            this.style.filter = '';
        });
        
        // Simulate signal strength changes
        setInterval(() => {
            const randomVariation = (Math.random() - 0.5) * 10;
            const currentRadius = parseFloat(point.getAttribute('r'));
            point.setAttribute('r', Math.max(6, Math.min(14, currentRadius + randomVariation)));
        }, 2000);
    });
    
    // Radar sweep effect
    animateRadarSweep();
    
    // Update signal analysis
    updateSignalAnalysis();
}

function animateRadarSweep() {
    const sweep = document.querySelector('.radar-sweep');
    if (!sweep) return;
    
    // Add glow effect on sweep
    const radarSvg = document.querySelector('.radar-svg');
    let lastAngle = 0;
    
    setInterval(() => {
        const transform = sweep.getAttribute('transform');
        const match = transform.match(/rotate\((\d+)/);
        if (match) {
            const angle = parseFloat(match[1]);
            
            // Check for signal intersections
            checkSignalIntersections(angle);
            
            lastAngle = angle;
        }
    }, 50);
}

function checkSignalIntersections(sweepAngle) {
    const signalPoints = document.querySelectorAll('.signal-point');
    const centerX = 300;
    const centerY = 300;
    
    signalPoints.forEach(point => {
        const x = parseFloat(point.getAttribute('cx'));
        const y = parseFloat(point.getAttribute('cy'));
        
        // Calculate angle from center
        const pointAngle = Math.atan2(y - centerY, x - centerX) * (180 / Math.PI) + 90;
        const normalizedAngle = (pointAngle + 360) % 360;
        
        // Check if sweep is near signal
        if (Math.abs(normalizedAngle - sweepAngle) < 5) {
            // Pulse the signal
            point.style.filter = 'brightness(2) drop-shadow(0 0 30px currentColor)';
            setTimeout(() => {
                point.style.filter = '';
            }, 500);
        }
    });
}

function updateSignalAnalysis() {
    // Simulate real-time signal updates
    setInterval(() => {
        const signalItems = document.querySelectorAll('.signal-value');
        signalItems.forEach(item => {
            const currentValue = parseInt(item.textContent);
            const change = Math.floor((Math.random() - 0.5) * 5);
            const newValue = Math.max(0, Math.min(100, currentValue + change));
            item.textContent = newValue + '%';
            
            // Update signal status based on value
            const signalItem = item.closest('.signal-item');
            signalItem.classList.remove('optimal', 'good', 'warning', 'critical');
            
            if (newValue >= 90) signalItem.classList.add('optimal');
            else if (newValue >= 75) signalItem.classList.add('good');
            else if (newValue >= 60) signalItem.classList.add('warning');
            else signalItem.classList.add('critical');
        });
    }, 3000);
}

// Trajectory Predictor
function initializeTrajectoryPredictor() {
    const canvas = document.getElementById('trajectoryCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = 400;
    
    // Draw 3D trajectory paths
    draw3DTrajectories(ctx);
    
    // Handle time range controls
    const trajectoryControls = document.querySelectorAll('.trajectory-controls .control-btn');
    trajectoryControls.forEach(btn => {
        btn.addEventListener('click', function() {
            trajectoryControls.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Redraw with new time range
            draw3DTrajectories(ctx, this.textContent);
        });
    });
}

function draw3DTrajectories(ctx, timeRange = '30 Days') {
    // Clear canvas
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    
    const width = ctx.canvas.width;
    const height = ctx.canvas.height;
    const centerX = width / 2;
    const centerY = height - 50;
    
    // Create gradient for depth
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(0, 255, 255, 0.8)');
    gradient.addColorStop(1, 'rgba(0, 255, 255, 0.1)');
    
    // Draw grid
    drawPerspectiveGrid(ctx, centerX, centerY);
    
    // Draw trajectory paths
    const paths = [
        { type: 'current', color: '#00ffff', offset: 0 },
        { type: 'optimal', color: '#00ff88', offset: 20 },
        { type: 'risk', color: '#ff0055', offset: -20 }
    ];
    
    paths.forEach(path => {
        drawTrajectoryPath(ctx, centerX, centerY, path);
    });
    
    // Add time markers
    drawTimeMarkers(ctx, centerX, centerY, timeRange);
}

function drawPerspectiveGrid(ctx, centerX, centerY) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    
    // Vertical lines
    for (let i = -5; i <= 5; i++) {
        ctx.beginPath();
        const x = centerX + i * 40;
        ctx.moveTo(x, centerY);
        
        // Create perspective effect
        const topX = centerX + i * 20;
        ctx.lineTo(topX, 50);
        ctx.stroke();
    }
    
    // Horizontal lines
    for (let i = 0; i <= 10; i++) {
        ctx.beginPath();
        const y = centerY - i * 30;
        const perspective = i / 10;
        
        ctx.moveTo(centerX - 200 * (1 - perspective * 0.5), y);
        ctx.lineTo(centerX + 200 * (1 - perspective * 0.5), y);
        ctx.stroke();
    }
}

function drawTrajectoryPath(ctx, centerX, centerY, path) {
    ctx.strokeStyle = path.color;
    ctx.lineWidth = 3;
    ctx.shadowColor = path.color;
    ctx.shadowBlur = 20;
    
    ctx.beginPath();
    
    // Generate path points
    const points = [];
    for (let i = 0; i <= 30; i++) {
        const x = centerX + path.offset + (Math.random() - 0.5) * 20;
        const y = centerY - i * 10 - Math.sin(i * 0.2) * 20;
        
        if (path.type === 'optimal') {
            // Optimal path trends upward
            points.push({ x, y: y - i * 2 });
        } else if (path.type === 'risk') {
            // Risk path trends downward
            points.push({ x, y: y + i * 1.5 });
        } else {
            // Current path with some variation
            points.push({ x, y });
        }
    }
    
    // Draw smooth curve through points
    ctx.moveTo(points[0].x, points[0].y);
    
    for (let i = 1; i < points.length - 1; i++) {
        const cp1x = (points[i].x + points[i + 1].x) / 2;
        const cp1y = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, cp1x, cp1y);
    }
    
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Add glow particles along path
    if (path.type === 'current') {
        addPathParticles(ctx, points, path.color);
    }
}

function addPathParticles(ctx, points, color) {
    const time = Date.now() * 0.001;
    const particleIndex = Math.floor((time % 3) * 10);
    
    if (particleIndex < points.length) {
        const point = points[particleIndex];
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 30;
        
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.shadowBlur = 0;
    }
}

function drawTimeMarkers(ctx, centerX, centerY, timeRange) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = '12px JetBrains Mono';
    ctx.textAlign = 'center';
    
    const markers = timeRange === '30 Days' ? ['Now', '10d', '20d', '30d'] :
                   timeRange === '60 Days' ? ['Now', '20d', '40d', '60d'] :
                   ['Now', '30d', '60d', '90d'];
    
    markers.forEach((marker, index) => {
        const y = centerY - index * 100;
        ctx.fillText(marker, centerX - 250, y);
    });
}

// AI Health Co-Pilot
function initializeCoPilot() {
    // Chat functionality
    const chatInput = document.querySelector('.co-pilot-chat .chat-input input');
    const sendBtn = document.querySelector('.co-pilot-chat .send-btn');
    const chatMessages = document.querySelector('.co-pilot-chat .chat-messages');
    
    if (sendBtn && chatInput) {
        sendBtn.addEventListener('click', () => sendCoPilotMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCoPilotMessage();
        });
    }
    
    // Voice button
    const voiceBtn = document.querySelector('.voice-btn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            voiceBtn.classList.add('recording');
            // In production, implement actual voice recording
            setTimeout(() => {
                voiceBtn.classList.remove('recording');
                addSystemNotification('Voice input received', 'info');
            }, 2000);
        });
    }
    
    // Guidance card actions
    document.querySelectorAll('.guidance-actions .action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.guidance-card');
            card.style.opacity = '0.5';
            addSystemNotification('Action applied successfully', 'success');
        });
    });
}

function sendCoPilotMessage() {
    const input = document.querySelector('.co-pilot-chat .chat-input input');
    const messages = document.querySelector('.co-pilot-chat .chat-messages');
    
    if (!input.value.trim()) return;
    
    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';
    userMessage.innerHTML = `<p>${input.value}</p>`;
    messages.appendChild(userMessage);
    
    // Clear input
    const question = input.value;
    input.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        const aiMessage = document.createElement('div');
        aiMessage.className = 'message co-pilot';
        aiMessage.innerHTML = `<p>Analyzing your question: "${question}"</p>
            <p>Based on your current metrics, I recommend...</p>`;
        messages.appendChild(aiMessage);
        
        // Scroll to bottom
        messages.scrollTop = messages.scrollHeight;
    }, 1000);
}

// Flight Recorder
function initializeFlightRecorder() {
    const recorderControls = document.querySelectorAll('.recorder-controls .control-btn');
    
    recorderControls.forEach(btn => {
        btn.addEventListener('click', function() {
            recorderControls.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Load different time period data
            loadFlightRecorderData(this.textContent);
        });
    });
    
    // Replay button
    const replayBtn = document.querySelector('.replay-btn');
    if (replayBtn) {
        replayBtn.addEventListener('click', () => {
            startTimeReplay();
        });
    }
}

function loadFlightRecorderData(period) {
    const timeline = document.querySelector('.timeline');
    
    // Add loading effect
    timeline.classList.add('loading');
    
    setTimeout(() => {
        timeline.classList.remove('loading');
        addSystemNotification(`Flight data loaded for ${period}`, 'info');
    }, 500);
}

function startTimeReplay() {
    const events = document.querySelectorAll('.event-item');
    
    events.forEach((event, index) => {
        setTimeout(() => {
            event.style.opacity = '0';
            event.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                event.style.opacity = '1';
                event.style.transform = 'translateX(0)';
                event.style.transition = 'all 0.5s ease';
            }, 100);
        }, index * 200);
    });
    
    addSystemNotification('Time replay initiated', 'info');
}

// Health Weather System
function initializeWeatherSystem() {
    // Animate weather changes
    const weatherIcon = document.querySelector('.weather-icon');
    const weatherConditions = ['☀️', '⛅', '☁️', '🌧️', '⛈️'];
    let currentCondition = 0;
    
    // Simulate weather changes
    setInterval(() => {
        if (Math.random() > 0.7) {
            currentCondition = (currentCondition + 1) % weatherConditions.length;
            updateWeatherDisplay(weatherConditions[currentCondition]);
        }
    }, 10000);
    
    // Forecast interactions
    document.querySelectorAll('.forecast-day').forEach(day => {
        day.addEventListener('click', function() {
            showDayDetails(this);
        });
    });
}

function updateWeatherDisplay(condition) {
    const weatherIcon = document.querySelector('.weather-icon');
    const weatherTitle = document.querySelector('.weather-details h3');
    const weatherDesc = document.querySelector('.weather-desc');
    
    weatherIcon.textContent = condition;
    
    // Update description based on condition
    const descriptions = {
        '☀️': { title: 'Clear Skies', desc: 'Perfect conditions for personal records' },
        '⛅': { title: 'Partly Cloudy', desc: 'Good conditions with minor variations' },
        '☁️': { title: 'Overcast', desc: 'Moderate conditions, adjust intensity' },
        '🌧️': { title: 'Recovery Weather', desc: 'Rest day recommended' },
        '⛈️': { title: 'Storm Warning', desc: 'High stress detected, caution advised' }
    };
    
    const desc = descriptions[condition];
    if (desc) {
        weatherTitle.textContent = desc.title;
        weatherDesc.textContent = desc.desc;
    }
}

function showDayDetails(dayElement) {
    // Create modal or tooltip with detailed forecast
    const dayName = dayElement.querySelector('.day-name').textContent;
    const condition = dayElement.querySelector('.day-condition').textContent;
    
    addSystemNotification(`${dayName}: ${condition} - Click for detailed forecast`, 'info');
}

// Knowledge Navigator
function initializeKnowledgeNavigator() {
    // Article interactions
    document.querySelectorAll('.queue-item').forEach(article => {
        article.addEventListener('click', function() {
            openArticle(this);
        });
    });
    
    // Library button
    const libraryBtn = document.querySelector('.library-btn');
    if (libraryBtn) {
        libraryBtn.addEventListener('click', () => {
            openPersonalLibrary();
        });
    }
}

function openArticle(articleElement) {
    const title = articleElement.querySelector('h4').textContent;
    
    // Add reading progress
    articleElement.style.borderColor = 'var(--neon-green)';
    
    // In production, this would open the actual article
    addSystemNotification(`Opening article: ${title}`, 'success');
}

function openPersonalLibrary() {
    // In production, this would open a modal or new panel
    addSystemNotification('Personal Library: 47 articles, 23 notes', 'info');
}

// Mission Control Chat
function initializeMissionControl() {
    const chatToggle = document.querySelector('.chat-toggle');
    const chatWindow = document.querySelector('.chat-window');
    const chatClose = document.querySelector('.chat-close');
    const chatInput = document.querySelector('.chat-footer input');
    const chatSend = document.querySelector('.chat-send');
    
    if (chatToggle && chatWindow) {
        chatToggle.addEventListener('click', () => {
            chatWindow.classList.toggle('active');
            // Clear notification
            const notification = chatToggle.querySelector('.chat-notification');
            if (notification) notification.style.display = 'none';
        });
        
        chatClose.addEventListener('click', () => {
            chatWindow.classList.remove('active');
        });
        
        if (chatSend && chatInput) {
            chatSend.addEventListener('click', () => sendMissionControlMessage());
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMissionControlMessage();
            });
        }
    }
}

function sendMissionControlMessage() {
    const input = document.querySelector('.chat-footer input');
    const messages = document.querySelector('.chat-window .chat-messages');
    
    if (!input.value.trim()) return;
    
    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';
    userMessage.innerHTML = `<p>${input.value}</p>`;
    messages.appendChild(userMessage);
    
    // Clear input
    const question = input.value;
    input.value = '';
    
    // Simulate system response
    setTimeout(() => {
        const systemMessage = document.createElement('div');
        systemMessage.className = 'message system';
        
        // Generate response based on question
        let response = generateMissionControlResponse(question);
        systemMessage.innerHTML = response;
        messages.appendChild(systemMessage);
        
        // Scroll to bottom
        messages.scrollTop = messages.scrollHeight;
    }, 800);
}

function generateMissionControlResponse(question) {
    const lowerQuestion = question.toLowerCase();
    
    if (lowerQuestion.includes('protein')) {
        return `<p>Analyzing your protein intake...</p>
                <div class="decision-tree">
                    <div class="decision-node">
                        <span>Current: 165g/day</span>
                        <span>Target: 180g/day</span>
                        <span class="recommendation">↑ Increase by 15g</span>
                    </div>
                </div>
                <p>This adjustment will optimize muscle protein synthesis.</p>`;
    } else if (lowerQuestion.includes('train') || lowerQuestion.includes('workout')) {
        return `<p>Checking your recovery metrics...</p>
                <p>✅ HRV: Normal range<br>
                   ⚠️ Sleep: Slightly below optimal<br>
                   ✅ Stress: Low</p>
                <p>Recommendation: Proceed with 85% intensity today.</p>`;
    } else {
        return `<p>Processing your query: "${question}"</p>
                <p>I'm analyzing your health data to provide the best guidance. 
                   What specific aspect would you like me to focus on?</p>`;
    }
}

// System Effects
function initializeSystemEffects() {
    // Add glitch effect on hover
    document.querySelectorAll('.panel-title').forEach(title => {
        title.addEventListener('mouseenter', function() {
            this.style.animation = 'glitch 0.3s infinite';
        });
        
        title.addEventListener('mouseleave', function() {
            this.style.animation = '';
        });
    });
    
    // Create glitch animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(-2px, -2px); }
            60% { transform: translate(2px, 2px); }
            80% { transform: translate(2px, -2px); }
        }
        
        .recording {
            animation: pulse 1s infinite;
            background: var(--neon-red) !important;
        }
    `;
    document.head.appendChild(style);
}

// System Animations
function startSystemAnimations() {
    // Animate status indicator
    const statusIndicator = document.querySelector('.status-indicator');
    if (statusIndicator) {
        setInterval(() => {
            statusIndicator.style.animationDuration = Math.random() * 2 + 1 + 's';
        }, 3000);
    }
    
    // Random system notifications
    setTimeout(() => {
        addSystemNotification('All systems operational', 'success');
    }, 2000);
    
    // Periodic health checks
    setInterval(() => {
        if (Math.random() > 0.9) {
            const notifications = [
                'Pattern detected in your training data',
                'Recovery optimization available',
                'New health insight unlocked',
                'Trajectory update computed'
            ];
            const randomNotification = notifications[Math.floor(Math.random() * notifications.length)];
            addSystemNotification(randomNotification, 'info');
        }
    }, 30000);
}

// System Notifications
function addSystemNotification(message, type = 'info') {
    const container = document.querySelector('.system-notifications');
    
    const notification = document.createElement('div');
    notification.className = `system-notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.4s ease forwards';
        setTimeout(() => notification.remove(), 400);
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': '✓',
        'info': 'ℹ',
        'warning': '⚠',
        'error': '✕'
    };
    return icons[type] || 'ℹ';
}

// Panel-specific initialization
function initializePanelFeatures(panelId) {
    switch (panelId) {
        case 'signal-scanner':
            // Re-initialize scanner animations
            animateRadarSweep();
            break;
        case 'trajectory':
            // Redraw trajectory canvas
            const canvas = document.getElementById('trajectoryCanvas');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                draw3DTrajectories(ctx);
            }
            break;
        case 'co-pilot':
            // Focus chat input
            const chatInput = document.querySelector('.co-pilot-chat .chat-input input');
            if (chatInput) chatInput.focus();
            break;
        // Add more panel-specific initializations as needed
    }
}

// Utility function for sound effects (placeholder)
function playSystemSound(soundType) {
    // In production, this would play actual sound effects
    console.log(`Playing sound: ${soundType}`);
}

// Add smooth scrolling for all panels
document.querySelectorAll('.feature-panel').forEach(panel => {
    panel.addEventListener('wheel', function(e) {
        if (this.scrollHeight > this.clientHeight) {
            e.stopPropagation();
        }
    });
});

// Initialize resize handlers for responsive canvas
window.addEventListener('resize', () => {
    const canvas = document.getElementById('trajectoryCanvas');
    if (canvas && canvas.offsetParent !== null) {
        canvas.width = canvas.offsetWidth;
        const ctx = canvas.getContext('2d');
        draw3DTrajectories(ctx);
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to open Mission Control
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const chatWindow = document.querySelector('.chat-window');
        if (chatWindow) {
            chatWindow.classList.toggle('active');
            const input = chatWindow.querySelector('input');
            if (input) input.focus();
        }
    }
    
    // Escape to close chat
    if (e.key === 'Escape') {
        const chatWindow = document.querySelector('.chat-window');
        if (chatWindow) chatWindow.classList.remove('active');
    }
});

// Export functions for external use
window.MDPilotNext = {
    addNotification: addSystemNotification,
    updateSignal: updateSignalAnalysis,
    refreshTrajectory: () => {
        const canvas = document.getElementById('trajectoryCanvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            draw3DTrajectories(ctx);
        }
    }
};