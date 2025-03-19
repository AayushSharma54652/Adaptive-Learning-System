import matplotlib
matplotlib.use('Agg')  # Non-interactive backend that doesn't require a GUI

import numpy as np
import pandas as pd
import sqlite3
import json
import logging
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LearningStyleDetection:
    """
    Uses machine learning to detect and adapt to student learning styles.
    Identifies visual, auditory, kinesthetic, and reading/writing preferences
    based on interaction patterns and performance.
    """
    
    def __init__(self, db_path='database/adaptive_learning.db'):
        """Initialize with database path"""
        self.db_path = db_path
        self.style_model = None
        self.scaler = StandardScaler()
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def extract_learning_style_features(self, user_id):
        """Extract features related to learning style preferences"""
        conn = self.get_db_connection()
        
        # Get user interaction data
        interactions = conn.execute('''
            SELECT content_id, interaction_type, timestamp, details
            FROM user_interaction_log
            WHERE user_id = ? AND details IS NOT NULL
            ORDER BY timestamp
        ''', (user_id,)).fetchall()
        
        # Get content types for each interaction
        content_types = {}
        
        for interaction in interactions:
            if interaction['content_id'] not in content_types:
                content_data = conn.execute('''
                    SELECT content_type, content_data
                    FROM content
                    WHERE id = ?
                ''', (interaction['content_id'],)).fetchone()
                
                if content_data:
                    content_types[interaction['content_id']] = {
                        'type': content_data['content_type'],
                        'data': json.loads(content_data['content_data']) if content_data['content_data'] else {}
                    }
        
        # Initialize feature counters
        visual_time = 0
        text_time = 0
        interactive_time = 0
        audio_time = 0
        
        visual_engagement = 0
        text_engagement = 0
        interactive_engagement = 0
        audio_engagement = 0
        
        # Process interaction details
        for interaction in interactions:
            content_id = interaction['content_id']
            details = json.loads(interaction['details']) if interaction['details'] else {}
            
            # Track time spent on different content types
            if 'text_time' in details:
                text_time += details['text_time']
            
            if 'visual_time' in details:
                visual_time += details['visual_time']
            
            if 'interactive_time' in details:
                interactive_time += details['interactive_time']
            
            if 'audio_time' in details:
                audio_time += details['audio_time']
            
            # Track engagement with different content elements
            if 'example_clicks' in details:
                interactive_engagement += details['example_clicks']
            
            if 'theory_clicks' in details:
                text_engagement += details['theory_clicks']
            
            if 'media_interactions' in details:
                visual_engagement += details.get('media_interactions', 0)
            
            if 'audio_interactions' in details:
                audio_engagement += details.get('audio_interactions', 0)
        
        # Get assessment performance by content type
        content_performance = {}
        
        assessment_data = conn.execute('''
            SELECT ai.id, ai.question_type, ur.is_correct
            FROM user_responses ur
            JOIN assessment_items ai ON ur.assessment_item_id = ai.id
            WHERE ur.user_id = ?
        ''', (user_id,)).fetchall()
        
        for item in assessment_data:
            q_type = item['question_type']
            if q_type not in content_performance:
                content_performance[q_type] = {
                    'correct': 0,
                    'total': 0
                }
            
            content_performance[q_type]['total'] += 1
            if item['is_correct']:
                content_performance[q_type]['correct'] += 1
        
        conn.close()
        
        # Calculate performance percentages
        visual_performance = content_performance.get('visual', {'correct': 0, 'total': 0})
        visual_score = visual_performance['correct'] / max(1, visual_performance['total'])
        
        text_performance = content_performance.get('text', {'correct': 0, 'total': 0})
        text_score = text_performance['correct'] / max(1, text_performance['total'])
        
        interactive_performance = content_performance.get('interactive', {'correct': 0, 'total': 0})
        interactive_score = interactive_performance['correct'] / max(1, interactive_performance['total'])
        
        # Calculate total time and normalize
        total_time = max(1, visual_time + text_time + interactive_time + audio_time)
        
        # Assemble features
        features = {
            'visual_time_ratio': visual_time / total_time,
            'text_time_ratio': text_time / total_time,
            'interactive_time_ratio': interactive_time / total_time,
            'audio_time_ratio': audio_time / total_time,
            
            'visual_engagement': visual_engagement,
            'text_engagement': text_engagement,
            'interactive_engagement': interactive_engagement,
            'audio_engagement': audio_engagement,
            
            'visual_performance': visual_score,
            'text_performance': text_score,
            'interactive_performance': interactive_score
        }
        
        return features
    
    def train_style_model(self):
        """Train a model to classify learning styles"""
        conn = self.get_db_connection()
        
        # Get all users with significant interaction data
        users = conn.execute('''
            SELECT user_id, COUNT(*) as count
            FROM user_interaction_log
            WHERE details IS NOT NULL
            GROUP BY user_id
            HAVING count >= 20
        ''').fetchall()
        
        conn.close()
        
        if not users or len(users) < 5:
            logger.warning("Not enough user data to train learning style model")
            return False
        
        # Extract features for each user
        features_list = []
        user_ids = []
        
        for user in users:
            user_id = user['user_id']
            user_features = self.extract_learning_style_features(user_id)
            
            if user_features:
                features_list.append(list(user_features.values()))
                user_ids.append(user_id)
        
        if not features_list:
            logger.warning("Could not extract learning style features")
            return False
        
        # Scale features
        features_array = np.array(features_list)
        scaled_features = self.scaler.fit_transform(features_array)
        
        # Use clustering to identify learning style patterns
        kmeans = KMeans(n_clusters=4, random_state=42)
        clusters = kmeans.fit_predict(scaled_features)
        
        # Map clusters to learning styles
        # This is a simplified approach; in a real system we would analyze cluster centers
        style_mapping = {
            0: 'visual',
            1: 'auditory',
            2: 'kinesthetic',
            3: 'reading/writing'
        }
        
        # Create labeled dataset for supervised learning
        X = features_array
        y = [style_mapping[c] for c in clusters]
        
        # Train a classifier
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        pipeline.fit(X, y)
        
        # Save the model
        joblib.dump(pipeline, 'models/learning_style_model.pkl')
        joblib.dump(self.scaler, 'models/learning_style_scaler.pkl')
        
        self.style_model = pipeline
        
        logger.info(f"Trained learning style model on {len(user_ids)} users")
        
        return True
    
    def detect_learning_style(self, user_id):
        """Detect a user's learning style"""
        if not self.style_model:
            try:
                self.style_model = joblib.load('models/learning_style_model.pkl')
                self.scaler = joblib.load('models/learning_style_scaler.pkl')
            except:
                logger.warning("No learning style model available. Training a new model.")
                success = self.train_style_model()
                if not success:
                    logger.error("Failed to train learning style model")
                    return self._get_default_style()
        
        # Extract features
        features = self.extract_learning_style_features(user_id)
        
        if not features:
            return self._get_default_style()
        
        # Prepare features
        features_array = np.array(list(features.values())).reshape(1, -1)
        
        # Make prediction
        predicted_style = self.style_model.predict(features_array)[0]
        probabilities = self.style_model.predict_proba(features_array)[0]
        
        # Get the confidence for the predicted style
        style_index = list(self.style_model.classes_).index(predicted_style)
        confidence = probabilities[style_index]
        
        # Calculate style scores
        style_scores = {}
        for i, style in enumerate(self.style_model.classes_):
            style_scores[style] = float(probabilities[i])
        
        # Determine if we have enough data for a confident prediction
        enough_data = (features.get('visual_time_ratio', 0) + 
              features.get('text_time_ratio', 0) + 
              features.get('interactive_time_ratio', 0) + 
              features.get('audio_time_ratio', 0)) > 0.1
        
        style_descriptions = {
            'visual': 'Learns best through images, diagrams, and visual demonstrations',
            'auditory': 'Learns best through listening to explanations and discussions',
            'kinesthetic': 'Learns best through hands-on activities and practice',
            'reading/writing': 'Learns best through reading and writing text-based content'
        }
        
        return {
            'style': predicted_style,
            'confidence': float(confidence),
            'style_scores': style_scores,
            'enough_data': enough_data,
            'description': style_descriptions.get(predicted_style, ''),
            'features': features
        }
    
    def _get_default_style(self):
        """Return default style when not enough data is available"""
        return {
            'style': 'visual',
            'confidence': 0.5,
            'style_scores': {
                'visual': 0.5,
                'auditory': 0.2,
                'kinesthetic': 0.2,
                'reading/writing': 0.1
            },
            'enough_data': False,
            'description': 'Default learning style (not enough data)',
            'features': {}
        }
    
    def generate_style_visualization(self, user_id):
        """
        Generate a visualization of the user's learning style preferences.
        Uses a non-interactive backend to avoid GUI thread issues.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Base64 encoded image data for the visualization
        """
        try:
            # Get the learning style data
            style_data = self.detect_learning_style(user_id)
            
            # Create a new figure with the Agg backend
            fig = plt.figure(figsize=(8, 8))
            
            # Create data for radar chart
            categories = ['Visual', 'Auditory', 'Kinesthetic', 'Reading/Writing']
            values = [
                style_data['style_scores'].get('visual', 0),
                style_data['style_scores'].get('auditory', 0),
                style_data['style_scores'].get('kinesthetic', 0),
                style_data['style_scores'].get('reading/writing', 0)
            ]
            
            # Duplicate the first value to close the loop
            values += values[:1]
            
            # Calculate angles for the radar chart
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Close the loop
            
            # Plot the radar chart
            ax = fig.add_subplot(111, polar=True)
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), categories)
            
            ax.set_ylim(0, 1)
            ax.set_title(f"Learning Style Profile: {style_data['style'].title()}")
            
            # Convert plot to base64 image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            # Make sure to close the figure to free up resources
            plt.close(fig)
            
            # Return as data URI
            return f"data:image/png;base64,{img_str}"
        
        except Exception as e:
            logger.error(f"Error generating learning style visualization: {e}")
            # Return a placeholder or error message
            return None
    
    def get_style_recommendations(self, user_id):
        """Get recommendations for content presentation based on learning style"""
        style_data = self.detect_learning_style(user_id)
        style = style_data['style']
        
        recommendations = {
            'content_types': [],
            'presentation_tips': []
        }
        
        if style == 'visual':
            recommendations['content_types'] = [
                'diagrams', 'charts', 'videos', 'infographics', 'mind maps'
            ]
            recommendations['presentation_tips'] = [
                'Use color coding to highlight important information',
                'Provide visual summaries for text-heavy content',
                'Include diagrams to illustrate relationships between concepts',
                'Use animated explanations for complex processes'
            ]
        
        elif style == 'auditory':
            recommendations['content_types'] = [
                'audio lectures', 'discussions', 'podcasts', 'verbal explanations'
            ]
            recommendations['presentation_tips'] = [
                'Include audio narration with text content',
                'Encourage verbal repetition of key concepts',
                'Provide opportunities for discussion-based learning',
                'Use mnemonics and rhymes for memorization'
            ]
        
        elif style == 'kinesthetic':
            recommendations['content_types'] = [
                'interactive simulations', 'hands-on exercises', 'practice problems', 'case studies'
            ]
            recommendations['presentation_tips'] = [
                'Include frequent interactive activities',
                'Provide real-world applications for abstract concepts',
                'Break learning into short, activity-based segments',
                'Incorporate movement and physical involvement when possible'
            ]
        
        elif style == 'reading/writing':
            recommendations['content_types'] = [
                'detailed text', 'written explanations', 'note-taking exercises', 'written summaries'
            ]
            recommendations['presentation_tips'] = [
                'Provide comprehensive written explanations',
                'Include opportunities for note-taking and summarization',
                'Use structured outlines and bullet points',
                'Incorporate writing activities for concept reinforcement'
            ]
        
        return recommendations