// Onboarding Flow JavaScript

let onboardingData = {};
let sessionId = null;
let currentWeightUnit = 'lbs';

// Initialize Step 1: Profile Setup
function initializeStep1() {
    // Get session ID from localStorage or URL params
    sessionId = localStorage.getItem('onboarding_session_id') || 
               new URLSearchParams(window.location.search).get('session');
    
    // Username validation
    const usernameInput = document.getElementById('username');
    const usernameFeedback = document.getElementById('username-feedback');
    let usernameTimeout;
    
    usernameInput.addEventListener('input', function() {
        clearTimeout(usernameTimeout);
        const username = this.value.trim();
        
        if (username.length < 3) {
            usernameFeedback.textContent = 'Username must be at least 3 characters';
            usernameFeedback.className = 'form-feedback error';
            return;
        }
        
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            usernameFeedback.textContent = 'Only letters, numbers, and underscores allowed';
            usernameFeedback.className = 'form-feedback error';
            return;
        }
        
        usernameFeedback.textContent = 'Checking availability...';
        usernameFeedback.className = 'form-feedback checking';
        
        // Debounce username check
        usernameTimeout = setTimeout(() => checkUsernameAvailability(username), 500);
    });
    
    // Weight unit toggle
    document.querySelectorAll('.unit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.unit-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentWeightUnit = this.dataset.unit;
            document.getElementById('weight_unit').value = currentWeightUnit;
            
            // Convert weight if needed
            const weightInput = document.getElementById('body_weight');
            if (weightInput.value) {
                const currentValue = parseFloat(weightInput.value);
                if (this.dataset.unit === 'kg' && currentWeightUnit === 'lbs') {
                    weightInput.value = (currentValue / 2.20462).toFixed(1);
                } else if (this.dataset.unit === 'lbs' && currentWeightUnit === 'kg') {
                    weightInput.value = (currentValue * 2.20462).toFixed(1);
                }
            }
        });
    });
    
    // Height calculation
    const heightFeet = document.getElementById('height_feet');
    const heightInches = document.getElementById('height_inches');
    const heightInput = document.getElementById('height');
    
    function calculateHeight() {
        const feet = parseInt(heightFeet.value) || 0;
        const inches = parseInt(heightInches.value) || 0;
        const totalInches = (feet * 12) + inches;
        heightInput.value = totalInches > 0 ? totalInches : '';
    }
    
    heightFeet.addEventListener('input', calculateHeight);
    heightInches.addEventListener('input', calculateHeight);
    
    // Form submission
    document.getElementById('profile-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        // Store data for later
        onboardingData = { ...onboardingData, ...data };
        
        // Show loading
        showLoading('Setting up your profile...');
        
        try {
            // Submit profile data
            const response = await fetch('/api/onboarding/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...data,
                    session_id: sessionId
                })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to update profile');
            }
            
            // Store weight unit for next step
            localStorage.setItem('weight_unit', currentWeightUnit);
            
            // Navigate to step 2
            window.location.href = '/onboarding/goals';
            
        } catch (error) {
            hideLoading();
            showError('Error: ' + error.message);
        }
    });
}

// Initialize Step 2: Goals Setup
function initializeStep2() {
    // Get weight unit from previous step
    const weightUnit = localStorage.getItem('weight_unit') || 'lbs';
    document.getElementById('target-weight-unit').textContent = weightUnit;
    
    // Load fitness goals
    loadFitnessGoals();
    
    // Form submission
    document.getElementById('goals-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        if (!data.primary_goal) {
            showError('Please select a fitness goal');
            return;
        }
        
        // Show loading
        showLoading('Finalizing your setup...');
        
        try {
            // Submit goals data
            const response = await fetch('/api/onboarding/goals', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...data,
                    session_id: sessionId
                })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to update goals');
            }
            
            // Clear onboarding data
            localStorage.removeItem('onboarding_session_id');
            localStorage.removeItem('weight_unit');
            
            // Navigate to completion
            window.location.href = '/onboarding/complete';
            
        } catch (error) {
            hideLoading();
            showError('Error: ' + error.message);
        }
    });
}

