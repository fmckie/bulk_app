// Nutrition tracking functionality
class NutritionTracker {
    constructor() {
        this.currentDate = new Date().toISOString().split('T')[0];
        this.currentData = {
            calories: 0,
            protein: 0,
            carbs: 0,
            fats: 0
        };
        this.targets = {
            calories: 0,
            protein: 0,
            carbs: 0,
            fats: 0
        };
        this.isTrainingDay = false;
        
        this.init();
    }
    
    init() {
        // Event listeners
        document.getElementById('dateInput').addEventListener('change', (e) => {
            this.currentDate = e.target.value;
            this.loadData();
        });
        
        document.getElementById('prevDay').addEventListener('click', () => {
            this.changeDate(-1);
        });
        
        document.getElementById('nextDay').addEventListener('click', () => {
            this.changeDate(1);
        });
        
        document.getElementById('nutritionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveNutrition();
        });
        
        // Quick add buttons
        document.querySelectorAll('.quick-add-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.quickAdd(btn.dataset);
            });
        });
        
        // Load initial data
        this.loadData();
    }
    
    changeDate(days) {
        const date = new Date(this.currentDate);
        date.setDate(date.getDate() + days);
        this.currentDate = date.toISOString().split('T')[0];
        document.getElementById('dateInput').value = this.currentDate;
        this.loadData();
    }
    
    async loadData() {
        this.showLoading(true);
        
        try {
            // Load nutrition data and targets in parallel
            const [nutritionResponse, targetsResponse] = await Promise.all([
                fetch(`/api/nutrition/${this.currentDate}`),
                fetch(`/api/nutrition/targets?date=${this.currentDate}`)
            ]);
            
            if (nutritionResponse.ok) {
                const nutritionData = await nutritionResponse.json();
                this.currentData = {
                    calories: nutritionData.calories || 0,
                    protein: nutritionData.protein_g || 0,
                    carbs: nutritionData.carbs_g || 0,
                    fats: nutritionData.fats_g || 0
                };
                this.isTrainingDay = nutritionData.is_training_day;
                
                // Update form with existing data
                document.getElementById('manualCalories').value = this.currentData.calories || '';
                document.getElementById('manualProtein').value = this.currentData.protein || '';
                document.getElementById('manualCarbs').value = this.currentData.carbs || '';
                document.getElementById('manualFats').value = this.currentData.fats || '';
                document.getElementById('notes').value = nutritionData.notes || '';
            }
            
            if (targetsResponse.ok) {
                const targetsData = await targetsResponse.json();
                this.targets = targetsData.targets;
                this.isTrainingDay = targetsData.is_training_day;
                this.updateTargetsDisplay(targetsData);
            } else if (targetsResponse.status === 400) {
                // No body weight set
                const error = await targetsResponse.json();
                this.showMessage(error.error, 'error');
            }
            
            this.updateDisplay();
            await this.loadWeeklySummary();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showMessage('Error loading nutrition data', 'error');
            // Try to load from local storage
            this.loadFromLocalStorage();
        } finally {
            this.showLoading(false);
        }
    }
    
    updateTargetsDisplay(data) {
        // Update target values
        document.getElementById('targetCalories').textContent = this.targets.calories;
        document.getElementById('targetProtein').textContent = this.targets.protein;
        document.getElementById('targetCarbs').textContent = this.targets.carbs;
        document.getElementById('targetFats').textContent = this.targets.fats;
        
        // Update training day indicator
        const indicator = document.getElementById('trainingIndicator');
        const dayType = document.getElementById('dayType');
        
        if (this.isTrainingDay) {
            indicator.className = 'training-indicator training-day';
            dayType.textContent = 'Training Day (+500 cal)';
        } else {
            indicator.className = 'training-indicator rest-day';
            dayType.textContent = 'Rest Day (+100 cal)';
        }
    }
    
    updateDisplay() {
        // Update current values
        document.getElementById('currentCalories').textContent = Math.round(this.currentData.calories);
        document.getElementById('currentProtein').textContent = Math.round(this.currentData.protein);
        document.getElementById('currentCarbs').textContent = Math.round(this.currentData.carbs);
        document.getElementById('currentFats').textContent = Math.round(this.currentData.fats);
        
        // Update progress bars
        this.updateProgressBar('calories', this.currentData.calories, this.targets.calories);
        this.updateProgressBar('protein', this.currentData.protein, this.targets.protein);
        this.updateProgressBar('carbs', this.currentData.carbs, this.targets.carbs);
        this.updateProgressBar('fats', this.currentData.fats, this.targets.fats);
        
        // Update date display
        const date = new Date(this.currentDate);
        const formattedDate = date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        document.querySelector('.subtitle').textContent = formattedDate;
    }
    
    updateProgressBar(macro, current, target) {
        const progressBar = document.getElementById(`${macro}Progress`);
        const percentage = target > 0 ? (current / target) * 100 : 0;
        
        progressBar.style.width = Math.min(percentage, 100) + '%';
        
        // Color coding
        if (percentage < 80) {
            progressBar.className = `progress-fill ${macro} under`;
        } else if (percentage <= 110) {
            progressBar.className = `progress-fill ${macro} optimal`;
        } else {
            progressBar.className = `progress-fill ${macro} over`;
        }
    }
    
    quickAdd(data) {
        // Add to current values
        this.currentData.calories += parseInt(data.calories) || 0;
        this.currentData.protein += parseInt(data.protein) || 0;
        this.currentData.carbs += parseInt(data.carbs) || 0;
        this.currentData.fats += parseInt(data.fats) || 0;
        
        // Update form values
        document.getElementById('manualCalories').value = this.currentData.calories;
        document.getElementById('manualProtein').value = this.currentData.protein;
        document.getElementById('manualCarbs').value = this.currentData.carbs;
        document.getElementById('manualFats').value = this.currentData.fats;
        
        // Update display
        this.updateDisplay();
        
        // Visual feedback
        this.showMessage('Added to daily totals', 'success');
    }
    
    async saveNutrition() {
        const formData = {
            date: this.currentDate,
            calories: parseInt(document.getElementById('manualCalories').value) || 0,
            protein: parseFloat(document.getElementById('manualProtein').value) || 0,
            carbs: parseFloat(document.getElementById('manualCarbs').value) || 0,
            fats: parseFloat(document.getElementById('manualFats').value) || 0,
            notes: document.getElementById('notes').value
        };
        
        // Save to local storage first
        this.saveToLocalStorage(formData);
        
        try {
            const response = await fetch('/api/nutrition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showMessage('Nutrition saved successfully!', 'success');
                this.currentData = {
                    calories: formData.calories,
                    protein: formData.protein,
                    carbs: formData.carbs,
                    fats: formData.fats
                };
                this.updateDisplay();
                
                // Clear local storage for this date
                this.clearLocalStorage(this.currentDate);
            } else {
                const error = await response.json();
                this.showMessage(error.error || 'Error saving nutrition', 'error');
            }
        } catch (error) {
            console.error('Error saving nutrition:', error);
            this.showMessage('Saved locally. Will sync when online.', 'warning');
        }
    }
    
    async loadWeeklySummary() {
        try {
            const response = await fetch('/api/nutrition/history?days=7');
            
            if (response.ok) {
                const history = await response.json();
                
                if (history.length > 0) {
                    // Calculate averages
                    const totals = history.reduce((acc, day) => {
                        acc.calories += day.calories || 0;
                        acc.protein += day.protein_g || 0;
                        return acc;
                    }, { calories: 0, protein: 0 });
                    
                    const avgCalories = Math.round(totals.calories / history.length);
                    const avgProtein = Math.round(totals.protein / history.length);
                    
                    // Calculate weekly surplus/deficit
                    const weeklyCalories = totals.calories;
                    const weeklyMaintenance = this.targets.calories ? 
                        (this.targets.calories - (this.isTrainingDay ? 500 : 100)) * 7 : 0;
                    const weeklyDifference = weeklyCalories - weeklyMaintenance;
                    
                    // Update display
                    document.getElementById('avgCalories').textContent = avgCalories;
                    document.getElementById('avgProtein').textContent = avgProtein + 'g';
                    document.getElementById('weeklyDeficit').textContent = 
                        weeklyDifference > 0 ? `+${weeklyDifference}` : weeklyDifference;
                }
            }
        } catch (error) {
            console.error('Error loading weekly summary:', error);
        }
    }
    
    // Local Storage Methods
    saveToLocalStorage(data) {
        const storageKey = `nutrition_${this.currentDate}`;
        localStorage.setItem(storageKey, JSON.stringify(data));
        
        // Keep track of offline entries
        const offlineEntries = JSON.parse(localStorage.getItem('offline_nutrition') || '[]');
        if (!offlineEntries.includes(this.currentDate)) {
            offlineEntries.push(this.currentDate);
            localStorage.setItem('offline_nutrition', JSON.stringify(offlineEntries));
        }
    }
    
    loadFromLocalStorage() {
        const storageKey = `nutrition_${this.currentDate}`;
        const savedData = localStorage.getItem(storageKey);
        
        if (savedData) {
            const data = JSON.parse(savedData);
            this.currentData = {
                calories: data.calories || 0,
                protein: data.protein || 0,
                carbs: data.carbs || 0,
                fats: data.fats || 0
            };
            
            // Update form
            document.getElementById('manualCalories').value = data.calories || '';
            document.getElementById('manualProtein').value = data.protein || '';
            document.getElementById('manualCarbs').value = data.carbs || '';
            document.getElementById('manualFats').value = data.fats || '';
            document.getElementById('notes').value = data.notes || '';
            
            this.updateDisplay();
            this.showMessage('Loaded from local storage', 'info');
        }
    }
    
    clearLocalStorage(date) {
        localStorage.removeItem(`nutrition_${date}`);
        
        // Remove from offline entries list
        const offlineEntries = JSON.parse(localStorage.getItem('offline_nutrition') || '[]');
        const index = offlineEntries.indexOf(date);
        if (index > -1) {
            offlineEntries.splice(index, 1);
            localStorage.setItem('offline_nutrition', JSON.stringify(offlineEntries));
        }
    }
    
    async syncOfflineData() {
        const offlineEntries = JSON.parse(localStorage.getItem('offline_nutrition') || '[]');
        
        for (const date of offlineEntries) {
            const storageKey = `nutrition_${date}`;
            const data = localStorage.getItem(storageKey);
            
            if (data) {
                try {
                    const response = await fetch('/api/nutrition', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: data
                    });
                    
                    if (response.ok) {
                        this.clearLocalStorage(date);
                    }
                } catch (error) {
                    console.error('Error syncing offline data:', error);
                }
            }
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    showMessage(message, type = 'info') {
        const toast = document.getElementById('messageToast');
        toast.textContent = message;
        toast.className = `message-toast ${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.nutritionTracker = new NutritionTracker();
    
    // Try to sync offline data on load
    if (navigator.onLine) {
        window.nutritionTracker.syncOfflineData();
    }
    
    // Sync when coming back online
    window.addEventListener('online', () => {
        window.nutritionTracker.syncOfflineData();
    });
});