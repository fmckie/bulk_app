// Workout Page JavaScript - RPT Logic and Timer

// Global variables
let currentExercise = null;
let workoutData = [];
let timerInterval = null;
let timerSeconds = 180; // Default 3 minutes
let audioContext = null;

// Exercise data with strength standards multipliers
const exerciseStandards = {
    'incline-bench': { good: 1.0, great: 1.2, godlike: 1.4 },
    'standing-press': { good: 0.7, great: 0.85, godlike: 1.0 },
    'weighted-chins': { good: 0.3, great: 0.5, godlike: 0.7 }, // % of bodyweight added
    'close-grip-bench': { good: 0.85, great: 1.0, godlike: 1.15 },
    'weighted-dips': { good: 0.3, great: 0.5, godlike: 0.7 }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWorkout();
    loadLastWorkout();
    setupEventListeners();
});

function initializeWorkout() {
    // Get current date
    const dateElement = document.querySelector('.workout-date');
    if (dateElement) {
        dateElement.textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Initialize audio context for timer sound
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
}

function setupEventListeners() {
    // Exercise selection
    const exerciseSelect = document.getElementById('exercise-select');
    exerciseSelect.addEventListener('change', handleExerciseSelection);

    // Category buttons
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', handleCategoryFilter);
    });

    // Warm-up calculator
    document.getElementById('calculate-warmup').addEventListener('click', calculateWarmup);
    document.getElementById('working-weight').addEventListener('input', function() {
        document.getElementById('warmup-sets').classList.add('hidden');
    });

    // RPT set completion
    document.querySelectorAll('.complete-set').forEach(btn => {
        btn.addEventListener('click', handleSetCompletion);
    });

    // Timer controls
    document.getElementById('start-timer').addEventListener('click', startTimer);
    document.getElementById('stop-timer').addEventListener('click', stopTimer);
    document.getElementById('reset-timer').addEventListener('click', resetTimer);

    // Timer presets
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            timerSeconds = parseInt(this.dataset.time);
            updateTimerDisplay();
            resetTimer();
        });
    });

    // Weight input for RPT calculation
    document.querySelector('.set-weight[data-set="1"]').addEventListener('input', calculateRPTWeights);

    // Save/Finish buttons
    document.getElementById('save-exercise').addEventListener('click', saveExercise);
    document.getElementById('finish-workout').addEventListener('click', finishWorkout);
}

function handleExerciseSelection(e) {
    currentExercise = e.target.value;
    
    if (!currentExercise) {
        hideAllSections();
        return;
    }

    // Show relevant sections
    document.getElementById('warmup-section').classList.remove('hidden');
    document.getElementById('rpt-sets').classList.remove('hidden');
    document.getElementById('rest-timer').classList.remove('hidden');
    
    // Show strength standards for applicable exercises
    if (exerciseStandards[currentExercise]) {
        document.getElementById('strength-standards').classList.remove('hidden');
        updateStrengthStandards();
    } else {
        document.getElementById('strength-standards').classList.add('hidden');
    }

    // Load last workout data for this exercise
    loadLastExerciseData(currentExercise);
    
    // Reset sets
    resetSets();
}

function handleCategoryFilter(e) {
    const category = e.target.dataset.category;
    
    // Update active button
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');

    // Filter exercise options
    const select = document.getElementById('exercise-select');
    const options = select.querySelectorAll('option[data-category]');
    
    options.forEach(option => {
        if (category === 'all' || option.dataset.category === category) {
            option.style.display = 'block';
        } else {
            option.style.display = 'none';
        }
    });
}

function calculateWarmup() {
    const workingWeight = parseFloat(document.getElementById('working-weight').value);
    
    if (!workingWeight || workingWeight <= 0) {
        KinobodyApp.showNotification('Please enter a valid working weight', 'error');
        return;
    }

    const warmupSets = document.getElementById('warmup-sets');
    const warmupWeights = warmupSets.querySelectorAll('.warmup-weight');
    
    // Calculate warm-up sets (60%, 75%, 90%)
    const percentages = [0.6, 0.75, 0.9];
    
    warmupWeights.forEach((element, index) => {
        const weight = Math.round(workingWeight * percentages[index] / 5) * 5; // Round to nearest 5
        element.textContent = weight + ' lbs';
    });
    
    warmupSets.classList.remove('hidden');
    
    // Auto-populate first set weight
    document.querySelector('.set-weight[data-set="1"]').value = workingWeight;
    calculateRPTWeights();
}

function calculateRPTWeights() {
    const set1Weight = parseFloat(document.querySelector('.set-weight[data-set="1"]').value);
    
    if (!set1Weight || set1Weight <= 0) return;
    
    // Calculate Set 2 (90% of Set 1) and Set 3 (80% of Set 1)
    const set2Weight = Math.round(set1Weight * 0.9 / 2.5) * 2.5; // Round to nearest 2.5
    const set3Weight = Math.round(set1Weight * 0.8 / 2.5) * 2.5; // Round to nearest 2.5
    
    document.querySelector('.set-weight[data-set="2"]').value = set2Weight;
    document.querySelector('.set-weight[data-set="3"]').value = set3Weight;
}

