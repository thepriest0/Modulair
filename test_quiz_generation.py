#!/usr/bin/env python3
"""
Test script for focused quiz and exam generation
This script tests the new individual question generation approach
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

from ai_service import AIService

def test_quiz_generation():
    """Test the new quiz generation system"""
    
    # Check if API key is available
    api_key = os.environ.get("A4F_API_KEY")
    if not api_key or api_key == "default-key":
        print("❌ A4F_API_KEY not found or is default. Please set it in your .env file or environment.")
        print("   Create a .env file with: A4F_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"✅ Using A4F API key: {api_key[:10]}...")
    
    # Initialize AIService without app context for testing
    ai_service = AIService()
    
    print("Testing Focused Quiz and Exam Generation")
    print("=" * 50)
    
    # Test data
    outline_data = {
        "outline": ["Introduction", "Basics", "Advanced", "Practice", "Review"]
    }
    
    try:
        print("\n1. Testing single question generation...")
        question = ai_service._generate_single_question("Python Programming", "Beginner", 1)
        if question:
            print(f"✅ Single question generated successfully")
            print(f"   Type: {question.get('type')}")
            print(f"   Question: {question.get('question', '')[:50]}...")
        else:
            print("❌ Single question generation failed")
            return False
        
        print("\n2. Testing single quiz generation...")
        quiz = ai_service._generate_single_quiz("Python Programming", "Beginner", 1, 2, outline_data)
        if quiz:
            print(f"✅ Single quiz generated successfully")
            print(f"   Title: {quiz.get('title')}")
            print(f"   Questions: {len(quiz.get('questions', []))}")
        else:
            print("❌ Single quiz generation failed")
            return False
        
        print("\n3. Testing full quiz generation...")
        quizzes = ai_service._generate_quizzes(outline_data, "Python Programming", "Beginner", "test-id")
        if quizzes:
            print(f"✅ Full quiz generation successful")
            print(f"   Total quizzes: {len(quizzes)}")
            for i, quiz in enumerate(quizzes):
                print(f"   Quiz {i+1}: {len(quiz.get('questions', []))} questions")
        else:
            print("❌ Full quiz generation failed")
            return False
        
        print("\n4. Testing final exam question generation...")
        exam_question = ai_service._generate_final_exam_question("Python Programming", "Beginner", 1, outline_data)
        if exam_question:
            print(f"✅ Final exam question generated successfully")
            print(f"   Type: {exam_question.get('type')}")
        else:
            print("❌ Final exam question generation failed")
            return False
        
        print("\n5. Testing assignment generation...")
        assignment = ai_service._generate_assignment("Python Programming", "Beginner")
        if assignment:
            print(f"✅ Assignment generated successfully")
            print(f"   Title: {assignment.get('title')}")
        else:
            print("❌ Assignment generation failed")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! The focused quiz/exam generation is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_quiz_generation()
    if success:
        print("\nThe focused fix for quiz and exam generation is ready!")
        print("This should significantly reduce JSON parsing errors.")
    else:
        print("\nSome tests failed. The system may need further adjustments.") 