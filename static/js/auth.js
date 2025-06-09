// Authentication JavaScript

// Constants
let API_BASE = '/api/auth';
const PASSWORD_MIN_LENGTH = 8;

// Check if we're in demo mode
async function checkDemoMode() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        if (data.mode === 'demo') {
            API_BASE = '/api/demo/auth';
            console.log('Running in demo mode, API_BASE:', API_BASE);
        }
    } catch (error) {
        console.error('Failed to check demo mode:', error);
    }
}

// Initialize demo mode check immediately
checkDemoMode().then(() => {
    console.log('Demo mode check complete, API_BASE:', API_BASE);
});

// Password strength checker
function checkPasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= PASSWORD_MIN_LENGTH) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    
    if (strength <= 2) return 'weak';
    if (strength <= 4) return 'medium';
    return 'strong';
}

// Update password strength indicator
function updatePasswordStrength(inputId, barId) {
    const password = document.getElementById(inputId).value;
    const strengthBar = document.getElementById(barId);
    
    if (!password) {
        strengthBar.className = 'strength-bar';
        return;
    }
    
    const strength = checkPasswordStrength(password);
    strengthBar.className = `strength-bar ${strength}`;
}

// Validate email format
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Show error message
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
    }
}

// Clear error messages
function clearErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
    });
}

// Show alert message
function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i>
        <span>${message}</span>
    `;
    
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Toggle button loading state
function setButtonLoading(buttonId, loading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    const textSpan = button.querySelector('.button-text');
    const loaderSpan = button.querySelector('.button-loader');
    
    button.disabled = loading;
    if (textSpan) textSpan.style.display = loading ? 'none' : 'inline';
    if (loaderSpan) loaderSpan.style.display = loading ? 'inline' : 'none';
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    clearErrors();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // Validate
    if (!validateEmail(email)) {
        showError('emailError', 'Please enter a valid email address');
        return;
    }
    
    if (!password) {
        showError('passwordError', 'Password is required');
        return;
    }
    
    setButtonLoading('loginButton', true);
    
    try {
        const response = await fetch(`${API_BASE}/signin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password, rememberMe })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert('Login successful! Redirecting...', 'success');
            
            // Store auth state
            localStorage.setItem('isAuthenticated', 'true');
            if (data.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
            }
            
            // Redirect to dashboard or return URL
            const returnUrl = new URLSearchParams(window.location.search).get('return') || '/';
            setTimeout(() => {
                window.location.href = returnUrl;
            }, 1000);
        } else {
            showAlert(data.error || 'Invalid email or password', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setButtonLoading('loginButton', false);
    }
}

