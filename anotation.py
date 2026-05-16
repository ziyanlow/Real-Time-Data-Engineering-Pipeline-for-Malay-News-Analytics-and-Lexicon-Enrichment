import malaya
import pymongo
from bson import ObjectId
import nltk
from nltk.wsd import lesk

# Download WordNet data (if not already downloaded)
nltk.download('wordnet')
nltk.download('omw-1.4')


# MongoDB Connection Class
class MongoConnector:
    def __init__(self, uri, db_name, collection_name):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def get_document_by_id(self, target_object_id):
        """Retrieve a document from MongoDB by its ObjectId"""
        document = self.collection.find_one({"_id": target_object_id})
        if not document:
            raise ValueError(f"No document found with Object ID {target_object_id}")
        return document

    def update_document(self, target_object_id, updated_data):
        """Update the document with new data"""
        self.collection.update_one({"_id": target_object_id}, {"$set": updated_data})


# Malaya Models Class
class MalayaModels:
    def __init__(self):
        self.sentiment_model = malaya.sentiment.huggingface()
        self.pos_model = malaya.pos.huggingface()
        
    def predict_sentiment(self, text):
        return self.sentiment_model.predict([text])[0]
    
    def predict_pos(self, text):
        pos_tags = self.pos_model.predict(text)
        return pos_tags[0][1] if pos_tags else "Unknown"


# Word Sense Disambiguation Class
class WordSenseDisambiguation:
    @staticmethod
    def disambiguate(word):
        """Disambiguates the word using NLTK's Lesk Algorithm."""
        synsets = lesk([word], word)
        if synsets:
            return synsets.name()  # Return the name of the best sense
        return "Unknown"  # Return 'Unknown' if no sense is found


# Annotator Class
class Annotator:
    def __init__(self):
        self.malaya_models = MalayaModels()
        self.ws_disambiguation = WordSenseDisambiguation()
    
    def annotate_word(self, word):
        try:
            word_str = str(word)
            
            # Predict sentiment
            sentiment = self.malaya_models.predict_sentiment(word_str)
            
            # Predict POS
            pos_tag = self.malaya_models.predict_pos(word_str)
            
            # Word Sense Disambiguation prediction
            word_sense = self.ws_disambiguation.disambiguate(word_str)
            
            return {"word": word_str, "sentiment": sentiment, "pos": pos_tag, "word_sense": word_sense}
        
        except Exception as e:
            return {"word": word, "sentiment": "Error", "pos": "Error", "word_sense": "Error"}


# Main Annotation Process Class
class AnnotationProcess:
    def __init__(self, mongo_uri, db_name, collection_name, object_id):
        self.mongo_connector = MongoConnector(mongo_uri, db_name, collection_name)
        self.annotator = Annotator()
        self.target_object_id = ObjectId(object_id)

    def get_tokens(self):
        """Retrieve the tokens from MongoDB"""
        document = self.mongo_connector.get_document_by_id(self.target_object_id)
        return document.get("tokens", [])

    def annotate_tokens(self, tokens_array):
        """Annotate each token with sentiment, POS, and word sense"""
        annotated_data = []
        for token in tokens_array:
            annotation = self.annotator.annotate_word(token)
            annotated_data.append(annotation)
        return annotated_data

    def update_document(self, annotated_data):
        """Update the MongoDB document with annotated data"""
        self.mongo_connector.update_document(self.target_object_id, {"tokens": annotated_data})

    def run(self):
        """Run the annotation process"""
        tokens_array = self.get_tokens()
        annotated_data = self.annotate_tokens(tokens_array)
        self.update_document(annotated_data)
        print("Annotation completed including sentiment, POS tagging, and word sense disambiguation. Data updated in MongoDB.")
