// Meal Prep Planner JavaScript

// Global variables
let currentMealPlan = null;
let currentDay = 1;
let savedPlans = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeMealPrep();
    loadSavedPlans();
    setupEventListeners();
});

// Initialize meal prep features
function initializeMealPrep() {
    // Check if user is logged in
    checkAuthStatus();
    
    // Set up form defaults
    const budgetInput = document.getElementById('budget');
    if (budgetInput) {
        budgetInput.value = localStorage.getItem('mealPrepBudget') || 150;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    const form = document.getElementById('mealPlanForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // Day tabs
    document.querySelectorAll('.day-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            switchDay(parseInt(this.dataset.day));
        });
    });
    
    // Action buttons
    const saveBtn = document.getElementById('savePlanBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveMealPlan);
    }
    
    const exportBtn = document.getElementById('exportPlanBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportMealPlan);
    }
    
    const regenerateBtn = document.getElementById('regenerateBtn');
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', regenerateMealPlan);
    }
    
    const printListBtn = document.getElementById('printListBtn');
    if (printListBtn) {
        printListBtn.addEventListener('click', printShoppingList);
    }
    
    // AI Chat
    const aiFab = document.getElementById('aiFab');
    const aiChat = document.getElementById('aiChat');
    const chatClose = document.getElementById('chatClose');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    
    if (aiFab) {
        aiFab.addEventListener('click', () => {
            aiChat.style.display = aiChat.style.display === 'none' ? 'flex' : 'none';
            if (aiChat.style.display === 'flex') {
                chatInput.focus();
            }
        });
    }
    
    if (chatClose) {
        chatClose.addEventListener('click', () => {
            aiChat.style.display = 'none';
        });
    }
    
    if (chatSend) {
        chatSend.addEventListener('click', sendChatMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    // Recipe modal
    const modal = document.getElementById('recipeModal');
    const closeModal = modal.querySelector('.close');
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Collect form data
    const formData = new FormData(e.target);
    const dietaryRequirements = formData.getAll('dietary_requirements');
    
    const requestData = {
        dietary_requirements: dietaryRequirements,
        budget: parseFloat(formData.get('budget')),
        use_ai: document.getElementById('aiAssistant').checked
    };
    
    // Save preferences
    localStorage.setItem('mealPrepBudget', requestData.budget);
    
    // Show loading state
    showLoadingState();
    
    try {
        // Generate meal plan - using test endpoint
        const response = await fetch('/api/meal-prep/test-generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.status === 401) {
            showMessage('Please log in to generate meal plans', 'error');
            window.location.href = '/login';
            return;
        }
        
        const data = await response.json();
        
        if (response.ok) {
            currentMealPlan = data;
            displayMealPlan(data);
            hideLoadingState();
            showMessage('Meal plan generated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to generate meal plan');
        }
    } catch (error) {
        hideLoadingState();
        showMessage(error.message, 'error');
        console.error('Error generating meal plan:', error);
    }
}

// Show loading state
function showLoadingState() {
    document.getElementById('generationSection').style.display = 'none';
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('mealPlanSection').style.display = 'none';
    
    // Cycle through loading messages
    const messages = [
        'Analyzing nutritional requirements...',
        'Optimizing for your budget and preferences...',
        'Selecting recipes from thousands of options...',
        'Calculating precise macronutrients...',
        'Creating your shopping list...',
        'Almost done...'
    ];
    
    let messageIndex = 0;
    const messageElement = document.getElementById('loadingMessage');
    
    const messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % messages.length;
        messageElement.textContent = messages[messageIndex];
    }, 2000);
    
    // Store interval ID to clear later
    window.loadingMessageInterval = messageInterval;
}

// Hide loading state
function hideLoadingState() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('mealPlanSection').style.display = 'block';
    
    // Clear loading message interval
    if (window.loadingMessageInterval) {
        clearInterval(window.loadingMessageInterval);
    }
}

