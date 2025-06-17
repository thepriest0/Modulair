#!/usr/bin/env python3
"""
Test script for focused quiz and exam generation with environment setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

def check_environment():
    """Check if the environment is properly configured"""
    print("Environment Check")
    print("=" * 30)
    
    api_key = os.environ.get("A4F_API_KEY")
    if not api_key or api_key == "default-key":
        print("❌ A4F_API_KEY not found or is default")
        print("\nTo fix this:")
        print("1. Create a .env file in this directory")
        print("2. Add: A4F_API_KEY=your_actual_api_key_here")
        print("3. Replace 'your_actual_api_key_here' with your real A4F API key")
        return False
    
    print(f"✅ A4F_API_KEY found: {api_key[:10]}...")
    
    youtube_key = os.environ.get("YOUTUBE_API_KEY")
    if youtube_key:
        print(f"✅ YOUTUBE_API_KEY found: {youtube_key[:10]}...")
    else:
        print("⚠️  YOUTUBE_API_KEY not found (optional)")
    
    return True

def test_basic_functionality():
    """Test basic functionality without making API calls"""
    print("\nBasic Functionality Test")
    print("=" * 30)
    
    try:
        from ai_service import AIService
        ai_service = AIService()
        print("✅ AIService initialized successfully")
        
        # Test the robust JSON parsing with a simple case
        test_json = '{"test": "value"}'
        result = ai_service._robust_json_parse(test_json)
        if result and result.get('test') == 'value':
            print("✅ Robust JSON parsing works")
        else:
            print("❌ Robust JSON parsing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_api_connection():
    """Test API connection if environment is configured"""
    print("\nAPI Connection Test")
    print("=" * 30)
    
    try:
        from ai_service import AIService
        ai_service = AIService()
        
        # Test a simple API call
        print("Testing API connection...")
        response = ai_service.client.chat.completions.create(
            model=ai_service.model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
            timeout=15.0
        )
        
        if response and response.choices:
            print("✅ API connection successful")
            return True
        else:
            print("❌ API connection failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Focused Fix Test Suite")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Test basic functionality
    basic_ok = test_basic_functionality()
    
    # Test API connection if environment is OK
    api_ok = False
    if env_ok:
        api_ok = test_api_connection()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Environment: {'✅ OK' if env_ok else '❌ FAILED'}")
    print(f"Basic Functionality: {'✅ OK' if basic_ok else '❌ FAILED'}")
    print(f"API Connection: {'✅ OK' if api_ok else '❌ FAILED'}")
    
    if env_ok and basic_ok and api_ok:
        print("\n🎉 All tests passed! You can now run the full quiz generation test.")
        print("Run: python test_quiz_generation.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running the full test.") 