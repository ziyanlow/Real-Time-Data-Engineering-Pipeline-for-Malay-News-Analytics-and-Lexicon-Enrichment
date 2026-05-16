import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class TextSentimentAnalyzer:
    def __init__(self, lexicon_path, article_path):
        self.lexicon_path = lexicon_path
        self.article_path = article_path
        self.lexicon_words = []
        self.relevant_sentences = []
        self.matched_words = []
        self.sentiment_results = []
    
    def load_lexicon(self):
        """Load the lexicon data (CSV file with a 'Word' column)."""
        lexicon_df = pd.read_csv(self.lexicon_path)
        self.lexicon_words = lexicon_df['Word'].tolist()
    
    def load_article(self):
        """Load the raw article text."""
        with open(self.article_path, 'r', encoding='utf-8') as file:
            raw_text = file.read()
        return raw_text

    def split_text_into_sentences(self, raw_text):
        """Split the raw text into sentences based on punctuation."""
        sentences = re.split(r'(?<=[.!?])\s+', raw_text)
        return sentences
    
    def find_relevant_sentences(self, sentences):
        """Find sentences containing words from the lexicon."""
        for sentence in sentences:
            for word in self.lexicon_words:
                if word.lower() in sentence.lower():  # case-insensitive search
                    self.relevant_sentences.append(sentence)
                    self.matched_words.append(word)  # Store the matched word
                    break  # Stop once a match is found in this sentence

    def perform_sentiment_analysis(self):
        """Perform sentiment analysis using VADER."""
        analyzer = SentimentIntensityAnalyzer()
        
        for sentence, matched_word in zip(self.relevant_sentences, self.matched_words):
            sentiment_score = analyzer.polarity_scores(sentence)
            if sentiment_score['compound'] >= 0.05:
                sentiment_category = 'Positive'
            elif sentiment_score['compound'] <= -0.05:
                sentiment_category = 'Negative'
            else:
                sentiment_category = 'Neutral'
            
            self.sentiment_results.append({
                'sentence': sentence,
                'matched_word': matched_word,
                'positive_score': sentiment_score['pos'],
                'neutral_score': sentiment_score['neu'],
                'negative_score': sentiment_score['neg'],
                'compound_score': sentiment_score['compound'],
                'sentiment_category': sentiment_category
            })

    def save_results(self, output_path):
        """Save sentiment results to a CSV file."""
        sentiment_df = pd.DataFrame(self.sentiment_results)
        sentiment_df.to_csv(output_path, index=False)
        print(f"Results saved to '{output_path}'")
