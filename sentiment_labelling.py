from transformers import pipeline

class SentimentLabelling:
    def __init__(self):
        # Load a multilingual model fine-tuned for sentiment analysis
        self.sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
    
    # Function to get sentiment score
    def analyze_sentiment(self, word):
        result = self.sentiment_pipeline(word)  # Run the sentiment analysis
        label = result[0]['label']         # Extract the label (e.g., '1 star', '5 star')
        score = result[0]['score']         # Extract the confidence score
        # Map star ratings to numeric sentiment scores
        if "1 star" in label:  # Highly negative
            return -1 * score
        elif "2 star" in label:  # Negative
            return -0.5 * score
        elif "3 star" in label:  # Neutral
            return 0
        elif "4 star" in label:  # Positive
            return 0.5 * score
        elif "5 star" in label:  # Highly positive
            return 1 * score
        else:
            return 0  # Default to neutral if label is unexpected

    # Function to assign sentimental label based on sentiment score
    def assign_sentimental_label(self, score):
        if score > 0.0:  # Positive range
            return "Positive"
        elif score < 0.0:  # Negative range
            return "Negative"
        elif score == 0.0:  # Neutral score
            return "Neutral"
