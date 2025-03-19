import numpy as np
import sqlite3
import logging
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Make sure NLTK resources are downloaded
try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')

logger = logging.getLogger(__name__)

class ContentRecommendation:
    """
    Provides enhanced content recommendations using NLP techniques 
    to better match content with student needs and interests.
    """
    
    def __init__(self, db_path='database/adaptive_learning.db'):
        """Initialize with database path"""
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.content_vectors = None
        self.content_ids = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def preprocess_text(self, text):
        """Preprocess text for NLP analysis"""
        if not text:
            return ""
        # Tokenize
        tokens = word_tokenize(text.lower())
        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token) for token in tokens 
            if token.isalpha() and token not in self.stop_words
        ]
        return " ".join(processed_tokens)
    
    def build_content_vectors(self):
        """Build TF-IDF vectors for all content items"""
        conn = self.get_db_connection()
        
        # Get all content
        contents = conn.execute('''
            SELECT id, title, description, content_data, tags
            FROM content
        ''').fetchall()
        
        content_texts = []
        self.content_ids = []
        
        for content in contents:
            # Combine all textual information about the content
            content_text = f"{content['title']} {content['description']} "
            
            # Extract text from content_data (JSON)
            content_data = json.loads(content['content_data'])
            for section in content_data.get('sections', []):
                section_text = section.get('content', '')
                content_text += section_text + " "
            
            # Add tags
            if content['tags']:
                content_text += content['tags'] + " "
            
            # Preprocess text
            processed_text = self.preprocess_text(content_text)
            content_texts.append(processed_text)
            self.content_ids.append(content['id'])
        
        conn.close()
        
        # Build vectors
        self.content_vectors = self.vectorizer.fit_transform(content_texts)
        
        logger.info(f"Built content vectors for {len(self.content_ids)} content items")
        
        return self.content_vectors
    
    def get_content_similarity(self, content_id):
        """Calculate similarity between a content item and all others"""
        if self.content_vectors is None:
            self.build_content_vectors()
        
        # Find index of the content
        try:
            content_index = self.content_ids.index(content_id)
        except ValueError:
            logger.error(f"Content ID {content_id} not found in vector database")
            return []
        
        # Get content vector
        content_vector = self.content_vectors[content_index]
        
        # Calculate similarities
        similarities = cosine_similarity(content_vector, self.content_vectors).flatten()
        
        # Create list of (content_id, similarity) tuples
        content_similarities = [
            (self.content_ids[i], float(similarities[i]))
            for i in range(len(self.content_ids))
            if i != content_index  # Exclude the content itself
        ]
        
        # Sort by similarity (descending)
        content_similarities.sort(key=lambda x: x[1], reverse=True)
        
        return content_similarities
    
    def get_user_interests(self, user_id):
        """Extract user interests based on interaction history"""
        conn = self.get_db_connection()
        
        # Get recent content interactions
        interactions = conn.execute('''
            SELECT content_id, interaction_type, 
                   COUNT(*) as interaction_count
            FROM user_interaction_log
            WHERE user_id = ? AND content_id IS NOT NULL
            GROUP BY content_id, interaction_type
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        # Calculate interest scores for each content
        content_interest = {}
        
        for interaction in interactions:
            content_id = interaction['content_id']
            interaction_type = interaction['interaction_type']
            count = interaction['interaction_count']
            
            # Weight different interaction types
            weight = 1.0
            if interaction_type == 'complete':
                weight = 3.0
            elif interaction_type == 'start':
                weight = 1.5
            elif interaction_type == 'like' or interaction_type == 'bookmark':
                weight = 4.0
            
            if content_id not in content_interest:
                content_interest[content_id] = 0
            
            content_interest[content_id] += count * weight
        
        return content_interest
    
    def get_user_content_vector(self, user_id):
        """Create a vector representation of user interests"""
        if self.content_vectors is None:
            self.build_content_vectors()
        
        # Get user interests
        content_interest = self.get_user_interests(user_id)
        
        if not content_interest:
            return None
        
        # Calculate weighted average of content vectors
        total_weight = sum(content_interest.values())
        user_vector = np.zeros(self.content_vectors.shape[1])
        
        for content_id, weight in content_interest.items():
            try:
                idx = self.content_ids.index(content_id)
                content_vector = self.content_vectors[idx].toarray().flatten()
                user_vector += (weight / total_weight) * content_vector
            except ValueError:
                # Content not found in vectors
                continue
        
        return user_vector.reshape(1, -1)
    
    def recommend_similar_content(self, content_id, limit=5):
        """Recommend content similar to a given content item"""
        similarities = self.get_content_similarity(content_id)
        
        # Get top similar content
        top_similar = similarities[:limit]
        
        # Get content details
        conn = self.get_db_connection()
        
        recommended_content = []
        for similar_id, similarity in top_similar:
            content = conn.execute('''
                SELECT id, title, description, content_type, difficulty, tags
                FROM content
                WHERE id = ?
            ''', (similar_id,)).fetchone()
            
            if content:
                recommended_content.append({
                    'content_id': content['id'],
                    'title': content['title'],
                    'description': content['description'],
                    'content_type': content['content_type'],
                    'difficulty': content['difficulty'],
                    'tags': content['tags'].split(',') if content['tags'] else [],
                    'similarity_score': similarity,
                    'recommendation_type': 'content_similarity'
                })
        
        conn.close()
        
        return recommended_content
    
    def recommend_for_user_interests(self, user_id, limit=5):
        """Recommend content based on user interests"""
        user_vector = self.get_user_content_vector(user_id)
        
        if user_vector is None or self.content_vectors is None:
            return []
        
        # Calculate similarities to all content
        similarities = cosine_similarity(user_vector, self.content_vectors).flatten()
        
        # Create list of (content_id, similarity) tuples
        content_similarities = [
            (self.content_ids[i], float(similarities[i]))
            for i in range(len(self.content_ids))
        ]
        
        # Sort by similarity (descending)
        content_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get content details
        conn = self.get_db_connection()
        
        # Get already viewed content
        viewed_content = conn.execute('''
            SELECT DISTINCT content_id
            FROM user_interaction_log
            WHERE user_id = ? AND content_id IS NOT NULL
        ''', (user_id,)).fetchall()
        
        viewed_ids = {vc['content_id'] for vc in viewed_content}
        
        recommended_content = []
        for similar_id, similarity in content_similarities:
            # Skip already viewed content
            if similar_id in viewed_ids:
                continue
                
            content = conn.execute('''
                SELECT id, title, description, content_type, difficulty, tags
                FROM content
                WHERE id = ?
            ''', (similar_id,)).fetchone()
            
            if content:
                recommended_content.append({
                    'content_id': content['id'],
                    'title': content['title'],
                    'description': content['description'],
                    'content_type': content['content_type'],
                    'difficulty': content['difficulty'],
                    'tags': content['tags'].split(',') if content['tags'] else [],
                    'similarity_score': similarity,
                    'recommendation_type': 'interest_based'
                })
                
                if len(recommended_content) >= limit:
                    break
        
        conn.close()
        
        return recommended_content
    
    def recommend_for_knowledge_gaps(self, user_id, limit=5):
        """Recommend content to address knowledge gaps"""
        conn = self.get_db_connection()
        
        # Get knowledge components with low mastery
        knowledge_gaps = conn.execute('''
            SELECT knowledge_component_id, mastery_level
            FROM user_knowledge_state
            WHERE user_id = ? AND mastery_level < 0.6
            ORDER BY mastery_level ASC
        ''', (user_id,)).fetchall()
        
        if not knowledge_gaps:
            conn.close()
            return []
        
        # Get content for these knowledge components
        recommended_content = []
        
        for gap in knowledge_gaps:
            kc_id = gap['knowledge_component_id']
            mastery = gap['mastery_level']
            
            # Get content targeting this knowledge component
            content_items = conn.execute('''
                SELECT c.id, c.title, c.description, c.content_type, c.difficulty, c.tags,
                       ckm.relevance_weight
                FROM content c
                JOIN content_knowledge_map ckm ON c.id = ckm.content_id
                WHERE ckm.knowledge_component_id = ?
                ORDER BY ckm.relevance_weight DESC, c.difficulty ASC
                LIMIT 2
            ''', (kc_id,)).fetchall()
            
            for content in content_items:
                # Check if this content is already in recommendations
                if any(r['content_id'] == content['id'] for r in recommended_content):
                    continue
                    
                recommended_content.append({
                    'content_id': content['id'],
                    'title': content['title'],
                    'description': content['description'],
                    'content_type': content['content_type'],
                    'difficulty': content['difficulty'],
                    'tags': content['tags'].split(',') if content['tags'] else [],
                    'relevance_weight': content['relevance_weight'],
                    'mastery_gap': 1.0 - mastery,
                    'recommendation_type': 'knowledge_gap'
                })
                
                if len(recommended_content) >= limit:
                    break
            
            if len(recommended_content) >= limit:
                break
        
        conn.close()
        
        return recommended_content
    
    def get_diverse_recommendations(self, user_id, limit=5):
        """Get a diverse set of content recommendations"""
        # Get recommendations from different sources
        interest_recs = self.recommend_for_user_interests(user_id, limit=3)
        gap_recs = self.recommend_for_knowledge_gaps(user_id, limit=3)
        
        # Get a recently viewed content for similarity recommendations
        conn = self.get_db_connection()
        recent_content = conn.execute('''
            SELECT content_id
            FROM user_interaction_log
            WHERE user_id = ? AND content_id IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (user_id,)).fetchone()
        conn.close()
        
        similarity_recs = []
        if recent_content:
            similarity_recs = self.recommend_similar_content(recent_content['content_id'], limit=2)
        
        # Combine and deduplicate recommendations
        all_recs = []
        content_ids = set()
        
        # First add knowledge gap recommendations (highest priority)
        for rec in gap_recs:
            if rec['content_id'] not in content_ids:
                content_ids.add(rec['content_id'])
                all_recs.append(rec)
        
        # Then add interest-based recommendations
        for rec in interest_recs:
            if rec['content_id'] not in content_ids:
                content_ids.add(rec['content_id'])
                all_recs.append(rec)
        
        # Finally add similarity recommendations
        for rec in similarity_recs:
            if rec['content_id'] not in content_ids:
                content_ids.add(rec['content_id'])
                all_recs.append(rec)
        
        # Return limited number of recommendations
        return all_recs[:limit]