import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db_schema():
    """Update the database schema to add support for adapted content"""
    # Connect to the database
    db_path = 'database/adaptive_learning.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database {db_path} does not exist! Please run init_db.py first.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Updating database schema...")
        
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='adapted_content'")
        adapted_content_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_failures'")
        assessment_failures_exists = cursor.fetchone() is not None
        
        # Create the adapted_content table if it doesn't exist
        if not adapted_content_exists:
            cursor.execute('''
            CREATE TABLE adapted_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_content_id INTEGER NOT NULL,
                adapted_content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (original_content_id) REFERENCES content (id)
            )
            ''')
            logger.info("Created adapted_content table")
        else:
            logger.info("adapted_content table already exists")
        
        # Add some new fields to track student failures in the assessment results
        if not assessment_failures_exists:
            cursor.execute('''
            CREATE TABLE assessment_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_id INTEGER NOT NULL,
                failure_count INTEGER NOT NULL DEFAULT 1,
                last_score REAL NOT NULL,
                last_attempt_at TIMESTAMP NOT NULL,
                adaptation_provided BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (content_id) REFERENCES content (id)
            )
            ''')
            logger.info("Created assessment_failures table")
        else:
            logger.info("assessment_failures table already exists")
        
        # Commit the changes
        conn.commit()
        
        # Verify that tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='adapted_content'")
        if not cursor.fetchone():
            logger.error("Failed to create adapted_content table!")
            return False
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_failures'")
        if not cursor.fetchone():
            logger.error("Failed to create assessment_failures table!")
            return False
        
        logger.info("Database schema update complete!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    update_db_schema()