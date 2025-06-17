#!/usr/bin/env python3
"""
Test script for robust JSON parsing functionality
This script tests the AIService's robust JSON parsing methods with various malformed JSON inputs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_service import AIService

def test_robust_json_parsing():
    """Test the robust JSON parsing with various malformed inputs"""
    
    # Initialize AIService without app context for testing
    ai_service = AIService()
    
    # Test cases with malformed JSON that should be fixed
    test_cases = [
        {
            "name": "Unescaped newlines in content",
            "input": '''{
                "lessons": [
                    {
                        "title": "Test Lesson",
                        "content": "<h1>Title</h1>
<p>This paragraph has
multiple lines and "quotes"</p>"
                    }
                ]
            }''',
            "expected_keys": ["lessons"]
        },
        {
            "name": "Unescaped quotes in content",
            "input": '''{
                "title": "Course with "quotes" in title",
                "description": "Description with 'single' and "double" quotes"
            }''',
            "expected_keys": ["title", "description"]
        },
        {
            "name": "Markdown code blocks",
            "input": '''```json
{
    "test": "value",
    "content": "Some content with
newlines"
}
```''',
            "expected_keys": ["test", "content"]
        },
        {
            "name": "Control characters",
            "input": '''{
                "text": "Text with control chars: \x00\x01\x02 and unicode: \ufffd"
            }''',
            "expected_keys": ["text"]
        },
        {
            "name": "Mixed issues",
            "input": '''```json
{
    "title": "Title with "quotes" and
newlines",
    "content": "Content with \t tabs and \r carriage returns"
}
```''',
            "expected_keys": ["title", "content"]
        }
    ]
    
    print("Testing robust JSON parsing...")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Test the robust parsing
            result = ai_service._robust_json_parse(test_case['input'])
            
            # Check if expected keys are present
            missing_keys = [key for key in test_case['expected_keys'] if key not in result]
            
            if missing_keys:
                print(f"❌ FAILED: Missing expected keys: {missing_keys}")
                print(f"   Result keys: {list(result.keys())}")
                failed += 1
            else:
                print(f"✅ PASSED: Successfully parsed JSON")
                print(f"   Result keys: {list(result.keys())}")
                passed += 1
                
        except Exception as e:
            print(f"❌ FAILED: Exception occurred: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The robust JSON parsing is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. The robust JSON parsing may need improvements.")
        return False

def test_sanitization():
    """Test the sanitization function specifically"""
    
    ai_service = AIService()
    
    print("\nTesting sanitization function...")
    print("=" * 50)
    
    # Test sanitization of problematic content
    problematic_content = '''{
        "title": "Title with "unescaped quotes" and
newlines",
        "content": "Content with \t tabs and \r returns"
    }'''
    
    try:
        sanitized = ai_service._sanitize_json_content(problematic_content)
        print("Original content preview:")
        print(problematic_content[:100] + "...")
        print("\nSanitized content preview:")
        print(sanitized[:100] + "...")
        
        # Try to parse the sanitized content
        import json
        parsed = json.loads(sanitized)
        print(f"\n✅ Sanitization successful! Parsed keys: {list(parsed.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Sanitization failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Robust JSON Parsing Test Suite")
    print("=" * 50)
    
    # Run tests
    parsing_success = test_robust_json_parsing()
    sanitization_success = test_sanitization()
    
    if parsing_success and sanitization_success:
        print("\n🎉 All tests completed successfully!")
        print("The robust JSON parsing system is ready to handle malformed API responses.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.") 