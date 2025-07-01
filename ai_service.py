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

class AIService:
    def __init__(self):
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

    def start_course_generation(self, topic, proficiency, learning_style, generation_id):
        """Start course generation in background thread"""
        self.generation_status[generation_id] = {
            'status': 'starting',
            'progress': 0,
            'message': 'Initializing course generation...'
        }

        thread = threading.Thread(
            target=self._generate_course_background,
            args=(topic, proficiency, learning_style, generation_id)
        )
        thread.daemon = True
        thread.start()

        return generation_id

    def _generate_course_background(self, topic, proficiency, learning_style, generation_id):
        """Background thread for course generation"""
        try:
            self.generation_status[generation_id] = {
                'status': 'generating',
                'progress': 25,
                'message': 'Connecting to AI service...'
            }

            # Generate course in background
            course_data = self._perform_course_generation(topic, proficiency, learning_style, generation_id)

            self.generation_status[generation_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Course generation completed!'
            }

            self.generation_results[generation_id] = course_data

        except Exception as e:
            logging.error(f"Background generation error: {str(e)}")
            self.generation_status[generation_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Generation failed: {str(e)}'
            }

    def _perform_course_generation(self, topic, proficiency, learning_style, generation_id):
        """Actual course generation with progress updates - using smaller requests"""
        if not self.client:
            raise Exception("AI client not available. Please check your A4F API key configuration.")

        try:
            # Step 1: Generate course outline and structure
            self.generation_status[generation_id]['message'] = 'Creating course outline...'
            self.generation_status[generation_id]['progress'] = 20

            outline_data = self._generate_course_outline(topic, proficiency, learning_style, generation_id)

            # Step 2: Generate lessons in batches
            self.generation_status[generation_id]['message'] = 'Generating lessons...'
            self.generation_status[generation_id]['progress'] = 40

            lessons = self._generate_lessons_batch(outline_data, topic, proficiency, learning_style, generation_id)

            # Step 3: Generate quizzes
            self.generation_status[generation_id]['message'] = 'Creating quizzes...'
            self.generation_status[generation_id]['progress'] = 70

            quizzes = self._generate_quizzes(outline_data, topic, proficiency, generation_id)

            # Step 4: Generate final exam and assignment
            self.generation_status[generation_id]['message'] = 'Creating final exam...'
            self.generation_status[generation_id]['progress'] = 85

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

            self.generation_status[generation_id]['message'] = 'Finalizing course...'
            self.generation_status[generation_id]['progress'] = 95

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

        response = self._make_api_request(system_prompt, user_prompt)
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

            # Update progress
            progress = 40 + (i / len(topics)) * 25
            self.generation_status[generation_id]['progress'] = int(progress)

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

        response = self._make_api_request(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        # Keep track of used videos to avoid duplicates
        used_videos = set()

        # Process each lesson
        for lesson in data.get("lessons", []):
            # Search for a relevant YouTube video with more specific query
            search_query = f"{lesson['title']} {topic} tutorial {proficiency} level"
            logging.info(f"Searching for video for lesson: {lesson['title']}")
            
            # Try up to 3 times to find a unique video
            max_attempts = 3
            video_found = False
            
            for attempt in range(max_attempts):
                video_id, video_title = self.search_youtube_video(search_query)
                
                if video_id and video_id not in used_videos:
                    logging.info(f"Adding video {video_id} to lesson {lesson['title']}")
                    # Add as a video resource
                    if 'resources' not in lesson:
                        lesson['resources'] = []
                    
                    lesson['resources'].append({
                        "type": "video",
                        "title": video_title,
                        "url": f"https://www.youtube.com/embed/{video_id}"
                    })
                    used_videos.add(video_id)
                    video_found = True
                    break
                elif attempt < max_attempts - 1:
                    # Modify search query for next attempt
                    search_query = f"{topic} {lesson['title']} {proficiency} programming tutorial"
            
            if not video_found:
                logging.warning(f"No unique video found for lesson: {lesson['title']}")

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
        """Generate quizzes for each lesson"""
        import random
        try:
            # Randomize question counts for each quiz (1-3 questions each)
            quiz_counts = [random.randint(1, 3) for _ in range(min(6, len(outline_data.get('outline', []))))]
            quiz_structure = ", ".join([f"Quiz {i+1}: {count} question{'s' if count > 1 else ''}" for i, count in enumerate(quiz_counts)])

            prompt = f"""Create quizzes for {topic} course topics with this specific structure: {quiz_structure}
        - EXACTLY follow the question count specified for each quiz
        - Mix of multiple_choice, fill_blank, short_answer, and code_writing questions (for relevant courses)
        - Each quiz should test knowledge from the SPECIFIC lesson it follows (not cumulative)
        - Questions should focus on the concepts taught in that particular lesson
        - Clear explanations for each answer
        - Focus on practical application and understanding rather than memorization
        - IMPORTANT: Every question must have a correct_answer field that matches the question type"""

            system_prompt = """Create quizzes in JSON format:
        {
            "quizzes": [
                {
                    "title": "Quiz Title",
                    "lesson_dependency": 1,
                    "questions": [
                        {
                            "question": "Question text?",
                            "type": "multiple_choice",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Option A",
                            "explanation": "Explanation"
                        },
                        {
                            "question": "Fill in the blank: _____ is important.",
                            "type": "fill_blank",
                            "correct_answer": "answer",
                            "explanation": "Explanation"
                        },
                        {
                            "question": "Explain briefly.",
                            "type": "short_answer",
                            "correct_answer": "Sample answer",
                            "explanation": "What makes a good answer"
                        },
                         {
                            "question": "Write a Python code snippet to...",
                            "type": "code_writing",
                            "correct_answer": "Sample code",
                            "explanation": "Explanation of the code"
                        }
                    ]
                }
            ]
        }"""

            response = self._make_api_request(system_prompt, prompt)
            data = self._parse_json_response(response)

            # Randomly distribute quizzes throughout the course
            quizzes = data.get("quizzes", [])
            num_lessons = len(outline_data["outline"])

            if num_lessons > 0 and quizzes:
                # Create a list of possible lesson dependencies (starting from lesson 3 so quizzes test previous content)
                # Each quiz must have at least 2 lessons to test, so min dependency is 3
                available_positions = list(range(3, num_lessons + 1))

                # Randomly select positions for quizzes, ensuring they're spaced reasonably
                # Sort to maintain logical order (earlier quizzes test fewer lessons)
                random.shuffle(available_positions)
                quiz_positions = sorted(available_positions[:len(quizzes)])

                # If we have more quizzes than good positions, fill remaining with later positions
                while len(quiz_positions) < len(quizzes):
                    quiz_positions.append(num_lessons)
            else:
                quiz_positions = []

            # Attach random lesson dependency to each quiz
            for i, quiz in enumerate(quizzes):
                if quiz_positions and i < len(quiz_positions):
                    quiz["lesson_dependency"] = quiz_positions[i]
                else:
                    quiz["lesson_dependency"] = max(3, num_lessons)  # Default to testing multiple lessons
            return quizzes

        except Exception as e:
            logging.error(f"Quiz generation failed: {e}")
            return []

    def _generate_final_components(self, outline_data, topic, proficiency, generation_id):
        """Generate final exam and assignment"""
        import random
        try:
            # Generate final exam in smaller chunks
            final_exam = self._generate_final_exam(topic, proficiency, generation_id)
            
            # Generate assignment separately
            assignment = self._generate_assignment(topic, proficiency, generation_id)
            
            return final_exam, assignment

        except Exception as e:
            logging.error(f"Final component generation failed: {e}")
            return None, None

    def _generate_final_exam(self, topic, proficiency, generation_id):
        """Generate final exam in smaller chunks"""
        try:
            # Generate questions in smaller batches
            questions = []
            batch_size = 5  # Generate 5 questions at a time
            total_questions = 25
            
            for i in range(0, total_questions, batch_size):
                remaining = min(batch_size, total_questions - len(questions))
                
                prompt = f"""Create {remaining} questions for {topic} final exam.
                - Questions should be mixed types (multiple choice and code analysis)
                - Test comprehensive understanding
                - Each question must have clear correct_answer and explanation
                - Questions {len(questions)+1} to {len(questions)+remaining} of {total_questions} total"""

                system_prompt = """Create exam questions in JSON format:
        {
                "questions": [
                    {
                        "question": "Question text?",
                        "type": "multiple_choice",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "explanation": "Explanation"
                        }
                    ]
                }"""

                response = self._make_api_request(system_prompt, prompt)
                data = self._parse_json_response(response)
                
                if data and 'questions' in data:
                    questions.extend(data['questions'])
                    
                # Update progress
                progress = 85 + (len(questions) / total_questions) * 10
                self.generation_status[generation_id]['progress'] = int(progress)
                self.generation_status[generation_id]['message'] = f'Creating final exam ({len(questions)}/{total_questions} questions)...'

            # Ensure we have exactly the right number of questions
            if len(questions) > total_questions:
                questions = questions[:total_questions]
            
            return {
                "title": f"{topic} Final Exam",
                "questions": questions
            }

        except Exception as e:
            logging.error(f"Final exam generation failed: {e}")
            raise

    def _generate_assignment(self, topic, proficiency, generation_id):
        """Generate practical assignment with properly formatted instructions and no resources field"""
        try:
            prompt = f"""Create a practical, hands-on project assignment for {topic} course ({proficiency} level).
            - Should be challenging but achievable
            - Include clear, numbered step-by-step instructions as a list (not a string)
            - Provide estimated completion time
            - Do NOT include a 'resources' field or any placeholder resources
            - Use appropriate difficulty level based on {proficiency}"""

            system_prompt = """Create assignment in JSON format:
            {
                "title": "Assignment Title",
                "description": "Assignment description",
                "instructions": ["Step 1", "Step 2", "Step 3"],
                "type": "practical",
                "difficulty": "beginner",
                "estimated_hours": 2
            }"""

            response = self._make_api_request(system_prompt, prompt)
            data = self._parse_json_response(response)

            # Ensure instructions is a list
            if isinstance(data.get('instructions'), str):
                data['instructions'] = [step.strip() for step in data['instructions'].split('\n') if step.strip()]

            # Remove 'resources' if present
            data.pop('resources', None)

            # Update progress
            self.generation_status[generation_id]['progress'] = 95
            self.generation_status[generation_id]['message'] = 'Creating final assignment...'
            return data

        except Exception as e:
            logging.error(f"Assignment generation failed: {e}")
            raise

    def _make_api_request(self, system_prompt, user_prompt):
        """Make API request with retry logic and exponential backoff"""
        max_retries = 4  # Maximum number of retries
        base_timeout = 60.0  # Base timeout in seconds
        base_delay = 2  # Base delay for exponential backoff

        for retry in range(max_retries):
            try:
                # Increase timeout with each retry
                current_timeout = base_timeout * (1 + retry * 0.5)  # 60s, 90s, 120s, 150s
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=3000,
                    timeout=current_timeout
                )
                
                # Validate response structure before returning
                if not response or not response.choices or len(response.choices) == 0:
                    raise Exception("Invalid response structure")
                    
                return response
                
            except Exception as e:
                error_msg = str(e).lower()

                # Don't retry on certain errors
                if "unauthorized" in error_msg or "401" in str(e):
                    raise Exception("Invalid A4F API key. Please check your A4F_API_KEY environment variable.")
                elif "429" in str(e) or "rate limit" in error_msg:
                    # Special handling for rate limits - longer backoff
                    if retry < max_retries - 1:
                        delay = (base_delay ** (retry + 2)) + (retry * 2)  # Longer delays for rate limits
                        logging.warning(f"Rate limit hit, waiting {delay} seconds before retry {retry + 1}")
                        time.sleep(delay)
                    continue
                
                # For other errors, use standard exponential backoff
                if retry < max_retries - 1:
                    delay = base_delay ** (retry + 1)  # Exponential backoff: 2, 4, 8, 16 seconds
                    logging.warning(f"API request failed, waiting {delay} seconds before retry {retry + 1}. Error: {str(e)}")
                    time.sleep(delay)
                    continue
                    
                # If we've exhausted all retries, raise the appropriate error
                if "timeout" in error_msg or "timed out" in error_msg:
                    raise Exception("The AI service is taking longer than expected to respond. This may be due to high demand.")
                elif "connection" in error_msg or "network" in error_msg:
                    raise Exception("Network connection error. The A4F API service may be temporarily unavailable.")
                elif any(code in str(e) for code in ["502", "503", "504"]):
                    raise Exception("A4F API service is temporarily unavailable. Please try again in a few minutes.")
                else:
                    raise Exception(f"A4F API service error: {str(e)[:100]}...")

    def _parse_json_response(self, response):
        """Parse JSON response from API with enhanced error handling"""
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

        # Extract JSON from markdown code blocks
            json_content = content_str
        if '```' in content_str:
            # Find all code blocks
            code_blocks = []
            start_indices = [i for i in range(len(content_str)) if content_str.startswith('```', i)]
            
            for i in range(0, len(start_indices), 2):
                if i + 1 < len(start_indices):
                    block = content_str[start_indices[i]:start_indices[i+1]].strip('`').strip()
                    if block.startswith('json'):
                        block = block[4:].strip()
                    code_blocks.append(block)
            
            # Use the largest valid JSON block
            valid_jsons = []
            for block in code_blocks:
                try:
                    parsed = json.loads(block)
                    valid_jsons.append((len(str(parsed)), parsed))
                except:
                    continue
            
            if valid_jsons:
                # Use the largest valid JSON block
                json_content = max(valid_jsons, key=lambda x: x[0])[1]
                return json_content

        # If no valid JSON found in code blocks, try to extract JSON directly
        try:
            # Find the first { or [ and last } or ]
            start = content_str.find('{')
            if start == -1:
                start = content_str.find('[')
            if start == -1:
                raise Exception("No JSON object or array found in response")
                
            end = content_str.rfind('}')
            if end == -1:
                end = content_str.rfind(']')
            if end == -1:
                raise Exception("No JSON object or array found in response")
                
            json_content = content_str[start:end+1]
            
            # Try to parse the extracted content
            return json.loads(json_content)
            
        except json.JSONDecodeError as e:
            # Log the error and content for debugging
            logging.error(f"JSON parse error: {str(e)}")
            logging.error(f"Content preview: {content_str[:200]}...")
            logging.error(f"Full content: {content_str}")
            
            # Try to clean the content
            try:
                # Remove any non-JSON text before the first { or [
                cleaned = re.sub(r'^[^{[]*', '', content_str)
                # Remove any non-JSON text after the last } or ]
                cleaned = re.sub(r'[^\]}]*$', '', cleaned)
                # Fix common JSON formatting issues
                cleaned = cleaned.replace('\n', ' ').replace('\r', '')
                cleaned = re.sub(r'\s+', ' ', cleaned)
                # Fix unescaped quotes
                cleaned = re.sub(r'(?<!\\)"(?![:,}\]])', '\\"', cleaned)
                
                return json.loads(cleaned)
            except:
                raise Exception("A4F API returned invalid JSON format that could not be cleaned. This may be due to service overload. Please try again.")

    def get_generation_status(self, generation_id):
        """Get current status of course generation"""
        return self.generation_status.get(generation_id, {
            'status': 'not_found',
            'progress': 0,
            'message': 'Generation ID not found'
        })

    def get_generation_result(self, generation_id):
        """Get completed course generation result"""
        return self.generation_results.get(generation_id)

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

            # Parse JSON response
            import json
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()

            result = json.loads(content)
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

            # Parse JSON response
            import json
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()

            result = json.loads(content)
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