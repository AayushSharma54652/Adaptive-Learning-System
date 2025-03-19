import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PredictiveAnalytics:
    """
    Uses machine learning to predict student performance, identify at-risk students,
    and provide early intervention recommendations.
    """
    
    def __init__(self, db_path='database/adaptive_learning.db'):
        """Initialize with database path"""
        self.db_path = db_path
        self.performance_model = None
        self.engagement_model = None
        self.scaler = StandardScaler()
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def extract_features(self, user_id):
        """Extract features for a specific user to use in predictions"""
        conn = self.get_db_connection()
        
        # Time-based features
        one_week_ago = datetime.now() - timedelta(days=7)
        
        # Learning activity metrics
        activity_metrics = conn.execute(
            '''
            SELECT 
                COUNT(*) as total_interactions,
                AVG(CASE WHEN json_extract(details, '$.text_time') IS NOT NULL 
                    THEN json_extract(details, '$.text_time') ELSE 0 END) as avg_text_time,
                AVG(CASE WHEN json_extract(details, '$.visual_time') IS NOT NULL 
                    THEN json_extract(details, '$.visual_time') ELSE 0 END) as avg_visual_time,
                COUNT(DISTINCT content_id) as unique_contents,
                COUNT(DISTINCT strftime('%Y-%m-%d', timestamp)) as active_days
            FROM user_interaction_log
            WHERE user_id = ? AND timestamp > ?
            ''',
            (user_id, one_week_ago)
        ).fetchone()
        
        # Assessment performance
        assessment_metrics = conn.execute(
            '''
            SELECT 
                COUNT(*) as total_assessments,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                AVG(response_time_seconds) as avg_response_time
            FROM user_responses
            WHERE user_id = ? AND timestamp > ?
            ''',
            (user_id, one_week_ago)
        ).fetchone()
        
        # Knowledge state metrics
        knowledge_metrics = conn.execute(
            '''
            SELECT 
                AVG(mastery_level) as avg_mastery,
                MIN(mastery_level) as min_mastery,
                MAX(mastery_level) as max_mastery,
                COUNT(*) as total_components,
                SUM(CASE WHEN mastery_level < 0.4 THEN 1 ELSE 0 END) as weak_components
            FROM user_knowledge_state
            WHERE user_id = ?
            ''',
            (user_id,)
        ).fetchone()
        
        # Session patterns
        session_data = conn.execute(
            '''
            SELECT 
                timestamp,
                interaction_type
            FROM user_interaction_log
            WHERE user_id = ?
            ORDER BY timestamp
            ''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        
        # Calculate session patterns
        session_times = []
        current_session_start = None
        
        for i, interaction in enumerate(session_data):
            if i == 0 or current_session_start is None:
                current_session_start = datetime.fromisoformat(interaction['timestamp'])
                continue
                
            current_time = datetime.fromisoformat(interaction['timestamp'])
            time_diff = (current_time - current_session_start).total_seconds() / 60  # in minutes
            
            # If more than 30 minutes between interactions, consider it a new session
            if time_diff > 30:
                session_times.append(time_diff)
                current_session_start = current_time
        
        avg_session_time = np.mean(session_times) if session_times else 0
        session_count = len(session_times) + 1
        
        # Combine features
        features = {
            # Activity features
            'total_interactions': activity_metrics['total_interactions'] if activity_metrics else 0,
            'avg_text_time': activity_metrics['avg_text_time'] if activity_metrics else 0,
            'avg_visual_time': activity_metrics['avg_visual_time'] if activity_metrics else 0,
            'unique_contents': activity_metrics['unique_contents'] if activity_metrics else 0,
            'active_days': activity_metrics['active_days'] if activity_metrics else 0,
            
            # Assessment features
            'total_assessments': assessment_metrics['total_assessments'] if assessment_metrics else 0,
            'assessment_accuracy': (assessment_metrics['correct_answers'] / assessment_metrics['total_assessments']) 
                                  if assessment_metrics and assessment_metrics['total_assessments'] > 0 else 0,
            'avg_response_time': assessment_metrics['avg_response_time'] if assessment_metrics else 0,
            
            # Knowledge features
            'avg_mastery': knowledge_metrics['avg_mastery'] if knowledge_metrics else 0,
            'mastery_range': (knowledge_metrics['max_mastery'] - knowledge_metrics['min_mastery']) 
                             if knowledge_metrics else 0,
            'weak_component_ratio': (knowledge_metrics['weak_components'] / knowledge_metrics['total_components']) 
                                    if knowledge_metrics and knowledge_metrics['total_components'] > 0 else 0,
            
            # Session features
            'avg_session_time': avg_session_time,
            'session_count': session_count,
            'sessions_per_day': session_count / 7  # assuming 7 days of data
        }
        
        return features
    
    def train_performance_model(self):
        """Train a model to predict future assessment performance"""
        conn = self.get_db_connection()
        
        # Get all users
        users = conn.execute('SELECT id FROM users').fetchall()
        
        training_data = []
        target_data = []
        
        for user in users:
            user_id = user['id']
            
            # Get user features
            features = self.extract_features(user_id)
            
            # Get future performance (target)
            future_performance = conn.execute(
                '''
                SELECT 
                    AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as performance
                FROM user_responses
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
                ''',
                (user_id,)
            ).fetchone()
            
            if future_performance and future_performance['performance'] is not None:
                training_data.append(list(features.values()))
                target_data.append(future_performance['performance'])
        
        conn.close()
        
        if len(training_data) < 10:
            logger.warning("Not enough training data for performance model")
            return False
        
        # Create and train the model
        X_train, X_test, y_train, y_test = train_test_split(
            np.array(training_data), np.array(target_data), test_size=0.2, random_state=42
        )
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(n_estimators=100, random_state=42))
        ])
        
        pipeline.fit(X_train, y_train)
        
        # Evaluate model
        score = pipeline.score(X_test, y_test)
        logger.info(f"Performance model R² score: {score}")
        
        self.performance_model = pipeline
        
        # Save model
        joblib.dump(pipeline, 'models/performance_model.pkl')
        
        return True
    
    def train_engagement_model(self):
        """Train a model to predict student disengagement"""
        conn = self.get_db_connection()
        
        # Get all users
        users = conn.execute('SELECT id FROM users').fetchall()
        
        training_data = []
        target_data = []
        
        for user in users:
            user_id = user['id']
            
            # Get user features
            features = self.extract_features(user_id)
            
            # Define disengagement as no activity in the past week
            engagement_status = conn.execute(
                '''
                SELECT 
                    CASE WHEN MAX(julianday(timestamp)) > julianday('now', '-7 days') THEN 0 ELSE 1 END as disengaged
                FROM user_interaction_log
                WHERE user_id = ?
                ''',
                (user_id,)
            ).fetchone()
            
            if engagement_status:
                training_data.append(list(features.values()))
                target_data.append(engagement_status['disengaged'])
        
        conn.close()
        
        if len(training_data) < 10:
            logger.warning("Not enough training data for engagement model")
            return False
        
        # Create and train the model
        X_train, X_test, y_train, y_test = train_test_split(
            np.array(training_data), np.array(target_data), test_size=0.2, random_state=42
        )
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        pipeline.fit(X_train, y_train)
        
        # Evaluate model
        score = pipeline.score(X_test, y_test)
        logger.info(f"Engagement model accuracy: {score}")
        
        self.engagement_model = pipeline
        
        # Save model
        joblib.dump(pipeline, 'models/engagement_model.pkl')
        
        return True
    
    def predict_performance(self, user_id):
        """Predict future assessment performance for a user"""
        if not self.performance_model:
            try:
                self.performance_model = joblib.load('models/performance_model.pkl')
            except:
                logger.error("No performance model available. Train the model first.")
                return None
        
        features = self.extract_features(user_id)
        
        # Convert features to array
        features_array = np.array(list(features.values())).reshape(1, -1)
        
        # Make prediction
        predicted_performance = self.performance_model.predict(features_array)[0]
        
        return {
            'predicted_performance': predicted_performance,
            'confidence': 0.8,  # Placeholder - in a real system this would be calculated
            'features_importance': features
        }
    
    def predict_disengagement_risk(self, user_id):
        """Predict risk of disengagement for a user"""
        if not self.engagement_model:
            try:
                self.engagement_model = joblib.load('models/engagement_model.pkl')
            except:
                logger.error("No engagement model available. Train the model first.")
                return None
        
        features = self.extract_features(user_id)
        
        # Convert features to array
        features_array = np.array(list(features.values())).reshape(1, -1)
        
        # Make prediction
        disengagement_prob = self.engagement_model.predict_proba(features_array)[0][1]
        
        risk_level = 'low'
        if disengagement_prob > 0.7:
            risk_level = 'high'
        elif disengagement_prob > 0.4:
            risk_level = 'medium'
        
        return {
            'disengagement_probability': disengagement_prob,
            'risk_level': risk_level,
            'contributing_factors': self._identify_contributing_factors(features)
        }
    
    def _identify_contributing_factors(self, features):
        """Identify factors contributing to disengagement risk"""
        contributing_factors = []
        
        if features['active_days'] <= 2:
            contributing_factors.append({
                'factor': 'Low activity frequency',
                'description': 'Student has been active on fewer than 3 days in the past week'
            })
        
        if features['assessment_accuracy'] < 0.6:
            contributing_factors.append({
                'factor': 'Poor assessment performance',
                'description': 'Student has been scoring below 60% on recent assessments'
            })
        
        if features['avg_session_time'] < 10 and features['total_interactions'] > 0:
            contributing_factors.append({
                'factor': 'Short session duration',
                'description': 'Average session duration is less than 10 minutes'
            })
        
        if features['weak_component_ratio'] > 0.5:
            contributing_factors.append({
                'factor': 'Knowledge gaps',
                'description': 'More than half of knowledge components have low mastery levels'
            })
        
        return contributing_factors
    
    def get_intervention_recommendations(self, user_id):
        """Generate personalized intervention recommendations"""
        disengagement_risk = self.predict_disengagement_risk(user_id)
        performance_prediction = self.predict_performance(user_id)
        
        if not disengagement_risk or not performance_prediction:
            return []
        
        recommendations = []
        
        # Base recommendations on disengagement risk
        if disengagement_risk['risk_level'] == 'high':
            recommendations.append({
                'type': 'engagement',
                'priority': 'high',
                'action': 'Send personalized re-engagement message',
                'description': 'Student shows high risk of dropping out. Send a personalized message to reconnect.'
            })
            
            # Add specific recommendations based on contributing factors
            for factor in disengagement_risk['contributing_factors']:
                if factor['factor'] == 'Low activity frequency':
                    recommendations.append({
                        'type': 'schedule',
                        'priority': 'high',
                        'action': 'Suggest learning schedule',
                        'description': 'Create a recommended learning schedule for the student.'
                    })
                
                if factor['factor'] == 'Poor assessment performance':
                    recommendations.append({
                        'type': 'content',
                        'priority': 'high',
                        'action': 'Provide remedial content',
                        'description': 'Offer simpler content focused on fundamentals.'
                    })
        
        # Add recommendations based on performance prediction
        if performance_prediction['predicted_performance'] < 0.7:
            recommendations.append({
                'type': 'support',
                'priority': 'medium',
                'action': 'Offer additional support resources',
                'description': 'Student may struggle with upcoming assessments. Provide additional practice materials.'
            })
        
        return recommendations