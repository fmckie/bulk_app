// Epic Dashboard JavaScript - Forge of Gods
document.addEventListener('DOMContentLoaded', function() {
    // Initialize epic dashboard
    initParallaxEffects();
    initCrystalInteractions();
    initBattleCommands();
    loadNewsScrolls();
    initAchievementSystem();
    initSoundEffects();
    
    // Add entrance animation
    animateEntrance();
});

// Entrance Animation
function animateEntrance() {
    const crystals = document.querySelectorAll('.crystal-container');
    const commands = document.querySelectorAll('.battle-btn');
    const header = document.querySelector('.warrior-header');
    
    // Animate header
    header.style.opacity = '0';
    header.style.transform = 'translateY(-50px)';
    
    setTimeout(() => {
        header.style.transition = 'all 1s cubic-bezier(0.4, 0, 0.2, 1)';
        header.style.opacity = '1';
        header.style.transform = 'translateY(0)';
    }, 100);
    
    // Animate crystals
    crystals.forEach((crystal, index) => {
        crystal.style.opacity = '0';
        crystal.style.transform = 'translateY(50px) scale(0.8)';
        
        setTimeout(() => {
            crystal.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            crystal.style.opacity = '1';
            crystal.style.transform = 'translateY(0) scale(1)';
        }, 300 + (index * 150));
    });
    
    // Animate commands
    commands.forEach((btn, index) => {
        btn.style.opacity = '0';
        btn.style.transform = 'translateX(-30px)';
        
        setTimeout(() => {
            btn.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            btn.style.opacity = '1';
            btn.style.transform = 'translateX(0)';
        }, 800 + (index * 100));
    });
}

