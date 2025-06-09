#!/usr/bin/env python3
"""
Check database connection and setup
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Checking database configuration...")

# Check environment variables
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    print("\n⚠️  WARNING: Supabase credentials not found!")
    print("The app will run in DEMO MODE.")
    print("\nTo use Supabase:")
    print("1. Create a Supabase project at https://supabase.com")
    print("2. Copy your project URL and anon key")
    print("3. Add them to your .env file:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_KEY=your-anon-key-here")
else:
    print("✅ Supabase credentials found")
    print(f"   URL: {supabase_url}")
    print("   Key: ****" + supabase_key[-4:])
    
    try:
        from database.connection import check_supabase_connection
        if check_supabase_connection():
            print("✅ Successfully connected to Supabase!")
        else:
            print("❌ Failed to connect to Supabase")
            print("   Please check your credentials")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        print("   The app will run in DEMO MODE.")

print("\nTo run the app:")
print("  python3 app.py")
print("\nThe app will be available at:")
print("  http://localhost:8000")