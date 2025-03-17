import sqlite3
from datetime import datetime
import json
import logging
import os
import numpy as np
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

class UserProfile:
    """
    Manages user profiles, learning styles, knowledge states, and interactions.
    Responsible for tracking and updating learner information.
    """
    
    def __init__(self):
        """Initialize UserProfile with database connection"""
        self.db_path = 'database/adaptive_learning.db'
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_user(self, user_id):
        """Initialize a new user's profile with default knowledge states"""
        conn = self.get_db_connection()
        
        # Get all knowledge components
        knowledge_components = conn.execute(
            'SELECT id FROM knowledge_components'
        ).fetchall()
        
        # Initialize user knowledge state for each component
        for kc in knowledge_components:
            conn.execute(
                'INSERT INTO user_knowledge_state (user_id, knowledge_component_id, mastery_level) VALUES (?, ?, ?)',
                (user_id, kc['id'], 0.0)
            )
        
        # Initialize user with the default learning path
        default_path = conn.execute(
            'SELECT id FROM learning_paths ORDER BY id LIMIT 1'
        ).fetchone()
        
        if default_path:
            conn.execute(
                'INSERT INTO user_learning_paths (user_id, learning_path_id, current_position) VALUES (?, ?, ?)',
                (user_id, default_path['id'], 0)
            )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized user profile for user ID: {user_id}")
    
    def get_profile(self, user_id):
        """Get user profile data including knowledge state"""
        conn = self.get_db_connection()
        
        # Get user basic info
        user = conn.execute(
            'SELECT username, email, created_at FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        
        # Get knowledge state
        knowledge_state = conn.execute(
            '''
            SELECT kc.id, kc.name, kc.domain, uks.mastery_level
            FROM user_knowledge_state uks
            JOIN knowledge_components kc ON uks.knowledge_component_id = kc.id
            WHERE uks.user_id = ?
            ''',
            (user_id,)
        ).fetchall()
        
        # Get current learning path
        learning_path = conn.execute(
            '''
            SELECT lp.id, lp.name, lp.description, ulp.current_position, ulp.completed
            FROM user_learning_paths ulp
            JOIN learning_paths lp ON ulp.learning_path_id = lp.id
            WHERE ulp.user_id = ?
            ''',
            (user_id,)
        ).fetchone()
        
        # Get learning style (if any)
        learning_style = self._determine_learning_style(user_id)
        
        conn.close()
        
        # Construct the profile object
        profile = {
            'user_info': dict(user) if user else {},
            'knowledge_state': [dict(ks) for ks in knowledge_state],
            'learning_path': dict(learning_path) if learning_path else {},
            'learning_style': learning_style
        }
        
        return profile
    
    def update_knowledge_state(self, user_id, content_id, assessment_results):
        """Update the user's knowledge state based on assessment results"""
        conn = self.get_db_connection()
        
        # Get knowledge components related to this content
        kc_mappings = conn.execute(
            '''
            SELECT knowledge_component_id, relevance_weight
            FROM content_knowledge_map
            WHERE content_id = ?
            ''',
            (content_id,)
        ).fetchall()
        
        # Check the structure of assessment_results
        # It might be a dictionary with 'questions' key instead of a list
        if isinstance(assessment_results, dict) and 'questions' in assessment_results:
            questions_results = assessment_results['questions']
        else:
            questions_results = assessment_results
        
        for kc_map in kc_mappings:
            kc_id = kc_map['knowledge_component_id']
            weight = kc_map['relevance_weight']
            
            # Get the current mastery level
            current_mastery = conn.execute(
                'SELECT mastery_level FROM user_knowledge_state WHERE user_id = ? AND knowledge_component_id = ?',
                (user_id, kc_id)
            ).fetchone()['mastery_level']
            
            # Check if there are assessment results for this knowledge component
            kc_results = []
            
            # Safely extract results for this knowledge component
            for r in questions_results:
                # Handle both dictionary and object access
                if isinstance(r, dict) and 'knowledge_component_id' in r:
                    if r['knowledge_component_id'] == kc_id:
                        kc_results.append(r)
                elif hasattr(r, 'knowledge_component_id'):
                    if r.knowledge_component_id == kc_id:
                        kc_results.append(r)
            
            if kc_results:
                # Calculate average score for this knowledge component
                # Safely extract scores
                total_score = 0
                for r in kc_results:
                    if isinstance(r, dict) and 'score' in r:
                        total_score += r['score']
                    elif hasattr(r, 'score'):
                        total_score += r.score
                    else:
                        # Default to 0.5 if no score available
                        total_score += 0.5
                
                avg_score = total_score / len(kc_results)
                
                # Update knowledge state with a learning rate factor
                learning_rate = 0.1
                new_mastery = current_mastery + learning_rate * weight * (avg_score - current_mastery)
                
                # Ensure mastery is between 0 and 1
                new_mastery = max(0.0, min(1.0, new_mastery))
                
                # Update the database
                conn.execute(
                    '''
                    UPDATE user_knowledge_state
                    SET mastery_level = ?, last_updated = ?
                    WHERE user_id = ? AND knowledge_component_id = ?
                    ''',
                    (new_mastery, datetime.now(), user_id, kc_id)
                )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated knowledge state for user ID: {user_id}")
    
    def log_interaction(self, user_id, content_id, interaction_type, timestamp, details=None):
        """Log user interaction with the system"""
        conn = self.get_db_connection()
        
        details_json = json.dumps(details) if details else None
        
        conn.execute(
            '''
            INSERT INTO user_interaction_log (user_id, content_id, interaction_type, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (user_id, content_id, interaction_type, timestamp, details_json)
        )
        
        conn.commit()
        conn.close()
    
    def get_progress_metrics(self, user_id):
        """Get progress metrics for the user"""
        conn = self.get_db_connection()
        
        # Get overall knowledge mastery
        knowledge_state = conn.execute(
            'SELECT knowledge_component_id, mastery_level FROM user_knowledge_state WHERE user_id = ?',
            (user_id,)
        ).fetchall()
        
        # Get learning path progress
        learning_path = conn.execute(
            '''
            SELECT lp.id, lp.name, ulp.current_position, COUNT(lpi.id) as total_items
            FROM user_learning_paths ulp
            JOIN learning_paths lp ON ulp.learning_path_id = lp.id
            JOIN learning_path_items lpi ON lp.id = lpi.learning_path_id
            WHERE ulp.user_id = ?
            GROUP BY lp.id
            ''',
            (user_id,)
        ).fetchone()
        
        # Get assessment performance
        assessment_performance = conn.execute(
            '''
            SELECT COUNT(*) as total_questions, SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
            FROM user_responses
            WHERE user_id = ?
            ''',
            (user_id,)
        ).fetchone()
        
        # Get recent activity
        recent_activity = conn.execute(
            '''
            SELECT interaction_type, content_id, timestamp
            FROM user_interaction_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
            ''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        
        # Calculate average mastery
        total_mastery = sum(ks['mastery_level'] for ks in knowledge_state)
        avg_mastery = total_mastery / len(knowledge_state) if knowledge_state else 0
        
        # Calculate path completion percentage
        path_completion = 0
        if learning_path:
            if learning_path['total_items'] > 0:
                path_completion = (learning_path['current_position'] / learning_path['total_items']) * 100
        
        # Calculate assessment accuracy
        assessment_accuracy = 0
        if assessment_performance and assessment_performance['total_questions'] > 0:
            assessment_accuracy = (assessment_performance['correct_answers'] / assessment_performance['total_questions']) * 100
        
        return {
            'average_mastery': avg_mastery,
            'path_completion': path_completion,
            'assessment_accuracy': assessment_accuracy,
            'recent_activity': [dict(activity) for activity in recent_activity]
        }
    
    def _determine_learning_style(self, user_id):
        """
        Determine the user's learning style based on interaction patterns
        Uses a simple clustering approach based on time spent and interaction types
        """
        conn = self.get_db_connection()
        
        # Get user interactions
        interactions = conn.execute(
            '''
            SELECT interaction_type, details, timestamp
            FROM user_interaction_log
            WHERE user_id = ? AND details IS NOT NULL
            ORDER BY timestamp
            ''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        
        # If not enough interactions, return default style
        if len(interactions) < 10:
            return {
                'style': 'visual',
                'confidence': 0.5,
                'description': 'Default learning style (not enough data)'
            }
        
        # Extract features from interactions
        features = []
        for interaction in interactions:
            details = json.loads(interaction['details']) if interaction['details'] else {}
            
            # Example features:
            # - Time spent on text vs. visual content
            # - Frequency of pausing video
            # - Speed of answering questions
            # - Preference for examples vs. theory
            
            text_time = details.get('text_time', 0)
            visual_time = details.get('visual_time', 0)
            example_clicks = details.get('example_clicks', 0)
            theory_clicks = details.get('theory_clicks', 0)
            
            if text_time or visual_time or example_clicks or theory_clicks:
                features.append([text_time, visual_time, example_clicks, theory_clicks])
        
        # If no useful features, return default
        if not features:
            return {
                'style': 'visual',
                'confidence': 0.5,
                'description': 'Default learning style (insufficient data)'
            }
        
        # Simple clustering to determine style (in a real system, use more sophisticated methods)
        try:
            features_array = np.array(features)
            kmeans = KMeans(n_clusters=3, random_state=0).fit(features_array)
            cluster = kmeans.predict([np.mean(features_array, axis=0)])[0]
            
            # Map cluster to learning style
            styles = ['visual', 'auditory', 'kinesthetic']
            style = styles[cluster % len(styles)]
            
            # Calculate confidence based on cluster distance
            distances = kmeans.transform([np.mean(features_array, axis=0)])
            total_distance = sum(distances[0])
            confidence = 1.0 - (distances[0][cluster] / total_distance) if total_distance > 0 else 0.5
            
            style_descriptions = {
                'visual': 'Learns best through images, diagrams, and visual demonstrations',
                'auditory': 'Learns best through listening to explanations and discussions',
                'kinesthetic': 'Learns best through hands-on activities and practice'
            }
            
            return {
                'style': style,
                'confidence': confidence,
                'description': style_descriptions.get(style, '')
            }
        
        except Exception as e:
            logger.error(f"Error determining learning style: {e}")
            return {
                'style': 'visual',
                'confidence': 0.5,
                'description': 'Default learning style (error in analysis)'
            }