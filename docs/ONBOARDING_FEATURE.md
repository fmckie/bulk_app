# Enhanced User Profile Onboarding Feature

## Overview
This feature implements a mandatory multi-step onboarding flow for new users, ensuring they provide essential fitness information during signup.

## Features

### 1. **Multi-Step Signup Flow**
- **Step 1**: Email & Password (simplified initial signup)
- **Step 2**: Profile Setup (username, weight, height)
- **Step 3**: Fitness Goals (primary goal, targets, activity level)
- **Step 4**: Welcome & Next Steps

### 2. **Smart Features**
- Real-time username availability checking
- Weight unit conversion (lbs/kg)
- BMI auto-calculation
- Reserved username protection
- Session management with 24-hour expiration
- Skip option for optional flow

### 3. **Security & Validation**
- Username format validation (3-20 chars, alphanumeric + underscore)
- Weight range validation (50-500 lbs)
- Reserved usernames list
- Row Level Security (RLS) on all tables
- Secure onboarding sessions

## Database Schema

### New Tables
1. **onboarding_sessions** - Manages multi-step onboarding state
2. **fitness_goals** - Predefined fitness goal options
3. **reserved_usernames** - Blocked usernames list

### Enhanced Tables
1. **profiles** - Added fields:
   - `weight_unit` (lbs/kg)
   - `height` (inches)
   - `bmi` (auto-calculated)
   - `onboarding_completed` (boolean)
   - `onboarding_started_at` / `onboarding_completed_at`

## Implementation

### Backend Components
- **ProfileDB**: Enhanced with validation methods
- **OnboardingDB**: New class for session management
- **API Endpoints**: 
  - `/api/onboarding/start`
  - `/api/onboarding/check-username`
  - `/api/onboarding/profile`
  - `/api/onboarding/goals`
  - `/api/onboarding/skip`

### Frontend Components
- **Templates**: Step-by-step onboarding pages
- **JavaScript**: Form validation and API integration
- **CSS**: Professional, mobile-responsive design

### Middleware
- `require_onboarding_complete()` decorator ensures users complete profile setup

## Setup Instructions

1. **Run Database Migration**
   ```bash
   python scripts/setup_onboarding.py
   ```
   Copy the SQL output and run in Supabase SQL editor.

2. **Deploy Application**
   - Commit changes to git
   - Deploy to your hosting platform

3. **Test the Flow**
   - Sign up as a new user
   - Complete the onboarding steps
   - Verify profile data is saved

## User Flow

1. User signs up with email/password only
2. Automatically redirected to `/onboarding/profile`
3. Enters username, weight, and optional height
4. Proceeds to `/onboarding/goals`
5. Selects fitness goal and sets targets
6. Completes at `/onboarding/complete` with summary
7. Can access full app features

## Customization

### Adding New Goals
Add to the `fitness_goals` table:
```sql
INSERT INTO fitness_goals (id, name, description, icon, recommended_activity_level)
VALUES ('custom_goal', 'Custom Goal', 'Your description', '🎯', 'moderately_active');
```

### Modifying Required Fields
Update validation in `ProfileDB.update_profile_with_validation()`:
```python
required_fields = ['username', 'body_weight', 'primary_goal']  # Add/remove as needed
```

### Styling
Edit `/static/css/onboarding.css` for visual customizations.

## Best Practices

1. **Data Privacy**: All user data is isolated with RLS
2. **Validation**: Always validate on both client and server
3. **User Experience**: Keep forms simple and provide clear feedback
4. **Mobile First**: Test on mobile devices (425px width)
5. **Accessibility**: Include ARIA labels and keyboard navigation

## Troubleshooting

### Common Issues

1. **"Username not available"**
   - Check if username is in reserved list
   - Ensure it meets format requirements

2. **Onboarding session expired**
   - Sessions expire after 24 hours
   - User needs to start signup again

3. **Profile not updating**
   - Check browser console for errors
   - Verify user is authenticated
   - Check Supabase logs

### Debug Mode
Enable debug logging:
```javascript
// In onboarding.js
const DEBUG = true;  // Set to true for console logging
```

## Future Enhancements

1. **Social Login Onboarding**: Handle OAuth users
2. **Progress Photos**: Initial photo upload during onboarding
3. **Fitness Assessment**: Quick questionnaire for personalization
4. **Referral Tracking**: Track how users found the app
5. **A/B Testing**: Test different onboarding flows