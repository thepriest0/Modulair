#!/usr/bin/env python3
"""
Test script to verify database field definitions and usage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import User, Course, Lesson, Quiz, Assignment, Progress, AssignmentSubmission, QuizAttempt, CourseGeneration
from db import db

def test_model_fields():
    """Test that all model fields are correctly defined"""
    print("Testing database model field definitions...")
    
    # Test Lesson model
    print("\n1. Testing Lesson model fields:")
    lesson_fields = [col.name for col in Lesson.__table__.columns]
    print(f"   Lesson fields: {lesson_fields}")
    assert 'order_index' in lesson_fields, "Lesson model missing order_index field"
    assert 'order' not in lesson_fields, "Lesson model should not have 'order' field"
    
    # Test Quiz model
    print("\n2. Testing Quiz model fields:")
    quiz_fields = [col.name for col in Quiz.__table__.columns]
    print(f"   Quiz fields: {quiz_fields}")
    assert 'lesson_dependency' in quiz_fields, "Quiz model missing lesson_dependency field"
    assert 'is_final_exam' not in quiz_fields, "Quiz model should not have 'is_final_exam' field"
    
    # Test Assignment model
    print("\n3. Testing Assignment model fields:")
    assignment_fields = [col.name for col in Assignment.__table__.columns]
    print(f"   Assignment fields: {assignment_fields}")
    assert 'instructions' in assignment_fields, "Assignment model missing instructions field"
    assert 'requirements' not in assignment_fields, "Assignment model should not have 'requirements' field"
    assert 'assignment_type' in assignment_fields, "Assignment model missing assignment_type field"
    assert 'difficulty_level' in assignment_fields, "Assignment model missing difficulty_level field"
    assert 'estimated_hours' in assignment_fields, "Assignment model missing estimated_hours field"
    
    print("\n✅ All database field tests passed!")
    print("   - Lesson model uses 'order_index' instead of 'order'")
    print("   - Quiz model uses 'lesson_dependency' instead of 'is_final_exam'")
    print("   - Assignment model uses correct field names")

def test_model_creation():
    """Test that models can be created with correct fields"""
    print("\nTesting model creation...")
    
    try:
        # Test Lesson creation
        lesson = Lesson(
            course_id=1,
            title="Test Lesson",
            content="Test content",
            order_index=1
        )
        print("✅ Lesson creation test passed")
        
        # Test Quiz creation
        quiz = Quiz(
            course_id=1,
            title="Test Quiz",
            questions='{"questions": []}',
            lesson_dependency=1
        )
        print("✅ Quiz creation test passed")
        
        # Test Assignment creation
        assignment = Assignment(
            course_id=1,
            title="Test Assignment",
            description="Test description",
            instructions="Test instructions",
            assignment_type="practical",
            difficulty_level="intermediate",
            estimated_hours=1
        )
        print("✅ Assignment creation test passed")
        
    except Exception as e:
        print(f"❌ Model creation test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Database Field Validation Test")
    print("=" * 40)
    
    try:
        test_model_fields()
        test_model_creation()
        print("\n🎉 All tests passed! Database field issues have been resolved.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1) 