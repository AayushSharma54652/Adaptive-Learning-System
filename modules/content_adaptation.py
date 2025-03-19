import sqlite3
import json
import logging
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize

# Initialize logging
logger = logging.getLogger(__name__)

class ContentAdaptation:
    """
    ContentAdaptation class handles adapting learning content for students
    based on their assessment performance, providing simplified content and
    additional explanations for struggling students.
    """
    
    def __init__(self, db_path='database/adaptive_learning.db'):
        """Initialize ContentAdaptation with database path"""
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def adapt_content_for_struggling_student(self, user_id, content_id, assessment_results):
        """
        Generate adapted content for a student who failed the assessment.
        
        Args:
            user_id: The ID of the user
            content_id: The ID of the content to adapt
            assessment_results: Results from the assessment
            
        Returns:
            Adapted content with simplified explanations and additional resources
        """
        logger.info(f"Adapting content {content_id} for user {user_id}")
        
        try:
            # Get the original content
            conn = self.get_db_connection()
            content = conn.execute(
                'SELECT title, content_data FROM content WHERE id = ?',
                (content_id,)
            ).fetchone()
            
            if not content:
                conn.close()
                logger.error(f"Content {content_id} not found")
                return None
            
            # Parse the content data
            try:
                content_data = json.loads(content['content_data'])
                logger.info(f"Successfully loaded content data with {len(content_data.get('sections', []))} sections")
            except json.JSONDecodeError:
                conn.close()
                logger.error(f"Failed to parse content data for content {content_id}")
                return None
                
            title = content['title']
            
            # Identify the knowledge components the student struggled with
            struggled_kcs = self._identify_struggled_components(user_id, assessment_results)
            logger.info(f"Identified {len(struggled_kcs)} struggled knowledge components")
            
            # If no struggled components identified, use a default approach
            if not struggled_kcs:
                logger.warning("No struggled knowledge components identified, using content ID to determine component")
                # Try to get the knowledge component directly from the content mapping
                content_kcs = conn.execute(
                    '''
                    SELECT kc.id, kc.name, kc.description
                    FROM content_knowledge_map ckm
                    JOIN knowledge_components kc ON ckm.knowledge_component_id = kc.id
                    WHERE ckm.content_id = ?
                    ''',
                    (content_id,)
                ).fetchall()
                
                if content_kcs:
                    # Use the first mapped knowledge component
                    kc = content_kcs[0]
                    struggled_kcs = [{
                        'id': kc['id'],
                        'name': kc['name'],
                        'description': kc['description'],
                        'mastery_level': 0.3  # Assume low mastery
                    }]
                    logger.info(f"Using default knowledge component: {kc['name']}")
                else:
                    logger.error(f"Could not find any knowledge components for content {content_id}")
            
            # Get related knowledge components and content
            related_content = self._get_related_content(struggled_kcs)
            logger.info(f"Found related content for {len(related_content)} knowledge components")
            
            conn.close()
            
            # Adapt the content
            logger.info("Simplifying content...")
            adapted_content = self._simplify_content(content_data, struggled_kcs)
            
            # Add additional explanations
            logger.info("Adding explanations...")
            adapted_content = self._add_explanations(adapted_content, struggled_kcs, related_content)
            
            # Adjust the difficulty level
            logger.info("Adjusting difficulty...")
            adapted_content = self._adjust_difficulty(adapted_content)
            
            # Create the adapted content object
            adapted_content_obj = {
                'original_content_id': content_id,
                'title': f"{title} - Adapted Version",
                'content_data': adapted_content,
                'adaptation_timestamp': datetime.now().isoformat(),
                'adaptation_reason': 'Assessment failure',
                'targeted_components': [kc['id'] for kc in struggled_kcs]
            }
            
            logger.info(f"Successfully created adapted content with {len(adapted_content.get('sections', []))} sections")
            return adapted_content_obj
            
        except Exception as e:
            logger.error(f"Error adapting content: {e}", exc_info=True)
            return None
        
    def _identify_struggled_components(self, user_id, assessment_results):
        """
        Identify knowledge components where the student struggled based on assessment results.
        
        Args:
            user_id: The ID of the user
            assessment_results: Results from the assessment
            
        Returns:
            List of knowledge component objects the student struggled with
        """
        logger.info(f"Identifying struggled components for user {user_id}")
        
        # Extract the questions from assessment results
        if isinstance(assessment_results, dict):
            questions = assessment_results.get('questions', [])
        else:
            questions = assessment_results
        
        logger.info(f"Found {len(questions)} questions in assessment results")
        
        # Identify questions the student got wrong
        incorrect_questions = []
        for q in questions:
            # Handle both dictionary and object access
            if isinstance(q, dict):
                if not q.get('is_correct', False):
                    incorrect_questions.append(q)
            else:
                if not getattr(q, 'is_correct', False):
                    incorrect_questions.append(q)
        
        logger.info(f"Found {len(incorrect_questions)} incorrect questions")
        
        # Extract knowledge component IDs from incorrect questions
        kc_ids = []
        for question in incorrect_questions:
            if isinstance(question, dict):
                kc_id = question.get('knowledge_component_id')
                if kc_id:
                    kc_ids.append(kc_id)
            else:
                kc_id = getattr(question, 'knowledge_component_id', None)
                if kc_id:
                    kc_ids.append(kc_id)
        
        logger.info(f"Extracted {len(kc_ids)} knowledge component IDs")
        
        # If no specific KCs identified, return empty list
        if not kc_ids:
            logger.warning("No knowledge component IDs identified from incorrect questions")
            return []
        
        # Get details about these knowledge components
        conn = self.get_db_connection()
        
        # Get knowledge components
        struggled_kcs = []
        for kc_id in kc_ids:
            try:
                kc = conn.execute(
                    'SELECT id, name, description FROM knowledge_components WHERE id = ?',
                    (kc_id,)
                ).fetchone()
                
                if kc:
                    # Get the user's current mastery level for this component
                    mastery = conn.execute(
                        'SELECT mastery_level FROM user_knowledge_state WHERE user_id = ? AND knowledge_component_id = ?',
                        (user_id, kc_id)
                    ).fetchone()
                    
                    kc_obj = dict(kc)
                    kc_obj['mastery_level'] = mastery['mastery_level'] if mastery else 0.0
                    struggled_kcs.append(kc_obj)
                    logger.info(f"Added knowledge component: {kc_obj['name']}")
                else:
                    logger.warning(f"Knowledge component with ID {kc_id} not found")
            except Exception as e:
                logger.error(f"Error getting knowledge component {kc_id}: {e}")
        
        conn.close()
        logger.info(f"Returning {len(struggled_kcs)} struggled knowledge components")
        return struggled_kcs
    
    def _get_related_content(self, knowledge_components):
        """
        Get related content for the given knowledge components.
        
        Args:
            knowledge_components: List of knowledge component objects
            
        Returns:
            Dictionary mapping KC IDs to related content
        """
        if not knowledge_components:
            return {}
        
        conn = self.get_db_connection()
        related_content = {}
        
        for kc in knowledge_components:
            kc_id = kc['id']
            
            # Find easier content that targets this knowledge component
            content_items = conn.execute(
                '''
                SELECT c.id, c.title, c.content_data, c.difficulty
                FROM content c
                JOIN content_knowledge_map ckm ON c.id = ckm.content_id
                WHERE ckm.knowledge_component_id = ?
                AND c.difficulty <= 2
                ORDER BY c.difficulty ASC
                LIMIT 3
                ''',
                (kc_id,)
            ).fetchall()
            
            related_content[kc_id] = [dict(item) for item in content_items]
        
        conn.close()
        return related_content
    
    def _simplify_content(self, content_data, struggled_kcs):
        """
        Simplify the content to make it more accessible for struggling students.
        
        Args:
            content_data: Original content data
            struggled_kcs: Knowledge components the student struggled with
            
        Returns:
            Simplified content data
        """
        # Create a deep copy to avoid modifying the original
        simplified_content = dict(content_data)
        
        # Check if the content has sections
        if 'sections' not in simplified_content:
            return simplified_content
        
        # Extract the names of the components the student struggled with
        kc_names = [kc['name'] for kc in struggled_kcs]
        
        # Process each section
        for i, section in enumerate(simplified_content['sections']):
            # Check if the section content is related to any of the struggled components
            is_related = any(kc_name.lower() in section.get('title', '').lower() or 
                            kc_name.lower() in section.get('content', '').lower() 
                            for kc_name in kc_names)
            
            if is_related:
                # Simplify the section content if it's related to a struggled component
                section_content = section.get('content', '')
                
                # Break long paragraphs into shorter ones
                paragraphs = section_content.split('\n')
                simplified_paragraphs = []
                
                for paragraph in paragraphs:
                    # Check if paragraph is too long
                    if len(paragraph) > 100:
                        # Split into sentences
                        sentences = sent_tokenize(paragraph)
                        # Recombine sentences into shorter paragraphs
                        current_paragraph = ""
                        for sentence in sentences:
                            if len(current_paragraph) + len(sentence) > 100:
                                simplified_paragraphs.append(current_paragraph)
                                current_paragraph = sentence
                            else:
                                if current_paragraph:
                                    current_paragraph += " " + sentence
                                else:
                                    current_paragraph = sentence
                        
                        if current_paragraph:
                            simplified_paragraphs.append(current_paragraph)
                    else:
                        simplified_paragraphs.append(paragraph)
                
                # Update the section with simplified content
                section['content'] = '\n\n'.join(simplified_paragraphs)
                
                # Add a note that this is an adapted section
                section['title'] = f"{section['title']} (Simplified)"
                
                # Add learning tips if not present
                if 'learning_tips' not in section:
                    section['learning_tips'] = []
                
                section['learning_tips'].append(
                    "This section has been simplified to help with your understanding. Take your time reading through it."
                )
                
                # Update the section in the content data
                simplified_content['sections'][i] = section
        
        return simplified_content
    
    def _add_explanations(self, content_data, struggled_kcs, related_content):
        """
        Add additional explanations and examples to the content to help with understanding.
        
        Args:
            content_data: The content data to enhance
            struggled_kcs: Knowledge components the student struggled with
            related_content: Related content for each knowledge component
            
        Returns:
            Enhanced content data with additional explanations
        """
        # Create a deep copy to avoid modifying the original
        enhanced_content = dict(content_data)
        
        # Extract the names of the components the student struggled with
        kc_names = [kc['name'] for kc in struggled_kcs]
        
        # Create a new section with additional explanations
        additional_section = {
            'title': "Additional Explanations and Examples",
            'content': "Here are some additional explanations and examples to help you understand the concepts:",
            'media_url': None,
            'learning_tips': [
                "These explanations are tailored to the areas where you had difficulty.",
                "Try working through the examples step by step.",
                "If you're still having trouble, don't hesitate to ask for help."
            ]
        }
        
        # For each struggled knowledge component, add explanations and examples
        for kc in struggled_kcs:
            kc_id = kc['id']
            kc_name = kc['name']
            kc_description = kc['description']
            
            # Add a subsection for this knowledge component
            kc_explanation = f"\n\n## {kc_name}\n\n{kc_description}\n\n"
            
            # Extract explanations and examples from related content
            if kc_id in related_content:
                for content_item in related_content[kc_id]:
                    item_data = json.loads(content_item['content_data'])
                    
                    for section in item_data.get('sections', []):
                        # Find sections that contain examples
                        if 'example' in section.get('title', '').lower():
                            kc_explanation += f"\n### Example from '{content_item['title']}'\n\n"
                            kc_explanation += section.get('content', '')
                            break
            
            # Add simple extra examples
            if kc_name == 'Addition':
                kc_explanation += "\n\n### Extra Examples\n\n"
                kc_explanation += "1 + 1 = 2\n\n2 + 2 = 4\n\n5 + 3 = 8\n\n"
                kc_explanation += "Remember, addition means combining quantities together to find the total."
            
            elif kc_name == 'Subtraction':
                kc_explanation += "\n\n### Extra Examples\n\n"
                kc_explanation += "5 - 2 = 3\n\n10 - 4 = 6\n\n8 - 3 = 5\n\n"
                kc_explanation += "Remember, subtraction means taking away one quantity from another."
            
            elif kc_name == 'Multiplication':
                kc_explanation += "\n\n### Extra Examples\n\n"
                kc_explanation += "2 × 3 = 6\n\n4 × 4 = 16\n\n5 × 2 = 10\n\n"
                kc_explanation += "Remember, multiplication is repeated addition: 5 × 2 means 5 + 5 = 10"
            
            elif kc_name == 'Division':
                kc_explanation += "\n\n### Extra Examples\n\n"
                kc_explanation += "6 ÷ 2 = 3\n\n10 ÷ 5 = 2\n\n8 ÷ 4 = 2\n\n"
                kc_explanation += "Remember, division means splitting into equal parts: 6 ÷ 2 means dividing 6 into 2 equal groups, with 3 in each group."
            
            # Add the explanation to the additional section
            additional_section['content'] += kc_explanation
        
        # Add the additional section to the content
        if enhanced_content.get('sections'):
            enhanced_content['sections'].append(additional_section)
        else:
            enhanced_content['sections'] = [additional_section]
        
        return enhanced_content
    
    def _adjust_difficulty(self, content_data):
        """
        Adjust the difficulty level of the content.
        
        Args:
            content_data: The content data to adjust
            
        Returns:
            Adjusted content data
        """
        # Create a deep copy to avoid modifying the original
        adjusted_content = dict(content_data)
        
        # Add a section with practice exercises at an easier level
        practice_section = {
            'title': "Practice Exercises - Building Confidence",
            'content': "Here are some practice exercises to help you build confidence with these concepts:",
            'media_url': None,
            'learning_tips': [
                "Start with the easier exercises and work your way up.",
                "Don't rush - take your time to understand each step."
            ]
        }
        
        # Add some simple practice exercises
        practice_content = "\n\n### Addition Practice\n\n"
        practice_content += "1. 2 + 3 = ?\n2. 5 + 4 = ?\n3. 3 + 7 = ?\n\n"
        
        practice_content += "### Subtraction Practice\n\n"
        practice_content += "1. 7 - 3 = ?\n2. 10 - 4 = ?\n3. 9 - 5 = ?\n\n"
        
        practice_content += "### Multiplication Practice\n\n"
        practice_content += "1. 2 × 3 = ?\n2. 3 × 4 = ?\n3. 5 × 2 = ?\n\n"
        
        practice_content += "### Division Practice\n\n"
        practice_content += "1. 6 ÷ 2 = ?\n2. 8 ÷ 4 = ?\n3. 10 ÷ 5 = ?\n\n"
        
        practice_content += "### Answers\n\n"
        practice_content += "Addition: 1. 5  2. 9  3. 10\n"
        practice_content += "Subtraction: 1. 4  2. 6  3. 4\n"
        practice_content += "Multiplication: 1. 6  2. 12  3. 10\n"
        practice_content += "Division: 1. 3  2. 2  3. 2"
        
        practice_section['content'] += practice_content
        
        # Add the practice section to the content
        if adjusted_content.get('sections'):
            adjusted_content['sections'].append(practice_section)
        else:
            adjusted_content['sections'] = [practice_section]
        
        return adjusted_content
    
    def store_adapted_content(self, user_id, adapted_content):
        """
        Store the adapted content in the database so it can be retrieved later.
        
        Args:
            user_id: The ID of the user
            adapted_content: The adapted content object
            
        Returns:
            ID of the stored adapted content
        """
        conn = self.get_db_connection()
        
        # Convert adapted content to JSON
        adapted_content_json = json.dumps(adapted_content)
        
        # Insert the adapted content
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO adapted_content 
            (user_id, original_content_id, adapted_content, created_at) 
            VALUES (?, ?, ?, ?)
            ''',
            (
                user_id, 
                adapted_content['original_content_id'], 
                adapted_content_json, 
                datetime.now().isoformat()
            )
        )
        
        # Get the ID of the inserted content
        adapted_content_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return adapted_content_id
    
    def get_adapted_content(self, user_id, original_content_id):
        """
        Retrieve previously adapted content for a user and original content ID.
        
        Args:
            user_id: The ID of the user
            original_content_id: The ID of the original content
            
        Returns:
            Adapted content object or None if not found
        """
        try:
            conn = self.get_db_connection()
            
            # Get the most recent adapted content
            adapted_content_row = conn.execute(
                '''
                SELECT id, adapted_content 
                FROM adapted_content 
                WHERE user_id = ? AND original_content_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
                ''',
                (user_id, original_content_id)
            ).fetchone()
            
            conn.close()
            
            if not adapted_content_row:
                logger.info(f"No adapted content found for user {user_id}, content {original_content_id}")
                return None
            
            # Parse the JSON content
            try:
                adapted_content = json.loads(adapted_content_row['adapted_content'])
                adapted_content['id'] = adapted_content_row['id']
                logger.info(f"Successfully retrieved adapted content with ID {adapted_content_row['id']}")
                return adapted_content
            except json.JSONDecodeError:
                logger.error(f"Failed to parse adapted content JSON for ID {adapted_content_row['id']}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving adapted content: {e}")
            return None