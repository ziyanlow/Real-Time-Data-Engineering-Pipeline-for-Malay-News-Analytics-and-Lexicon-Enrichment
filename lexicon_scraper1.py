import logging
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import csv
import re
from bson.objectid import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)

# MongoDB connection function
def get_words_from_mongo_by_id(object_id):
    try:
        client = MongoClient("")
        db = client["my_database"]  # Replace with your database name
        collection = db["tokens_collection"]  # Replace with your collection name
        doc = collection.find_one({"_id": ObjectId(object_id)})
        if doc and 'tokens' in doc:
            return [token['word'] for token in doc['tokens'] if 'word' in token]
        return []
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return []

def get_words_from_mongo(missing_sentiment_pos_index):
    try:
        client = MongoClient("")
        db = client["my_database"]  # Replace with your database name
        collection = db["tokens_collection"]  # Replace with your collection name
        words = []

        # Iterate through all documents and retrieve words starting from the missing_sentiment_pos_index
        for doc in collection.find({}, {'tokens': 1, '_id': 0}):
            tokens = doc.get('tokens', [])
            for index, token in enumerate(tokens):
                if index >= missing_sentiment_pos_index:  # Start from the specified index
                    if 'word' in token:
                        words.append(token['word'])
        return words
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return []

# Function to fetch the HTML content of a word
def soup_of_DBP(word):
    url = f"https://prpm.dbp.gov.my/Cari1?keyword={word}"  # Example URL
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        raise Exception(f"Error fetching data for {word}")

# Function to scrape dictionary data
def scrape_DBP_data(word):
    try:
        soup = soup_of_DBP(word)
        logging.info(f"Scraping data for {word}...")
        
        panel_body = soup.find('div', class_='panel-body')
        if not panel_body:
            logging.warning(f"No data found for the word: {word}")
            return None

        # Extract definitions
        definitions_list = []
        i = 1
        definitions_div = panel_body.find('div', id=i)
        while definitions_div:
            definitions_text = definitions_div.get_text(separator=' ', strip=True)
            definitions_list.append(definitions_text)
            i += 1
            definitions_div = panel_body.find('div', id=i)
        
        if not definitions_list:
            logging.warning(f"No definitions found for {word}, skipping...")
            return None  # Skip the word if no definitions found

        # Scrape extra information
        stemmed_word, contexts, synonyms, antonyms, derived_words, part_of_speech = scrape_extra_information(word)

        stemmed_word = stemmed_word 
        contexts = contexts 
        synonyms = synonyms 
        antonyms = antonyms 
        derived_words = derived_words 
        
        # Construct the Lexicon object
        lexicon = Lexicon(
            word=word,
            stemmed_word=stemmed_word,
            definitions=definitions_list,
            part_of_speech=part_of_speech,
            synonyms=synonyms,
            antonyms=antonyms,
            contexts=contexts,
            derived_words=derived_words,
        )
        return lexicon
    except requests.exceptions.RequestException as req_e:
        logging.error(f"Request error while scraping {word}: {req_e}")
    except Exception as e:
        logging.error(f"Error while scraping data for {word}: {e}")
    return None

