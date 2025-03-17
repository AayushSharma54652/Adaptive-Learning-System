import sqlite3
import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with schema and sample data"""
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    # Connect to database (will create if not exists)
    conn = sqlite3.connect('database/adaptive_learning.db')
    cursor = conn.cursor()
    
    logger.info("Creating database schema...")
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create content table for learning materials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        content_type TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        tags TEXT,
        prerequisites TEXT,
        content_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create knowledge_components table (concepts/skills to be learned)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        domain TEXT NOT NULL
    )
    ''')
    
    # Create content_knowledge_map to map content to knowledge components
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_knowledge_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER NOT NULL,
        knowledge_component_id INTEGER NOT NULL,
        relevance_weight REAL NOT NULL,
        FOREIGN KEY (content_id) REFERENCES content (id),
        FOREIGN KEY (knowledge_component_id) REFERENCES knowledge_components (id)
    )
    ''')
    
    # Create user_knowledge_state to track user mastery of components
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_knowledge_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        knowledge_component_id INTEGER NOT NULL,
        mastery_level REAL NOT NULL DEFAULT 0.0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (knowledge_component_id) REFERENCES knowledge_components (id)
    )
    ''')
    
    # Create assessment_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessment_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL,
        options TEXT,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        difficulty REAL NOT NULL,
        knowledge_component_id INTEGER NOT NULL,
        FOREIGN KEY (knowledge_component_id) REFERENCES knowledge_components (id)
    )
    ''')
    
    # Create user_responses table to track assessment responses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        assessment_item_id INTEGER NOT NULL,
        user_response TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL,
        response_time_seconds REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (assessment_item_id) REFERENCES assessment_items (id)
    )
    ''')
    
    # Create user_interaction_log to track all user interactions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_interaction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_id INTEGER,
        interaction_type TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        details TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (content_id) REFERENCES content (id)
    )
    ''')
    
    # Create learning_paths table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create learning_path_items to define sequence of content in paths
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_path_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        learning_path_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        sequence_order INTEGER NOT NULL,
        FOREIGN KEY (learning_path_id) REFERENCES learning_paths (id),
        FOREIGN KEY (content_id) REFERENCES content (id)
    )
    ''')
    
    # Create user_learning_paths to track user progress through paths
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_learning_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        learning_path_id INTEGER NOT NULL,
        current_position INTEGER NOT NULL DEFAULT 0,
        completed BOOLEAN NOT NULL DEFAULT 0,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (learning_path_id) REFERENCES learning_paths (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        learning_style TEXT,
        difficulty_preference INTEGER DEFAULT 3,
        learning_pace TEXT DEFAULT 'normal',
        email_notifications BOOLEAN DEFAULT 1,
        notify_progress BOOLEAN DEFAULT 1,
        notify_recommendations BOOLEAN DEFAULT 1,
        notify_reminders BOOLEAN DEFAULT 1,
        text_size TEXT DEFAULT 'medium',
        high_contrast BOOLEAN DEFAULT 0,
        share_progress BOOLEAN DEFAULT 0,
        data_collection BOOLEAN DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Commit schema changes
    conn.commit()
    
    # Insert sample data
    insert_sample_data(conn)
    
    # Close connection
    conn.close()
    logger.info("Database initialization complete!")

def insert_sample_data(conn):
    """Insert sample data into the database"""
    cursor = conn.cursor()
    
    # Insert sample knowledge components (math domain)
    knowledge_components = [
        ('Addition', 'Basic addition of numbers', 'Mathematics'),
        ('Subtraction', 'Basic subtraction of numbers', 'Mathematics'),
        ('Multiplication', 'Basic multiplication of numbers', 'Mathematics'),
        ('Division', 'Basic division of numbers', 'Mathematics'),
        ('Fractions', 'Understanding and working with fractions', 'Mathematics'),
        ('Decimals', 'Understanding and working with decimals', 'Mathematics'),
        ('Percentages', 'Understanding and calculating percentages', 'Mathematics'),
        ('Basic Algebra', 'Solving simple algebraic equations', 'Mathematics')
    ]
    
    logger.info("Inserting sample knowledge components...")
    cursor.executemany('''
    INSERT INTO knowledge_components (name, description, domain) VALUES (?, ?, ?)
    ''', knowledge_components)
    
    # Insert sample content
    sample_contents = [
        (
            'Introduction to Addition', 
            'Learn the basics of addition', 
            'lesson', 
            1, 
            'math,basics,addition', 
            '', 
            json.dumps({
                'sections': [
                    {
                        'title': 'What is Addition?',
                        'content': 'Addition is the process of combining two or more numbers together to find their sum.',
                        'media_url': None
                    },
                    {
                        'title': 'Addition Symbol',
                        'content': 'The plus sign (+) indicates addition.',
                        'media_url': None
                    },
                    {
                        'title': 'Examples',
                        'content': '1 + 1 = 2\n2 + 3 = 5\n4 + 5 = 9',
                        'media_url': None
                    }
                ]
            })
        ),
        (
            'Basic Subtraction', 
            'Learn the fundamentals of subtraction', 
            'lesson', 
            1, 
            'math,basics,subtraction', 
            '1', 
            json.dumps({
                'sections': [
                    {
                        'title': 'What is Subtraction?',
                        'content': 'Subtraction is the process of taking one number away from another.',
                        'media_url': None
                    },
                    {
                        'title': 'Subtraction Symbol',
                        'content': 'The minus sign (-) indicates subtraction.',
                        'media_url': None
                    },
                    {
                        'title': 'Examples',
                        'content': '5 - 3 = 2\n10 - 4 = 6\n7 - 7 = 0',
                        'media_url': None
                    }
                ]
            })
        ),
        (
            'Multiplication Basics', 
            'Learn how to multiply numbers', 
            'lesson', 
            2, 
            'math,basics,multiplication', 
            '1,2', 
            json.dumps({
                'sections': [
                    {
                        'title': 'What is Multiplication?',
                        'content': 'Multiplication is a way of adding a number to itself multiple times.',
                        'media_url': None
                    },
                    {
                        'title': 'Multiplication Symbol',
                        'content': 'The multiplication sign (×) or asterisk (*) indicates multiplication.',
                        'media_url': None
                    },
                    {
                        'title': 'Examples',
                        'content': '2 × 3 = 6\n4 × 5 = 20\n7 × 7 = 49',
                        'media_url': None
                    }
                ]
            })
        ),
        (
            'Division Fundamentals', 
            'Learn the basics of division', 
            'lesson', 
            2, 
            'math,basics,division', 
            '1,2,3', 
            json.dumps({
                'sections': [
                    {
                        'title': 'What is Division?',
                        'content': 'Division is the process of splitting a number into equal parts.',
                        'media_url': None
                    },
                    {
                        'title': 'Division Symbol',
                        'content': 'The division sign (÷) or forward slash (/) indicates division.',
                        'media_url': None
                    },
                    {
                        'title': 'Examples',
                        'content': '6 ÷ 3 = 2\n10 ÷ 2 = 5\n9 ÷ 3 = 3',
                        'media_url': None
                    }
                ]
            })
        )
    ]
    
    logger.info("Inserting sample content...")
    cursor.executemany('''
    INSERT INTO content (title, description, content_type, difficulty, tags, prerequisites, content_data)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_contents)
    
    # Map content to knowledge components
    content_knowledge_mappings = [
        (1, 1, 1.0),  # Addition content to Addition KC
        (2, 2, 1.0),  # Subtraction content to Subtraction KC
        (3, 3, 1.0),  # Multiplication content to Multiplication KC
        (4, 4, 1.0),  # Division content to Division KC
    ]
    
    logger.info("Creating content to knowledge component mappings...")
    cursor.executemany('''
    INSERT INTO content_knowledge_map (content_id, knowledge_component_id, relevance_weight)
    VALUES (?, ?, ?)
    ''', content_knowledge_mappings)
    
    # Insert sample assessment items
    assessment_items = [
        ('What is 2 + 3?', 'multiple_choice', json.dumps(['4', '5', '6', '7']), '5', 'The sum of 2 and 3 is 5.', 1.0, 1),
        ('What is 7 - 4?', 'multiple_choice', json.dumps(['2', '3', '4', '5']), '3', 'When you subtract 4 from 7, you get 3.', 1.0, 2),
        ('What is 3 × 6?', 'multiple_choice', json.dumps(['12', '15', '18', '21']), '18', '3 multiplied by 6 equals 18.', 1.5, 3),
        ('What is 8 ÷ 2?', 'multiple_choice', json.dumps(['2', '3', '4', '5']), '4', '8 divided by 2 equals 4.', 1.5, 4)
    ]
    
    logger.info("Inserting sample assessment items...")
    cursor.executemany('''
    INSERT INTO assessment_items (question_text, question_type, options, correct_answer, explanation, difficulty, knowledge_component_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', assessment_items)
    
    # Create a sample learning path
    cursor.execute('''
    INSERT INTO learning_paths (name, description)
    VALUES (?, ?)
    ''', ('Basic Arithmetic', 'A path to learn the fundamentals of arithmetic operations'))
    
    learning_path_id = cursor.lastrowid
    
    # Add content to the learning path
    learning_path_items = [
        (learning_path_id, 1, 1),  # Addition first
        (learning_path_id, 2, 2),  # Subtraction second
        (learning_path_id, 3, 3),  # Multiplication third
        (learning_path_id, 4, 4)   # Division fourth
    ]
    
    logger.info("Creating sample learning path...")
    cursor.executemany('''
    INSERT INTO learning_path_items (learning_path_id, content_id, sequence_order)
    VALUES (?, ?, ?)
    ''', learning_path_items)
    
    # Commit all sample data
    conn.commit()
    logger.info("Sample data inserted successfully!")

if __name__ == '__main__':
    init_db()