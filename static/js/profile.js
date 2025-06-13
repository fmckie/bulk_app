// Profile Management JavaScript
let isEditMode = false;
let originalData = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Edit mode toggle
    document.getElementById('editProfileBtn').addEventListener('click', toggleEditMode);
    document.getElementById('saveProfileBtn').addEventListener('click', saveProfile);
    document.getElementById('cancelEditBtn').addEventListener('click', cancelEdit);
    
    // Avatar upload
    document.getElementById('avatarUpload').addEventListener('change', handleAvatarUpload);
    
    // Account actions
    document.getElementById('changePasswordBtn').addEventListener('click', showPasswordModal);
    document.getElementById('exportDataBtn').addEventListener('click', exportUserData);
    document.getElementById('deleteAccountBtn').addEventListener('click', confirmDeleteAccount);
    
    // Password form
    document.getElementById('changePasswordForm').addEventListener('submit', handlePasswordChange);
}

// Load user profile data
async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile', {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load profile');
        }
        
        const data = await response.json();
        displayProfile(data);
        originalData = JSON.parse(JSON.stringify(data)); // Deep copy
    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('Error loading profile data', 'error');
    }
}

// Display profile data
function displayProfile(data) {
    // Account info
    document.getElementById('userEmail').textContent = data.email || 'Not set';
    document.getElementById('username').textContent = data.username || 'Not set';
    document.getElementById('fullName').textContent = data.full_name || 'Not set';
    
    // Format and display member since date
    if (data.created_at) {
        const date = new Date(data.created_at);
        document.getElementById('memberSince').textContent = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    // Avatar
    if (data.avatar_url) {
        document.getElementById('userAvatar').src = data.avatar_url;
    }
    
    // Fitness metrics
    if (data.body_weight) {
        document.getElementById('bodyWeight').textContent = data.body_weight;
    }
    if (data.body_fat_percentage) {
        document.getElementById('bodyFat').textContent = data.body_fat_percentage;
    }
    if (data.program_start_date) {
        document.getElementById('programStartDate').textContent = formatDate(data.program_start_date);
    }
    if (data.activity_level) {
        document.getElementById('activityLevel').textContent = formatActivityLevel(data.activity_level);
    }
    
    // Goals
    if (data.primary_goal) {
        document.getElementById('primaryGoal').textContent = formatGoal(data.primary_goal);
    }
    if (data.target_weight) {
        document.getElementById('targetWeight').textContent = data.target_weight;
    }
    if (data.target_body_fat) {
        document.getElementById('targetBodyFat').textContent = data.target_body_fat;
    }
    
    // Set input values for edit mode
    document.getElementById('usernameInput').value = data.username || '';
    document.getElementById('fullNameInput').value = data.full_name || '';
    document.getElementById('bodyWeightInput').value = data.body_weight || '';
    document.getElementById('bodyFatInput').value = data.body_fat_percentage || '';
    document.getElementById('programStartDateInput').value = data.program_start_date || '';
    document.getElementById('activityLevelInput').value = data.activity_level || '';
    document.getElementById('primaryGoalInput').value = data.primary_goal || '';
    document.getElementById('targetWeightInput').value = data.target_weight || '';
    document.getElementById('targetBodyFatInput').value = data.target_body_fat || '';
}

// Toggle edit mode
function toggleEditMode() {
    isEditMode = !isEditMode;
    
    const sections = document.querySelectorAll('.profile-section');
    const editActions = document.querySelector('.edit-actions');
    const editBtn = document.getElementById('editProfileBtn');
    
    if (isEditMode) {
        sections.forEach(section => section.classList.add('edit-mode'));
        editActions.style.display = 'flex';
        editBtn.style.display = 'none';
    } else {
        sections.forEach(section => section.classList.remove('edit-mode'));
        editActions.style.display = 'none';
        editBtn.style.display = 'block';
    }
}

// Cancel edit mode
function cancelEdit() {
    toggleEditMode();
    displayProfile(originalData); // Restore original data
}

// Save profile changes
async function saveProfile() {
    const profileData = {
        username: document.getElementById('usernameInput').value,
        full_name: document.getElementById('fullNameInput').value,
        body_weight: parseFloat(document.getElementById('bodyWeightInput').value) || null,
        body_fat_percentage: parseFloat(document.getElementById('bodyFatInput').value) || null,
        program_start_date: document.getElementById('programStartDateInput').value || null,
        activity_level: document.getElementById('activityLevelInput').value || null,
        primary_goal: document.getElementById('primaryGoalInput').value || null,
        target_weight: parseFloat(document.getElementById('targetWeightInput').value) || null,
        target_body_fat: parseFloat(document.getElementById('targetBodyFatInput').value) || null
    };
    
    try {
        const response = await fetch('/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save profile');
        }
        
        const data = await response.json();
        showAlert('Profile updated successfully', 'success');
        displayProfile(data);
        originalData = JSON.parse(JSON.stringify(data));
        toggleEditMode();
    } catch (error) {
        console.error('Error saving profile:', error);
        showAlert('Error saving profile', 'error');
    }
}