function handleSetCompletion(e) {
    const setNumber = parseInt(e.target.dataset.set);
    const setDiv = document.querySelector(`.rpt-set[data-set="${setNumber}"]`);
    const weight = parseFloat(document.querySelector(`.set-weight[data-set="${setNumber}"]`).value);
    const reps = parseInt(document.querySelector(`.set-reps[data-set="${setNumber}"]`).value);
    
    if (!weight || !reps) {
        KinobodyApp.showNotification('Please enter weight and reps', 'error');
        return;
    }
    
    // Mark set as completed
    setDiv.classList.add('completed');
    setDiv.querySelector('.set-status').textContent = 'COMPLETED';
    e.target.disabled = true;
    
    // Enable next set
    if (setNumber < 3) {
        const nextSet = document.querySelector(`.rpt-set[data-set="${setNumber + 1}"]`);
        nextSet.classList.remove('disabled');
        nextSet.querySelector('.set-status').textContent = 'PENDING';
        nextSet.querySelector('.set-reps').disabled = false;
        nextSet.querySelector('.complete-set').disabled = false;
    }
    
    // Auto-start rest timer
    if (setNumber < 3) {
        startTimer();
    }
    
    // Show save button after all sets
    if (setNumber === 3) {
        document.getElementById('save-exercise').classList.remove('hidden');
    }
    
    // Check if this is a PR
    checkPersonalRecord(weight, reps);
}

