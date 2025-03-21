from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
import logging
from datetime import datetime, timedelta

# Import modules
from modules.user import UserProfile
from modules.content import ContentModule
from modules.assessment import AssessmentEngine
from modules.adaptation import AdaptationEngine

from modules.predictive_analytics import PredictiveAnalytics
from modules.content_recommendation import ContentRecommendation
from modules.learning_style_detection import LearningStyleDetection
from modules.ai_api import ai_api
from modules.content_adaptation import ContentAdaptation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Register blueprint
app.register_blueprint(ai_api)

# Initialize database connection
def get_db_connection():
    conn = sqlite3.connect('database/adaptive_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize core components
user_profile = UserProfile()
content_module = ContentModule()
assessment_engine = AssessmentEngine()
adaptation_engine = AdaptationEngine()

# Initialize AI components
predictive_analytics = PredictiveAnalytics()
content_recommendation = ContentRecommendation()
learning_style_detection = LearningStyleDetection()

# Routes


def is_admin(user_id):
    """Check if a user has admin privileges"""
    conn = get_db_connection()
    user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return user and user['is_admin'] == 1

@app.context_processor
def inject_is_admin():
    """Add is_admin flag to all templates"""
    if 'user_id' in session:
        return {'is_admin': is_admin(session['user_id'])}
    return {'is_admin': False}



@app.route('/')
def index():
    """Landing page route"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        
        # Check if username already exists
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', 
                                    (username,)).fetchone()
        
        if existing_user:
            conn.close()
            return render_template('index.html', registration_error="Username already exists")
        
        # Create new user
        conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, hashed_password, email))
        conn.commit()
        
        # Get the new user's ID
        user_id = conn.execute('SELECT id FROM users WHERE username = ?', 
                              (username,)).fetchone()[0]
        
        # Initialize user profile
        user_profile.initialize_user(user_id)
        
        conn.close()
        
        # Auto-login the user
        session['user_id'] = user_id
        session['username'] = username
        
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT id, username, password FROM users WHERE username = ?', 
                           (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        
        return render_template('index.html', login_error="Invalid username or password")
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    """User logout route"""
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Student dashboard route with AI-powered insights"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get user profile data
    profile_data = user_profile.get_profile(user_id)
    
    # Get recommended content - using traditional method first for safety
    recommended_content = adaptation_engine.get_recommendations(user_id)
    
    # Try to get AI-powered features, but gracefully handle errors
    learning_style = None
    risk_assessment = None
    performance_prediction = None
    
    try:
        # Get AI-enhanced learning style
        learning_style = learning_style_detection.detect_learning_style(user_id)
        profile_data['learning_style'] = learning_style
    except Exception as e:
        logger.error(f"Error getting learning style: {e}")
        # Use default learning style
        profile_data['learning_style'] = {
            'style': 'visual',
            'confidence': 0.5,
            'description': 'Default learning style (AI not yet available)'
        }
    
    try:
        # Get disengagement risk assessment
        risk_assessment = predictive_analytics.predict_disengagement_risk(user_id)
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        # Use default risk assessment
        risk_assessment = {
            'disengagement_risk': 'low',
            'reason': 'Not enough data for analysis',
            'intervention': None
        }
    
    try:
        # Get predicted performance
        performance_prediction = predictive_analytics.predict_performance(user_id)
    except Exception as e:
        logger.error(f"Error getting performance prediction: {e}")
        # Use default prediction
        performance_prediction = {
            'predicted_performance': 0.75,
            'confidence': 0.5,
            'features_importance': {}
        }
    
    # Get progress metrics
    progress = user_profile.get_progress_metrics(user_id)
    
    return render_template('dashboard.html', 
                          username=session['username'],
                          profile=profile_data,
                          recommended_content=recommended_content,
                          progress=progress,
                          risk_assessment=risk_assessment,
                          performance_prediction=performance_prediction)


@app.route('/learning/<content_id>')
def learning_content(content_id):
    """Learning content page route with adaptation for struggling students"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Initialize modules
    content_module = ContentModule()
    assessment_engine = AssessmentEngine()
    content_adaptation = ContentAdaptation()
    
    # Get original content first (needed regardless of adaptation)
    original_content = content_module.get_content(content_id)
    
    # Try to get previously adapted content - do this first
    adapted_content_obj = content_adaptation.get_adapted_content(user_id, content_id)
    
    if adapted_content_obj:
        # We found adapted content, use it
        logger.info(f"Found existing adapted content for user {user_id}, content {content_id}")
        content = dict(original_content)
        content['title'] = adapted_content_obj['title']
        content['content_data'] = adapted_content_obj['content_data']
        content['is_adapted'] = True
        content['adaptation_reason'] = adapted_content_obj.get('adaptation_reason', 'Customized for your learning needs')
        logger.info(f"Using adapted content with {len(content['content_data'].get('sections', []))} sections")
    else:
        # Check if we need to create adapted content
        needs_adaptation = assessment_engine.check_needs_adapted_content(user_id, content_id)
        logger.info(f"User {user_id} needs adaptation for content {content_id}: {needs_adaptation}")
        
        if needs_adaptation:
            logger.info("No adapted content found, generating new adaptation")
            # No adapted content exists, create it using the last assessment results
            conn = get_db_connection()
            try:
                # Get the most recent assessment responses for this content
                last_assessment = conn.execute(
                    '''
                    SELECT ur.user_response, ur.is_correct, ai.id as question_id, 
                           ai.knowledge_component_id, ai.correct_answer, ai.explanation
                    FROM user_responses ur
                    JOIN assessment_items ai ON ur.assessment_item_id = ai.id
                    JOIN content_knowledge_map ckm ON ai.knowledge_component_id = ckm.knowledge_component_id
                    WHERE ur.user_id = ? AND ckm.content_id = ?
                    ORDER BY ur.timestamp DESC
                    LIMIT 5
                    ''',
                    (user_id, content_id)
                ).fetchall()
                
                # Format assessment results for the adaptation function
                assessment_results = {
                    'questions': [
                        {
                            'question_id': row['question_id'],
                            'is_correct': bool(row['is_correct']),
                            'correct_answer': row['correct_answer'],
                            'explanation': row['explanation'],
                            'knowledge_component_id': row['knowledge_component_id']
                        }
                        for row in last_assessment
                    ],
                    'total_score': 0.0,  # Assume failed assessment
                    'mastery_achieved': False
                }
                
                # If we have assessment results, use them
                if assessment_results['questions']:
                    logger.info(f"Creating adapted content with {len(assessment_results['questions'])} questions")
                    # Create adapted content
                    adapted_content_obj = content_adaptation.adapt_content_for_struggling_student(
                        user_id, content_id, assessment_results
                    )
                    
                    # Store the adapted content for future use
                    if adapted_content_obj:
                        logger.info("Successfully created adapted content, storing it")
                        content_adaptation.store_adapted_content(user_id, adapted_content_obj)
                        
                        # Mark adaptation as provided
                        assessment_engine.mark_adaptation_provided(user_id, content_id)
                        
                        # Use the newly created adapted content
                        content = dict(original_content)
                        content['title'] = adapted_content_obj['title']
                        content['content_data'] = adapted_content_obj['content_data']
                        content['is_adapted'] = True
                        content['adaptation_reason'] = adapted_content_obj.get('adaptation_reason', 'Customized for your learning needs')
                    else:
                        logger.error("Failed to create adapted content")
                        content = original_content
                else:
                    logger.warning("No assessment results found for adaptation")
                    content = original_content
            except Exception as e:
                logger.error(f"Error creating adapted content: {e}", exc_info=True)
                content = original_content
            finally:
                conn.close()
        else:
            # No adaptation needed, use regular content
            content = original_content
            logger.info("Using original content (no adaptation needed)")
    
    # Log that user has started this content
    user_profile = UserProfile()
    user_profile.log_interaction(user_id, content_id, 'start', datetime.now())
    
    return render_template('learning.html', 
                          content=content,
                          username=session['username'])



@app.route('/assessment/<content_id>')
def assessment(content_id):
    """Assessment page route"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get appropriate assessment for this content and user
    assessment_data = assessment_engine.generate_assessment(content_id, user_id)
    
    return render_template('assessment.html',
                          assessment=assessment_data,
                          content_id=content_id,
                          username=session['username'])

# Updated API endpoint for assessment submission - add to app.py

@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    """API endpoint to submit assessment responses with enhanced feedback for failed assessments"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        content_id = data['content_id']
        responses = data['responses']
        
        # Initialize modules
        assessment_engine = AssessmentEngine()
        user_profile = UserProfile()
        adaptation_engine = AdaptationEngine()
        content_adaptation = ContentAdaptation()
        
        # Process the assessment
        results = assessment_engine.evaluate_assessment(user_id, content_id, responses)
        
        # Update user knowledge state
        user_profile.update_knowledge_state(user_id, content_id, results)
        
        # Get next content recommendation
        next_content = adaptation_engine.get_next_content(user_id, content_id, results)
        
        # Enhance response with adaptation information if needed
        if results.get('needs_adaptation', False):
            try:
                # Create adapted content for future use
                adapted_content = content_adaptation.adapt_content_for_struggling_student(
                    user_id, content_id, results
                )
                
                if adapted_content:
                    # Store the adapted content
                    adapted_id = content_adaptation.store_adapted_content(user_id, adapted_content)
                    
                    # Mark that adaptation has been provided
                    assessment_engine.mark_adaptation_provided(user_id, content_id)
                    
                    # Add adaptation info to results
                    results['adaptation_available'] = True
                    results['adaptation_message'] = (
                        "We've prepared a simplified version of this content tailored to your learning needs. "
                        "Review the areas you struggled with before trying the assessment again."
                    )
                else:
                    results['adaptation_available'] = False
            except Exception as e:
                logger.error(f"Error creating adapted content: {e}")
                results['adaptation_available'] = False
        
        return jsonify({
            'results': results,
            'next_content': next_content
        })
    except Exception as e:
        logger.error(f"Error in submit_assessment: {e}")
        return jsonify({'error': 'An error occurred while processing your assessment.'}), 500
    

@app.route('/api/log-interaction', methods=['POST'])
def log_interaction():
    """API endpoint to log user interactions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    content_id = data['content_id']
    interaction_type = data['type']
    
    # Fix for ISO timestamp with Z suffix (UTC timezone)
    timestamp_str = data['timestamp']
    if timestamp_str.endswith('Z'):
        # Remove the Z and handle the timezone
        timestamp_str = timestamp_str[:-1]  # Remove 'Z'
    
    try:
        # First try direct parsing
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        # If that fails, try a more flexible approach
        from datetime import datetime as dt
        timestamp = dt.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
    
    details = data.get('details', {})
    
    # Log the interaction
    user_profile.log_interaction(user_id, content_id, interaction_type, timestamp, details)
    
    return jsonify({'status': 'success'})

@app.route('/settings')
def settings():
    """User settings page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    try:
        # Get user info - only select columns we know exist
        user = conn.execute(
            'SELECT id, username, email FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        
        # Convert to dictionary and add placeholder values for missing columns
        user_dict = dict(user)
        user_dict.setdefault('bio', '')
        user_dict.setdefault('profile_pic', '')
        
        # Get user preferences (create if not exists)
        preferences = conn.execute(
            'SELECT * FROM user_preferences WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        if not preferences:
            # Insert default preferences
            conn.execute(
                '''
                INSERT INTO user_preferences 
                (user_id, learning_style, difficulty_preference, learning_pace, 
                 email_notifications, notify_progress, notify_recommendations, notify_reminders,
                 text_size, high_contrast, share_progress, data_collection) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (user_id, 'auto', 3, 'normal', 1, 1, 1, 1, 'medium', 0, 0, 1)
            )
            conn.commit()
            
            preferences = conn.execute(
                'SELECT * FROM user_preferences WHERE user_id = ?',
                (user_id,)
            ).fetchone()
        
        # Convert preferences to a dictionary for easier access in the template
        user_preferences = dict(preferences) if preferences else {}
        
    except sqlite3.Error as e:
        # Handle database errors
        conn.close()
        print(f"Database error: {e}")
        flash("An error occurred while loading settings. Please try again later.")
        return redirect(url_for('dashboard'))
    
    conn.close()
    
    return render_template('settings.html', 
                          user=user_dict, 
                          user_preferences=user_preferences,
                          username=session['username'])


@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data
    display_name = request.form['display_name']
    email = request.form['email']
    bio = request.form['bio']
    
    conn = get_db_connection()
    
    # Update user info
    conn.execute(
        '''
        UPDATE users 
        SET username = ?, email = ?, bio = ?
        WHERE id = ?
        ''',
        (display_name, email, bio, user_id)
    )
    conn.commit()
    conn.close()
    
    # Update session username if changed
    if display_name != session['username']:
        session['username'] = display_name
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', profile_updated=True))

@app.route('/change_password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # Validate passwords match
    if new_password != confirm_password:
        return redirect(url_for('settings', password_error="Passwords do not match"))
    
    conn = get_db_connection()
    
    # Get current password hash
    user = conn.execute(
        'SELECT password FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    
    # Verify current password
    if not check_password_hash(user['password'], current_password):
        conn.close()
        return redirect(url_for('settings', password_error="Current password is incorrect"))
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    conn.execute(
        'UPDATE users SET password = ? WHERE id = ?',
        (hashed_password, user_id)
    )
    conn.commit()
    conn.close()
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', password_updated=True))

@app.route('/update_learning_preferences', methods=['POST'])
def update_learning_preferences():
    """Update learning preferences"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data
    learning_style = request.form.get('learning_style', 'auto')
    difficulty_preference = int(request.form.get('difficulty_preference', 3))
    learning_pace = request.form.get('learning_pace', 'normal')
    
    conn = get_db_connection()
    
    # Update preferences
    conn.execute(
        '''
        UPDATE user_preferences 
        SET learning_style = ?, difficulty_preference = ?, learning_pace = ?
        WHERE user_id = ?
        ''',
        (learning_style, difficulty_preference, learning_pace, user_id)
    )
    conn.commit()
    conn.close()
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', learning_prefs_updated=True))

@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    """Update notification preferences"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data (checkboxes will be absent if not checked)
    email_notifications = 1 if 'email_notifications' in request.form else 0
    notify_progress = 1 if 'notify_progress' in request.form else 0
    notify_recommendations = 1 if 'notify_recommendations' in request.form else 0
    notify_reminders = 1 if 'notify_reminders' in request.form else 0
    
    conn = get_db_connection()
    
    # Update preferences
    conn.execute(
        '''
        UPDATE user_preferences 
        SET email_notifications = ?, notify_progress = ?, 
            notify_recommendations = ?, notify_reminders = ?
        WHERE user_id = ?
        ''',
        (email_notifications, notify_progress, notify_recommendations, notify_reminders, user_id)
    )
    conn.commit()
    conn.close()
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', notifications_updated=True))

@app.route('/update_accessibility', methods=['POST'])
def update_accessibility():
    """Update accessibility preferences"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data
    text_size = request.form.get('text_size', 'medium')
    high_contrast = 1 if 'high_contrast' in request.form else 0
    
    conn = get_db_connection()
    
    # Update preferences
    conn.execute(
        '''
        UPDATE user_preferences 
        SET text_size = ?, high_contrast = ?
        WHERE user_id = ?
        ''',
        (text_size, high_contrast, user_id)
    )
    conn.commit()
    conn.close()
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', accessibility_updated=True))

@app.route('/update_privacy', methods=['POST'])
def update_privacy():
    """Update privacy preferences"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Get form data
    share_progress = 1 if 'share_progress' in request.form else 0
    data_collection = 1 if 'data_collection' in request.form else 0
    
    conn = get_db_connection()
    
    # Update preferences
    conn.execute(
        '''
        UPDATE user_preferences 
        SET share_progress = ?, data_collection = ?
        WHERE user_id = ?
        ''',
        (share_progress, data_collection, user_id)
    )
    conn.commit()
    conn.close()
    
    # Redirect back to settings with success message
    return redirect(url_for('settings', privacy_updated=True))

# API routes for data management
@app.route('/api/export-user-data')
def export_user_data():
    """Export user data as JSON"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Get user data (excluding password)
    user = conn.execute(
        'SELECT id, username, email, bio, created_at FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    
    # Get knowledge state
    knowledge_state = conn.execute(
        '''
        SELECT kc.name, kc.domain, uks.mastery_level, uks.last_updated
        FROM user_knowledge_state uks
        JOIN knowledge_components kc ON uks.knowledge_component_id = kc.id
        WHERE uks.user_id = ?
        ''',
        (user_id,)
    ).fetchall()
    
    # Get learning paths
    learning_paths = conn.execute(
        '''
        SELECT lp.name, lp.description, ulp.current_position, ulp.completed, 
               ulp.started_at, ulp.completed_at
        FROM user_learning_paths ulp
        JOIN learning_paths lp ON ulp.learning_path_id = lp.id
        WHERE ulp.user_id = ?
        ''',
        (user_id,)
    ).fetchall()
    
    # Get assessment history
    assessments = conn.execute(
        '''
        SELECT ai.question_text, ur.user_response, ur.is_correct, ur.response_time_seconds, 
               ur.timestamp, kc.name as knowledge_component
        FROM user_responses ur
        JOIN assessment_items ai ON ur.assessment_item_id = ai.id
        JOIN knowledge_components kc ON ai.knowledge_component_id = kc.id
        WHERE ur.user_id = ?
        ORDER BY ur.timestamp DESC
        ''',
        (user_id,)
    ).fetchall()
    
    # Get interaction history
    interactions = conn.execute(
        '''
        SELECT uil.interaction_type, uil.timestamp, c.title as content_title, uil.details
        FROM user_interaction_log uil
        LEFT JOIN content c ON uil.content_id = c.id
        WHERE uil.user_id = ?
        ORDER BY uil.timestamp DESC
        LIMIT 500
        ''',
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    # Assemble the data
    user_data = {
        'user_info': dict(user),
        'knowledge_state': [dict(ks) for ks in knowledge_state],
        'learning_paths': [dict(lp) for lp in learning_paths],
        'assessments': [dict(a) for a in assessments],
        'interactions': [dict(i) for i in interactions],
        'export_date': datetime.now().isoformat()
    }
    
    # Create response with appropriate headers for download
    response = make_response(json.dumps(user_data, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=learning_data_{user_id}.json'
    
    return response

@app.route('/api/clear-learning-history', methods=['POST'])
def clear_learning_history():
    """Clear user learning history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Clear interaction history
    conn.execute('DELETE FROM user_interaction_log WHERE user_id = ?', (user_id,))
    
    # Clear assessment responses
    conn.execute('DELETE FROM user_responses WHERE user_id = ?', (user_id,))
    
    # Reset knowledge state
    conn.execute(
        'UPDATE user_knowledge_state SET mastery_level = 0.0 WHERE user_id = ?',
        (user_id,)
    )
    
    # Reset learning paths
    conn.execute(
        'UPDATE user_learning_paths SET current_position = 0, completed = 0, completed_at = NULL WHERE user_id = ?',
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/delete-account', methods=['POST'])
def delete_account():
    """Delete user account and all associated data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Delete user data
    conn.execute('DELETE FROM user_interaction_log WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM user_responses WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM user_knowledge_state WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM user_learning_paths WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
    
    # Finally, delete the user
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    # Clear session
    session.clear()
    
    return jsonify({'status': 'success'})


@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Check if user is admin
    if not is_admin(user_id):
        flash("You don't have permission to access this page.")
        return redirect(url_for('dashboard'))
    
    # Get system stats
    conn = get_db_connection()
    
    # Get total users
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    
    # Get new users this week
    one_week_ago = datetime.now() - timedelta(days=7)
    new_users = conn.execute(
        'SELECT COUNT(*) as count FROM users WHERE created_at > ?',
        (one_week_ago,)
    ).fetchone()['count']
    
    # Get total content items
    total_content = conn.execute('SELECT COUNT(*) as count FROM content').fetchone()['count']
    
    # Get new content this month
    one_month_ago = datetime.now() - timedelta(days=30)
    new_content = conn.execute(
        'SELECT COUNT(*) as count FROM content WHERE created_at > ?',
        (one_month_ago,)
    ).fetchone()['count']
    
    # Get daily sessions (placeholder in this version)
    daily_sessions = 125
    activity_change = 8
    
    # Get completion rate (placeholder in this version)
    completion_rate = 72
    completion_change = 3
    
    stats = {
        'total_users': total_users,
        'new_users': new_users,
        'total_content': total_content,
        'new_content': new_content,
        'daily_sessions': daily_sessions,
        'activity_change': activity_change,
        'completion_rate': completion_rate,
        'completion_change': completion_change
    }
    
    # Get recent activity
    recent_activity = conn.execute(
        '''
        SELECT u.username, uil.interaction_type, uil.timestamp,
               CASE 
                   WHEN uil.interaction_type = 'start' THEN 'Started learning content'
                   WHEN uil.interaction_type = 'complete' THEN 'Completed learning content' 
                   WHEN uil.interaction_type = 'assessment' THEN 'Completed assessment'
                   ELSE uil.interaction_type
               END as description
        FROM user_interaction_log uil
        JOIN users u ON uil.user_id = u.id
        ORDER BY uil.timestamp DESC
        LIMIT 10
        '''
    ).fetchall()
    
    # Get users (paginated)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    users = conn.execute(
        '''
        SELECT u.id, u.username, u.email, u.created_at,
               (SELECT MAX(timestamp) FROM user_interaction_log WHERE user_id = u.id) as last_active,
               (SELECT AVG(mastery_level) * 100 FROM user_knowledge_state WHERE user_id = u.id) as progress
        FROM users u
        ORDER BY u.id
        LIMIT ? OFFSET ?
        ''',
        (per_page, offset)
    ).fetchall()
    
    # Convert to list of dicts and format dates
    users_list = []
    for user in users:
        user_dict = dict(user)
        if user_dict['last_active']:
            user_dict['last_active'] = datetime.fromisoformat(user_dict['last_active']).strftime('%Y-%m-%d %H:%M')
        else:
            user_dict['last_active'] = 'Never'
        
        user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at']).strftime('%Y-%m-%d')
        user_dict['progress'] = round(user_dict['progress'] if user_dict['progress'] else 0, 1)
        users_list.append(user_dict)
    
    # Get total users count for pagination
    total_users_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    total_pages = (total_users_count + per_page - 1) // per_page
    
    # Get content items (paginated)
    content_page = request.args.get('content_page', 1, type=int)
    content_offset = (content_page - 1) * per_page
    
    contents = conn.execute(
        '''
        SELECT c.id, c.title, c.content_type, c.difficulty,
               (SELECT GROUP_CONCAT(kc.name, ', ') 
                FROM content_knowledge_map ckm 
                JOIN knowledge_components kc ON ckm.knowledge_component_id = kc.id 
                WHERE ckm.content_id = c.id) as knowledge_components,
               (SELECT COUNT(*) FROM user_interaction_log WHERE content_id = c.id AND interaction_type = 'start') as views
        FROM content c
        ORDER BY c.id
        LIMIT ? OFFSET ?
        ''',
        (per_page, content_offset)
    ).fetchall()
    
    # Convert to list of dicts
    contents_list = [dict(content) for content in contents]
    
    # Get total content count for pagination
    total_content_count = conn.execute('SELECT COUNT(*) as count FROM content').fetchone()['count']
    content_total_pages = (total_content_count + per_page - 1) // per_page
    
    # Get assessment items (paginated)
    assessment_page = request.args.get('assessment_page', 1, type=int)
    assessment_offset = (assessment_page - 1) * per_page
    
    assessment_items = conn.execute(
        '''
        SELECT ai.id, ai.question_text, ai.question_type, ai.difficulty,
               kc.name as knowledge_component,
               (SELECT COUNT(*) FROM user_responses WHERE assessment_item_id = ai.id) as total_attempts,
               (SELECT COUNT(*) FROM user_responses WHERE assessment_item_id = ai.id AND is_correct = 1) as correct_attempts
        FROM assessment_items ai
        JOIN knowledge_components kc ON ai.knowledge_component_id = kc.id
        ORDER BY ai.id
        LIMIT ? OFFSET ?
        ''',
        (per_page, assessment_offset)
    ).fetchall()
    
    # Calculate success rate and convert to list of dicts
    assessment_items_list = []
    for item in assessment_items:
        item_dict = dict(item)
        if item_dict['total_attempts'] > 0:
            item_dict['success_rate'] = round((item_dict['correct_attempts'] / item_dict['total_attempts']) * 100, 1)
        else:
            item_dict['success_rate'] = 0
        assessment_items_list.append(item_dict)
    
    # Get total assessment items count for pagination
    total_assessment_count = conn.execute('SELECT COUNT(*) as count FROM assessment_items').fetchone()['count']
    assessment_total_pages = (total_assessment_count + per_page - 1) // per_page
    
    # Get knowledge components for filter
    knowledge_components = conn.execute(
        'SELECT id, name FROM knowledge_components ORDER BY name'
    ).fetchall()
    
    # Get system settings
    system_settings = {
        'learning_rate': 0.1,
        'recommendation_diversity': 0.3,
        'mastery_threshold': 0.8
    }
    
    # Generate insights (placeholders in this version)
    insights = [
        {
            'type': 'trend',
            'title': 'Rising Engagement',
            'description': 'User session time has increased by 12% in the last week.',
            'metrics': 'Avg. session: 28 minutes'
        },
        {
            'type': 'warning',
            'title': 'Difficult Content Identified',
            'description': 'Division assessment items show a below-average success rate.',
            'metrics': '45% success vs. 72% average'
        },
        {
            'type': 'success',
            'title': 'Effective Learning Path',
            'description': 'Basic Arithmetic path shows high completion rate.',
            'metrics': '85% completion, 25% above average'
        },
        {
            'type': 'trend',
            'title': 'Learning Style Distribution',
            'description': 'Visual learners are the largest group in the system.',
            'metrics': '45% visual, 32% kinesthetic, 23% auditory'
        }
    ]
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                          stats=stats,
                          recent_activity=recent_activity,
                          users=users_list,
                          page=page,
                          total_pages=total_pages,
                          contents=contents_list,
                          content_page=content_page,
                          content_total_pages=content_total_pages,
                          assessment_items=assessment_items_list,
                          assessment_page=assessment_page,
                          assessment_total_pages=assessment_total_pages,
                          knowledge_components=knowledge_components,
                          system_settings=system_settings,
                          insights=insights,
                          username=session['username'])

# Admin API routes
@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    """API endpoint to get users list"""
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # Implementation would fetch users from database with pagination and search
    # This is a placeholder
    
    return jsonify({
        'users': [],
        'page': page,
        'total_pages': 1
    })

@app.route('/api/admin/content', methods=['GET'])
def api_admin_content():
    """API endpoint to get content list"""
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Implementation would fetch content with filters
    # This is a placeholder
    
    return jsonify({
        'content': [],
        'page': 1,
        'total_pages': 1
    })

@app.route('/api/admin/assessment', methods=['GET'])
def api_admin_assessment():
    """API endpoint to get assessment items"""
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Implementation would fetch assessment items with filters
    # This is a placeholder
    
    return jsonify({
        'items': [],
        'page': 1,
        'total_pages': 1
    })

@app.route('/api/admin/analytics', methods=['GET'])
def api_admin_analytics():
    """API endpoint to get analytics data"""
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    date_range = request.args.get('date_range', '30')
    group_by = request.args.get('group_by', 'day')
    
    # Implementation would generate analytics data based on parameters
    # This is a placeholder
    
    return jsonify({
        'engagement_data': {},
        'mastery_data': {},
        'assessment_data': {},
        'effectiveness_data': {}
    })

@app.route('/api/admin/settings', methods=['POST'])
def api_admin_settings():
    """API endpoint to update system settings"""
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Implementation would update system settings in database
    # This is a placeholder
    
    return jsonify({'status': 'success'})


@app.route('/admin/ai-dashboard')
def ai_dashboard():
    """AI System dashboard for administrators"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    # Check if user is admin
    if not is_admin(user_id):
        flash("You don't have permission to access this page.")
        return redirect(url_for('dashboard'))
    
    # Get AI system statistics
    ai_stats = {
        'models_count': 4,  # Number of ML models
        'models_accuracy': 82,  # Average model accuracy
        'predictions_count': 15840,  # Total predictions made
        'predictions_daily_avg': 528,  # Average daily predictions
        'recommendations_count': 42650,  # Total recommendations
        'recommendations_engagement': 78,  # Recommendation engagement rate
        'styles_detected': 325,  # Number of users with detected learning styles
        'style_confidence': 84  # Average confidence in style detection
    }
    
    # Get AI system insights
    ai_insights = [
        {
            'type': 'improvement',
            'title': 'Performance Model Accuracy Improving',
            'description': 'The performance prediction model has improved by 8% in the last month.'
        },
        {
            'type': 'warning',
            'title': 'Content Recommendation Gap',
            'description': 'Visual learners have fewer appropriate content options in the Science domain.'
        },
        {
            'type': 'action',
            'title': 'Training Data Needed',
            'description': 'The engagement model needs more training data for better predictions.'
        }
    ]
    
    # Get models information
    models = {
        'performance_model': {
            'active': True,
            'last_trained': '2025-03-10',
            'training_samples': 845,
            'accuracy': 82
        },
        'engagement_model': {
            'active': True,
            'last_trained': '2025-03-12',
            'training_samples': 912,
            'accuracy': 78
        },
        'learning_style_model': {
            'active': True,
            'last_trained': '2025-03-05',
            'training_samples': 764,
            'accuracy': 76
        },
        'content_recommendation': {
            'active': True,
            'last_trained': '2025-03-15',
            'content_count': 328,
            'effectiveness': 85
        }
    }
    
    # Get high-risk students
    high_risk_students = [
        {
            'user_id': 45,
            'username': 'john_doe',
            'risk_type': 'Disengagement',
            'risk_level': 'high',
            'predicted_value': '87% probability',
            'factors': 'Low activity, poor assessment performance'
        },
        {
            'user_id': 78,
            'username': 'alice_smith',
            'risk_type': 'Performance',
            'risk_level': 'high',
            'predicted_value': '42% expected score',
            'factors': 'Knowledge gaps, short session duration'
        },
        {
            'user_id': 112,
            'username': 'bob_johnson',
            'risk_type': 'Disengagement',
            'risk_level': 'medium',
            'predicted_value': '68% probability',
            'factors': 'Irregular activity pattern'
        }
    ]
    
    # Get recommendation metrics
    recommendation_metrics = {
        'engagement_rate': 78,
        'completion_rate': 65,
        'avg_relevance': 4.2,
        'mastery_improvement': 24
    }
    
    # Get effective content
    effective_content = [
        {
            'title': 'Visual Introduction to Fractions',
            'content_type': 'video',
            'recommendation_count': 245,
            'engagement_rate': 92,
            'completion_rate': 88,
            'mastery_gain': 32
        },
        {
            'title': 'Interactive Algebra Practice',
            'content_type': 'interactive',
            'recommendation_count': 198,
            'engagement_rate': 87,
            'completion_rate': 76,
            'mastery_gain': 28
        },
        {
            'title': 'Geometry Fundamentals',
            'content_type': 'lesson',
            'recommendation_count': 176,
            'engagement_rate': 82,
            'completion_rate': 74,
            'mastery_gain': 26
        }
    ]
    
    # Get learning style statistics
    learning_style_stats = {
        'visual': {
            'percentage': 45,
            'count': 146,
            'avg_performance': 78
        },
        'auditory': {
            'percentage': 23,
            'count': 75,
            'avg_performance': 72
        },
        'kinesthetic': {
            'percentage': 20,
            'count': 65,
            'avg_performance': 74
        },
        'reading_writing': {
            'percentage': 12,
            'count': 39,
            'avg_performance': 76
        }
    }
    
    # Get learning style insights
    learning_style_insights = [
        {
            'title': 'Visual Learners Dominate',
            'description': 'Visual learners make up the largest group and show highest engagement with video content.',
            'stats': '45% of users, 78% avg. performance'
        },
        {
            'title': 'Content Type Effectiveness',
            'description': 'Interactive content is most effective across all learning styles.',
            'stats': '+28% average mastery improvement'
        },
        {
            'title': 'Learning Style Shifts',
            'description': 'Users often shift learning preferences as they advance in a subject.',
            'stats': '18% of users changed primary style'
        }
    ]
    
    return render_template('admin/ai_dashboard.html',
                          ai_stats=ai_stats,
                          ai_insights=ai_insights,
                          models=models,
                          high_risk_students=high_risk_students,
                          recommendation_metrics=recommendation_metrics,
                          effective_content=effective_content,
                          learning_style_stats=learning_style_stats,
                          learning_style_insights=learning_style_insights,
                          username=session['username'])


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Check if database exists, if not initialize it
    if not os.path.exists('database/adaptive_learning.db'):
        from database.init_db import init_db
        init_db()

    # Start the Flask app
    app.run(debug=True)