// Display generated meal plan
function displayMealPlan(mealPlanData) {
    // Update nutritional summary
    updateNutritionalSummary(mealPlanData);
    
    // Display first day by default
    switchDay(1);
    
    // Display shopping list
    displayShoppingList(mealPlanData.shopping_list);
    
    // Display prep schedule
    displayPrepSchedule(mealPlanData.meal_prep_schedule);
}

// Update nutritional summary
function updateNutritionalSummary(mealPlanData) {
    let totalCalories = 0;
    let totalProtein = 0;
    let trainingDayCalories = 0;
    let restDayCalories = 0;
    let trainingDays = 0;
    let restDays = 0;
    
    // Calculate averages
    for (let i = 1; i <= 7; i++) {
        const day = mealPlanData.meal_plan[`day_${i}`];
        if (day) {
            totalCalories += day.target_calories;
            totalProtein += day.target_protein;
            
            if (day.is_training_day) {
                trainingDayCalories += day.target_calories;
                trainingDays++;
            } else {
                restDayCalories += day.target_calories;
                restDays++;
            }
        }
    }
    
    // Update UI
    document.getElementById('avgCalories').textContent = Math.round(totalCalories / 7);
    document.getElementById('avgProtein').textContent = Math.round(totalProtein / 7) + 'g';
    document.getElementById('trainingCalories').textContent = 
        trainingDays > 0 ? Math.round(trainingDayCalories / trainingDays) : '-';
    document.getElementById('restCalories').textContent = 
        restDays > 0 ? Math.round(restDayCalories / restDays) : '-';
}

// Switch between days
function switchDay(dayNumber) {
    currentDay = dayNumber;
    
    // Update tab styling
    document.querySelectorAll('.day-tab').forEach(tab => {
        tab.classList.toggle('active', parseInt(tab.dataset.day) === dayNumber);
    });
    
    // Display day content
    displayDayContent(dayNumber);
}

// Display content for a specific day
function displayDayContent(dayNumber) {
    if (!currentMealPlan) return;
    
    const dayData = currentMealPlan.meal_plan[`day_${dayNumber}`];
    if (!dayData) return;
    
    const dayContent = document.getElementById('dayContent');
    
    // Format date
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + dayNumber - 1);
    const dateStr = startDate.toLocaleDateString('en-US', { 
        weekday: 'long', 
        month: 'short', 
        day: 'numeric' 
    });
    
    let html = `
        <div class="day-header">
            <div class="day-info">
                <h3>${dateStr}</h3>
                <span class="training-badge ${dayData.is_training_day ? '' : 'rest-day'}">
                    ${dayData.is_training_day ? 'Training Day' : 'Rest Day'}
                </span>
            </div>
            <div class="day-macros">
                <div class="macro-item">
                    <span class="value">${dayData.target_calories}</span>
                    <span class="label">Calories</span>
                </div>
                <div class="macro-item">
                    <span class="value">${dayData.target_protein}g</span>
                    <span class="label">Protein</span>
                </div>
                <div class="macro-item">
                    <span class="value">${dayData.target_carbs}g</span>
                    <span class="label">Carbs</span>
                </div>
                <div class="macro-item">
                    <span class="value">${dayData.target_fats}g</span>
                    <span class="label">Fats</span>
                </div>
            </div>
        </div>
        
        <div class="meals-container">
    `;
    
    // Add meals
    for (const [mealKey, meal] of Object.entries(dayData.meals)) {
        if (typeof meal === 'object' && meal.name) {
            html += createMealCard(meal, dayNumber, mealKey);
        }
    }
    
    html += '</div>';
    
    dayContent.innerHTML = html;
    
    // Add meal card click handlers
    dayContent.querySelectorAll('.meal-card').forEach(card => {
        card.addEventListener('click', function() {
            const mealKey = this.dataset.mealKey;
            showRecipeDetails(dayData.meals[mealKey]);
        });
    });
}

