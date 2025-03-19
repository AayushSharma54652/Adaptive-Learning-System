import sqlite3
import json
import logging
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdaptationEngine:
    """
    Manages the adaptation of the learning experience based on user performance and preferences.
    Responsible for content recommendation, difficulty adjustment, and learning path optimization.
    Uses AI/ML techniques for enhanced personalization.
    """
    
    def __init__(self):
        """Initialize AdaptationEngine with database connection"""
        self.db_path = 'database/adaptive_learning.db'
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_recommendations(self, user_id):
        """
        Generate personalized content recommendations for a user using AI techniques.
        """
        # First, try to use the AI-powered recommendation system
        try:
            from modules.content_recommendation import ContentRecommendation
            recommender = ContentRecommendation()
            ai_recommendations = recommender.get_diverse_recommendations(user_id)
            
            if ai_recommendations and len(ai_recommendations) >= 3:
                return ai_recommendations
        except Exception as e:
            logger.error(f"Error using AI recommendations: {e}")
            # Fall back to traditional recommendation method
        
        # Original recommendation code as fallback
        conn = self.get_db_connection()
        
        # Get user's knowledge state
        knowledge_state = conn.execute(
            '''
            SELECT knowledge_component_id, mastery_level
            FROM user_knowledge_state
            WHERE user_id = ?
            ''',
            (user_id,)
        ).fetchall()
        
        # Create a dictionary of component mastery levels
        mastery_levels = {ks['knowledge_component_id']: ks['mastery_level'] for ks in knowledge_state}
        
        # Get user's current learning path progress
        learning_path = conn.execute(
            '''
            SELECT lp.id, ulp.current_position
            FROM user_learning_paths ulp
            JOIN learning_paths lp ON ulp.learning_path_id = lp.id
            WHERE ulp.user_id = ? AND ulp.completed = 0
            ORDER BY ulp.started_at DESC
            LIMIT 1
            ''',
            (user_id,)
        ).fetchone()
        
        recommendations = []
        
        # 1. Next content in learning path
        if learning_path:
            path_id = learning_path['id']
            current_position = learning_path['current_position']
            
            next_in_path = conn.execute(
                '''
                SELECT lpi.content_id, c.title, c.description, c.difficulty, c.tags
                FROM learning_path_items lpi
                JOIN content c ON lpi.content_id = c.id
                WHERE lpi.learning_path_id = ? AND lpi.sequence_order > ?
                ORDER BY lpi.sequence_order
                LIMIT 1
                ''',
                (path_id, current_position)
            ).fetchone()
            
            if next_in_path:
                recommendations.append({
                    'content_id': next_in_path['content_id'],
                    'title': next_in_path['title'],
                    'description': next_in_path['description'],
                    'difficulty': next_in_path['difficulty'],
                    'tags': next_in_path['tags'].split(',') if next_in_path['tags'] else [],
                    'recommendation_type': 'next_in_path',
                    'relevance_score': 1.0  # Highest priority
                })
        
        # 2. Content for knowledge components with low mastery
        weak_components = [(kc_id, mastery) for kc_id, mastery in mastery_levels.items() if mastery < 0.6]
        weak_components.sort(key=lambda x: x[1])  # Sort by mastery level (ascending)
        
        for kc_id, mastery in weak_components[:3]:  # Top 3 weak components
            # Find content that targets this knowledge component
            remedial_content = conn.execute(
                '''
                SELECT c.id, c.title, c.description, c.difficulty, c.tags
                FROM content c
                JOIN content_knowledge_map ckm ON c.id = ckm.content_id
                WHERE ckm.knowledge_component_id = ?
                ORDER BY c.difficulty ASC
                LIMIT 1
                ''',
                (kc_id,)
            ).fetchone()
            
            if remedial_content:
                # Check if this content is already in recommendations
                if not any(r['content_id'] == remedial_content['id'] for r in recommendations):
                    recommendations.append({
                        'content_id': remedial_content['id'],
                        'title': remedial_content['title'],
                        'description': remedial_content['description'],
                        'difficulty': remedial_content['difficulty'],
                        'tags': remedial_content['tags'].split(',') if remedial_content['tags'] else [],
                        'recommendation_type': 'remedial',
                        'relevance_score': 0.9 - mastery  # Higher for lower mastery
                    })
        
        # 3. Content similar to recently accessed (content-based filtering)
        recent_content = conn.execute(
            '''
            SELECT content_id
            FROM user_interaction_log
            WHERE user_id = ? AND content_id IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 5
            ''',
            (user_id,)
        ).fetchall()
        
        recent_content_ids = [rc['content_id'] for rc in recent_content if rc['content_id']]
        
        if recent_content_ids:
            # For simplicity, we'll just use tag similarity
            # In a real system, use more sophisticated content-based similarity metrics
            for content_id in recent_content_ids:
                content_tags = conn.execute(
                    'SELECT tags FROM content WHERE id = ?',
                    (content_id,)
                ).fetchone()
                
                if content_tags and content_tags['tags']:
                    tags = content_tags['tags'].split(',')
                    
                    # Find content with similar tags
                    tag_conditions = ' OR '.join(['tags LIKE ?' for _ in tags])
                    tag_params = [f'%{tag}%' for tag in tags]
                    
                    similar_content = conn.execute(
                        f'''
                        SELECT id, title, description, difficulty, tags
                        FROM content
                        WHERE id != ? AND ({tag_conditions})
                        ORDER BY RANDOM()
                        LIMIT 2
                        ''',
                        [content_id] + tag_params
                    ).fetchall()
                    
                    for sc in similar_content:
                        if not any(r['content_id'] == sc['id'] for r in recommendations):
                            recommendations.append({
                                'content_id': sc['id'],
                                'title': sc['title'],
                                'description': sc['description'],
                                'difficulty': sc['difficulty'],
                                'tags': sc['tags'].split(',') if sc['tags'] else [],
                                'recommendation_type': 'similar_content',
                                'relevance_score': 0.7  # Medium priority
                            })
        
        # 4. Collaborative filtering (users with similar performance patterns)
        # This is a simplified version - a real implementation would use more sophisticated CF
        if len(recommendations) < 5:
            # Find users with similar knowledge states
            user_mastery_avg = sum(mastery_levels.values()) / len(mastery_levels) if mastery_levels else 0
            
            similar_users = conn.execute(
                '''
                SELECT user_id, AVG(mastery_level) as avg_mastery
                FROM user_knowledge_state
                WHERE user_id != ?
                GROUP BY user_id
                ORDER BY ABS(avg_mastery - ?) ASC
                LIMIT 5
                ''',
                (user_id, user_mastery_avg)
            ).fetchall()
            
            for similar_user in similar_users:
                # Find content that this similar user has interacted with positively
                positive_content = conn.execute(
                    '''
                    SELECT DISTINCT uil.content_id, c.title, c.description, c.difficulty, c.tags
                    FROM user_interaction_log uil
                    JOIN content c ON uil.content_id = c.id
                    WHERE uil.user_id = ? 
                      AND uil.interaction_type IN ('complete', 'like', 'bookmark')
                      AND uil.content_id NOT IN (
                          SELECT content_id 
                          FROM user_interaction_log 
                          WHERE user_id = ? AND content_id IS NOT NULL
                      )
                    LIMIT 2
                    ''',
                    (similar_user['user_id'], user_id)
                ).fetchall()
                
                for pc in positive_content:
                    if not any(r['content_id'] == pc['content_id'] for r in recommendations):
                        recommendations.append({
                            'content_id': pc['content_id'],
                            'title': pc['title'],
                            'description': pc['description'],
                            'difficulty': pc['difficulty'],
                            'tags': pc['tags'].split(',') if pc['tags'] else [],
                            'recommendation_type': 'collaborative',
                            'relevance_score': 0.6  # Lower priority
                        })
        
        conn.close()
        
        # Sort by relevance score and limit to 5 recommendations
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        return recommendations[:5]
    
    def get_next_content(self, user_id, current_content_id, assessment_results=None):
        """
        Determine the next content to present based on the user's performance on the current content.
        Updates the user's learning path position.
        """
        # Try to use ML-enhanced recommendation first
        try:
            from modules.predictive_analytics import PredictiveAnalytics
            predictor = PredictiveAnalytics()
            
            # If we have assessment results and they indicate poor performance
            if assessment_results and not assessment_results.get('mastery_achieved', False):
                # Get knowledge gaps and provide targeted content
                from modules.assessment import AssessmentEngine
                assessment_engine = AssessmentEngine()
                knowledge_gaps = assessment_engine.get_knowledge_gaps(user_id)
                
                if knowledge_gaps:
                    # Use the content recommendation system to find content for the top gap
                    from modules.content_recommendation import ContentRecommendation
                    recommender = ContentRecommendation()
                    gap_recommendations = recommender.recommend_for_knowledge_gaps(user_id, limit=1)
                    
                    if gap_recommendations:
                        return {
                            'content_id': gap_recommendations[0]['content_id'],
                            'title': gap_recommendations[0]['title'],
                            'description': gap_recommendations[0]['description'],
                            'recommendation_type': 'knowledge_gap'
                        }
        except Exception as e:
            logger.error(f"Error using ML-enhanced next content selection: {e}")
            # Fall back to traditional method
        
        # Original method as fallback
        conn = self.get_db_connection()
        
        # Get current learning path
        learning_path = conn.execute(
            '''
            SELECT ulp.id, ulp.learning_path_id, ulp.current_position
            FROM user_learning_paths ulp
            JOIN learning_path_items lpi ON ulp.learning_path_id = lpi.learning_path_id
            WHERE ulp.user_id = ? AND lpi.content_id = ?
            LIMIT 1
            ''',
            (user_id, current_content_id)
        ).fetchone()
        
        # If we have assessment results, use them to determine if we should move forward
        should_advance = True
        if assessment_results:
            # Check if the user achieved mastery
            should_advance = assessment_results.get('mastery_achieved', False)
        
        next_content = None
        
        if learning_path and should_advance:
            # Update the current position in the learning path
            conn.execute(
                '''
                UPDATE user_learning_paths
                SET current_position = current_position + 1
                WHERE id = ?
                ''',
                (learning_path['id'],)
            )
            
            # Get the next content in the path
            next_in_path = conn.execute(
                '''
                SELECT lpi.content_id, c.title, c.description
                FROM learning_path_items lpi
                JOIN content c ON lpi.content_id = c.id
                WHERE lpi.learning_path_id = ? AND lpi.sequence_order > ?
                ORDER BY lpi.sequence_order
                LIMIT 1
                ''',
                (learning_path['learning_path_id'], learning_path['current_position'])
            ).fetchone()
            
            if next_in_path:
                next_content = dict(next_in_path)
            else:
                # Mark the learning path as completed
                conn.execute(
                    '''
                    UPDATE user_learning_paths
                    SET completed = 1, completed_at = ?
                    WHERE id = ?
                    ''',
                    (datetime.now(), learning_path['id'])
                )
        
        # If no next content from the path or should not advance, get a recommendation
        if not next_content:
            if not should_advance:
                # Recommend remedial content for the same knowledge components
                kc_mappings = conn.execute(
                    '''
                    SELECT knowledge_component_id
                    FROM content_knowledge_map
                    WHERE content_id = ?
                    ''',
                    (current_content_id,)
                ).fetchall()
                
                kc_ids = [kc['knowledge_component_id'] for kc in kc_mappings]
                
                if kc_ids:
                    # Find alternative content for the same knowledge components
                    alternative_content = conn.execute(
                        f'''
                        SELECT DISTINCT c.id, c.title, c.description
                        FROM content c
                        JOIN content_knowledge_map ckm ON c.id = ckm.content_id
                        WHERE c.id != ? AND ckm.knowledge_component_id IN ({','.join(['?'] * len(kc_ids))})
                        ORDER BY c.difficulty ASC
                        LIMIT 1
                        ''',
                        [current_content_id] + kc_ids
                    ).fetchone()
                    
                    if alternative_content:
                        next_content = dict(alternative_content)
            
            # If still no next content, get the top recommendation
            if not next_content:
                recommendations = self.get_recommendations(user_id)
                if recommendations:
                    next_content = {
                        'content_id': recommendations[0]['content_id'],
                        'title': recommendations[0]['title'],
                        'description': recommendations[0]['description']
                    }
        
        conn.commit()
        conn.close()
        
        return next_content
    
    def adjust_content_difficulty(self, user_id, knowledge_component_id):
        """
        Adjust content difficulty based on the user's mastery level for a knowledge component.
        Returns the optimal difficulty level for new content.
        """
        # Try to use ML-enhanced difficulty adjustment first
        try:
            from modules.predictive_analytics import PredictiveAnalytics
            predictor = PredictiveAnalytics()
            
            # Get performance prediction
            performance = predictor.predict_performance(user_id)
            
            if performance and 'predicted_performance' in performance:
                # Adjust difficulty based on predicted performance
                prediction = performance['predicted_performance']
                
                if prediction > 0.85:  # Very high predicted performance
                    return 3  # Challenging
                elif prediction > 0.7:  # Good predicted performance
                    return 2  # Moderate
                else:  # Lower predicted performance
                    return 1  # Easier
        except Exception as e:
            logger.error(f"Error using ML-enhanced difficulty adjustment: {e}")
            # Fall back to traditional method
        
        # Original method as fallback
        conn = self.get_db_connection()
        
        # Get the user's mastery level for this knowledge component
        mastery = conn.execute(
            '''
            SELECT mastery_level
            FROM user_knowledge_state
            WHERE user_id = ? AND knowledge_component_id = ?
            ''',
            (user_id, knowledge_component_id)
        ).fetchone()
        
        conn.close()
        
        if not mastery:
            return 1  # Default to easiest difficulty
        
        mastery_level = mastery['mastery_level']
        
        # Dynamic difficulty adjustment
        # - If mastery is low, provide easier content for reinforcement
        # - If mastery is high, provide more challenging content
        # - Apply a slight challenge increase for optimal learning (Zone of Proximal Development)
        
        if mastery_level < 0.3:
            # Low mastery - provide easy content
            optimal_difficulty = 1
        elif mastery_level < 0.6:
            # Medium mastery - provide moderate difficulty
            optimal_difficulty = 2
        else:
            # High mastery - provide challenging content
            optimal_difficulty = 3
        
        return optimal_difficulty
    
    def detect_disengagement(self, user_id):
        """
        Detect potential user disengagement based on interaction patterns.
        Uses ML predictions when available.
        Returns a risk assessment and recommended interventions.
        """
        # Try to use ML-enhanced disengagement detection first
        try:
            from modules.predictive_analytics import PredictiveAnalytics
            predictor = PredictiveAnalytics()
            
            # Get disengagement risk prediction
            risk = predictor.predict_disengagement_risk(user_id)
            
            if risk and 'risk_level' in risk:
                # Get intervention recommendations
                interventions = predictor.get_intervention_recommendations(user_id)
                
                # If we have recommended interventions, return them
                if interventions:
                    primary_intervention = interventions[0]
                    
                    return {
                        'disengagement_risk': risk['risk_level'],
                        'reason': ', '.join([factor['factor'] for factor in risk['contributing_factors']]) 
                                if 'contributing_factors' in risk and risk['contributing_factors'] else 'ML-detected pattern',
                        'intervention': primary_intervention['action']
                    }
                
                # Otherwise, return the risk assessment with a generic intervention
                return {
                    'disengagement_risk': risk['risk_level'],
                    'reason': 'ML-detected pattern',
                    'intervention': f"Personalized {risk['risk_level']} priority intervention recommended"
                }
        except Exception as e:
            logger.error(f"Error using ML-enhanced disengagement detection: {e}")
            # Fall back to traditional method
        
        # Original method as fallback
        conn = self.get_db_connection()
        
        # Get recent interaction data (within the last week)
        one_week_ago = datetime.now() - timedelta(days=7)
        
        interactions = conn.execute(
            '''
            SELECT interaction_type, timestamp, details
            FROM user_interaction_log
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
            ''',
            (user_id, one_week_ago)
        ).fetchall()
        
        # Get assessment performance trend
        assessment_trend = conn.execute(
            '''
            SELECT is_correct, timestamp
            FROM user_responses
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp
            ''',
            (user_id, one_week_ago)
        ).fetchall()
        
        conn.close()
        
        # Analyze interaction frequency
        if not interactions:
            return {
                'disengagement_risk': 'high',
                'reason': 'No recent activity',
                'intervention': 'Send a re-engagement notification with personalized content recommendations'
            }
        
        # Calculate days since last interaction
        last_interaction = datetime.fromisoformat(interactions[0]['timestamp'])
        days_since_last = (datetime.now() - last_interaction).days
        
        if days_since_last > 3:
            return {
                'disengagement_risk': 'medium',
                'reason': f'No activity for {days_since_last} days',
                'intervention': 'Send a gentle reminder with interesting content preview'
            }
        
        # Analyze interaction types
        interaction_types = [i['interaction_type'] for i in interactions]
        
        # Check for signs of frustration (quick page exits, skipped content)
        if interaction_types.count('exit') > 5 and interaction_types.count('complete') < 2:
            return {
                'disengagement_risk': 'medium',
                'reason': 'Multiple exits without completing content',
                'intervention': 'Offer easier content or alternative learning formats'
            }
        
        # Analyze assessment performance trend
        if assessment_trend:
            recent_performance = [1 if ar['is_correct'] else 0 for ar in assessment_trend[-5:]] if len(assessment_trend) >= 5 else []
            if recent_performance and sum(recent_performance) / len(recent_performance) < 0.4:
                return {
                    'disengagement_risk': 'medium',
                    'reason': 'Declining assessment performance',
                    'intervention': 'Offer remedial content and additional practice'
                }
        
        # Default case - no disengagement risk detected
        return {
            'disengagement_risk': 'low',
            'reason': 'Regular engagement patterns',
            'intervention': None
        }