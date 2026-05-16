# neo4j_processor.py
from googletrans import Translator
import nltk
import spacy
import pandas as pd
from py2neo import Graph
from neo4j import GraphDatabase  # Import the missing GraphDatabase class
from nltk import pos_tag, word_tokenize

# neo4j_processor.py
# neo4j_processor.py
class Neo4jProcessor:
    def __init__(self, neo4j_uri, neo4j_username, neo4j_password):
        # Neo4j connection details
        self.URI = neo4j_uri
        self.USERNAME = neo4j_username
        self.PASSWORD = neo4j_password

        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.URI, auth=(self.USERNAME, self.PASSWORD))

        # Initialize the translator
        self.translator = Translator()

        # Load spaCy model for POS tagging
        self.nlp = spacy.load("en_core_web_sm")

        # Download NLTK resources for POS tagging
        nltk.download('averaged_perceptron_tagger')
        nltk.download('punkt')

        # Neo4j connection for graph querying
        self.graph = Graph(self.URI, auth=(self.USERNAME, self.PASSWORD))

    # Function to fetch words where part_of_speech is NOT NULL
    def fetch_words_with_pos(self):
        query = """
        MATCH (w:Word)
        WHERE w.part_of_speech IS NOT NULL AND NOT w.part_of_speech CONTAINS "NaN"
        RETURN w.name AS word
        LIMIT 100
        """
        with self.driver.session() as session:
            # Run the query and fetch results
            result = session.read_transaction(lambda tx: list(tx.run(query)))
            
            # Consume the result inside the transaction scope and return the words
            word_list = [record["word"] for record in result]  # This ensures that we consume the result before the session closes
            
        return word_list


    # Function to translate words to English
    def translate_words(self, words):
        translations = []
        for word in words:
            try:
                translated = self.translator.translate(word, src="ms", dest="en").text
                translations.append({"Word": word, "Translated Word": translated})
            except Exception as e:
                print(f"Error translating word '{word}': {e}")
                translations.append({"Word": word, "Translated Word": None})
        return translations

    # Function to tag POS for translated words using spaCy
    def tag_pos_spacy(self, data):
        pos_tags = []
        for word in data['Word']:
            if word:  # Check for non-empty words
                doc = self.nlp(word)
                pos_tags.append(doc[0].pos_)
            else:
                pos_tags.append(None)
        data['POS'] = pos_tags
        return data

    # Function to create Gold Standard DataFrame
    def create_gold_standard_df(self):
        word_list = self.fetch_words_with_pos()
        translations = self.translate_words(word_list)
        df_translations = pd.DataFrame(translations)
        df_english = self.tag_pos_spacy(df_translations)
        df_english = df_english.drop(columns=["Translated Word"])

        # Mapping English POS to Malay equivalents
        pos_translation_map = {
            "NOUN": "kata nama",
            "VERB": "kata kerja",
            "ADJ": "kata adjektif",
            "PRON": "kata ganti nama",
            "ADP": "kata sendi nama",
            "ADV": "kata adverba",
            "CCONJ": "kata hubung",
            "SCONJ": "kata hubung",
            "INTJ": "kata seru",
            "AUX": "kata bantu",
            "PART": "kata tugas",
            "DET": "kata tugas",
            "NUM": "kata tugas",
            "PROPN": "kata nama",
            "SYM": "kata tugas",
            "X": "kata tugas"
        }

        df_english['POS Malay'] = df_english['POS'].map(pos_translation_map).str.lower()
        return df_english.drop(columns=["POS"])

    # Function to fetch data from Neo4j and merge with Gold Standard DataFrame
    def compare_pos_with_gold_standard(self):
        query = """
        MATCH (w:Word)
        WHERE w.part_of_speech IS NOT NULL AND NOT w.part_of_speech CONTAINS "NaN"
        RETURN w.name AS word, w.part_of_speech AS part_of_speech
        """
        df_compare = self.graph.run(query).to_data_frame()

        df_compare['word'] = df_compare['word'].str.strip().str.lower()
        gold_standard_df = self.create_gold_standard_df()
        gold_standard_df['Word'] = gold_standard_df['Word'].str.strip().str.lower()

        # Merging results
        merged_df = pd.merge(df_compare, gold_standard_df, left_on='word', right_on='Word', how='inner')
        merged_df['pos_match'] = merged_df['POS Malay'] == merged_df['part_of_speech']

        # Calculate accuracy
        correct_matches = merged_df['pos_match'].sum()
        total_words = len(merged_df)
        accuracy = correct_matches / total_words

        return merged_df, total_words, correct_matches, accuracy