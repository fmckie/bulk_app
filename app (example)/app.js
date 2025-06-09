// Mobile Fitness App - Kinobody Greek God Program
class KinobodyApp {
    constructor() {
        this.appState = {
            user: {
                name: "User",
                age: 23,
                height: "6'5\"",
                currentWeight: 85,
                goalWeight: 90
            },
            nutrition: {
                training: { calories: 3300, protein: 200, fats: 80, carbs: 400 },
                rest: { calories: 3100, protein: 200, fats: 80, carbs: 360 }
            },
            workouts: [],
            meals: [],
            measurements: [],
            currentExercise: 0,
            currentWorkout: 'A',
            theme: 'auto',
            timerInterval: null,
            timerSeconds: 0,
            timerRunning: false,
            fastingInterval: null
        };

        this.workoutData = {
            A: [
                { name: "Incline Barbell Bench Press", type: "RPT", sets: [5, 6, 8], rest: 180 },
                { name: "Standing Barbell Shoulder Press", type: "RPT", sets: [5, 6, 8], rest: 180 },
                { name: "Weighted Dips", type: "Standard", sets: "3x6-10", rest: 120 },
                { name: "Lateral Raises", type: "Standard", sets: "3x12-15", rest: 90 },
                { name: "Rope Tricep Pushdowns", type: "Standard", sets: "3x12", rest: 90 }
            ],
            B: [
                { name: "Weighted Chin-Ups", type: "RPT", sets: [5, 6, 8], rest: 180 },
                { name: "Sumo Deadlifts", type: "RPT", sets: [5, 6, 8], rest: 180 },
                { name: "Barbell Curls", type: "Standard", sets: "3x6-10", rest: 120 },
                { name: "Pistol Squats", type: "Standard", sets: "3x8-10/side", rest: 120 },
                { name: "Calf Raises", type: "Standard", sets: "3x15", rest: 90 }
            ]
        };

        this.quickFoods = {
            'protein-shake': { name: 'Protein Shake', calories: 150, protein: 30, carbs: 5, fats: 2 },
            'banana': { name: 'Banana', calories: 105, protein: 1, carbs: 27, fats: 0 },
            'chicken-breast': { name: 'Chicken 100g', calories: 165, protein: 31, carbs: 0, fats: 4 },
            'rice': { name: 'Rice 100g', calories: 130, protein: 3, carbs: 28, fats: 0 }
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDashboard();
        this.setupCharts();
        this.updateFastingTimer();
        this.startFastingTimer();
        this.updateCurrentDate();
        this.updateTodayWorkout();
        this.updateMealsDisplay();
        this.updateMacroProgress();
    }

    setupEventListeners() {
        // Bottom navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const screen = e.currentTarget.dataset.screen;
                this.navigateToScreen(screen);
            });
        });

        // Quick action buttons
        document.querySelectorAll('.action-btn[data-screen]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const screen = e.currentTarget.dataset.screen;
                this.navigateToScreen(screen);
            });
        });

        // Workout selection
        document.querySelectorAll('.workout-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const workout = e.currentTarget.dataset.workout;
                this.selectWorkout(workout);
            });
        });

        // Exercise navigation
        document.getElementById('next-exercise')?.addEventListener('click', () => {
            this.nextExercise();
        });

        document.getElementById('prev-exercise')?.addEventListener('click', () => {
            this.prevExercise();
        });

        // Timer controls
        document.getElementById('start-timer')?.addEventListener('click', () => {
            this.toggleTimer();
        });

        document.getElementById('reset-timer')?.addEventListener('click', () => {
            this.resetTimer();
        });

        // Complete workout
        document.getElementById('complete-workout')?.addEventListener('click', () => {
            this.completeWorkout();
        });

        // Nutrition day type
        document.querySelectorAll('.day-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchNutritionType(e.currentTarget.dataset.type);
            });
        });

        // Quick food buttons
        document.querySelectorAll('.food-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const foodKey = e.currentTarget.dataset.food;
                this.addQuickFood(foodKey);
            });
        });

        // Add custom food
        document.getElementById('add-food')?.addEventListener('click', () => {
            this.addCustomFood();
        });

        // Progress tracking
        document.getElementById('log-weight')?.addEventListener('click', () => {
            this.logWeight();
        });

        document.getElementById('log-measurements')?.addEventListener('click', () => {
            this.logMeasurements();
        });

        // Exercise selector for strength chart
        document.querySelectorAll('.exercise-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.updateStrengthChart(e.currentTarget.dataset.exercise);
                document.querySelectorAll('.exercise-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });

        // Theme toggle
        document.getElementById('theme-toggle')?.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Swipe gestures for exercise navigation
        this.setupSwipeGestures();

        // Auto-calculate RPT weights
        this.setupRPTCalculation();

        // Pull to refresh simulation
        this.setupPullToRefresh();
    }

    navigateToScreen(screenName) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        document.getElementById(screenName)?.classList.add('active');

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-screen="${screenName}"]`)?.classList.add('active');

        // Trigger screen-specific updates
        if (screenName === 'nutrition') {
            this.updateNutritionDisplay();
        } else if (screenName === 'progress') {
            this.updateProgressCharts();
        }
    }

    updateCurrentDate() {
        const today = new Date();
        const options = { weekday: 'long', month: 'long', day: 'numeric' };
        const dateString = today.toLocaleDateString('en-US', options);
        const element = document.getElementById('current-date');
        if (element) {
            element.textContent = dateString;
        }
    }

    updateTodayWorkout() {
        const today = new Date();
        const dayOfWeek = today.getDay();
        
        let workoutType = "Rest Day";
        if (dayOfWeek === 1 || dayOfWeek === 5) {
            workoutType = "Workout A";
        } else if (dayOfWeek === 3) {
            workoutType = "Workout B";
        }
        
        const workoutElement = document.getElementById('today-workout');
        if (workoutElement) {
            workoutElement.textContent = workoutType;
        }
        
        // Update calories
        const isTrainingDay = workoutType !== "Rest Day";
        const calories = isTrainingDay ? this.appState.nutrition.training.calories : this.appState.nutrition.rest.calories;
        const caloriesElement = document.getElementById('today-calories');
        if (caloriesElement) {
            caloriesElement.textContent = calories.toLocaleString();
        }
    }

    selectWorkout(workoutType) {
        this.appState.currentWorkout = workoutType;
        this.appState.currentExercise = 0;

        // Update workout button states
        document.querySelectorAll('.workout-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-workout="${workoutType}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Show correct workout exercises
        document.querySelectorAll('.workout-exercises').forEach(workout => {
            workout.classList.remove('active');
        });
        const activeWorkout = document.getElementById(`workout-${workoutType}`);
        if (activeWorkout) {
            activeWorkout.classList.add('active');
        }

        this.updateExerciseProgress();
        this.updateExerciseDisplay();
    }

    nextExercise() {
        const totalExercises = this.workoutData[this.appState.currentWorkout].length;
        if (this.appState.currentExercise < totalExercises - 1) {
            this.appState.currentExercise++;
            this.updateExerciseDisplay();
            this.updateExerciseProgress();
        }
    }

    prevExercise() {
        if (this.appState.currentExercise > 0) {
            this.appState.currentExercise--;
            this.updateExerciseDisplay();
            this.updateExerciseProgress();
        }
    }

    updateExerciseDisplay() {
        const currentWorkout = document.getElementById(`workout-${this.appState.currentWorkout}`);
        if (!currentWorkout) return;
        
        const exercises = currentWorkout.querySelectorAll('.exercise-card');
        
        exercises.forEach((exercise, index) => {
            if (index === this.appState.currentExercise) {
                exercise.classList.add('active');
            } else {
                exercise.classList.remove('active');
            }
        });

        // Update navigation buttons
        const prevBtn = document.getElementById('prev-exercise');
        const nextBtn = document.getElementById('next-exercise');
        
        if (prevBtn) {
            prevBtn.disabled = this.appState.currentExercise === 0;
        }
        
        if (nextBtn) {
            const totalExercises = this.workoutData[this.appState.currentWorkout].length;
            if (this.appState.currentExercise === totalExercises - 1) {
                nextBtn.textContent = 'Finish';
                nextBtn.classList.add('success');
            } else {
                nextBtn.textContent = 'Next →';
                nextBtn.classList.remove('success');
            }
        }
    }

    updateExerciseProgress() {
        const totalExercises = this.workoutData[this.appState.currentWorkout].length;
        const currentNum = this.appState.currentExercise + 1;
        const progress = (currentNum / totalExercises) * 100;

        const currentElement = document.getElementById('current-exercise');
        const totalElement = document.getElementById('total-exercises');
        
        if (currentElement) currentElement.textContent = currentNum;
        if (totalElement) totalElement.textContent = totalExercises;
        
        const progressFill = document.querySelector('.exercise-progress .progress-fill');
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
    }

    toggleTimer() {
        const timerBtn = document.getElementById('start-timer');
        if (!timerBtn) return;
        
        if (this.appState.timerRunning) {
            // Stop timer
            clearInterval(this.appState.timerInterval);
            this.appState.timerRunning = false;
            timerBtn.textContent = 'Start';
        } else {
            // Start timer
            if (this.appState.timerSeconds === 0) {
                // Get rest time for current exercise
                const currentExercise = this.workoutData[this.appState.currentWorkout][this.appState.currentExercise];
                this.appState.timerSeconds = currentExercise.rest;
            }
            
            this.appState.timerRunning = true;
            timerBtn.textContent = 'Pause';
            
            this.appState.timerInterval = setInterval(() => {
                if (this.appState.timerSeconds > 0) {
                    this.appState.timerSeconds--;
                    this.updateTimerDisplay();
                } else {
                    this.timerComplete();
                }
            }, 1000);
        }
    }

    resetTimer() {
        clearInterval(this.appState.timerInterval);
        this.appState.timerRunning = false;
        
        const currentExercise = this.workoutData[this.appState.currentWorkout][this.appState.currentExercise];
        this.appState.timerSeconds = currentExercise.rest;
        
        this.updateTimerDisplay();
        const startBtn = document.getElementById('start-timer');
        if (startBtn) {
            startBtn.textContent = 'Start';
        }
    }

    updateTimerDisplay() {
        const minutes = Math.floor(this.appState.timerSeconds / 60);
        const seconds = this.appState.timerSeconds % 60;
        const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        const timerDisplay = document.getElementById('timer-display');
        if (timerDisplay) {
            timerDisplay.textContent = display;
        }
    }

    timerComplete() {
        clearInterval(this.appState.timerInterval);
        this.appState.timerRunning = false;
        this.appState.timerSeconds = 0;
        
        const startBtn = document.getElementById('start-timer');
        const timerDisplay = document.getElementById('timer-display');
        
        if (startBtn) startBtn.textContent = 'Start';
        if (timerDisplay) timerDisplay.textContent = '0:00';
        
        // Visual feedback
        this.showTimerComplete();
    }

    showTimerComplete() {
        // Simple visual feedback
        const timerDisplay = document.getElementById('timer-display');
        if (timerDisplay) {
            timerDisplay.style.color = 'var(--color-success)';
            setTimeout(() => {
                timerDisplay.style.color = 'var(--color-primary)';
            }, 2000);
        }
    }

    completeWorkout() {
        const workoutData = this.collectWorkoutData();
        this.appState.workouts.push(workoutData);
        this.showWorkoutCompleteModal();
        this.updateDashboard();
    }

    collectWorkoutData() {
        const activeWorkout = document.querySelector('.workout-exercises.active');
        if (!activeWorkout) return { date: new Date().toISOString(), type: this.appState.currentWorkout, exercises: [] };
        
        const exerciseCards = activeWorkout.querySelectorAll('.exercise-card');
        
        const workoutData = {
            date: new Date().toISOString(),
            type: this.appState.currentWorkout,
            exercises: []
        };

        exerciseCards.forEach((card, index) => {
            const exerciseName = this.workoutData[this.appState.currentWorkout][index].name;
            const sets = [];
            
            const weightInputs = card.querySelectorAll('.weight-input');
            const repsInputs = card.querySelectorAll('.reps-input');
            
            for (let i = 0; i < weightInputs.length; i++) {
                const weight = parseFloat(weightInputs[i].value);
                const reps = parseInt(repsInputs[i].value);
                
                if (weight && reps) {
                    sets.push({ weight, reps });
                }
            }
            
            if (sets.length > 0) {
                workoutData.exercises.push({
                    name: exerciseName,
                    sets: sets
                });
            }
        });
        
        return workoutData;
    }

    showWorkoutCompleteModal() {
        const modal = document.getElementById('workout-complete-modal');
        if (modal) {
            modal.classList.add('show');
        }
    }

    closeModal() {
        const modal = document.getElementById('workout-complete-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    switchNutritionType(type) {
        // Update button states
        document.querySelectorAll('.day-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-type="${type}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        this.updateNutritionDisplay(type);
    }

    updateNutritionDisplay(type = 'training') {
        const targets = this.appState.nutrition[type];
        
        // Update macro targets in the display
        const caloriesTotal = document.querySelector('.calories-total');
        if (caloriesTotal) {
            caloriesTotal.textContent = `/ ${targets.calories}`;
        }
        
        // Update macro values displays
        const macroElements = document.querySelectorAll('.macro-values');
        if (macroElements[0]) {
            macroElements[0].querySelector('span:last-child').textContent = `/ ${targets.protein}g`;
        }
        if (macroElements[1]) {
            macroElements[1].querySelector('span:last-child').textContent = `/ ${targets.carbs}g`;
        }
        if (macroElements[2]) {
            macroElements[2].querySelector('span:last-child').textContent = `/ ${targets.fats}g`;
        }

        this.updateMacroProgress();
    }

    addQuickFood(foodKey) {
        const food = this.quickFoods[foodKey];
        if (food) {
            this.addMeal(food);
        }
    }

    addCustomFood() {
        const nameElement = document.getElementById('food-name');
        const caloriesElement = document.getElementById('food-calories');
        const proteinElement = document.getElementById('food-protein');
        const carbsElement = document.getElementById('food-carbs');
        const fatsElement = document.getElementById('food-fats');
        
        if (!nameElement || !caloriesElement) return;
        
        const name = nameElement.value;
        const calories = parseFloat(caloriesElement.value) || 0;
        const protein = parseFloat(proteinElement?.value) || 0;
        const carbs = parseFloat(carbsElement?.value) || 0;
        const fats = parseFloat(fatsElement?.value) || 0;

        if (name && calories > 0) {
            this.addMeal({ name, calories, protein, carbs, fats });
            this.clearFoodForm();
        }
    }

    addMeal(meal) {
        const mealEntry = {
            id: Date.now(),
            date: new Date().toISOString().split('T')[0],
            ...meal
        };

        this.appState.meals.push(mealEntry);
        this.updateMealsDisplay();
        this.updateMacroProgress();
    }

    clearFoodForm() {
        const elements = ['food-name', 'food-calories', 'food-protein', 'food-carbs', 'food-fats'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });
    }

    updateMealsDisplay() {
        const mealsList = document.getElementById('meals-list');
        if (!mealsList) return;
        
        const today = new Date().toISOString().split('T')[0];
        const todayMeals = this.appState.meals.filter(meal => meal.date === today);

        if (todayMeals.length === 0) {
            mealsList.innerHTML = `
                <div class="empty-meals">
                    <span class="empty-icon">🍽️</span>
                    <p>No meals logged yet</p>
                </div>
            `;
        } else {
            mealsList.innerHTML = todayMeals.map(meal => `
                <div class="meal-item">
                    <div class="meal-info">
                        <strong>${meal.name}</strong>
                        <div style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: 4px;">
                            ${meal.calories} cal • ${meal.protein}g protein • ${meal.carbs}g carbs • ${meal.fats}g fats
                        </div>
                    </div>
                    <button onclick="app.removeMeal(${meal.id})" style="background: none; border: none; color: var(--color-error); font-size: 18px; cursor: pointer;">×</button>
                </div>
            `).join('');
        }
    }

    removeMeal(mealId) {
        this.appState.meals = this.appState.meals.filter(meal => meal.id !== mealId);
        this.updateMealsDisplay();
        this.updateMacroProgress();
    }

    updateMacroProgress() {
        const today = new Date().toISOString().split('T')[0];
        const todayMeals = this.appState.meals.filter(meal => meal.date === today);
        
        const consumed = todayMeals.reduce((totals, meal) => ({
            calories: totals.calories + meal.calories,
            protein: totals.protein + meal.protein,
            carbs: totals.carbs + meal.carbs,
            fats: totals.fats + meal.fats
        }), { calories: 0, protein: 0, carbs: 0, fats: 0 });

        const isTrainingActive = document.querySelector('.day-btn.active')?.dataset.type === 'training';
        const targets = isTrainingActive ? this.appState.nutrition.training : this.appState.nutrition.rest;

        // Update consumed values
        const elements = {
            calories: document.getElementById('calories-consumed'),
            protein: document.getElementById('protein-consumed'),
            carbs: document.getElementById('carbs-consumed'),
            fats: document.getElementById('fats-consumed')
        };

        if (elements.calories) elements.calories.textContent = Math.round(consumed.calories);
        if (elements.protein) elements.protein.textContent = Math.round(consumed.protein);
        if (elements.carbs) elements.carbs.textContent = Math.round(consumed.carbs);
        if (elements.fats) elements.fats.textContent = Math.round(consumed.fats);

        // Update progress bars
        const caloriesProgress = Math.min(100, (consumed.calories / targets.calories) * 100);
        const proteinProgress = Math.min(100, (consumed.protein / targets.protein) * 100);
        const carbsProgress = Math.min(100, (consumed.carbs / targets.carbs) * 100);
        const fatsProgress = Math.min(100, (consumed.fats / targets.fats) * 100);

        const progressElements = {
            protein: document.getElementById('protein-progress'),
            carbs: document.getElementById('carbs-progress'),
            fats: document.getElementById('fats-progress')
        };

        if (progressElements.protein) progressElements.protein.style.width = `${proteinProgress}%`;
        if (progressElements.carbs) progressElements.carbs.style.width = `${carbsProgress}%`;
        if (progressElements.fats) progressElements.fats.style.width = `${fatsProgress}%`;

        // Update calorie ring
        this.updateCalorieRing(caloriesProgress);
    }

    updateCalorieRing(progress) {
        const circle = document.querySelector('.progress-ring-circle');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = 2 * Math.PI * radius;
            const strokeDasharray = circumference;
            const strokeDashoffset = circumference - (progress / 100) * circumference;
            
            circle.style.strokeDasharray = strokeDasharray;
            circle.style.strokeDashoffset = strokeDashoffset;
            circle.style.stroke = 'var(--color-primary)';
        }
    }

    updateFastingTimer() {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        const second = now.getSeconds();
        
        const eatingWindowStart = 12; // 12 PM
        const eatingWindowEnd = 20; // 8 PM
        
        let timeLeft, label, progress;
        
        if (hour >= eatingWindowStart && hour < eatingWindowEnd) {
            // Currently in eating window
            const endTime = new Date();
            endTime.setHours(eatingWindowEnd, 0, 0, 0);
            const remainingMs = endTime - now;
            const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
            const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
            const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
            
            timeLeft = `${remainingHours}:${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            label = "eating window ends";
            
            const eatingMinutes = (hour - eatingWindowStart) * 60 + minute;
            progress = (eatingMinutes / (8 * 60)) * 100;
        } else {
            // Currently fasting
            let nextEatingWindow;
            if (hour < eatingWindowStart) {
                nextEatingWindow = new Date();
                nextEatingWindow.setHours(eatingWindowStart, 0, 0, 0);
            } else {
                nextEatingWindow = new Date();
                nextEatingWindow.setDate(nextEatingWindow.getDate() + 1);
                nextEatingWindow.setHours(eatingWindowStart, 0, 0, 0);
            }
            
            const remainingMs = nextEatingWindow - now;
            const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
            const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
            const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
            
            timeLeft = `${remainingHours}:${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            label = "until eating window";
            
            const totalFastingMinutes = 16 * 60;
            const elapsedFastingMinutes = hour < eatingWindowStart ? 
                (24 - eatingWindowEnd + hour) * 60 + minute : 
                (hour - eatingWindowEnd) * 60 + minute;
            progress = (elapsedFastingMinutes / totalFastingMinutes) * 100;
        }
        
        const timeElement = document.getElementById('fasting-time');
        const labelElement = document.getElementById('fasting-label');
        const progressElement = document.getElementById('fasting-progress-bar');
        const statusElement = document.getElementById('fasting-status');
        
        if (timeElement) timeElement.textContent = timeLeft;
        if (labelElement) labelElement.textContent = label;
        if (progressElement) progressElement.style.width = `${Math.min(100, progress)}%`;
        
        // Update dashboard fasting status
        if (statusElement) {
            const shortTime = timeLeft.split(':')[0] + 'h left';
            statusElement.textContent = shortTime;
        }
    }

    startFastingTimer() {
        // Clear any existing interval
        if (this.appState.fastingInterval) {
            clearInterval(this.appState.fastingInterval);
        }
        
        // Update immediately
        this.updateFastingTimer();
        
        // Update every second for real-time countdown
        this.appState.fastingInterval = setInterval(() => {
            this.updateFastingTimer();
        }, 1000);
    }

    logWeight() {
        const weightInput = document.getElementById('weight-input');
        if (!weightInput) return;
        
        const weight = parseFloat(weightInput.value);
        
        if (weight) {
            const measurement = {
                date: new Date().toISOString().split('T')[0],
                weight: weight
            };
            
            this.appState.measurements.push(measurement);
            this.appState.user.currentWeight = weight;
            
            weightInput.value = '';
            this.updateDashboard();
            this.updateProgressCharts();
        }
    }

    logMeasurements() {
        const waistInput = document.getElementById('waist-input');
        const chestInput = document.getElementById('chest-input');
        const armsInput = document.getElementById('arms-input');
        
        const waist = waistInput ? parseFloat(waistInput.value) : null;
        const chest = chestInput ? parseFloat(chestInput.value) : null;
        const arms = armsInput ? parseFloat(armsInput.value) : null;
        
        if (waist || chest || arms) {
            const measurement = {
                date: new Date().toISOString().split('T')[0],
                waist: waist || null,
                chest: chest || null,
                arms: arms || null
            };
            
            this.appState.measurements.push(measurement);
            
            // Clear inputs
            if (waistInput) waistInput.value = '';
            if (chestInput) chestInput.value = '';
            if (armsInput) armsInput.value = '';
        }
    }

    updateDashboard() {
        // Update progress circle
        const progress = Math.max(0, Math.min(100, 
            ((this.appState.user.currentWeight - 85) / (this.appState.user.goalWeight - 85)) * 100
        ));
        
        const progressText = document.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
        
        // Update progress circle visual
        const progressCircle = document.querySelector('.progress-circle');
        if (progressCircle) {
            const angle = (progress / 100) * 360;
            progressCircle.style.background = `conic-gradient(var(--color-primary) ${angle}deg, var(--color-secondary) ${angle}deg)`;
        }
    }

    setupCharts() {
        this.setupWeightChart();
        this.setupStrengthChart();
    }

    setupWeightChart() {
        const ctx = document.getElementById('weight-chart')?.getContext('2d');
        if (!ctx) return;

        const sampleData = [
            { date: '2025-06-01', weight: 85.0 },
            { date: '2025-06-08', weight: 85.3 }
        ];

        this.weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sampleData.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Weight (kg)',
                    data: sampleData.map(d => d.weight),
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 84,
                        max: 92
                    }
                }
            }
        });
    }

    setupStrengthChart() {
        const ctx = document.getElementById('strength-chart')?.getContext('2d');
        if (!ctx) return;

        const sampleData = [
            { date: '2025-06-01', weight: 70 },
            { date: '2025-06-08', weight: 72.5 }
        ];

        this.strengthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sampleData.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Incline Bench (kg)',
                    data: sampleData.map(d => d.weight),
                    borderColor: '#FFC185',
                    backgroundColor: 'rgba(255, 193, 133, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    updateStrengthChart(exercise) {
        if (!this.strengthChart) return;

        let label, color, data;
        
        if (exercise === 'bench') {
            label = 'Incline Bench (kg)';
            color = '#FFC185';
            data = [70, 72.5, 75];
        } else {
            label = 'Weighted Chin-ups (kg)';
            color = '#B4413C';
            data = [15, 17.5, 20];
        }
        
        this.strengthChart.data.datasets[0].label = label;
        this.strengthChart.data.datasets[0].borderColor = color;
        this.strengthChart.data.datasets[0].backgroundColor = color.replace(')', ', 0.1)').replace('rgb', 'rgba');
        this.strengthChart.data.datasets[0].data = data;
        this.strengthChart.update();
    }

    updateProgressCharts() {
        if (this.weightChart && this.appState.measurements.length > 0) {
            const weightMeasurements = this.appState.measurements
                .filter(m => m.weight)
                .sort((a, b) => new Date(a.date) - new Date(b.date));
            
            this.weightChart.data.labels = weightMeasurements.map(m => 
                new Date(m.date).toLocaleDateString()
            );
            this.weightChart.data.datasets[0].data = weightMeasurements.map(m => m.weight);
            this.weightChart.update();
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-color-scheme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-color-scheme', newTheme);
        this.appState.theme = newTheme;
        
        // Update theme button
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) {
            themeBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }
    }

    setupSwipeGestures() {
        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;

        const workoutContent = document.getElementById('workout-content');
        if (!workoutContent) return;

        workoutContent.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        workoutContent.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Only trigger if horizontal swipe is larger than vertical
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    // Swipe right - previous exercise
                    this.prevExercise();
                } else {
                    // Swipe left - next exercise
                    this.nextExercise();
                }
            }
        });
    }

    setupRPTCalculation() {
        // Auto-calculate RPT weight reductions
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('weight-input')) {
                const exerciseCard = e.target.closest('.exercise-card');
                if (!exerciseCard) return;
                
                const exerciseType = exerciseCard.querySelector('.exercise-type');
                if (!exerciseType) return;
                
                const isRPT = exerciseType.textContent.includes('RPT');
                
                if (isRPT) {
                    const weightInputs = exerciseCard.querySelectorAll('.weight-input');
                    const firstWeight = parseFloat(weightInputs[0].value);
                    
                    if (firstWeight && e.target === weightInputs[0]) {
                        // Calculate 10% reductions for subsequent sets
                        if (weightInputs[1]) {
                            weightInputs[1].value = Math.round(firstWeight * 0.9 * 10) / 10;
                        }
                        if (weightInputs[2]) {
                            weightInputs[2].value = Math.round(firstWeight * 0.8 * 10) / 10;
                        }
                    }
                }
            }
        });
    }

    setupPullToRefresh() {
        let startY = 0;
        let pullDistance = 0;
        let isPulling = false;

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (isPulling && window.scrollY === 0) {
                pullDistance = e.touches[0].clientY - startY;
                
                if (pullDistance > 0) {
                    // Visual feedback for pull to refresh
                    document.body.style.transform = `translateY(${Math.min(pullDistance / 3, 50)}px)`;
                }
            }
        });

        document.addEventListener('touchend', (e) => {
            if (isPulling) {
                document.body.style.transform = '';
                
                if (pullDistance > 100) {
                    // Trigger refresh
                    this.refreshData();
                }
                
                isPulling = false;
                pullDistance = 0;
            }
        });
    }

    refreshData() {
        // Simulate data refresh
        this.updateDashboard();
        this.updateFastingTimer();
        this.updateMacroProgress();
        
        // Show refresh feedback
        const header = document.querySelector('.app-header');
        if (header) {
            header.style.backgroundColor = 'var(--color-success)';
            setTimeout(() => {
                header.style.backgroundColor = 'var(--color-surface)';
            }, 1000);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new KinobodyApp();
});

// Expose app globally for inline event handlers
window.app = null;