"""
Quick test to verify everything works without numpy
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic():
    print("Testing basic imports...")
    
    try:
        import google.generativeai
        print("✅ google-generativeai imported")
    except ImportError as e:
        print(f"❌ google-generativeai: {e}")
        return False
    
    try:
        import requests
        print("✅ requests imported")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        import streamlit
        print("✅ streamlit imported")
    except ImportError as e:
        print(f"❌ streamlit: {e}")
        return False
    
    try:
        from assistant.skills import Skills
        skills = Skills()
        print(f"✅ Skills created: {skills.get_time_date()}")
    except Exception as e:
        print(f"❌ Skills: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("AI Assistant - Quick Setup Test")
    print("=" * 60)
    
    if test_basic():
        print("\n" + "=" * 60)
        print("✅ All basic tests passed!")
        print("\nYou can now:")
        print("1. Get Gemini API key from: https://aistudio.google.com/app/apikey")
        print("2. Update .env file with your key")
        print("3. Run: python app.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed.")
        print("Try installing packages manually:")
        print("pip install google-generativeai streamlit requests")
        print("=" * 60)

if __name__ == "__main__":
    main()