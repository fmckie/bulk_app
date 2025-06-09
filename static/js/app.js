// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    
    navToggle.addEventListener('click', function() {
        mobileMenu.classList.toggle('active');
        
        // Animate hamburger menu
        const spans = navToggle.querySelectorAll('span');
        spans[0].style.transform = mobileMenu.classList.contains('active') 
            ? 'rotate(45deg) translateY(6px)' : 'none';
        spans[1].style.opacity = mobileMenu.classList.contains('active') ? '0' : '1';
        spans[2].style.transform = mobileMenu.classList.contains('active') 
            ? 'rotate(-45deg) translateY(-6px)' : 'none';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!navToggle.contains(event.target) && !mobileMenu.contains(event.target)) {
            mobileMenu.classList.remove('active');
            // Reset hamburger menu
            const spans = navToggle.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        }
    });
});

// PWA Install Prompt
let deferredPrompt;
const installPrompt = document.getElementById('install-prompt');
const installBtn = document.getElementById('install-btn');
const dismissBtn = document.getElementById('dismiss-btn');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install prompt after 30 seconds
    setTimeout(() => {
        if (installPrompt && !localStorage.getItem('installDismissed')) {
            installPrompt.classList.remove('hidden');
        }
    }, 30000);
});

if (installBtn) {
    installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        }
        
        deferredPrompt = null;
        installPrompt.classList.add('hidden');
    });
}

if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
        installPrompt.classList.add('hidden');
        localStorage.setItem('installDismissed', 'true');
    });
}

// Service Worker Registration (for PWA)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered:', registration))
            .catch(error => console.log('SW registration failed:', error));
    });
}

// API Helper Functions
const API = {
    baseURL: '/api',
    
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Workout methods
    async logWorkout(workoutData) {
        return this.request('/workouts', {
            method: 'POST',
            body: JSON.stringify(workoutData)
        });
    },
    
    async getWorkouts(limit = 10) {
        return this.request(`/workouts?limit=${limit}`);
    },
    
    // Nutrition methods
    async logNutrition(nutritionData) {
        return this.request('/nutrition', {
            method: 'POST',
            body: JSON.stringify(nutritionData)
        });
    },
    
    async getNutrition(date) {
        return this.request(`/nutrition?date=${date}`);
    },
    
    // Progress methods
    async updateMeasurements(measurements) {
        return this.request('/measurements', {
            method: 'POST',
            body: JSON.stringify(measurements)
        });
    },
    
    async getProgress(days = 30) {
        return this.request(`/progress?days=${days}`);
    }
};

// Local Storage Helper (for offline support)
const Storage = {
    get(key) {
        try {
            return JSON.parse(localStorage.getItem(key));
        } catch {
            return null;
        }
    },
    
    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },
    
    remove(key) {
        localStorage.removeItem(key);
    },
    
    // Queue for offline sync
    addToQueue(type, data) {
        const queue = this.get('syncQueue') || [];
        queue.push({ type, data, timestamp: Date.now() });
        this.set('syncQueue', queue);
    },
    
    async syncQueue() {
        const queue = this.get('syncQueue') || [];
        const failed = [];
        
        for (const item of queue) {
            try {
                switch (item.type) {
                    case 'workout':
                        await API.logWorkout(item.data);
                        break;
                    case 'nutrition':
                        await API.logNutrition(item.data);
                        break;
                    case 'measurements':
                        await API.updateMeasurements(item.data);
                        break;
                }
            } catch (error) {
                failed.push(item);
            }
        }
        
        this.set('syncQueue', failed);
    }
};

// Check online status and sync
window.addEventListener('online', () => {
    console.log('Back online, syncing data...');
    Storage.syncQueue();
});

// Utility Functions
function formatDate(date) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-US', options);
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export for use in other scripts
window.KinobodyApp = {
    API,
    Storage,
    showNotification,
    formatDate
};