// Create meal card HTML
function createMealCard(meal, dayNumber, mealKey) {
    return `
        <div class="meal-card" data-day="${dayNumber}" data-meal-key="${mealKey}">
            <div class="meal-header">
                <div>
                    <div class="meal-time">${meal.time}</div>
                    <h4 class="meal-title">${meal.name}</h4>
                    <div class="meal-macros">
                        <span>${meal.protein_g}g protein</span>
                        <span>${meal.carbs_g}g carbs</span>
                        <span>${meal.fats_g}g fats</span>
                    </div>
                </div>
                <div class="meal-calories">${meal.calories} cal</div>
            </div>
            <p class="meal-description">${meal.description || ''}</p>
            <div class="meal-actions">
                <button class="btn btn-sm" onclick="event.stopPropagation(); customizeMeal(${dayNumber}, '${mealKey}')">
                    <i class="fas fa-edit"></i> Customize
                </button>
                <button class="btn btn-sm" onclick="event.stopPropagation(); swapMeal(${dayNumber}, '${mealKey}')">
                    <i class="fas fa-exchange-alt"></i> Swap
                </button>
                <button class="btn btn-sm btn-recipe" onclick="event.stopPropagation(); showRecipeDetails(currentMealPlan.meal_plan.day_${dayNumber}.meals['${mealKey}'])">
                    <i class="fas fa-book"></i> Recipe
                </button>
            </div>
        </div>
    `;
}

// Show recipe details in modal
function showRecipeDetails(meal) {
    const modal = document.getElementById('recipeModal');
    const details = document.getElementById('recipeDetails');
    
    let ingredientsHtml = '<ul>';
    meal.ingredients.forEach(ing => {
        ingredientsHtml += `<li>${ing.amount} ${ing.unit} ${ing.name}</li>`;
    });
    ingredientsHtml += '</ul>';
    
    let instructionsHtml = '<ol>';
    meal.instructions.forEach(instruction => {
        instructionsHtml += `<li>${instruction}</li>`;
    });
    instructionsHtml += '</ol>';
    
    details.innerHTML = `
        <div class="recipe-header">
            <h2>${meal.name}</h2>
            <button class="btn btn-sm btn-print" onclick="printRecipe('${meal.name}')">
                <i class="fas fa-print"></i> Print Recipe
            </button>
        </div>
        <div class="recipe-stats">
            <span><i class="fas fa-clock"></i> Prep: ${meal.prep_time || 15} min</span>
            <span><i class="fas fa-fire"></i> Cook: ${meal.cook_time || 30} min</span>
            <span><i class="fas fa-utensils"></i> Servings: ${meal.servings || 1}</span>
        </div>
        <div class="recipe-nutrition">
            <h3>Nutrition per Serving</h3>
            <div class="nutrition-grid">
                <div>Calories: ${meal.calories}</div>
                <div>Protein: ${meal.protein_g}g</div>
                <div>Carbs: ${meal.carbs_g}g</div>
                <div>Fats: ${meal.fats_g}g</div>
                <div>Fiber: ${meal.fiber_g || 0}g</div>
            </div>
            ${meal.usda_verified ? '<span class="usda-badge"><i class="fas fa-check-circle"></i> USDA Verified</span>' : ''}
        </div>
        <div class="recipe-ingredients">
            <h3>Ingredients</h3>
            ${ingredientsHtml}
        </div>
        <div class="recipe-instructions">
            <h3>Instructions</h3>
            ${instructionsHtml}
        </div>
        ${meal.meal_prep_tips ? `
            <div class="recipe-tips">
                <h3>Meal Prep Tips</h3>
                <p>${meal.meal_prep_tips}</p>
            </div>
        ` : ''}
    `;
    
    modal.style.display = 'flex';
}

