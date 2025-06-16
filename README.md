# ModulAIr - AI-Powered Personalized Learning Platform

ModulAIr is a modern, AI-driven educational platform that creates personalized tech courses using GPT API integration. Users can specify their learning preferences, and the AI generates custom course content, lessons, quizzes, and resources tailored to their needs.

## Features

### 🤖 AI-Powered Course Generation
- Custom course creation using GPT-4 via Azure AI Inference SDK
- Personalized content based on topic, proficiency level, and learning style
- Automatic generation of lessons, quizzes, and resource links

### 📚 Comprehensive Learning Experience
- Interactive lessons with rich content and code examples
- Progress tracking with visual indicators
- Mandatory quizzes with 70% passing requirement
- Certificate generation upon course completion

### 🎨 Modern User Interface
- Coursera-inspired clean and professional design
- Fully responsive layout for desktop and mobile
- Tailwind CSS for modern styling
- Smooth animations and transitions

### 📱 Mobile-First Design
- Touch-friendly interface elements
- Hamburger menu for mobile navigation
- Responsive grid layouts
- Optimized for all screen sizes

## Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLite** - Database for course data storage
- **Azure AI Inference SDK** - GPT API integration
- **Python 3.8+** - Runtime environment

### Frontend
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript** - Interactive functionality
- **Google Fonts (Inter)** - Typography
- **Font Awesome** - Icons

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- GitHub Personal Access Token with model access

### Environment Setup

1. **Set the GitHub Token:**
   ```bash
   export GITHUB_TOKEN="your-github-token-here"
   ```

2. **Set Session Secret (optional):**
   ```bash
   export SESSION_SECRET="your-secret-key-here"
   ```

### Installation

1. **Clone or download the project files**

2. **Install required dependencies:**
   ```bash
   pip install flask azure-ai-inference flask-sqlalchemy
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

4. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - For Replit: The app will be automatically accessible via the provided URL

### GitHub Marketplace GPT API Setup

The application uses the Azure AI Inference SDK to connect to GitHub's marketplace GPT models:

```python
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "gpt-4o-mini"
token = os.environ["GITHUB_TOKEN"]

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

```

## Local Development Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```
SESSION_SECRET=your_secret_key_here
A4F_API_KEY=your_a4f_api_key_here
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
flask run
```

## Database Configuration

The application uses SQLite for local development. The database file will be created automatically in the `instance/` folder as `modulair.db`.

## Environment Variables

- `SESSION_SECRET`: Secret key for Flask sessions
- `A4F_API_KEY`: API key for AI features

## Project Structure

- `app.py`: Main application file
- `models.py`: Database models
- `ai_service.py`: AI integration services
- `instance/`: Contains SQLite database
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, etc.)
