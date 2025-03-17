import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class ContentModule:
    """
    Manages the learning content, including retrieval, organization, and metadata.
    Responsible for serving the right format of content based on learning style.
    """
    
    def __init__(self):
        """Initialize ContentModule with database connection"""
        self.db_path = 'database/adaptive_learning.db'
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_content(self, content_id):
        """Get content by ID with all metadata and formatted for display"""
        conn = self.get_db_connection()
        
        # Get content data
        content = conn.execute(
            '''
            SELECT id, title, description, content_type, difficulty, tags, prerequisites, content_data
            FROM content
            WHERE id = ?
            ''',
            (content_id,)
        ).fetchone()
        
        if not content:
            conn.close()
            return None
        
        # Get knowledge components related to this content
        knowledge_components = conn.execute(
            '''
            SELECT kc.id, kc.name, kc.description, ckm.relevance_weight
            FROM content_knowledge_map ckm
            JOIN knowledge_components kc ON ckm.knowledge_component_id = kc.id
            WHERE ckm.content_id = ?
            ''',
            (content_id,)
        ).fetchall()
        
        # Get related assessment items
        assessment_items = conn.execute(
            '''
            SELECT COUNT(ai.id) as assessment_count
            FROM assessment_items ai
            JOIN content_knowledge_map ckm ON ai.knowledge_component_id = ckm.knowledge_component_id
            WHERE ckm.content_id = ?
            ''',
            (content_id,)
        ).fetchone()
        
        conn.close()
        
        # Parse content data
        content_data = json.loads(content['content_data'])
        
        # Parse tags and prerequisites
        tags = content['tags'].split(',') if content['tags'] else []
        prerequisites = content['prerequisites'].split(',') if content['prerequisites'] else []
        
        # Build the full content object
        content_obj = {
            'id': content['id'],
            'title': content['title'],
            'description': content['description'],
            'content_type': content['content_type'],
            'difficulty': content['difficulty'],
            'tags': tags,
            'prerequisites': prerequisites,
            'knowledge_components': [dict(kc) for kc in knowledge_components],
            'has_assessment': assessment_items['assessment_count'] > 0,
            'content_data': content_data
        }
        
        return content_obj
    
    def get_content_list(self, filters=None):
        """Get a list of content items, optionally filtered"""
        conn = self.get_db_connection()
        
        query = '''
        SELECT id, title, description, content_type, difficulty, tags
        FROM content
        '''
        
        params = []
        
        # Apply filters if provided
        if filters:
            where_clauses = []
            
            if 'content_type' in filters:
                where_clauses.append('content_type = ?')
                params.append(filters['content_type'])
            
            if 'difficulty' in filters:
                where_clauses.append('difficulty = ?')
                params.append(filters['difficulty'])
            
            if 'tag' in filters:
                where_clauses.append('tags LIKE ?')
                params.append(f'%{filters["tag"]}%')
            
            if 'knowledge_component' in filters:
                query = '''
                SELECT c.id, c.title, c.description, c.content_type, c.difficulty, c.tags
                FROM content c
                JOIN content_knowledge_map ckm ON c.id = ckm.content_id
                WHERE ckm.knowledge_component_id = ?
                '''
                params = [filters['knowledge_component']]
            
            if where_clauses and 'knowledge_component' not in filters:
                query += ' WHERE ' + ' AND '.join(where_clauses)
        
        # Execute the query
        content_list = conn.execute(query, params).fetchall()
        
        conn.close()
        
        # Format the results
        result = []
        for content in content_list:
            tags = content['tags'].split(',') if content['tags'] else []
            
            result.append({
                'id': content['id'],
                'title': content['title'],
                'description': content['description'],
                'content_type': content['content_type'],
                'difficulty': content['difficulty'],
                'tags': tags
            })
        
        return result
    
    def get_prerequisites(self, content_id):
        """Get prerequisite content items for a given content ID"""
        conn = self.get_db_connection()
        
        # Get the content to check prerequisites
        content = conn.execute(
            'SELECT prerequisites FROM content WHERE id = ?',
            (content_id,)
        ).fetchone()
        
        if not content or not content['prerequisites']:
            conn.close()
            return []
        
        # Parse prerequisites and get their details
        prerequisite_ids = content['prerequisites'].split(',')
        
        # Get prerequisite content details
        prereq_content = []
        for prereq_id in prerequisite_ids:
            if not prereq_id.strip():
                continue
                
            content = conn.execute(
                '''
                SELECT id, title, description, content_type, difficulty
                FROM content
                WHERE id = ?
                ''',
                (prereq_id,)
            ).fetchone()
            
            if content:
                prereq_content.append(dict(content))
        
        conn.close()
        return prereq_content
    
    def format_content_for_style(self, content, learning_style):
        """
        Format content based on the user's learning style
        Adjusts the presentation and emphasizes different aspects based on style
        """
        if not content or not learning_style:
            return content
        
        # Clone the content to avoid modifying the original
        formatted_content = dict(content)
        
        # Get the content data
        content_data = formatted_content.get('content_data', {})
        
        # Adjust based on learning style
        if learning_style['style'] == 'visual':
            # Emphasize visual elements, diagrams, and illustrations
            # Reorder sections to prioritize visual content
            if 'sections' in content_data:
                # Move sections with media to the top
                sections = content_data['sections']
                visual_sections = [s for s in sections if s.get('media_url')]
                text_sections = [s for s in sections if not s.get('media_url')]
                content_data['sections'] = visual_sections + text_sections
        
        elif learning_style['style'] == 'auditory':
            # Emphasize explanations, discussions, and audio elements
            # Add note about reading aloud or discussing the content
            if 'sections' in content_data:
                for section in content_data['sections']:
                    if 'learning_tips' not in section:
                        section['learning_tips'] = []
                    section['learning_tips'].append(
                        "Try reading this section aloud or discussing it with someone to enhance understanding."
                    )
        
        elif learning_style['style'] == 'kinesthetic':
            # Emphasize interactive elements, examples, and practice exercises
            # Prioritize sections with exercises or activities
            if 'sections' in content_data:
                for section in content_data['sections']:
                    if 'learning_tips' not in section:
                        section['learning_tips'] = []
                    section['learning_tips'].append(
                        "Try applying this concept with hands-on practice or create your own examples."
                    )
        
        formatted_content['content_data'] = content_data
        return formatted_content
    
    def get_next_content(self, user_id, learning_path_id=None):
        """Get the next content item in the user's learning path"""
        conn = self.get_db_connection()
        
        if not learning_path_id:
            # Get the user's current learning path
            user_path = conn.execute(
                '''
                SELECT learning_path_id, current_position
                FROM user_learning_paths
                WHERE user_id = ? AND completed = 0
                ORDER BY started_at DESC
                LIMIT 1
                ''',
                (user_id,)
            ).fetchone()
            
            if not user_path:
                conn.close()
                return None
                
            learning_path_id = user_path['learning_path_id']
            current_position = user_path['current_position']
        else:
            # Get the user's position in the specified learning path
            user_path = conn.execute(
                '''
                SELECT current_position
                FROM user_learning_paths
                WHERE user_id = ? AND learning_path_id = ?
                ''',
                (user_id, learning_path_id)
            ).fetchone()
            
            if not user_path:
                # User hasn't started this path yet, initialize at position 0
                current_position = 0
            else:
                current_position = user_path['current_position']
        
        # Get the next content in the path
        next_item = conn.execute(
            '''
            SELECT lpi.content_id, c.title, c.description
            FROM learning_path_items lpi
            JOIN content c ON lpi.content_id = c.id
            WHERE lpi.learning_path_id = ? AND lpi.sequence_order > ?
            ORDER BY lpi.sequence_order
            LIMIT 1
            ''',
            (learning_path_id, current_position)
        ).fetchone()
        
        conn.close()
        
        if next_item:
            return dict(next_item)
        else:
            return None