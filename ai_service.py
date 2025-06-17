# Applying the specified changes to the original code file.
import os
import json
import logging
import threading
import time
from openai import OpenAI
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models import CourseGeneration, db

class AIService:
    def __init__(self, app=None):
        self.app = app
        self.a4f_api_key = os.environ.get("A4F_API_KEY", "default-key")
        self.a4f_base_url = "https://api.a4f.co/v1"
        self.model = "provider-5/gpt-4o"
        self.youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        
        # Add debug logging for YouTube API key
        logging.info(f"YouTube API Key present: {bool(self.youtube_api_key)}")

        # Track generation status
        self.generation_status = {}
        self.generation_results = {}

        try:
            self.client = OpenAI(
                api_key=self.a4f_api_key,
                base_url=self.a4f_base_url,
                timeout=120.0  # Increased to 2 minutes
            )
            
            # Initialize YouTube API client if key is available
            if self.youtube_api_key:
                logging.info("Attempting to initialize YouTube API client...")
                self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
                logging.info("YouTube API client initialized successfully")
            else:
                logging.warning("YouTube API key not found. Video search functionality will be limited.")
                self.youtube = None
                
        except Exception as e:
            logging.error(f"Failed to initialize AI client: {str(e)}")
            self.client = None

    def _sanitize_json_content(self, content):
        """Sanitize content to make it valid JSON by escaping control characters"""
        if not content:
            return content
            
        # Convert to string if needed
        content = str(content)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Handle common JSON extraction patterns
        # Remove markdown code blocks
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            if end == -1:
                end = len(content)
            content = content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            if end == -1:
                end = len(content)
            content = content[start:end].strip()
        
        # Find the actual JSON object
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            content = content[brace_start:brace_end + 1]
        
        # Now sanitize the content within the JSON using a more robust approach
        def sanitize_json_strings(content):
            """Sanitize JSON string values by properly escaping them"""
            import re
            
            # This regex finds JSON string values and sanitizes them
            def replace_string(match):
                # Get the string value (without the surrounding quotes)
                string_value = match.group(1)
                
                if not string_value:
                    return '""'
                
                # Escape control characters and quotes
                escaped = string_value.replace('\\', '\\\\')  # Escape backslashes first
                escaped = escaped.replace('"', '\\"')         # Escape quotes
                escaped = escaped.replace('\n', '\\n')        # Escape newlines
                escaped = escaped.replace('\r', '\\r')        # Escape carriage returns
                escaped = escaped.replace('\t', '\\t')        # Escape tabs
                escaped = escaped.replace('\b', '\\b')        # Escape backspace
                escaped = escaped.replace('\f', '\\f')        # Escape form feed
                
                # Remove any other control characters
                escaped = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', escaped)
                
                return f'"{escaped}"'
            
            # Use a more sophisticated regex to find JSON string values
            # This handles both simple strings and strings with escaped quotes
            pattern = r'"((?:[^"\\]|\\.)*)"'
            return re.sub(pattern, replace_string, content)
        
        # Apply the sanitization
        content = sanitize_json_strings(content)
        
        return content

    def _robust_json_parse(self, content, max_retries=3):
        """Robust JSON parsing with multiple fallback strategies and retry mechanism"""
        if not content:
            raise Exception("Empty content provided for JSON parsing")
        
        content = str(content).strip()
        
        # Strategy 1: Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logging.warning(f"Direct JSON parsing failed: {str(e)}")
        
        # Strategy 2: Try with sanitization
        try:
            sanitized_content = self._sanitize_json_content(content)
            return json.loads(sanitized_content)
        except json.JSONDecodeError as e:
            logging.warning(f"Sanitized JSON parsing failed: {str(e)}")
        
        # Strategy 3: Try with more aggressive cleaning
        try:
            # Remove any potential markdown or extra formatting
            cleaned_content = content
            if cleaned_content.startswith('```'):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # Find JSON object boundaries
            brace_start = cleaned_content.find('{')
            brace_end = cleaned_content.rfind('}')
            if brace_start != -1 and brace_end != -1:
                cleaned_content = cleaned_content[brace_start:brace_end + 1]
            
            # Apply sanitization again
            sanitized_content = self._sanitize_json_content(cleaned_content)
            return json.loads(sanitized_content)
        except json.JSONDecodeError as e:
            logging.warning(f"Aggressive cleaning JSON parsing failed: {str(e)}")
        
        # Strategy 4: Try with manual character replacement and structure fixing
        try:
            # Replace problematic characters manually
            manual_content = content
            
            # Find JSON object boundaries first
            brace_start = manual_content.find('{')
            brace_end = manual_content.rfind('}')
            if brace_start != -1 and brace_end != -1:
                manual_content = manual_content[brace_start:brace_end + 1]
            
            # Fix common structural issues
            # Remove any trailing commas before closing braces/brackets
            manual_content = re.sub(r',(\s*[}\]])', r'\1', manual_content)
            
            # Fix unescaped quotes in string values
            # This is a more aggressive approach to fix quotes
            lines = manual_content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Look for lines with unescaped quotes in string values
                if '":' in line and '"' in line.split('":')[1]:
                    # This line has a string value with potential unescaped quotes
                    parts = line.split('":', 1)
                    key_part = parts[0]
                    value_part = parts[1]
                    
                    # If the value part starts with a quote, we need to handle it carefully
                    if value_part.strip().startswith('"'):
                        # Find the end of the string value
                        value_start = value_part.find('"')
                        value_end = value_part.rfind('"')
                        
                        if value_start != -1 and value_end != -1 and value_end > value_start:
                            # Extract the string value
                            string_value = value_part[value_start + 1:value_end]
                            # Escape quotes and control characters
                            escaped_value = string_value.replace('\\', '\\\\')
                            escaped_value = escaped_value.replace('"', '\\"')
                            escaped_value = escaped_value.replace('\n', '\\n')
                            escaped_value = escaped_value.replace('\r', '\\r')
                            escaped_value = escaped_value.replace('\t', '\\t')
                            
                            # Reconstruct the line
                            fixed_line = f'{key_part}": "{escaped_value}"'
                            if value_end < len(value_part) - 1:
                                fixed_line += value_part[value_end + 1:]
                        else:
                            fixed_line = line
                    else:
                        fixed_line = line
                
                fixed_lines.append(fixed_line)
            
            manual_content = '\n'.join(fixed_lines)
            
            return json.loads(manual_content)
        except json.JSONDecodeError as e:
            logging.warning(f"Manual character replacement failed: {str(e)}")
        
        # Strategy 5: Last resort - try to extract and fix specific issues
        try:
            # Log the problematic content for debugging
            logging.error(f"All JSON parsing strategies failed. Content preview: {content[:200]}...")
            logging.error(f"Full content length: {len(content)} characters")
            
            # Try to identify the specific issue and fix it
            fixed_content = content
            
            # Remove any null bytes or other problematic characters
            fixed_content = fixed_content.replace('\x00', '')
            fixed_content = fixed_content.replace('\ufffd', '')
            
            # Try to fix common JSON issues
            fixed_content = re.sub(r'([^\\])"([^"]*?)([^\\])"', r'\1"\\2\\3"', fixed_content)
            
            return json.loads(fixed_content)
        except json.JSONDecodeError as e:
            logging.error(f"Final JSON parsing attempt failed: {str(e)}")
            raise Exception(f"A4F API returned invalid JSON format that could not be parsed. This may be due to service overload. Please try again. Error: {str(e)}")

    def _make_api_request_with_retry(self, system_prompt, user_prompt, max_retries=3):
        """Make API request with automatic retry on JSON parsing failures"""
        for attempt in range(max_retries):
            try:
                response = self._make_api_request(system_prompt, user_prompt)
                return response
            except Exception as e:
                error_str = str(e).lower()
                if "invalid json" in error_str or "json format" in error_str:
                    if attempt < max_retries - 1:
                        logging.warning(f"JSON parsing failed on attempt {attempt + 1}, retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        logging.error(f"All {max_retries} attempts failed due to JSON parsing errors")
                        raise
                else:
                    # Non-JSON errors should not be retried
                    raise
        
        # This should never be reached, but just in case
        raise Exception("Maximum retry attempts exceeded")

    def start_course_generation(self, topic, proficiency, learning_style, generation_id, user_id):
        """Start course generation in background thread"""
        # Create a new generation record in the database
        generation = CourseGeneration(
            id=generation_id,
            status='starting',
            progress=0,
            message='Initializing course generation...',
            user_id=user_id
        )
        db.session.add(generation)
        db.session.commit()

        thread = threading.Thread(
            target=self._generate_course_background,
            args=(topic, proficiency, learning_style, generation_id, user_id)
        )
        thread.daemon = True
        thread.start()

        return generation_id

    def _generate_course_background(self, topic, proficiency, learning_style, generation_id, user_id):
        """Background thread for course generation"""
        # Create application context for the background thread
        with self.app.app_context():
            try:
                # Update status in database
                generation = CourseGeneration.query.get(generation_id)
                if generation:
                    generation.status = 'generating'
                    generation.progress = 25
                    generation.message = 'Connecting to AI service...'
                    db.session.commit()

                # Generate course in background
                course_data = self._perform_course_generation(topic, proficiency, learning_style, generation_id)

                # Update status and store result in database
                generation = CourseGeneration.query.get(generation_id)
                if generation:
                    generation.status = 'completed'
                    generation.progress = 100
                    generation.message = 'Course generation completed!'
                    generation.result = course_data
                    db.session.commit()

            except Exception as e:
                logging.error(f"Background generation error: {str(e)}")
                # Update error status in database
                generation = CourseGeneration.query.get(generation_id)
                if generation:
                    generation.status = 'error'
                    generation.progress = 0
                    generation.message = f'Generation failed: {str(e)}'
                    db.session.commit()

    def _perform_course_generation(self, topic, proficiency, learning_style, generation_id):
        """Actual course generation with progress updates"""
        if not self.client:
            raise Exception("AI client not available. Please check your A4F API key configuration.")

        try:
            # Update progress in database for each step
            generation = CourseGeneration.query.get(generation_id)
            
            # Step 1: Generate course outline and structure
            if generation:
                generation.message = 'Creating course outline...'
                generation.progress = 20
                db.session.commit()

            outline_data = self._generate_course_outline(topic, proficiency, learning_style, generation_id)

            # Step 2: Generate lessons in batches
            if generation:
                generation.message = 'Generating lessons...'
                generation.progress = 40
                db.session.commit()

            lessons = self._generate_lessons_batch(outline_data, topic, proficiency, learning_style, generation_id)

            # Step 3: Generate quizzes
            if generation:
                generation.message = 'Creating quizzes...'
                generation.progress = 70
                db.session.commit()

            quizzes = self._generate_quizzes(outline_data, topic, proficiency, generation_id)

            # Step 4: Generate final exam and assignment
            if generation:
                generation.message = 'Creating final exam...'
                generation.progress = 85
                db.session.commit()

            final_exam, assignment = self._generate_final_components(outline_data, topic, proficiency, generation_id)

            # Combine all components
            course_data = {
                "title": outline_data["title"],
                "description": outline_data["description"],
                "outline": outline_data["outline"],
                "lessons": lessons,
                "quizzes": quizzes,
                "assignments": [assignment] if assignment else [],
                "final_exam": final_exam
            }

            if generation:
                generation.message = 'Finalizing course...'
                generation.progress = 95
                db.session.commit()

            return course_data

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                raise Exception("The AI service is taking longer than expected to respond. This may be due to high demand. The request will continue processing in the background.")
            elif "429" in str(e) or "rate limit" in error_msg:
                raise Exception("A4F API rate limit exceeded. Please wait 5-10 minutes and try again.")
            elif "connection" in error_msg or "network" in error_msg:
                raise Exception("Network connection error. The A4F API service may be temporarily unavailable. Please try again in a few minutes.")
            elif "unauthorized" in error_msg or "401" in str(e):
                raise Exception("Invalid A4F API key. Please check your A4F_API_KEY environment variable.")
            elif "502" in str(e) or "503" in str(e) or "504" in str(e):
                raise Exception("A4F API service is temporarily unavailable. Please try again in a few minutes.")
            elif "unexpected token" in error_msg and "not valid json" in error_msg:
                raise Exception("A4F API returned an invalid response format. This usually indicates a temporary service issue. Please try again.")
            else:
                logging.error(f"Detailed AI API error: {str(e)}")
                raise Exception(f"A4F API service error: {str(e)[:100]}...")

    def _generate_course_outline(self, topic, proficiency, learning_style, generation_id):
        """Generate course outline and basic structure"""
        system_prompt = """Create a course outline in JSON format:
        {
            "title": "Course Title",
            "description": "Detailed course description (200+ words)",
            "outline": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5", "Topic 6", "Topic 7", "Topic 8", "Topic 9", "Topic 10", "Topic 11", "Topic 12", "Topic 13", "Topic 14", "Topic 15"]
        }"""

        user_prompt = f"""Create a comprehensive {topic} course outline for {proficiency} learners ({learning_style} style).
        - Course should have 15 main topics/lessons
        - Include a detailed description explaining what students will learn
        - Topics should progress logically from basic to advanced concepts
        - Cover the subject thoroughly with good depth and breadth"""

        response = self._make_api_request_with_retry(system_prompt, user_prompt)
        return self._parse_json_response(response)

    def _generate_lessons_batch(self, outline_data, topic, proficiency, learning_style, generation_id):
        """Generate lessons in smaller batches"""
        lessons = []
        topics = outline_data["outline"]

        # Generate lessons in batches of 2-3 to avoid timeouts with more lessons
        for i in range(0, len(topics), 2):
            batch_topics = topics[i:i+2]
            batch_lessons = self._generate_lesson_batch(batch_topics, topic, proficiency, learning_style)
            lessons.extend(batch_lessons)

        return lessons

    def _generate_lesson_batch(self, batch_topics, topic, proficiency, learning_style):
        """Generate a batch of 3-4 lessons"""
        system_prompt = """Create lessons in JSON format:
        {
            "lessons": [
                {
                    "title": "Lesson Title",
                    "content": "Detailed lesson content with HTML formatting (600+ words)",
                    "resources": [
                        {"type": "article", "title": "Related Article Title", "url": "https://example.com/article"},
                        {"type": "documentation", "title": "Official Documentation", "url": "https://docs.example.com"}
                    ]
                }
            ]
        }"""

        topic_list = ", ".join(batch_topics)
        user_prompt = f"""Create lessons for these {topic} topics: {topic_list}

        For {proficiency} learners ({learning_style} style):
        - Each lesson 600+ words with HTML formatting
        - Include practical examples and case studies
        - Focus on clear explanations and real-world applications
        - No need to generate video URLs - these will be added automatically
        - 2-3 non-video resources per lesson from reputable sources"""

        response = self._make_api_request_with_retry(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        # Process each lesson
        for lesson in data.get("lessons", []):
            # Search for a relevant YouTube video
            search_query = f"{topic} {lesson['title']} tutorial {proficiency} level"
            logging.info(f"Searching for video for lesson: {lesson['title']}")
            video_id, video_title = self.search_youtube_video(search_query)

            # Update resources with valid video
            if video_id:
                logging.info(f"Adding video {video_id} to lesson {lesson['title']}")
                # Add as a video resource
                if 'resources' not in lesson:
                    lesson['resources'] = []
                
                lesson['resources'].append({
                    "type": "video",
                    "title": video_title,
                    "url": f"https://www.youtube.com/embed/{video_id}"
                })
            else:
                logging.warning(f"No suitable video found for lesson: {lesson['title']}")

            # Validate other resources
            if 'resources' in lesson:
                lesson['resources'] = self._validate_resources(lesson['resources'])

        return data.get("lessons", [])

    def _validate_resources(self, resources):
        """Validate and filter resource URLs"""
        valid_resources = []
        for resource in resources:
            # Skip validation for YouTube videos as they're already validated
            if resource['type'] == 'video' and 'youtube.com/embed/' in resource['url']:
                valid_resources.append(resource)
                continue

            # Basic URL validation for other resources
            if 'url' in resource and resource['url']:
                try:
                    # You might want to add more sophisticated URL validation here
                    if resource['url'].startswith(('http://', 'https://')):
                        valid_resources.append(resource)
                except Exception as e:
                    logging.warning(f"Invalid resource URL: {str(e)}")
                    continue

        return valid_resources

    def _generate_quizzes(self, outline_data, topic, proficiency, generation_id):
        """Generate quizzes for each lesson with robust JSON handling"""
        import random
        try:
            # Generate quizzes one by one to avoid complex JSON parsing issues
            quizzes = []
            num_lessons = len(outline_data.get('outline', []))
            
            # Generate 3-5 quizzes throughout the course
            num_quizzes = min(5, max(3, num_lessons // 3))
            
            for quiz_num in range(num_quizzes):
                try:
                    # Generate quiz with 2-3 questions each
                    question_count = random.randint(2, 3)
                    quiz = self._generate_single_quiz(topic, proficiency, quiz_num + 1, question_count, outline_data)
                    if quiz:
                        quizzes.append(quiz)
                except Exception as e:
                    logging.warning(f"Failed to generate quiz {quiz_num + 1}: {str(e)}")
                    continue
            
            # Distribute quizzes throughout the course
            if quizzes and num_lessons > 0:
                available_positions = list(range(3, num_lessons + 1))
                random.shuffle(available_positions)
                quiz_positions = sorted(available_positions[:len(quizzes)])
                
                for i, quiz in enumerate(quizzes):
                    if i < len(quiz_positions):
                        quiz["lesson_dependency"] = quiz_positions[i]
                    else:
                        quiz["lesson_dependency"] = max(3, num_lessons)
            
            logging.info(f"Successfully generated {len(quizzes)} quizzes")
            return quizzes

        except Exception as e:
            logging.error(f"Quiz generation failed: {e}")
            return []

    def _generate_single_quiz(self, topic, proficiency, quiz_num, question_count, outline_data):
        """Generate a single quiz with individual question generation"""
        try:
            # Generate questions one by one to avoid JSON parsing issues
            questions = []
            
            for question_num in range(question_count):
                try:
                    question = self._generate_single_question(topic, proficiency, question_num + 1)
                    if question:
                        questions.append(question)
                except Exception as e:
                    logging.warning(f"Failed to generate question {question_num + 1} for quiz {quiz_num}: {str(e)}")
                    continue
            
            if not questions:
                logging.warning(f"No questions generated for quiz {quiz_num}")
                return None
            
            # Create quiz structure
            quiz = {
                "title": f"Quiz {quiz_num}",
                "lesson_dependency": 3,  # Will be updated by parent method
                "questions": questions
            }
            
            return quiz
            
        except Exception as e:
            logging.error(f"Single quiz generation failed: {e}")
            return None

    def _generate_single_question(self, topic, proficiency, question_num):
        """Generate a single quiz question with robust JSON handling"""
        try:
            # Question types to cycle through
            question_types = ['multiple_choice', 'fill_blank', 'short_answer']
            question_type = question_types[(question_num - 1) % len(question_types)]
            
            system_prompt = f"""Generate a single {question_type} question for a {topic} course at {proficiency} level.

IMPORTANT: Return ONLY the JSON object for this single question. No additional text or markdown formatting.

Question requirements:
- Clear and concise
- Appropriate difficulty for {proficiency} level
- Practical application of {topic} concepts
- Include a brief explanation

Return in this exact JSON format:"""

            if question_type == 'multiple_choice':
                system_prompt += """
{
    "question": "What is the primary purpose of...?",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of why this is correct"
}"""
            elif question_type == 'fill_blank':
                system_prompt += """
{
    "question": "Fill in the blank: _____ is essential for...",
    "type": "fill_blank",
    "correct_answer": "answer",
    "explanation": "Brief explanation of the concept"
}"""
            else:  # short_answer
                system_prompt += """
{
    "question": "Explain briefly how...",
    "type": "short_answer",
    "correct_answer": "Sample answer demonstrating understanding",
    "explanation": "What makes this a good answer"
}"""

            user_prompt = f"""Create question {question_num} for {topic} course ({proficiency} level).
Focus on practical understanding and real-world application."""

            response = self._make_api_request_with_retry(system_prompt, user_prompt)
            
            # Use robust parsing specifically for single questions
            content = response.choices[0].message.content.strip()
            question_data = self._robust_json_parse(content)
            
            # Validate question structure
            required_fields = ['question', 'type', 'correct_answer', 'explanation']
            if all(field in question_data for field in required_fields):
                return question_data
            else:
                logging.warning(f"Generated question missing required fields: {list(question_data.keys())}")
                return None
                
        except Exception as e:
            logging.warning(f"Single question generation failed: {str(e)}")
            return None

    def _generate_final_components(self, outline_data, topic, proficiency, generation_id):
        """Generate final exam and assignment with robust JSON handling"""
        import random
        try:
            # Generate final exam with individual question generation
            exam_question_count = random.randint(15, 20)  # Reduced for reliability
            final_exam = self._generate_final_exam(topic, proficiency, exam_question_count, outline_data)
            
            # Generate assignment
            assignment = self._generate_assignment(topic, proficiency)
            
            return final_exam, assignment

        except Exception as e:
            logging.error(f"Final component generation failed: {e}")
            return None, None

    def _generate_final_exam(self, topic, proficiency, question_count, outline_data):
        """Generate final exam with individual question generation"""
        try:
            questions = []
            
            for question_num in range(question_count):
                try:
                    question = self._generate_final_exam_question(topic, proficiency, question_num + 1, outline_data)
                    if question:
                        questions.append(question)
                except Exception as e:
                    logging.warning(f"Failed to generate final exam question {question_num + 1}: {str(e)}")
                    continue
            
            if not questions:
                logging.warning("No questions generated for final exam")
                return None
            
            final_exam = {
                "title": "Final Exam",
                "questions": questions
            }
            
            logging.info(f"Successfully generated final exam with {len(questions)} questions")
            return final_exam
            
        except Exception as e:
            logging.error(f"Final exam generation failed: {e}")
            return None

    def _generate_final_exam_question(self, topic, proficiency, question_num, outline_data):
        """Generate a single final exam question with robust JSON handling"""
        try:
            # Question types for final exam
            question_types = ['multiple_choice', 'short_answer', 'code_analysis']
            question_type = question_types[(question_num - 1) % len(question_types)]
            
            system_prompt = f"""Generate a single {question_type} question for a {topic} course final exam at {proficiency} level.

IMPORTANT: Return ONLY the JSON object for this single question. No additional text or markdown formatting.

Question requirements:
- Comprehensive understanding of {topic} concepts
- Appropriate difficulty for {proficiency} level final exam
- Test practical application and theoretical knowledge
- Include a brief explanation

Return in this exact JSON format:"""

            if question_type == 'multiple_choice':
                system_prompt += """
{
    "question": "Which of the following best describes...?",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of why this is correct"
}"""
            elif question_type == 'code_analysis':
                system_prompt += """
{
    "question": "What does this code accomplish?",
    "type": "code_analysis",
    "code": "def example():\n    return 'result'",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of the code's purpose"
}"""
            else:  # short_answer
                system_prompt += """
{
    "question": "Explain the key differences between...",
    "type": "short_answer",
    "correct_answer": "Comprehensive answer demonstrating deep understanding",
    "explanation": "What makes this a complete and accurate answer"
}"""

            user_prompt = f"""Create final exam question {question_num} for {topic} course ({proficiency} level).
This should test comprehensive understanding of the entire course material."""

            response = self._make_api_request_with_retry(system_prompt, user_prompt)
            
            # Use robust parsing specifically for single questions
            content = response.choices[0].message.content.strip()
            question_data = self._robust_json_parse(content)
            
            # Validate question structure
            required_fields = ['question', 'type', 'correct_answer', 'explanation']
            if all(field in question_data for field in required_fields):
                return question_data
            else:
                logging.warning(f"Generated final exam question missing required fields: {list(question_data.keys())}")
                return None
                
        except Exception as e:
            logging.warning(f"Final exam question generation failed: {str(e)}")
            return None

    def _generate_assignment(self, topic, proficiency):
        """Generate a practical assignment"""
        try:
            system_prompt = f"""Generate a practical assignment for a {topic} course at {proficiency} level.

IMPORTANT: Return ONLY the JSON object for the assignment. No additional text or markdown formatting.

Return in this exact JSON format:
{{
    "title": "Assignment Title",
    "description": "Brief description of the assignment",
    "instructions": "Step-by-step instructions for completing the assignment",
    "type": "practical",
    "difficulty": "{proficiency}",
    "estimated_hours": 2,
    "resources": []
}}"""

            user_prompt = f"""Create a practical assignment for {topic} course ({proficiency} level).
Focus on hands-on application of concepts learned in the course."""

            response = self._make_api_request_with_retry(system_prompt, user_prompt)
            
            # Use robust parsing
            content = response.choices[0].message.content.strip()
            assignment_data = self._robust_json_parse(content)
            
            # Validate assignment structure
            required_fields = ['title', 'description', 'instructions', 'type', 'difficulty']
            if all(field in assignment_data for field in required_fields):
                return assignment_data
            else:
                logging.warning(f"Generated assignment missing required fields: {list(assignment_data.keys())}")
                return None
                
        except Exception as e:
            logging.warning(f"Assignment generation failed: {str(e)}")
            return None

    def _make_api_request(self, system_prompt, user_prompt):
        """Make API request with retry logic and exponential backoff"""
        max_retries = 4  # Increased retries
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=3000,
                    timeout=60.0  # Increased timeout
                )
                return response
            except Exception as api_error:
                retry_count += 1
                error_str = str(api_error).lower()

                logging.warning(f"API request failed (attempt {retry_count}/{max_retries}): {str(api_error)}")

                # Check for retryable errors
                retryable_errors = [
                    "504", "502", "503", "timeout", "gateway", "connection", 
                    "rate limit", "429", "server error", "service unavailable"
                ]

                is_retryable = any(error in error_str for error in retryable_errors)

                if is_retryable and retry_count < max_retries:
                    # Exponential backoff: 5s, 10s, 20s, 40s
                    wait_time = min(5 * (2 ** (retry_count - 1)), 60)
                    logging.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    if "429" in str(api_error) or "rate limit" in error_str:
                        raise Exception("A4F API rate limit exceeded. Please wait 5-10 minutes and try again.")
                    elif "html" in error_str or "page" in error_str:
                        raise Exception("A4F API is returning error pages. Service may be temporarily overloaded. Please try again in a few minutes.")
                    else:
                        raise Exception(f"A4F API error: {str(api_error)[:100]}...")

        raise Exception("A4F API service failed after multiple retries with exponential backoff.")

    def _parse_json_response(self, response):
        """Parse JSON response from API using robust parsing"""
        if not response or not response.choices or len(response.choices) == 0:
            raise Exception("Invalid response structure from A4F API")

        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from A4F API")

        content_str = str(content).strip()

        # Check for HTML error pages (but not HTML content within JSON)
        if (content_str.strip().startswith('<!DOCTYPE') or 
            content_str.strip().startswith('<html') or 
            (content_str.strip().startswith('<') and 'json' not in content_str[:100].lower())):
            logging.error(f"HTML response received: {content_str[:300]}...")
            raise Exception("A4F API service is temporarily returning error pages. This usually indicates high demand. Please wait a few minutes and try again.")

        # Use the robust JSON parsing system
        try:
            return self._robust_json_parse(content_str)
        except Exception as e:
            logging.error(f"Robust JSON parsing failed: {str(e)}")
            logging.error(f"Content preview: {content_str[:200]}...")
            logging.error(f"Full content: {content_str}")
            raise Exception(f"A4F API returned invalid JSON format. This may be due to service overload. Please try again.")

    def get_generation_status(self, generation_id):
        """Get generation status from database"""
        generation = CourseGeneration.query.get(generation_id)
        if generation:
            return {
                'status': generation.status,
                'progress': generation.progress,
                'message': generation.message
            }
        return None

    def get_generation_result(self, generation_id):
        """Get generation result from database"""
        generation = CourseGeneration.query.get(generation_id)
        if generation and generation.status == 'completed':
            return generation.result
        return None

    def cleanup_generation(self, generation_id):
        """Clean up generation data"""
        self.generation_status.pop(generation_id, None)
        self.generation_results.pop(generation_id, None)

    def check_a4f_service_health(self):
        """Check if A4F API service is available"""
        try:
            # Simple health check with minimal request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                timeout=15.0
            )

            # Check if we got a valid response
            if not response or not response.choices:
                logging.error("Health check failed: Invalid response structure")
                return False

            content = response.choices[0].message.content
            if not content or content.strip().startswith('<'):
                logging.error("Health check failed: Got HTML response instead of text")
                return False

            logging.info("A4F API health check passed")
            return True

        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in str(e):
                logging.error("A4F service health check failed: Rate limit exceeded")
            elif "html" in error_str or "page" in error_str:
                logging.error("A4F service health check failed: Service returning error pages")
            else:
                logging.error(f"A4F service health check failed: {str(e)}")
            return False

    def generate_course(self, topic, proficiency, learning_style):
        """Legacy method for backwards compatibility - now raises exception"""
        raise Exception("Direct course generation is no longer supported. Please use the asynchronous generation system.")

    def grade_answers_batch(self, questions_data, lesson_context=""):
        """Grade multiple answers in a single API call to prevent rate limiting"""
        if not questions_data:
            return []

        try:
            system_prompt = """You are an expert educational assessment AI. Grade multiple student answers intelligently and fairly.

            For each question, evaluate if the student demonstrates understanding of the concept.
            Be flexible with wording while maintaining accuracy requirements.
            Consider partial credit for partially correct answers.
            Provide constructive, encouraging feedback.

            Respond with JSON in this exact format:
            {
                "results": [
                    {
                        "score": 0.0-1.0,
                        "is_correct": true/false,
                        "feedback": "Brief constructive feedback",
                        "confidence": 0.0-1.0
                    }
                ]
            }

            Scoring guidelines:
            - 1.0: Completely correct, demonstrates full understanding
            - 0.5: Partially correct, shows some understanding
            - 0.0: Incorrect or no understanding shown"""

            # Format questions for batch processing
            questions_text = ""
            for i, q_data in enumerate(questions_data):
                questions_text += f"""
Question {i+1}:
Text: {q_data['question_text']}
Type: {q_data['question_type']}
Expected Answer: {q_data['correct_answer']}
Student Answer: {q_data['user_answer']}
---"""

            user_prompt = f"""Grade these student answers:

{questions_text}

Lesson Context: {lesson_context}

Provide scoring and feedback for each question in JSON format with a 'results' array."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000  # Increased for batch processing
            )

            content = response.choices[0].message.content.strip()

            # Use robust JSON parsing instead of manual parsing
            try:
                result = self._robust_json_parse(content)
            except Exception as e:
                logging.error(f"Failed to parse JSON in batch grading. Error: {str(e)}")
                logging.error(f"Content preview: {content[:200]}...")
                # Fallback to individual grading
                return [self._fallback_grade(
                    q_data['question_text'], 
                    q_data['correct_answer'], 
                    q_data['user_answer'], 
                    q_data['question_type']
                ) for q_data in questions_data]

            results = result.get('results', [])

            # Validate and sanitize responses
            graded_results = []
            for i, res in enumerate(results):
                if i >= len(questions_data):
                    break

                score = max(0.0, min(1.0, float(res.get('score', 0))))
                is_correct = res.get('is_correct', False) or score >= 0.7
                feedback = res.get('feedback', 'Answer evaluated.')
                confidence = max(0.0, min(1.0, float(res.get('confidence', 0.8))))

                graded_results.append({
                    'score': score,
                    'is_correct': is_correct,
                    'feedback': feedback,
                    'confidence': confidence
                })

            return graded_results

        except Exception as e:
            logging.error(f"Batch AI grading failed: {e}")
            # Fallback to individual grading for smaller batches
            return [self._fallback_grade(
                q_data['question_text'], 
                q_data['correct_answer'], 
                q_data['user_answer'], 
                q_data['question_type']
            ) for q_data in questions_data]

    def grade_answer(self, question_text, correct_answer, user_answer, question_type, lesson_context=""):
        """Use AI to intelligently grade student answers"""
        if not user_answer or not user_answer.strip():
            return {
                'score': 0,
                'is_correct': False,
                'feedback': 'No answer provided.',
                'confidence': 1.0
            }

        # Handle missing correct_answer (this was causing the warning in logs)
        if not correct_answer:
            return {
                'score': 0,
                'is_correct': False,
                'feedback': 'Unable to grade: no reference answer available.',
                'confidence': 1.0
            }

        # For multiple choice and true/false, use exact matching first for efficiency
        if question_type in ['multiple_choice', 'true_false']:
            if user_answer.strip().lower() == correct_answer.strip().lower():
                return {
                    'score': 1,
                    'is_correct': True,
                    'feedback': 'Correct!',
                    'confidence': 1.0
                }

        # Use AI for intelligent grading on all other cases
        try:
            system_prompt = """You are an expert educational assessment AI. Grade student answers intelligently and fairly.

            You should:
            1. Evaluate if the student demonstrates understanding of the concept
            2. Be flexible with wording while maintaining accuracy requirements
            3. Consider partial credit for partially correct answers
            4. Provide constructive, encouraging feedback
            5. Be fair but maintain educational standards

            Respond with JSON in this exact format:
            {
                "score": 0.0-1.0,
                "is_correct": true/false,
                "feedback": "Brief constructive feedback",
                "confidence": 0.0-1.0
            }

            Scoring guidelines:
            - 1.0: Completely correct, demonstrates full understanding
            - 0.5: Partially correct, shows some understanding
            - 0.0: Incorrect or no understanding shown"""

            user_prompt = f"""Grade this student answer:

            Question: {question_text}
            Question Type: {question_type}
            Expected Answer: {correct_answer}
            Student Answer: {user_answer}
            Lesson Context: {lesson_context}

            Provide scoring and feedback in JSON format."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent grading
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Use robust JSON parsing instead of manual parsing
            try:
                result = self._robust_json_parse(content)
            except Exception as e:
                logging.warning(f"AI grading JSON parsing failed: {e}")
                return self._fallback_grade(question_text, correct_answer, user_answer, question_type)

            score = max(0.0, min(1.0, float(result.get('score', 0))))
            is_correct = result.get('is_correct', False) or score >= 0.7  # Apply threshold
            feedback = result.get('feedback', 'Answer evaluated.')
            confidence = max(0.0, min(1.0, float(result.get('confidence', 0.8))))

            return {
                'score': score,
                'is_correct': is_correct,
                'feedback': feedback,
                'confidence': confidence
            }

        except Exception as e:
            logging.warning(f"AI grading failed: {e}")
            return self._fallback_grade(question_text, correct_answer, user_answer, question_type)

    def _fallback_grade(self, question_text, correct_answer, user_answer, question_type):
        """Basic grading fallback for error handling"""
        # Very basic keyword matching (improve in a real-world scenario)
        if not user_answer or not user_answer.strip():
            return {
                'score': 0,
                'is_correct': False,
                'feedback': 'No answer provided.',
                'confidence': 1.0
            }

        if question_type in ['multiple_choice', 'true_false']:
            if user_answer.strip().lower() == correct_answer.strip().lower():
                return {
                    'score': 1,
                    'is_correct': True,
                    'feedback': 'Correct!',
                    'confidence': 1.0
                }
            else:
                return {
                    'score': 0,
                    'is_correct': False,
                    'feedback': 'Incorrect.',
                    'confidence': 1.0
                }

        # For other types: simple keyword check
        keywords = correct_answer.lower().split()
        if any(keyword in user_answer.lower() for keyword in keywords):
            return {
                'score': 0.5,
                'is_correct': True,  # Partial credit
                'feedback': 'Partially correct. Mentions key concepts.',
                'confidence': 0.6
            }
        else:
            return {
                'score': 0,
                'is_correct': False,
                'feedback': 'Does not demonstrate understanding of key concepts.',
                'confidence': 0.4
            }

    def search_youtube_video(self, query, max_results=3):
        """
        Search for YouTube videos and return the best match
        Returns a tuple of (video_id, title) or (None, None) if no suitable video is found
        """
        logging.info(f"Attempting to search YouTube for: {query}")
        
        if not self.youtube:
            logging.warning("YouTube API not initialized. Cannot search for videos.")
            return None, None

        try:
            # Search for videos
            logging.info("Making YouTube API search request...")
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                videoEmbeddable='true',  # Only embeddable videos
                safeSearch='strict',  # Safe content only
                relevanceLanguage='en'  # English videos only
            ).execute()

            # Process each video
            for search_result in search_response.get('items', []):
                if search_result['id']['kind'] == 'youtube#video':
                    video_id = search_result['id']['videoId']
                    logging.info(f"Found potential video: {video_id}")
                    
                    # Get video statistics
                    video_response = self.youtube.videos().list(
                        part='statistics,status',
                        id=video_id
                    ).execute()

                    if video_response['items']:
                        video_info = video_response['items'][0]
                        
                        # Check if video is available and embeddable
                        if (video_info['status']['embeddable'] and 
                            video_info['status']['privacyStatus'] == 'public'):
                            
                            logging.info(f"Selected video: {video_id} - {search_result['snippet']['title']}")
                            return (
                                video_id,
                                search_result['snippet']['title']
                            )

            logging.warning("No suitable videos found")
            return None, None

        except HttpError as e:
            logging.error(f"YouTube API error: {str(e)}")
            return None, None
        except Exception as e:
            logging.error(f"Error searching YouTube: {str(e)}")
            return None, None