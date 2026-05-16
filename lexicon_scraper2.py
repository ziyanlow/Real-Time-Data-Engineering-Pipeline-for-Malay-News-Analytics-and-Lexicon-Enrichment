from nltk.corpus import wordnet

def get_hypernyms_hyponyms_meronyms_holonyms_in_malay(word):
    hypernyms = []
    hyponyms = []
    meronyms = []
    holonyms = []
    
    try:
        for synset in wordnet.synsets(word, lang='zsm'):  # Ensure it works for Malay
            # Hypernyms
            hypernyms.extend([lemma.name() for synset in synset.hypernyms() for lemma in synset.lemmas(lang='zsm')])
            # Hyponyms
            hyponyms.extend([lemma.name() for synset in synset.hyponyms() for lemma in synset.lemmas(lang='zsm')])
            # Meronyms
            meronyms.extend([lemma.name() for synset in synset.part_meronyms() + synset.substance_meronyms() + synset.member_meronyms() for lemma in synset.lemmas(lang='zsm')])
            # Holonyms
            holonyms.extend([lemma.name() for synset in synset.part_holonyms() + synset.substance_holonyms() + synset.member_holonyms() for lemma in synset.lemmas(lang='zsm')])
        
        # Use set to remove duplicates and limit to 3 words for each relation
        hypernyms = ', '.join(list(set(hypernyms))[:3])
        hyponyms = ', '.join(list(set(hyponyms))[:3])
        meronyms = ', '.join(list(set(meronyms))[:3])
        holonyms = ', '.join(list(set(holonyms))[:3])
    
    except Exception as e:
        print(f"Error processing word {word}: {e}")
        return "[]", "[]", "[]", "[]"
    
    return hypernyms, hyponyms, meronyms, holonyms