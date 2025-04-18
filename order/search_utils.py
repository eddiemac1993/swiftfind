from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Item
import pickle
import os

class SemanticSearch:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,  # Limit memory usage
            ngram_range=(1, 2)   # Consider 1-word and 2-word phrases
        )
        self.matrix = None
        self.item_ids = []
    
    def generate_embeddings(self):
        """Generate and save TF-IDF embeddings for all items"""
        items = Item.objects.all().only('id', 'name', 'description', 'category__name')
        
        # Combine relevant text fields
        texts = [
            f"{item.name} {item.description} {item.category.name}"
            for item in items
        ]
        self.item_ids = [item.id for item in items]
        
        # Create TF-IDF matrix
        self.matrix = self.vectorizer.fit_transform(texts)
        
        # Save to disk
        with open('search_embeddings.pkl', 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'matrix': self.matrix,
                'item_ids': self.item_ids
            }, f)
    
    def load_embeddings(self):
        """Load pre-generated embeddings or create new ones"""
        if os.path.exists('search_embeddings.pkl'):
            with open('search_embeddings.pkl', 'rb') as f:
                data = pickle.load(f)
                self.vectorizer = data['vectorizer']
                self.matrix = data['matrix']
                self.item_ids = data['item_ids']
        else:
            self.generate_embeddings()
    
    def search(self, query, threshold=0.25, top_n=5):
        """Perform semantic search"""
        self.load_embeddings()
        
        # Transform query to TF-IDF vector
        query_vec = self.vectorizer.transform([query])
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_vec, self.matrix).flatten()
        
        # Get top results
        results = sorted(zip(self.item_ids, similarities), 
                      key=lambda x: x[1], 
                      reverse=True)
        
        # Apply threshold and limit
        filtered = [r for r in results if r[1] >= threshold][:top_n]
        
        # Retrieve full item objects
        items = Item.objects.filter(id__in=[item_id for item_id, _ in filtered])
        item_map = {item.id: item for item in items}
        
        return [(item_map[item_id], score) 
               for item_id, score in filtered 
               if item_id in item_map]

# Global search instance
search_engine = SemanticSearch()