function startTimer() {
    if (timerInterval) return;
    
    const startBtn = document.getElementById('start-timer');
    const stopBtn = document.getElementById('stop-timer');
    const timerDisplay = document.querySelector('.timer-display');
    
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    timerDisplay.classList.add('active');
    
    timerInterval = setInterval(() => {
        timerSeconds--;
        updateTimerDisplay();
        
        if (timerSeconds <= 0) {
            stopTimer();
            playTimerSound();
            KinobodyApp.showNotification('Rest period complete!', 'success');
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    const startBtn = document.getElementById('start-timer');
    const stopBtn = document.getElementById('stop-timer');
    const timerDisplay = document.querySelector('.timer-display');
    
    startBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    timerDisplay.classList.remove('active');
}

function resetTimer() {
    stopTimer();
    timerSeconds = 180; // Default 3 minutes
    updateTimerDisplay();
}

function updateTimerDisplay() {
    const minutes = Math.floor(timerSeconds / 60);
    const seconds = timerSeconds % 60;
    
    document.getElementById('timer-minutes').textContent = minutes;
    document.getElementById('timer-seconds').textContent = seconds.toString().padStart(2, '0');
}

function playTimerSound() {
    if (!audioContext) return;
    
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

function updateStrengthStandards() {
    if (!exerciseStandards[currentExercise]) return;
    
    const userWeight = parseInt(document.getElementById('user-weight').textContent) || 180;
    const standards = exerciseStandards[currentExercise];
    
    if (currentExercise === 'weighted-chins' || currentExercise === 'weighted-dips') {
        // For weighted exercises, show additional weight
        document.getElementById('standard-good').textContent = Math.round(userWeight * standards.good);
        document.getElementById('standard-great').textContent = Math.round(userWeight * standards.great);
        document.getElementById('standard-godlike').textContent = Math.round(userWeight * standards.godlike);
    } else {
        // For other exercises, show total weight
        document.getElementById('standard-good').textContent = Math.round(userWeight * standards.good);
        document.getElementById('standard-great').textContent = Math.round(userWeight * standards.great);
        document.getElementById('standard-godlike').textContent = Math.round(userWeight * standards.godlike);
    }
}

function checkPersonalRecord(weight, reps) {
    const prKey = `pr_${currentExercise}`;
    const lastPR = parseFloat(localStorage.getItem(prKey) || 0);
    
    if (weight > lastPR) {
        localStorage.setItem(prKey, weight);
        KinobodyApp.showNotification('New Personal Record! 🎉', 'success');
        
        // Update PR display
        const prIndicator = document.querySelector('.pr-indicator');
        prIndicator.classList.remove('hidden');
        document.getElementById('pr-weight').textContent = weight;
    }
}

function saveExercise() {
    const exerciseData = {
        exercise: currentExercise,
        exerciseName: document.querySelector(`#exercise-select option[value="${currentExercise}"]`).textContent,
        sets: []
    };
    
    // Collect set data
    for (let i = 1; i <= 3; i++) {
        const weight = parseFloat(document.querySelector(`.set-weight[data-set="${i}"]`).value);
        const reps = parseInt(document.querySelector(`.set-reps[data-set="${i}"]`).value);
        
        if (weight && reps) {
            exerciseData.sets.push({ set: i, weight, reps });
        }
    }
    
    if (exerciseData.sets.length === 0) {
        KinobodyApp.showNotification('No completed sets to save', 'error');
        return;
    }
    
    // Add to workout data
    workoutData.push(exerciseData);
    
    // Save to local storage
    const today = new Date().toISOString().split('T')[0];
    const workoutKey = `workout_${today}`;
    localStorage.setItem(workoutKey, JSON.stringify(workoutData));
    
    // Save last workout for this exercise
    const lastWorkoutKey = `last_${currentExercise}`;
    localStorage.setItem(lastWorkoutKey, JSON.stringify({
        date: today,
        weight: exerciseData.sets[0].weight,
        reps: exerciseData.sets[0].reps
    }));
    
    // Update workout summary
    updateWorkoutSummary();
    
    // Reset for next exercise
    resetForNextExercise();
    
    KinobodyApp.showNotification('Exercise saved!', 'success');
}

function finishWorkout() {
    if (workoutData.length === 0) {
        KinobodyApp.showNotification('No exercises to save', 'error');
        return;
    }
    
    // Prepare workout data
    const workoutSession = {
        date: new Date().toISOString(),
        exercises: workoutData,
        duration: calculateWorkoutDuration()
    };
    
    // Try to save to server
    if (navigator.onLine) {
        KinobodyApp.API.logWorkout(workoutSession)
            .then(() => {
                KinobodyApp.showNotification('Workout saved successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            })
            .catch(error => {
                console.error('Failed to save workout:', error);
                KinobodyApp.Storage.addToQueue('workout', workoutSession);
                KinobodyApp.showNotification('Workout saved offline', 'warning');
            });
    } else {
        // Save to offline queue
        KinobodyApp.Storage.addToQueue('workout', workoutSession);
        KinobodyApp.showNotification('Workout saved offline', 'warning');
    }
}

function updateWorkoutSummary() {
    const summaryDiv = document.getElementById('workout-summary');
    const exerciseList = document.getElementById('exercise-list');
    
    summaryDiv.classList.remove('hidden');
    exerciseList.innerHTML = '';
    
    workoutData.forEach(exercise => {
        const exerciseItem = document.createElement('div');
        exerciseItem.className = 'exercise-item';
        
        const exerciseName = document.createElement('div');
        exerciseName.className = 'exercise-name';
        exerciseName.textContent = exercise.exerciseName;
        
        const exerciseSets = document.createElement('div');
        exerciseSets.className = 'exercise-sets';
        exerciseSets.textContent = exercise.sets.map(s => `${s.weight} lbs × ${s.reps}`).join(', ');
        
        exerciseItem.appendChild(exerciseName);
        exerciseItem.appendChild(exerciseSets);
        exerciseList.appendChild(exerciseItem);
    });
    
    document.getElementById('finish-workout').classList.remove('hidden');
}

function resetForNextExercise() {
    // Reset exercise selection
    document.getElementById('exercise-select').value = '';
    
    // Hide sections
    hideAllSections();
    
    // Reset form inputs
    document.querySelectorAll('.weight-input, .reps-input').forEach(input => {
        input.value = '';
    });
    
    // Reset sets
    resetSets();
    
    // Hide save button
    document.getElementById('save-exercise').classList.add('hidden');
}

function resetSets() {
    document.querySelectorAll('.rpt-set').forEach((set, index) => {
        set.classList.remove('completed');
        
        if (index === 0) {
            set.classList.remove('disabled');
            set.querySelector('.set-status').textContent = 'PENDING';
            set.querySelector('.complete-set').disabled = false;
        } else {
            set.classList.add('disabled');
            set.querySelector('.set-status').textContent = 'LOCKED';
            set.querySelector('.set-reps').disabled = true;
            set.querySelector('.complete-set').disabled = true;
        }
    });
}

function hideAllSections() {
    document.getElementById('warmup-section').classList.add('hidden');
    document.getElementById('rpt-sets').classList.add('hidden');
    document.getElementById('rest-timer').classList.add('hidden');
    document.getElementById('strength-standards').classList.add('hidden');
    document.getElementById('last-workout-info').classList.add('hidden');
}

function loadLastWorkout() {
    const today = new Date().toISOString().split('T')[0];
    const workoutKey = `workout_${today}`;
    const savedWorkout = localStorage.getItem(workoutKey);
    
    if (savedWorkout) {
        workoutData = JSON.parse(savedWorkout);
        updateWorkoutSummary();
    }
}

function loadLastExerciseData(exercise) {
    const lastWorkoutKey = `last_${exercise}`;
    const lastWorkout = localStorage.getItem(lastWorkoutKey);
    
    if (lastWorkout) {
        const data = JSON.parse(lastWorkout);
        const lastWorkoutInfo = document.getElementById('last-workout-info');
        
        lastWorkoutInfo.classList.remove('hidden');
        document.getElementById('last-weight').textContent = data.weight;
        document.getElementById('last-reps').textContent = data.reps;
        
        // Show PR if exists
        const prKey = `pr_${exercise}`;
        const pr = localStorage.getItem(prKey);
        if (pr) {
            document.querySelector('.pr-indicator').classList.remove('hidden');
            document.getElementById('pr-weight').textContent = pr;
        }
    }
}

function calculateWorkoutDuration() {
    // Simple duration calculation - could be enhanced with actual tracking
    return workoutData.length * 15; // Estimate 15 minutes per exercise
}