def scrape_extra_information(word):
    try:
        soup = soup_of_DBP(word)
        table = soup.find('table', class_='info')

        if not table:
            logging.warning(f"No extra information found for {word}")
            return [], [], [], [], [], None

        stemmed_word, contexts, synonyms, antonyms, derived_words = [], [], [], [], []
        part_of_speech = "-"
        
        # Extract part of speech
        part_of_speech_tag = table.find_next('font')
        if part_of_speech_tag:
            raw_text = part_of_speech_tag.text.strip()
            # Filter to include only alphanumeric words
            part_of_speech = " ".join(re.findall(r'\b[a-zA-Z]+\b', raw_text))
        
            # Process and translate the part of speech
            part_of_speech = process_part_of_speech(part_of_speech)
    
        # Extract contexts, synonyms, antonyms, and derived words
        b_tags = table.find_all('b')
        a_tags = table.find_all('a')
        
        for b in b_tags:
            text = b.text.strip()
            if any(text.startswith(prefix) for prefix in ['Dalam konteks', 'dalam konteks']):
                context = b.find_next('a').text.strip()
                contexts.append(context)
            elif any(text.startswith(prefix) for prefix in ['Bersinonim dengan', 'bersinonim dengan']):
                synonym = b.find_next('a').text.strip()
                synonyms.append(synonym)
            elif any(text.startswith(prefix) for prefix in ['Berantonim dengan', 'berantonim dengan']):
                antonym = b.find_next('a').text.strip()
                antonyms.append(antonym)
                
        # Extract derived words
        # Find the <th> with 'Tesaurus'
        th_tag = soup.find('th', text='Tesaurus')
        
        if th_tag:
            # Locate the next <tr> or <td> tag that contains the desired word
            stemmed_word = th_tag.find_next('tr').find_next('span')
            stemmed_word = stemmed_word.text.strip()
                
        kata_terbitan_tag = table.find_next('b', string="Kata Terbitan : ")
        if kata_terbitan_tag:
            derived_i_tags = kata_terbitan_tag.find_next('i')
            derived_a_tags = derived_i_tags.find_all('a')
            for d in derived_a_tags:
                derived_words.append(d.text.strip())

        return stemmed_word,contexts, synonyms, antonyms, derived_words, part_of_speech
    except Exception as e:
        logging.error(f"Error while scraping extra information for {word}: {e}")
        return [], [], [], [], [], None


def process_part_of_speech(part_of_speech):
    translation_map = {
        "adjektif": "kata sifat",
        "kata nama": "kata nama",
        "kata sendi": "kata sendi",
        "kata kerja": "kata kerja",
        "kata sifat": "kata sifat",
        "kata keterangan": "kata keterangan",
        "kata ganti nama": "kata ganti nama",
        "kata penentu": "kata penentu",
        "kata bilangan": "kata bilangan",
        "partikel": "partikel",
        "simbol": "simbol",
        "nama khas": "nama khas",
    }
    if part_of_speech in translation_map:
        return translation_map[part_of_speech]
    else:
        return ""
    #return translation_map.get(part_of_speech, "")

class Lexicon:
    def __init__(self, word, stemmed_word, definitions, part_of_speech, synonyms, antonyms, contexts, derived_words):
        self.word = word
        self.stemmed_word = stemmed_word
        self.definitions = definitions
        self.part_of_speech = part_of_speech
        self.synonyms = synonyms
        self.antonyms = antonyms
        self.contexts = contexts
        self.derived_words = derived_words

def write_to_csv(filename, lexicon_data):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Stemmed Word", "Definitions", "Part of Speech", "Contexts", "Synonyms", "Antonyms", "Derived Words"])
        for lexicon in lexicon_data:
            writer.writerow([
                lexicon.word,
                ''.join(lexicon.stemmed_word or []),
                '; '.join(lexicon.definitions or []),
                lexicon.part_of_speech,
                '; '.join(lexicon.contexts or []),
                '; '.join(lexicon.synonyms or []),
                '; '.join(lexicon.antonyms or []),
                ', '.join(lexicon.derived_words or [])
            ])

def write_to_csv(filename, lexicon_data):
    def replace_semicolons(value):
        """
        Replace semicolons with commas in the given value.
        Handles lists by joining with a comma instead of a semicolon.
        """
        if isinstance(value, list):  # For lists, join with commas
            return ', '.join(value)
        elif isinstance(value, str):  # For strings, replace semicolons with commas
            return value.replace(';', ',')
        return value  # Return value as is for non-list, non-string types

    def sanitize_part_of_speech(value):
        """
        Replace placeholder '-' with an empty string for part_of_speech.
        """
        return "" if value == "-" else value

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(["Word", "Stemmed Word", "Definitions", "Part of Speech", "Contexts", "Synonyms", "Antonyms", "Derived Words"])
        
        # Write data rows
        for lexicon in lexicon_data:
            writer.writerow([
                replace_semicolons(lexicon.word),
                replace_semicolons(''.join(lexicon.stemmed_word or [])),
                replace_semicolons('; '.join(lexicon.definitions or [])),
                sanitize_part_of_speech(lexicon.part_of_speech),  # Sanitize part_of_speech here
                replace_semicolons('; '.join(lexicon.contexts or [])),
                replace_semicolons('; '.join(lexicon.synonyms or [])),
                replace_semicolons('; '.join(lexicon.antonyms or [])),
                replace_semicolons(', '.join(lexicon.derived_words or []))
            ])