// Parallax Effects
function initParallaxEffects() {
    const parallaxLayers = document.querySelectorAll('.parallax-layer');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxLayers.forEach((layer, index) => {
            const speed = 0.5 + (index * 0.2);
            layer.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
    
    // Mouse parallax for crystals
    document.addEventListener('mousemove', (e) => {
        const crystals = document.querySelectorAll('.crystal-outer');
        const mouseX = e.clientX / window.innerWidth - 0.5;
        const mouseY = e.clientY / window.innerHeight - 0.5;
        
        crystals.forEach((crystal) => {
            const rotateX = mouseY * 20;
            const rotateY = mouseX * 20;
            crystal.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
    });
}

// Crystal Interactions
function initCrystalInteractions() {
    const crystals = document.querySelectorAll('.crystal-container');
    
    crystals.forEach(crystal => {
        crystal.addEventListener('click', function() {
            const crystalType = this.dataset.crystal;
            triggerCrystalPower(crystalType);
        });
        
        // Add hover effect
        crystal.addEventListener('mouseenter', function() {
            playSound('crystal-hover');
            this.classList.add('crystal-active');
        });
        
        crystal.addEventListener('mouseleave', function() {
            this.classList.remove('crystal-active');
        });
    });
}

// Crystal Power Effects
function triggerCrystalPower(type) {
    const effects = {
        strength: () => {
            createLavaExplosion();
            playSound('hammer-strike');
        },
        physique: () => {
            createIceShatter();
            playSound('ice-crack');
        },
        nutrition: () => {
            createEnergyBurst();
            playSound('energy-charge');
        },
        progress: () => {
            createFireBlast();
            playSound('fire-whoosh');
        }
    };
    
    if (effects[type]) {
        effects[type]();
    }
}

// Visual Effects
function createLavaExplosion() {
    const explosion = document.createElement('div');
    explosion.className = 'lava-explosion';
    explosion.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, #FF4500, transparent);
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        pointer-events: none;
        z-index: 1000;
    `;
    
    document.body.appendChild(explosion);
    
    requestAnimationFrame(() => {
        explosion.style.transition = 'all 0.8s ease-out';
        explosion.style.transform = 'translate(-50%, -50%) scale(3)';
        explosion.style.opacity = '0';
    });
    
    setTimeout(() => explosion.remove(), 800);
}

function createIceShatter() {
    for (let i = 0; i < 12; i++) {
        const shard = document.createElement('div');
        const angle = (i * 30) * Math.PI / 180;
        const distance = 200 + Math.random() * 100;
        
        shard.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 40px;
            background: linear-gradient(45deg, #00CED1, #1E90FF);
            clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 1000;
        `;
        
        document.body.appendChild(shard);
        
        requestAnimationFrame(() => {
            shard.style.transition = 'all 1s ease-out';
            shard.style.transform = `
                translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px)
                rotate(${Math.random() * 360}deg)
                scale(0)
            `;
            shard.style.opacity = '0';
        });
        
        setTimeout(() => shard.remove(), 1000);
    }
}

function createEnergyBurst() {
    const burst = document.createElement('div');
    burst.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        width: 200px;
        height: 200px;
        border: 3px solid #32CD32;
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        pointer-events: none;
        z-index: 1000;
    `;
    
    document.body.appendChild(burst);
    
    requestAnimationFrame(() => {
        burst.style.transition = 'all 0.6s ease-out';
        burst.style.transform = 'translate(-50%, -50%) scale(4)';
        burst.style.opacity = '0';
    });
    
    setTimeout(() => burst.remove(), 600);
}

function createFireBlast() {
    const particles = 20;
    for (let i = 0; i < particles; i++) {
        const particle = document.createElement('div');
        const size = 10 + Math.random() * 20;
        const angle = (Math.random() * 360) * Math.PI / 180;
        const distance = 100 + Math.random() * 200;
        
        particle.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            width: ${size}px;
            height: ${size}px;
            background: radial-gradient(circle, #FFD700, #FF4500);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 1000;
        `;
        
        document.body.appendChild(particle);
        
        requestAnimationFrame(() => {
            particle.style.transition = `all ${0.8 + Math.random() * 0.4}s ease-out`;
            particle.style.transform = `
                translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance - 50}px)
                scale(0)
            `;
            particle.style.opacity = '0';
        });
        
        setTimeout(() => particle.remove(), 1200);
    }
}

// Battle Commands
function initBattleCommands() {
    const battleBtns = document.querySelectorAll('.battle-btn');
    
    battleBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.classList.contains('news-scrolls')) {
                e.preventDefault();
                
                // Create ripple effect
                const ripple = document.createElement('div');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    background: radial-gradient(circle, rgba(255, 215, 0, 0.6), transparent);
                    border-radius: 50%;
                    transform: translate(-50%, -50%) scale(0);
                    pointer-events: none;
                `;
                
                ripple.style.left = `${e.clientX - rect.left}px`;
                ripple.style.top = `${e.clientY - rect.top}px`;
                
                this.appendChild(ripple);
                
                requestAnimationFrame(() => {
                    ripple.style.transition = 'all 0.6s ease-out';
                    ripple.style.transform = 'translate(-50%, -50%) scale(4)';
                    ripple.style.opacity = '0';
                });
                
                setTimeout(() => {
                    ripple.remove();
                    // Navigate after animation
                    if (this.onclick) {
                        this.onclick();
                    }
                }, 600);
            }
        });
    });
}

// News Scrolls Loading
async function loadNewsScrolls() {
    const container = document.getElementById('news-container');
    const loading = document.getElementById('news-loading');
    
    try {
        // Fetch news from API
        const response = await fetch('/api/news');
        const data = await response.json();
        
        if (data.articles && data.articles.length > 0) {
            container.innerHTML = data.articles.map(article => createScrollHTML(article)).join('');
            loading.style.display = 'none';
            container.classList.add('loaded');
            
            // Add click handlers
            document.querySelectorAll('.wisdom-scroll').forEach(scroll => {
                scroll.addEventListener('click', function() {
                    const url = this.dataset.url;
                    if (url) {
                        window.open(url, '_blank');
                    }
                });
            });
        } else {
            showNoScrollsMessage();
        }
    } catch (error) {
        console.error('Failed to load news:', error);
        showNoScrollsMessage();
    }
}

function createScrollHTML(article) {
    const date = new Date(article.published || Date.now()).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
    
    return `
        <div class="wisdom-scroll" data-url="${article.url || '#'}">
            <div class="scroll-seal">${article.featured ? '⭐' : '📜'}</div>
            <div class="scroll-date">${date}</div>
            <h3 class="scroll-title">${article.title || 'Ancient Wisdom'}</h3>
            <p class="scroll-excerpt">${article.excerpt || article.description || 'Click to unveil this sacred knowledge...'}</p>
            <span class="scroll-author">- MD Pilot</span>
        </div>
    `;
}

function showNoScrollsMessage() {
    const container = document.getElementById('news-container');
    const loading = document.getElementById('news-loading');
    
    loading.style.display = 'none';
    container.innerHTML = `
        <div class="no-scrolls-message" style="text-align: center; padding: 60px 20px; color: var(--marble-white);">
            <div style="font-size: 3rem; margin-bottom: 20px;">📜</div>
            <h3 style="font-family: 'Cinzel', serif; margin-bottom: 10px;">The Scrolls Are Being Prepared</h3>
            <p style="font-family: 'Crimson Text', serif; opacity: 0.8;">Ancient wisdom will be revealed soon...</p>
        </div>
    `;
    container.classList.add('loaded');
}

// Scroll to news section
function scrollToNews() {
    const newsSection = document.getElementById('news-section');
    newsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Achievement System
function initAchievementSystem() {
    // Check for achievements on load
    checkAchievements();
    
    // Listen for achievement triggers
    window.addEventListener('achievement-unlocked', (e) => {
        showAchievement(e.detail);
    });
}

function checkAchievements() {
    // This would normally check user's actual progress
    // For demo purposes, we'll randomly trigger an achievement
    if (Math.random() > 0.8) {
        setTimeout(() => {
            window.dispatchEvent(new CustomEvent('achievement-unlocked', {
                detail: {
                    title: 'STRENGTH OF ATLAS',
                    icon: '💪',
                    description: 'You lifted 100% of your bodyweight!'
                }
            }));
        }, 3000);
    }
}

function showAchievement(achievement) {
    const modal = document.getElementById('achievementModal');
    const title = modal.querySelector('.achievement-title');
    const icon = modal.querySelector('.achievement-icon');
    const desc = modal.querySelector('.achievement-desc');
    
    title.textContent = achievement.title;
    icon.textContent = achievement.icon;
    desc.textContent = achievement.description;
    
    modal.classList.add('active');
    playSound('achievement');
    
    // Create lightning effect
    createLightningEffect();
    
    setTimeout(() => {
        modal.classList.remove('active');
    }, 3000);
}

function createLightningEffect() {
    const lightning = document.createElement('div');
    lightning.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(180deg, transparent, rgba(30, 144, 255, 0.3), transparent);
        pointer-events: none;
        z-index: 999;
        opacity: 0;
    `;
    
    document.body.appendChild(lightning);
    
    // Flash effect
    for (let i = 0; i < 3; i++) {
        setTimeout(() => {
            lightning.style.opacity = '1';
            setTimeout(() => {
                lightning.style.opacity = '0';
            }, 50);
        }, i * 150);
    }
    
    setTimeout(() => lightning.remove(), 600);
}

// Sound Effects (Optional - requires audio files)
const sounds = {
    'crystal-hover': '/static/sounds/crystal-hover.mp3',
    'hammer-strike': '/static/sounds/hammer.mp3',
    'ice-crack': '/static/sounds/ice.mp3',
    'energy-charge': '/static/sounds/energy.mp3',
    'fire-whoosh': '/static/sounds/fire.mp3',
    'achievement': '/static/sounds/achievement.mp3'
};

function initSoundEffects() {
    // Preload sounds if they exist
    if ('Audio' in window) {
        Object.entries(sounds).forEach(([name, path]) => {
            const audio = new Audio();
            audio.src = path;
            audio.preload = 'auto';
            sounds[name] = audio;
        });
    }
}

function playSound(soundName) {
    // Only play if sounds are enabled and file exists
    if (sounds[soundName] && sounds[soundName].play) {
        try {
            const audio = sounds[soundName].cloneNode();
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Ignore errors if sound can't play
            });
        } catch (e) {
            // Ignore sound errors
        }
    }
}

// Performance Optimization - Throttle scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Apply throttling to scroll events
window.addEventListener('scroll', throttle(() => {
    // Parallax calculations here
}, 16));

// Progressive Enhancement - Check for WebGL support
function checkWebGLSupport() {
    try {
        const canvas = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && 
            (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch(e) {
        return false;
    }
}

// If WebGL is supported, we could add even more epic 3D effects
if (checkWebGLSupport()) {
    console.log('WebGL supported - Epic mode activated! 🔥');
    // Could initialize Three.js for 3D statues, etc.
}