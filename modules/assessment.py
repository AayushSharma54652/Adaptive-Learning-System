import sqlite3
import json
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class AssessmentEngine:
    """
    Manages the assessment process, including question selection,
    response evaluation, and feedback generation.
    Adapts question difficulty based on user performance.
    """
    
    def __init__(self):
        """Initialize AssessmentEngine with database connection"""
        self.db_path = 'database/adaptive_learning.db'
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_assessment(self, content_id, user_id):
        """
        Generate an adaptive assessment for a specific content and user.
        Selects questions that target the knowledge components of the content
        and adapts the difficulty based on the user's knowledge state.
        """
        conn = self.get_db_connection()
        
        # Get knowledge components related to this content
        knowledge_components = conn.execute(
            '''
            SELECT knowledge_component_id
            FROM content_knowledge_map
            WHERE content_id = ?
            ''',
            (content_id,)
        ).fetchall()
        
        kc_ids = [kc['knowledge_component_id'] for kc in knowledge_components]
        
        if not kc_ids:
            conn.close()
            return {
                'content_id': content_id,
                'questions': []
            }
        
        # Get user's knowledge state for these components
        knowledge_states = {}
        for kc_id in kc_ids:
            state = conn.execute(
                '''
                SELECT mastery_level
                FROM user_knowledge_state
                WHERE user_id = ? AND knowledge_component_id = ?
                ''',
                (user_id, kc_id)
            ).fetchone()
            
            if state:
                knowledge_states[kc_id] = state['mastery_level']
            else:
                knowledge_states[kc_id] = 0.0
        
        # Select appropriate questions for each knowledge component
        questions = []
        
        for kc_id in kc_ids:
            # Get the user's mastery level for this component
            mastery_level = knowledge_states.get(kc_id, 0.0)
            
            # Determine ideal question difficulty
            # If mastery is low, provide easier questions
            # If mastery is high, provide more challenging questions
            if mastery_level < 0.3:
                target_difficulty = 1.0  # Easy
            elif mastery_level < 0.7:
                target_difficulty = 1.5  # Medium
            else:
                target_difficulty = 2.0  # Challenging
            
            # Find questions close to the target difficulty
            kc_questions = conn.execute(
                '''
                SELECT id, question_text, question_type, options, difficulty, knowledge_component_id
                FROM assessment_items
                WHERE knowledge_component_id = ?
                ORDER BY ABS(difficulty - ?) ASC
                LIMIT 3
                ''',
                (kc_id, target_difficulty)
            ).fetchall()
            
            # Add questions to the assessment
            for question in kc_questions:
                questions.append({
                    'id': question['id'],
                    'text': question['question_text'],
                    'type': question['question_type'],
                    'options': json.loads(question['options']) if question['options'] else None,
                    'difficulty': question['difficulty'],
                    'knowledge_component_id': question['knowledge_component_id']
                })
        
        # Limit the total number of questions (adjust as needed)
        max_questions = 5
        if len(questions) > max_questions:
            questions = random.sample(questions, max_questions)
        
        conn.close()
        
        return {
            'content_id': content_id,
            'questions': questions
        }
    
    def evaluate_assessment(self, user_id, content_id, responses):
        """
        Evaluate user responses to assessment questions.
        Records responses, calculates scores, and provides feedback.
        """
        conn = self.get_db_connection()
        
        results = []
        
        for response in responses:
            question_id = response['question_id']
            user_answer = response['answer']
            response_time = response.get('response_time', 0)
            
            # Get the question details
            question = conn.execute(
                '''
                SELECT question_text, correct_answer, explanation, difficulty, knowledge_component_id
                FROM assessment_items
                WHERE id = ?
                ''',
                (question_id,)
            ).fetchone()
            
            if not question:
                continue
            
            # Check if the answer is correct
            is_correct = user_answer == question['correct_answer']
            
            # Calculate score (0-1)
            score = 1.0 if is_correct else 0.0
            
            # Record the response
            conn.execute(
                '''
                INSERT INTO user_responses
                (user_id, assessment_item_id, user_response, is_correct, response_time_seconds)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, question_id, user_answer, is_correct, response_time)
            )
            
            # Add to results
            results.append({
                'question_id': question_id,
                'is_correct': is_correct,
                'correct_answer': question['correct_answer'],
                'explanation': question['explanation'],
                'score': score,
                'knowledge_component_id': question['knowledge_component_id']
            })
        
        conn.commit()
        conn.close()
        
        # Calculate overall results
        total_score = sum(r['score'] for r in results) / len(results) if results else 0
        
        assessment_result = {
            'questions': results,
            'total_score': total_score,
            'mastery_achieved': total_score >= 0.8,  # Consider mastery at 80%
            'feedback': self._generate_feedback(results, total_score)
        }
        
        return assessment_result
    
    def _generate_feedback(self, results, total_score):
        """Generate feedback based on assessment results"""
        if not results:
            return "No assessment data available."
        
        # Count correct answers
        correct_count = sum(1 for r in results if r['is_correct'])
        total_count = len(results)
        
        # Generate overall feedback
        if total_score >= 0.8:
            overall = "Excellent work! You've demonstrated a strong understanding of the material."
        elif total_score >= 0.6:
            overall = "Good job! You've grasped most of the concepts, but there's still room for improvement."
        else:
            overall = "You're making progress, but you may need to review the material again to strengthen your understanding."
        
        # Generate specific feedback for incorrect answers
        specific_feedback = []
        for result in results:
            if not result['is_correct']:
                feedback = f"Question ID {result['question_id']}: {result['explanation']}"
                specific_feedback.append(feedback)
        
        # Combine feedback
        feedback = f"{overall}\n\nYou answered {correct_count} out of {total_count} questions correctly."
        
        if specific_feedback:
            feedback += "\n\nHere's feedback on questions you missed:\n" + "\n".join(specific_feedback)
        
        return feedback
    
    def get_knowledge_gaps(self, user_id):
        """
        Identify knowledge gaps based on assessment history.
        Returns knowledge components where the user has consistently performed poorly.
        """
        conn = self.get_db_connection()
        
        # Get recent assessment performance by knowledge component
        performance = conn.execute(
            '''
            SELECT 
                ai.knowledge_component_id,
                kc.name as component_name,
                COUNT(ur.id) as total_questions,
                SUM(CASE WHEN ur.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
            FROM user_responses ur
            JOIN assessment_items ai ON ur.assessment_item_id = ai.id
            JOIN knowledge_components kc ON ai.knowledge_component_id = kc.id
            WHERE ur.user_id = ?
            GROUP BY ai.knowledge_component_id
            ''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        
        # Identify components with low performance
        knowledge_gaps = []
        for p in performance:
            if p['total_questions'] >= 3:  # Only consider components with enough data
                accuracy = p['correct_answers'] / p['total_questions']
                if accuracy < 0.6:  # Below 60% accuracy indicates a gap
                    knowledge_gaps.append({
                        'knowledge_component_id': p['knowledge_component_id'],
                        'component_name': p['component_name'],
                        'accuracy': accuracy,
                        'total_questions': p['total_questions']
                    })
        
        # Sort by accuracy (lowest first)
        knowledge_gaps.sort(key=lambda x: x['accuracy'])
        
        return knowledge_gaps