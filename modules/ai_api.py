from flask import Blueprint, jsonify, request, session
import logging
import os
import json
from datetime import datetime

# Import AI modules
from modules.predictive_analytics import PredictiveAnalytics
from modules.content_recommendation import ContentRecommendation
from modules.learning_style_detection import LearningStyleDetection

logger = logging.getLogger(__name__)

# Initialize Blueprint
ai_api = Blueprint('ai_api', __name__, url_prefix='/api/ai')

# Initialize AI components
predictive_analytics = PredictiveAnalytics()
content_recommendation = ContentRecommendation()
learning_style_detection = LearningStyleDetection()

@ai_api.route('/predict/performance', methods=['GET'])
def predict_performance():
    """API endpoint to predict a user's future performance"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Make prediction
    prediction = predictive_analytics.predict_performance(user_id)
    
    if not prediction:
        return jsonify({
            'error': 'Could not generate prediction',
            'message': 'Not enough data available or model not trained'
        }), 500
    
    return jsonify(prediction)

@ai_api.route('/predict/disengagement', methods=['GET'])
def predict_disengagement():
    """API endpoint to predict disengagement risk"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Make prediction
    prediction = predictive_analytics.predict_disengagement_risk(user_id)
    
    if not prediction:
        return jsonify({
            'error': 'Could not generate prediction',
            'message': 'Not enough data available or model not trained'
        }), 500
    
    return jsonify(prediction)

@ai_api.route('/recommendations/interventions', methods=['GET'])
def get_interventions():
    """API endpoint to get intervention recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Get recommendations
    recommendations = predictive_analytics.get_intervention_recommendations(user_id)
    
    return jsonify({
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    })

@ai_api.route('/content/similar/<int:content_id>', methods=['GET'])
def similar_content(content_id):
    """API endpoint to get content similar to a given content item"""
    limit = request.args.get('limit', 5, type=int)
    
    # Get similar content
    recommendations = content_recommendation.recommend_similar_content(content_id, limit=limit)
    
    return jsonify({
        'content_id': content_id,
        'recommendations': recommendations
    })

@ai_api.route('/content/recommend', methods=['GET'])
def recommend_content():
    """API endpoint to get personalized content recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    limit = request.args.get('limit', 5, type=int)
    
    # Get recommendations
    recommendations = content_recommendation.get_diverse_recommendations(user_id, limit=limit)
    
    return jsonify({
        'user_id': user_id,
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    })

@ai_api.route('/user/learning-style', methods=['GET'])
def get_learning_style():
    """API endpoint to get a user's learning style"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Get learning style
    style_data = learning_style_detection.detect_learning_style(user_id)
    
    return jsonify(style_data)

@ai_api.route('/user/learning-style/visualization', methods=['GET'])
def get_style_visualization():
    """API endpoint to get a visualization of the user's learning style"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Generate visualization
    visualization = learning_style_detection.generate_style_visualization(user_id)
    
    return jsonify({
        'user_id': user_id,
        'visualization': visualization,
        'timestamp': datetime.now().isoformat()
    })

@ai_api.route('/user/learning-style/recommendations', methods=['GET'])
def get_style_recommendations():
    """API endpoint to get recommendations based on learning style"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Get recommendations
    recommendations = learning_style_detection.get_style_recommendations(user_id)
    
    return jsonify({
        'user_id': user_id,
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    })

@ai_api.route('/train/models', methods=['POST'])
def train_models():
    """API endpoint to train AI models (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check if user is admin
    from app import is_admin
    if not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    models_to_train = request.json.get('models', ['all'])
    results = {}
    
    if 'all' in models_to_train or 'performance' in models_to_train:
        results['performance_model'] = predictive_analytics.train_performance_model()
    
    if 'all' in models_to_train or 'engagement' in models_to_train:
        results['engagement_model'] = predictive_analytics.train_engagement_model()
    
    if 'all' in models_to_train or 'learning_style' in models_to_train:
        results['learning_style_model'] = learning_style_detection.train_style_model()
    
    if 'all' in models_to_train or 'content_vectors' in models_to_train:
        results['content_vectors'] = content_recommendation.build_content_vectors() is not None
    
    return jsonify({
        'success': True,
        'results': results,
        'timestamp': datetime.now().isoformat()
    })

# Add the blueprint to app.py by adding:
# from modules.ai_api import ai_api
# app.register_blueprint(ai_api)