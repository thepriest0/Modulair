# ModulAIr - AI-Powered Personalized Learning Platform

## Overview

ModulAIr is a modern AI-driven educational platform that creates personalized tech courses using GPT API integration. The platform allows users to specify their learning preferences (topic, proficiency level, and learning style), and the AI generates custom course content including lessons, quizzes, and resource links. Upon successful completion (70% quiz pass rate), users receive certificates.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: Azure AI Inference SDK with GitHub's GPT-4.1-nano model
- **Session Management**: Flask sessions with secure cookie handling
- **Deployment**: Gunicorn WSGI server with autoscale deployment target

### Frontend Architecture
- **UI Framework**: HTML5 with Tailwind CSS (CDN-based)
- **Styling**: Modern, Coursera-inspired design with Inter font family
- **Icons**: Font Awesome for consistent iconography
- **JavaScript**: Vanilla JavaScript for interactive functionality
- **Responsive Design**: Mobile-first approach with hamburger navigation

### Database Schema
- **Course**: Stores course metadata (title, topic, proficiency, learning style, description, outline)
- **Lesson**: Contains lesson content with order indexing and resource links
- **Quiz**: Holds quiz questions and answers in JSON format
- **Progress**: Tracks user progress with completion percentages and current lesson position

## Key Components

### AI Service (`ai_service.py`)
- Handles GPT API integration using Azure AI Inference SDK
- Generates complete course structures with lessons, quizzes, and resources
- Implements fallback mechanisms for API failures
- Uses structured JSON prompts for consistent course generation

### Models (`models.py`)
- SQLAlchemy models with proper relationships
- JSON field storage for complex data (outlines, resources, quiz questions)
- Timestamp tracking for creation and updates
- Foreign key relationships between courses, lessons, and quizzes

### Template System
- Jinja2 templates with base template inheritance
- Mobile-responsive design patterns
- Progress tracking visualization
- Interactive quiz interfaces with validation
- Certificate generation with completion verification

### Static Assets
- Custom CSS with gradient styling and smooth transitions
- JavaScript for mobile menu, form validation, and dynamic content
- Responsive grid layouts and animations

## Data Flow

1. **Course Creation**: User selects preferences → AI generates course structure → Preview generated content → Save to database
2. **Learning Flow**: Access course → Navigate lessons sequentially → Complete mandatory quizzes → Track progress
3. **Assessment**: Quiz submission → Validation (70% pass required) → Progress update → Certificate generation
4. **Progress Tracking**: Real-time progress calculation → Visual progress bars → Lesson completion status

## External Dependencies

### AI Integration
- **Azure AI Inference SDK**: GPT API access through GitHub's inference endpoint
- **Authentication**: GitHub Personal Access Token with model access
- **Model**: OpenAI GPT-4.1-nano for course content generation

### Frontend Dependencies
- **Tailwind CSS**: Utility-first CSS framework (CDN)
- **Google Fonts**: Inter font family for typography
- **Font Awesome**: Icon library for UI elements

### Backend Dependencies
- **Flask**: Web framework with SQLAlchemy integration
- **Gunicorn**: Production WSGI server
- **PostgreSQL**: Database support (psycopg2-binary included)
- **Additional**: Email validation, OAuth support, JWT handling

## Deployment Strategy

### Replit Configuration
- **Environment**: Python 3.11 with Nix package management
- **Packages**: OpenSSL and PostgreSQL system dependencies
- **Deployment**: Autoscale target with Gunicorn binding to 0.0.0.0:5000
- **Workflows**: Parallel execution with hot-reload development mode

### Production Setup
- **WSGI Server**: Gunicorn with reuse-port and reload options
- **Port Configuration**: Internal port 5000 mapped to external port 80
- **Environment Variables**: Secure session keys and GitHub token management
- **Database**: SQLite for development, PostgreSQL support for production scaling

### Security Considerations
- Session secret key configuration
- Token-based API authentication
- Input validation and sanitization
- HTTPS proxy configuration with ProxyFix middleware

## Changelog
- June 14, 2025. Initial setup with basic course platform
- June 14, 2025. Implemented comprehensive authentication system with Flask-Login
- June 14, 2025. Enhanced course features with assignments, detailed assessments, and final exams
- June 14, 2025. Added user registration/login with secure password hashing
- June 14, 2025. Integrated comprehensive quiz tracking and attempt management
- June 14, 2025. Implemented assignment submission system with status tracking
- June 14, 2025. Created final exam workflow with certificate generation
- June 15, 2025. Added comprehensive profile management system with enhanced User model
- June 15, 2025. Implemented account settings, password change, and account deletion features
- June 15, 2025. Created professional navigation with dropdown profile menu
- June 15, 2025. Fixed quiz system to ensure all question types have proper answer fields
- June 15, 2025. Limited quiz questions to 1-3 maximum for better user experience

## Recent System Enhancements

### Authentication System
- User registration and login with Flask-Login integration
- Secure password hashing using Werkzeug
- Session management with proper authentication decorators
- User profile management with full name display
- Protected routes requiring authentication

### Enhanced Course Features
- **Comprehensive Assessments**: Multiple quizzes between lessons with pass/fail tracking
- **Assignment System**: Practical assignments with submission tracking and feedback
- **Final Examinations**: Comprehensive final exams required for course completion
- **Certificate Generation**: Automated certificates upon successful course completion
- **Progress Tracking**: Enhanced progress tracking with quiz scores and assignment status

### Database Schema Updates
- User model with authentication fields
- Assignment and AssignmentSubmission models for hands-on work
- QuizAttempt model for detailed quiz tracking
- Enhanced Progress model with final exam scores and completion dates

### AI Course Generation
- Enhanced AI prompts for comprehensive course content (800+ words per lesson)
- Assignment generation with practical exercises
- Multi-level assessment creation (quizzes + final exam)
- Resource link integration with real-world references

## User Preferences

Preferred communication style: Simple, everyday language.