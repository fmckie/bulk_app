// MD Pilot Dashboard - Interactive Components

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeGauges();
    initializeProgressChart();
    initializeTimeSelectors();
    initializeActionCards();
    initializeIntelligenceFeed();
    animateOnScroll();
});

// Gauge Animations
function initializeGauges() {
    const gauges = [
        { id: 'strength-metric', value: 75, max: 100, color: '#FF6B35' },
        { id: 'composition-metric', value: 62, max: 100, color: '#6BCF7F' },
        { id: 'consistency-metric', value: 94, max: 100, color: '#FFD93D' }
    ];
    
    gauges.forEach(gauge => {
        animateGauge(gauge);
    });
}

function animateGauge(config) {
    const element = document.getElementById(config.id);
    if (!element) return;
    
    const svg = element.querySelector('.gauge-svg');
    const path = svg.querySelector('path:nth-child(2)');
    
    // Animate gauge fill
    let progress = 0;
    const duration = 2000;
    const startTime = Date.now();
    
    function animate() {
        const elapsed = Date.now() - startTime;
        const t = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - t, 4);
        progress = easeOutQuart * config.value;
        
        const angle = (progress / config.max) * 160;
        const radians = (angle - 80) * (Math.PI / 180);
        const x = 100 + 80 * Math.cos(radians);
        const y = 100 + 80 * Math.sin(radians);
        
        const largeArc = angle > 180 ? 1 : 0;
        const pathData = `M 20 100 A 80 80 0 ${largeArc} 1 ${x} ${y}`;
        
        if (path) {
            path.setAttribute('d', pathData);
        }
        
        if (t < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    // Start animation when element is in view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animate();
                observer.unobserve(entry.target);
            }
        });
    });
    
    observer.observe(element);
}

// Progress Chart
function initializeProgressChart() {
    const ctx = document.getElementById('progressChart');
    if (!ctx) return;
    
    // Generate sample data
    const labels = generateDateLabels(30);
    const data = generateProgressData(30);
    
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(255, 107, 53, 0.4)');
    gradient.addColorStop(1, 'rgba(255, 107, 53, 0.05)');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Strength Progress',
                data: data,
                borderColor: '#FF6B35',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointBackgroundColor: '#FF6B35',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#FF6B35',
                    borderWidth: 1,
                    displayColors: false,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + ' lbs';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 11
                        },
                        maxRotation: 0
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + ' lbs';
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Generate sample data
function generateDateLabels(days) {
    const labels = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    return labels;
}

function generateProgressData(days) {
    const data = [];
    let baseValue = 200;
    
    for (let i = 0; i < days; i++) {
        baseValue += Math.random() * 4 - 1;
        data.push(Math.round(baseValue));
    }
    
    return data;
}

// Time Selector Functionality
function initializeTimeSelectors() {
    // Time range selectors
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const parent = this.parentElement;
            parent.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update data based on selection
            updateMetricsData(this.textContent);
        });
    });
    
    // View controls
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const parent = this.parentElement;
            parent.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update chart based on selection
            updateChartData(this.textContent);
        });
    });
}

// Action Cards
function initializeActionCards() {
    document.querySelectorAll('.action-card').forEach(card => {
        card.addEventListener('click', function() {
            const action = this.querySelector('span').textContent;
            
            // Add ripple effect
            const ripple = document.createElement('div');
            ripple.className = 'ripple';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
            
            // Handle action
            handleQuickAction(action);
        });
    });
    
    // Focus action buttons
    document.querySelectorAll('.focus-action').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const action = this.textContent;
            handleFocusAction(action);
        });
    });
}

// Intelligence Feed
function initializeIntelligenceFeed() {
    // Simulate loading articles from MD Pilot
    loadIntelArticles();
    
    // Article click handlers
    document.querySelectorAll('.intel-card').forEach(card => {
        card.addEventListener('click', function() {
            // In production, this would link to the actual article
            console.log('Opening article:', this.querySelector('h3').textContent);
        });
    });
}

async function loadIntelArticles() {
    try {
        // In production, this would fetch from the actual MD Pilot API
        const response = await fetch('/api/news');
        if (response.ok) {
            const articles = await response.json();
            updateIntelligenceFeed(articles);
        }
    } catch (error) {
        console.log('Using default articles');
    }
}

// Scroll Animations
function animateOnScroll() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all panels
    document.querySelectorAll('section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(section);
    });
}

// Utility Functions
function updateMetricsData(timeRange) {
    // Simulate data update based on time range
    console.log('Updating metrics for:', timeRange);
    
    // Re-animate gauges with new values
    initializeGauges();
}

function updateChartData(viewType) {
    // Update chart based on view type
    console.log('Updating chart for:', viewType);
    
    // Would update the chart data here
}

function handleQuickAction(action) {
    const actionMap = {
        'Log Workout': '/workout',
        'Track Nutrition': '/nutrition',
        'Body Check-in': '/measurements',
        'View Reports': '/reports'
    };
    
    const route = actionMap[action];
    if (route) {
        // In production, navigate to the route
        console.log('Navigating to:', route);
    }
}

function handleFocusAction(action) {
    const actionMap = {
        'Begin Workout': '/workout/start',
        'Track Meals': '/nutrition/add'
    };
    
    const route = actionMap[action];
    if (route) {
        // In production, navigate to the route
        console.log('Starting:', action);
    }
}

function updateIntelligenceFeed(articles) {
    // Update the intelligence feed with new articles
    const intelGrid = document.querySelector('.intel-grid');
    if (!intelGrid || !articles) return;
    
    // Update featured article
    const featured = articles.find(a => a.featured) || articles[0];
    const featuredCard = intelGrid.querySelector('.intel-card.featured');
    if (featuredCard && featured) {
        featuredCard.querySelector('h3').textContent = featured.title;
        featuredCard.querySelector('p').textContent = featured.excerpt;
    }
}

// Add ripple effect styles
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 107, 53, 0.3);
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .action-card {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Initialize profile dropdown (for future implementation)
document.querySelector('.profile-avatar').addEventListener('click', function() {
    console.log('Profile menu clicked');
    // Would show profile dropdown here
});