// Handle avatar upload
async function handleAvatarUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showAlert('Please select an image file', 'error');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showAlert('Image size must be less than 5MB', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
        const response = await fetch('/api/profile/avatar', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to upload avatar');
        }
        
        const data = await response.json();
        document.getElementById('userAvatar').src = data.avatar_url;
        showAlert('Avatar updated successfully', 'success');
    } catch (error) {
        console.error('Error uploading avatar:', error);
        showAlert('Error uploading avatar', 'error');
    }
}

// Show password change modal
function showPasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'flex';
}

// Close password modal
function closePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'none';
    document.getElementById('changePasswordForm').reset();
}

// Handle password change
async function handlePasswordChange(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showAlert('New passwords do not match', 'error');
        return;
    }
    
    // Validate password strength
    if (!isPasswordValid(newPassword)) {
        showAlert('Password must be at least 8 characters with uppercase, lowercase, and numbers', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/profile/password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to change password');
        }
        
        showAlert('Password changed successfully', 'success');
        closePasswordModal();
    } catch (error) {
        console.error('Error changing password:', error);
        showAlert(error.message || 'Error changing password', 'error');
    }
}

// Export user data
async function exportUserData() {
    try {
        const response = await fetch('/api/profile/export', {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to export data');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kinobody_data_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert('Data exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting data:', error);
        showAlert('Error exporting data', 'error');
    }
}

// Confirm account deletion
function confirmDeleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        if (confirm('This will permanently delete all your data. Are you absolutely sure?')) {
            deleteAccount();
        }
    }
}

// Delete account
async function deleteAccount() {
    try {
        const response = await fetch('/api/profile', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete account');
        }
        
        showAlert('Account deleted successfully. Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    } catch (error) {
        console.error('Error deleting account:', error);
        showAlert('Error deleting account', 'error');
    }
}

// Helper functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatActivityLevel(level) {
    const levels = {
        'sedentary': 'Sedentary',
        'lightly_active': 'Lightly Active',
        'moderately_active': 'Moderately Active',
        'very_active': 'Very Active',
        'extremely_active': 'Extremely Active'
    };
    return levels[level] || level;
}

function formatGoal(goal) {
    const goals = {
        'muscle_gain': 'Muscle Gain',
        'fat_loss': 'Fat Loss',
        'strength': 'Strength Gain',
        'recomp': 'Body Recomposition',
        'maintenance': 'Maintenance'
    };
    return goals[goal] || goal;
}

function isPasswordValid(password) {
    // At least 8 characters, with uppercase, lowercase, and numbers
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return regex.test(password);
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('changePasswordModal');
    if (event.target === modal) {
        closePasswordModal();
    }
}