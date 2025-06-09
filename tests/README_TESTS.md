# Nutrition Feature Test Suite

## Overview
Comprehensive test suite for the nutrition tracking feature in the Kinobody Greek God Program Tracker.

## Test Structure

### 1. API Tests (`test_nutrition_api.py`)
- Tests all nutrition API endpoints
- Verifies proper request/response handling
- Tests authentication and demo mode behavior
- Tests training day detection integration

### 2. Business Logic Tests (`test_nutrition_calculations.py`)
- Tests nutrition calculation formulas
- Verifies Kinobody protocol implementation:
  - Maintenance calories: 15 cal/lb body weight
  - Training days: +500 calories
  - Rest days: +100 calories
  - Protein: 1g/lb body weight
  - Fats: 25% of total calories
  - Carbs: remaining calories

### 3. Integration Tests (`test_nutrition_integration.py`)
- Tests nutrition + workout integration
- Verifies training day detection from workouts
- Tests multi-day scenarios
- Tests edge cases

### 4. End-to-End Tests (`test_nutrition_e2e.py`)
- Tests complete user workflows
- Daily nutrition tracking scenarios
- Weekly review workflows
- Calorie cycling verification

## Running Tests

### Install Dependencies
```bash
pip3 install -r requirements.txt
```

### Run All Tests
```bash
python3 -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# API tests only
python3 -m pytest tests/test_nutrition_api.py -v

# Calculation tests only
python3 -m pytest tests/test_nutrition_calculations.py -v

# Integration tests only
python3 -m pytest tests/test_nutrition_integration.py -v

# E2E tests only
python3 -m pytest tests/test_nutrition_e2e.py -v
```

### Run with Coverage
```bash
python3 -m pytest tests/ --cov=. --cov-report=html
# View coverage report in htmlcov/index.html
```

### Run Specific Test
```bash
python3 -m pytest tests/test_nutrition_api.py::TestNutritionAPI::test_save_nutrition_demo_mode -v
```

## Test Data

### Demo User Profile
- Email: wfmckie@gmail.com
- Password: 123456
- Body weight: 175 lbs

### Calculated Targets (175 lb user)
- Maintenance: 2625 calories
- Training day: 3125 calories (+500)
- Rest day: 2725 calories (+100)
- Protein: 175g (all days)
- Training day macros: 175g protein, 87g fat, 411g carbs
- Rest day macros: 175g protein, 76g fat, 336g carbs

## Common Issues

### Tests Failing Due to Date Issues
Some tests use `date.today()` which can cause issues if run across date boundaries. Fixed by using static dates in critical tests.

### Demo Data Persistence
Tests use `clear_demo_data` fixture to ensure clean state between tests.

### Authentication in Tests
Use `auth_client` fixture for authenticated requests, which automatically signs in with demo credentials.

## Writing New Tests

1. Import required fixtures from conftest.py
2. Use `clear_demo_data` when testing requires clean state
3. Use `auth_client` for authenticated endpoints
4. Follow existing naming conventions:
   - `test_` prefix for all test functions
   - Descriptive names explaining what is tested
   - Group related tests in classes

## CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    python -m pytest tests/ --cov=. --cov-report=xml
```