// Initialize Completion Page
async function initializeCompletion() {
    try {
        // Fetch user profile to display summary
        const response = await fetch('/api/profile');
        const profile = await response.json();
        
        if (response.ok) {
            // Update summary display
            document.getElementById('user-name').textContent = profile.username || 'Warrior';
            
            // Get goal name
            const goalsResponse = await fetch('/api/onboarding/goals-list');
            const goalsData = await goalsResponse.json();
            const goal = goalsData.goals?.find(g => g.id === profile.primary_goal);
            
            document.getElementById('summary-goal').textContent = goal?.name || profile.primary_goal || 'Not set';
            document.getElementById('summary-weight').textContent = 
                profile.body_weight ? `${profile.body_weight} ${profile.weight_unit || 'lbs'}` : 'Not set';
            document.getElementById('summary-target').textContent = 
                profile.target_weight ? `${profile.target_weight} ${profile.weight_unit || 'lbs'}` : 'Not set';
        }
    } catch (error) {
        console.error('Error loading profile summary:', error);
    }
}

// Check username availability
async function checkUsernameAvailability(username) {
    const feedback = document.getElementById('username-feedback');
    
    try {
        const response = await fetch('/api/onboarding/check-username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });
        
        const result = await response.json();
        
        if (result.available) {
            feedback.textContent = 'Username is available!';
            feedback.className = 'form-feedback success';
        } else {
            feedback.textContent = result.message || 'Username is not available';
            feedback.className = 'form-feedback error';
        }
    } catch (error) {
        feedback.textContent = 'Error checking username';
        feedback.className = 'form-feedback error';
    }
}

// Load fitness goals
async function loadFitnessGoals() {
    try {
        const response = await fetch('/api/onboarding/goals-list');
        const data = await response.json();
        
        const goalsContainer = document.getElementById('goal-cards');
        goalsContainer.innerHTML = '';
        
        data.goals.forEach(goal => {
            const card = createGoalCard(goal);
            goalsContainer.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading goals:', error);
        // Show default goals
        const defaultGoals = [
            { id: 'muscle_building', name: 'Build Muscle', description: 'Focus on gaining lean muscle mass', icon: '💪' },
            { id: 'weight_loss', name: 'Lose Weight', description: 'Focus on fat loss', icon: '🔥' },
            { id: 'body_recomposition', name: 'Body Recomposition', description: 'Build muscle and lose fat', icon: '⚡' }
        ];
        
        const goalsContainer = document.getElementById('goal-cards');
        defaultGoals.forEach(goal => {
            const card = createGoalCard(goal);
            goalsContainer.appendChild(card);
        });
    }
}

// Create goal card element
function createGoalCard(goal) {
    const card = document.createElement('div');
    card.className = 'goal-card';
    card.dataset.goal = goal.id;
    
    card.innerHTML = `
        <div class="goal-icon">${goal.icon || '🎯'}</div>
        <h3>${goal.name}</h3>
        <p>${goal.description}</p>
    `;
    
    card.addEventListener('click', function() {
        // Remove active class from all cards
        document.querySelectorAll('.goal-card').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked card
        this.classList.add('active');
        
        // Set hidden input value
        document.getElementById('primary_goal').value = goal.id;
        
        // Show target metrics
        document.getElementById('target-metrics').style.display = 'block';
        
        // Scroll to metrics
        document.getElementById('target-metrics').scrollIntoView({ behavior: 'smooth' });
    });
    
    return card;
}

// Skip onboarding
async function skipOnboarding() {
    if (confirm('Are you sure you want to skip profile setup? You can complete it later from your profile page.')) {
        try {
            const response = await fetch('/api/onboarding/skip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            if (response.ok) {
                window.location.href = '/dashboard';
            }
        } catch (error) {
            console.error('Error skipping onboarding:', error);
            window.location.href = '/dashboard';
        }
    }
}

// Go back to previous step
function goBack() {
    window.location.href = '/onboarding/profile';
}

// Show loading modal
function showLoading(message) {
    const modal = document.getElementById('loading-modal');
    if (modal) {
        modal.querySelector('p').textContent = message || 'Loading...';
        modal.style.display = 'flex';
    }
}

// Hide loading modal
function hideLoading() {
    const modal = document.getElementById('loading-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Show error message
function showError(message) {
    // Create error toast
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}