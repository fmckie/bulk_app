# AI-Powered Meal Prep Feature - Setup Guide

This guide will walk you through setting up the new AI-powered meal prep feature for the Kinobody tracker.

## Prerequisites

- Python 3.8+ installed
- Supabase project (or use demo mode)
- OpenAI API key
- Basic familiarity with terminal/command line

## Step 1: Environment Setup

### 1.1 Create Environment File

Create a `.env` file in the project root (if it doesn't exist):

```bash
cp .env.example .env
```

### 1.2 Add Your OpenAI API Key

Edit the `.env` file and add your OpenAI API key:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-0125-preview
```

⚠️ **Security Warning**: Never commit your `.env` file to git. It should already be in `.gitignore`.

### 1.3 Get Your OpenAI API Key

If you don't have an API key:
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key and add it to your `.env` file

## Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- OpenAI (AI integration)
- Supabase (database)
- Redis (caching)
- Other dependencies

## Step 3: Database Setup (Supabase Users)

### 3.1 Run the Migration

If you have Supabase configured, run the migration to create the meal prep tables:

```bash
# Using Supabase CLI
supabase db push migrations/create_meal_prep_tables.sql

# Or manually in Supabase SQL Editor:
# 1. Go to your Supabase project
# 2. Navigate to SQL Editor
# 3. Copy contents of migrations/create_meal_prep_tables.sql
# 4. Run the query
```

### 3.2 Verify Tables Created

Check that these tables were created:
- `meal_plans`
- `recipes`
- `meal_plan_meals`
- `shopping_lists`
- `user_meal_preferences`

### 3.3 Demo Mode (No Supabase)

If you don't have Supabase configured, the app will run in demo mode automatically. Demo mode provides:
- Pre-generated meal plans
- Mock AI responses
- Local storage for testing

## Step 4: Running the Application

### 4.1 Start the Flask Server

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:8000
```

### 4.2 Access the Meal Prep Feature

Open your browser and navigate to:
- Main app: http://localhost:8000
- Meal prep feature: http://localhost:8000/meal-prep

## Step 5: Testing the Feature

### 5.1 Generate Your First Meal Plan

1. Click "Meal Prep" from the dashboard or navigation
2. Fill out the form:
   - Select dietary requirements (optional)
   - Set weekly budget ($150 recommended)
   - Choose preferred store
   - Add any food allergies/exclusions
3. Click "Generate Meal Plan"
4. Wait for AI to create your personalized plan (15-30 seconds)

### 5.2 Explore Generated Features

Once generated, you can:
- **View 7-Day Plan**: Click day tabs to see meals
- **Check Nutrition**: Each day shows calories and macros
- **Shopping List**: Organized by store sections with costs
- **Save Plan**: Click "Save Plan" to store for later
- **Export PDF**: Print or save as PDF
- **AI Chat**: Click the robot icon for help

### 5.3 Test Without OpenAI (Demo Mode)

To test without using OpenAI credits:
1. Uncheck "Use AI Assistant" in the form
2. Or remove OPENAI_API_KEY from `.env`
3. The system will use pre-built demo meal plans

## Step 6: Customization

### 6.1 Adjust Nutritional Formulas

Edit `services/meal_prep_service.py`:

```python
# Current Kinobody formula (line ~30)
maintenance_calories = body_weight * 15  # Change multiplier
protein_target = body_weight  # 1g per lb

# Training day surplus
if is_training_day:
    total_calories = maintenance_calories + 500  # Adjust surplus
else:
    total_calories = maintenance_calories + 100  # Adjust surplus
```

### 6.2 Add More Dietary Options

Edit `templates/meal-prep.html` (line ~20):

```html
<label class="checkbox-label">
    <input type="checkbox" name="dietary_requirements" value="your-new-diet">
    <span>Your New Diet</span>
</label>
```

### 6.3 Customize AI Behavior

Edit `services/openai_meal_service.py` to modify prompts and responses.

## Step 7: Production Deployment

### 7.1 Docker Deployment

```bash
# Build image
docker build -t kinobody-tracker .

# Run container
docker run -d -p 80:80 --env-file .env kinobody-tracker
```

### 7.2 DigitalOcean App Platform

1. Push code to GitHub
2. Create new app in DigitalOcean
3. Add environment variables in app settings
4. Deploy

### 7.3 Environment Variables for Production

Set these in your deployment platform:
```
FLASK_ENV=production
OPENAI_API_KEY=your-key
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
```

## Troubleshooting

### Issue: "AI service not available"
- **Solution**: Check OPENAI_API_KEY in `.env`
- Verify key is valid at https://platform.openai.com

### Issue: "Please log in to generate meal plans"
- **Solution**: Create account or use demo mode
- Set `DEMO_MODE=true` in environment

### Issue: Meal plan generation timeout
- **Solution**: OpenAI might be slow, wait 30-60 seconds
- Check browser console for errors

### Issue: Database errors
- **Solution**: Verify Supabase connection
- Check migrations were run successfully
- Use demo mode as fallback

## Usage Tips

### Optimal Settings for Kinobody Program
- **Budget**: $120-180/week for quality ingredients
- **Store**: Whole Foods or Trader Joe's for fresh options
- **Variety**: "Medium" for balance of efficiency and variety
- **Cooking Time**: 45 minutes max for practical meal prep

### Best Practices
1. Generate plans on Sunday for the week ahead
2. Review shopping list before going to store
3. Use AI chat for substitutions while shopping
4. Save successful plans for reuse
5. Rate meals to improve AI recommendations

## API Rate Limits

### OpenAI Limits
- GPT-4 Mini: ~90,000 tokens/min
- Each meal plan uses ~4,000 tokens
- Cost: ~$0.01-0.02 per meal plan generation

### Recommendations
- Cache generated plans in Redis
- Reuse saved plans when possible
- Use demo mode for testing

## Support

### Getting Help
- Check logs: `tail -f app.log`
- Review browser console for JS errors
- Test in demo mode first
- Verify all environment variables

### Common Questions

**Q: Can I use this without OpenAI?**
A: Yes, uncheck "Use AI Assistant" or remove API key for demo mode.

**Q: How accurate are the nutrition calculations?**
A: AI estimates are generally within 10% of actual values. For precision, use the recipe research endpoint.

**Q: Can I modify generated meal plans?**
A: Yes, use the AI chat to customize any meal or manually edit in the database.

**Q: Is my data secure?**
A: Yes, Supabase provides row-level security. Each user only sees their own data.

## Next Features (Roadmap)

- [ ] Grocery delivery integration
- [ ] Barcode scanning for nutrition
- [ ] Recipe photo upload
- [ ] Community meal plan sharing
- [ ] Macro tracking integration
- [ ] Cost tracking and analytics

---

**Ready to start?** Navigate to http://localhost:8000/meal-prep and create your first AI-powered meal plan!

For questions or issues, check the main [README.md](README.md) or open an issue on GitHub.