// Display shopping list
function displayShoppingList(shoppingList) {
    if (!shoppingList) return;
    
    const container = document.getElementById('shoppingList');
    let html = '';
    
    // Organize by category
    const categories = ['proteins', 'carbs', 'vegetables', 'fruits', 'dairy', 'pantry', 'spices', 'fats'];
    
    categories.forEach(category => {
        if (shoppingList[category] && shoppingList[category].length > 0) {
            html += `
                <div class="category-section">
                    <h4 class="category-title">${category.charAt(0).toUpperCase() + category.slice(1)}</h4>
                    <div class="shopping-items">
            `;
            
            shoppingList[category].forEach(item => {
                html += `
                    <div class="shopping-item">
                        <span class="item-name">${item.name}</span>
                        <div class="item-details">
                            <span class="item-quantity">${item.amount} ${item.unit}</span>
                            ${item.estimated_cost ? `<span class="item-cost">$${item.estimated_cost.toFixed(2)}</span>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }
    });
    
    container.innerHTML = html;
    
    // Update total cost
    const totalCost = currentMealPlan.total_estimated_cost || 0;
    document.getElementById('totalCost').textContent = `$${totalCost.toFixed(2)}`;
}

// Display prep schedule
function displayPrepSchedule(schedule) {
    if (!schedule) return;
    
    const container = document.getElementById('prepSchedule');
    let html = '';
    
    Object.entries(schedule).forEach(([day, tasks]) => {
        html += `
            <div class="schedule-day">
                <h4>${day.charAt(0).toUpperCase() + day.slice(1)}</h4>
                <div class="schedule-tasks">
        `;
        
        tasks.forEach(task => {
            html += `<div class="schedule-task">${task}</div>`;
        });
        
        html += '</div></div>';
    });
    
    container.innerHTML = html;
}

// Save meal plan
async function saveMealPlan() {
    if (!currentMealPlan) return;
    
    try {
        const response = await fetch('/api/meal-prep/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                meal_plan: currentMealPlan,
                name: `Meal Plan - ${new Date().toLocaleDateString()}`
            })
        });
        
        if (response.ok) {
            showMessage('Meal plan saved successfully!', 'success');
            loadSavedPlans();
        } else {
            throw new Error('Failed to save meal plan');
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// Export meal plan as PDF
function exportMealPlan() {
    // In a real implementation, this would generate a PDF
    // For now, we'll use the browser's print functionality
    window.print();
}

// Regenerate meal plan
function regenerateMealPlan() {
    if (confirm('Are you sure you want to regenerate the meal plan? Current changes will be lost.')) {
        const form = document.getElementById('mealPlanForm');
        form.dispatchEvent(new Event('submit'));
    }
}

// Print shopping list
function printShoppingList() {
    const printWindow = window.open('', '_blank');
    const shoppingListHtml = document.getElementById('shoppingList').innerHTML;
    const totalCost = document.getElementById('totalCost').textContent;
    
    printWindow.document.write(`
        <html>
        <head>
            <title>Shopping List</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
                .category-section { margin-bottom: 20px; }
                .category-title { font-weight: bold; margin-bottom: 10px; }
                .shopping-item { display: flex; justify-content: space-between; padding: 5px 0; }
                .total-cost { font-size: 1.2em; font-weight: bold; margin-top: 20px; }
                @media print { body { margin: 0; } }
            </style>
        </head>
        <body>
            <h1>Shopping List</h1>
            ${shoppingListHtml}
            <div class="total-cost">Total: ${totalCost}</div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
}

// Print individual recipe
function printRecipe(recipeName) {
    const recipeContent = document.getElementById('recipeDetails').innerHTML;
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
        <html>
        <head>
            <title>${recipeName} - Recipe</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 20px; 
                    max-width: 800px; 
                    margin: 0 auto;
                }
                h2 { color: #333; margin-bottom: 20px; }
                h3 { color: #555; margin-top: 25px; margin-bottom: 15px; }
                .recipe-stats { 
                    display: flex; 
                    gap: 20px; 
                    margin-bottom: 20px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #eee;
                }
                .nutrition-grid { 
                    display: grid; 
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #f5f5f5;
                    border-radius: 8px;
                }
                ul, ol { margin-left: 20px; }
                li { margin-bottom: 8px; line-height: 1.6; }
                .btn-print, .recipe-header button { display: none !important; }
                @media print { 
                    body { margin: 0; padding: 15px; }
                    .recipe-tips { 
                        background: #f0f0f0; 
                        padding: 15px; 
                        border-radius: 8px;
                        margin-top: 20px;
                    }
                }
            </style>
        </head>
        <body>
            ${recipeContent}
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.9em; color: #666;">
                Generated by Kinobody Meal Prep Planner • ${new Date().toLocaleDateString()}
            </footer>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
}

// Load saved meal plans
async function loadSavedPlans() {
    try {
        const response = await fetch('/api/meal-prep/plans');
        if (response.ok) {
            savedPlans = await response.json();
            displaySavedPlans();
        }
    } catch (error) {
        console.error('Error loading saved plans:', error);
    }
}

// Display saved plans
function displaySavedPlans() {
    const container = document.getElementById('savedPlans');
    
    if (savedPlans.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <p>No saved meal plans yet</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    savedPlans.forEach(plan => {
        const date = new Date(plan.created_at).toLocaleDateString();
        html += `
            <div class="saved-plan-card" onclick="loadSavedPlan('${plan.id}')">
                <div class="plan-date">${date}</div>
                <h4 class="plan-name">${plan.name}</h4>
                <div class="plan-stats">
                    <span>Budget: $${plan.budget}</span>
                    <span>Status: ${plan.status}</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load a saved plan
async function loadSavedPlan(planId) {
    try {
        const response = await fetch(`/api/meal-prep/plan/${planId}`);
        if (response.ok) {
            const data = await response.json();
            currentMealPlan = data;
            displayMealPlan(data);
            document.getElementById('generationSection').style.display = 'none';
            document.getElementById('mealPlanSection').style.display = 'block';
        }
    } catch (error) {
        showMessage('Error loading meal plan', 'error');
    }
}

// AI Chat functionality
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Send to AI
    try {
        const response = await fetch('/api/meal-prep/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: currentMealPlan
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            addChatMessage(data.response, 'assistant');
        }
    } catch (error) {
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

// Add message to chat
function addChatMessage(message, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `<p>${message}</p>`;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Customize meal
function customizeMeal(dayNumber, mealKey) {
    // Open AI chat with context
    const aiChat = document.getElementById('aiChat');
    aiChat.style.display = 'flex';
    
    const meal = currentMealPlan.meal_plan[`day_${dayNumber}`].meals[mealKey];
    addChatMessage(`I'd like to customize the ${meal.name}. What changes would you like to make?`, 'assistant');
}

// Swap meal
async function swapMeal(dayNumber, mealKey) {
    const meal = currentMealPlan.meal_plan[`day_${dayNumber}`].meals[mealKey];
    
    try {
        const response = await fetch('/api/meal-prep/swap-meal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_meal: meal,
                meal_type: meal.meal_type,
                dietary_requirements: currentMealPlan.metadata.user_requirements.dietary_requirements
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentMealPlan.meal_plan[`day_${dayNumber}`].meals[mealKey] = data.new_meal;
            displayDayContent(dayNumber);
            showMessage('Meal swapped successfully!', 'success');
        }
    } catch (error) {
        showMessage('Error swapping meal', 'error');
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/user');
        if (response.status === 401) {
            // Not logged in - show login prompt
            const aiToggle = document.querySelector('.ai-assistant-toggle');
            if (aiToggle) {
                aiToggle.innerHTML += '<p class="auth-warning">Please <a href="/login">log in</a> to use AI features</p>';
            }
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

// Show message toast
function showMessage(message, type = 'info') {
    const toast = document.getElementById('messageToast');
    toast.textContent = message;
    toast.className = `message-toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}