// Handle registration form submission
async function handleRegister(e) {
    e.preventDefault();
    clearErrors();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const username = document.getElementById('username').value.trim();
    const fullName = document.getElementById('fullName').value.trim();
    const bodyWeight = document.getElementById('bodyWeight').value;
    const terms = document.getElementById('terms').checked;
    
    // Validate
    let hasError = false;
    
    if (!validateEmail(email)) {
        showError('emailError', 'Please enter a valid email address');
        hasError = true;
    }
    
    if (password.length < PASSWORD_MIN_LENGTH) {
        showError('passwordError', `Password must be at least ${PASSWORD_MIN_LENGTH} characters`);
        hasError = true;
    } else if (checkPasswordStrength(password) === 'weak') {
        showError('passwordError', 'Password is too weak. Include uppercase, lowercase, and numbers');
        hasError = true;
    }
    
    if (password !== confirmPassword) {
        showError('confirmPasswordError', 'Passwords do not match');
        hasError = true;
    }
    
    if (username && username.length < 3) {
        showError('usernameError', 'Username must be at least 3 characters');
        hasError = true;
    }
    
    if (!terms) {
        showError('termsError', 'You must agree to the terms');
        hasError = true;
    }
    
    if (hasError) return;
    
    setButtonLoading('registerButton', true);
    
    try {
        const response = await fetch(`${API_BASE}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                username,
                full_name: fullName,
                body_weight: bodyWeight ? parseFloat(bodyWeight) : null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert('Account created successfully! Redirecting to login...', 'success');
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = '/login?registered=true';
            }, 2000);
        } else {
            showAlert(data.error || 'Registration failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setButtonLoading('registerButton', false);
    }
}

// Handle password reset request
async function handleResetRequest(e) {
    e.preventDefault();
    clearErrors();
    
    const email = document.getElementById('resetEmail').value.trim();
    
    if (!validateEmail(email)) {
        showError('resetEmailError', 'Please enter a valid email address');
        return;
    }
    
    setButtonLoading('resetRequestButton', true);
    
    try {
        const response = await fetch(`${API_BASE}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Show email sent confirmation
            document.getElementById('resetRequestStep').style.display = 'none';
            document.getElementById('emailSentStep').style.display = 'block';
            document.getElementById('sentEmail').textContent = email;
        } else {
            showAlert(data.error || 'Failed to send reset email. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Reset request error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setButtonLoading('resetRequestButton', false);
    }
}

// Handle new password form submission
async function handleNewPassword(e) {
    e.preventDefault();
    clearErrors();
    
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;
    const token = new URLSearchParams(window.location.search).get('token');
    
    // Validate
    let hasError = false;
    
    if (newPassword.length < PASSWORD_MIN_LENGTH) {
        showError('newPasswordError', `Password must be at least ${PASSWORD_MIN_LENGTH} characters`);
        hasError = true;
    } else if (checkPasswordStrength(newPassword) === 'weak') {
        showError('newPasswordError', 'Password is too weak. Include uppercase, lowercase, and numbers');
        hasError = true;
    }
    
    if (newPassword !== confirmNewPassword) {
        showError('confirmNewPasswordError', 'Passwords do not match');
        hasError = true;
    }
    
    if (!token) {
        showAlert('Invalid or expired reset link', 'error');
        hasError = true;
    }
    
    if (hasError) return;
    
    setButtonLoading('newPasswordButton', true);
    
    try {
        const response = await fetch(`${API_BASE}/reset-password/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token, password: newPassword })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Show success message
            document.getElementById('newPasswordStep').style.display = 'none';
            document.getElementById('successStep').style.display = 'block';
        } else {
            showAlert(data.error || 'Failed to reset password. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Password reset error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setButtonLoading('newPasswordButton', false);
    }
}

// Handle OAuth login/signup
async function handleOAuthLogin(provider) {
    try {
        const response = await fetch(`${API_BASE}/oauth/${provider}`, {
            method: 'GET'
        });
        
        const data = await response.json();
        
        if (response.ok && data.url) {
            // Redirect to OAuth provider
            window.location.href = data.url;
        } else {
            showAlert(`Failed to connect with ${provider}. Please try again.`, 'error');
        }
    } catch (error) {
        console.error('OAuth error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    }
}

// OAuth signup is the same as login for most providers
const handleOAuthSignup = handleOAuthLogin;

// Check authentication state
function checkAuthState() {
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const user = localStorage.getItem('user');
    
    return {
        isAuthenticated,
        user: user ? JSON.parse(user) : null
    };
}

// Initialize auth state on page load
function initializeAuth() {
    // Check if user just registered
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        showAlert('Registration successful! Please sign in.', 'success');
    }
    
    // Add event listeners
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        
        // Password strength indicator
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                updatePasswordStrength('password', 'strengthBar');
            });
        }
    }
    
    const resetRequestForm = document.getElementById('resetRequestForm');
    if (resetRequestForm) {
        resetRequestForm.addEventListener('submit', handleResetRequest);
    }
    
    const newPasswordForm = document.getElementById('newPasswordForm');
    if (newPasswordForm) {
        newPasswordForm.addEventListener('submit', handleNewPassword);
        
        // Password strength indicator
        const newPasswordInput = document.getElementById('newPassword');
        if (newPasswordInput) {
            newPasswordInput.addEventListener('input', () => {
                updatePasswordStrength('newPassword', 'newStrengthBar');
            });
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAuth);
} else {
    initializeAuth();
}

// Export functions for use in other scripts
window.authUtils = {
    checkAuthState,
    showAlert,
    handleOAuthLogin,
    handleOAuthSignup
};