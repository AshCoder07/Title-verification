from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
import jellyfish
from fuzzywuzzy import fuzz

app = Flask(__name__)
CORS(app)  # Enable CORS

# Load and preprocess data
df = pd.read_csv("dataset.csv", encoding='ISO-8859-1')
print(f"Loaded {len(df)} records")

def clean_text(text):
    return str(text).lower() if pd.notna(text) else ''

df['Title Name'] = df['Title Name'].apply(clean_text)
df['Hindi Title'] = df['Hindi Title'].apply(clean_text)

# Phonetic encoding
df['Title_Soundex'] = df['Title Name'].apply(jellyfish.soundex)
df['Title_Metaphone'] = df['Title Name'].apply(jellyfish.metaphone)

DISALLOWED_WORDS = {'police', 'crime', 'corruption', 'cbi', 'cid', 'army'}
DISALLOWED_PREFIXES = {'deadly', 'brutal', 'violent', 'killer', 'extreme'}
DISALLOWED_SUFFIXES = {'massacre', 'terror', 'attack', 'warfare', 'assassin'}

vectorizer = TfidfVectorizer(stop_words='english')
vectors = vectorizer.fit_transform(df['Title Name'] + ' ' + df['Hindi Title']).toarray().astype('float32')

dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

def phonetic_similarity(new_title, existing_title):
    new_soundex = jellyfish.soundex(new_title)
    existing_soundex = jellyfish.soundex(existing_title)
    new_metaphone = jellyfish.metaphone(new_title)
    existing_metaphone = jellyfish.metaphone(existing_title)
    return (new_soundex == existing_soundex) or (new_metaphone == existing_metaphone)

def verify_title(new_title, top_k=10):
    new_title_clean = clean_text(new_title)
    if any(word in DISALLOWED_WORDS for word in new_title_clean.split()):
        return {'verified': False, 'probability': 0, 'reason': "Contains disallowed words"}
    if any(new_title_clean.startswith(prefix) for prefix in DISALLOWED_PREFIXES):
        return {'verified': False, 'probability': 0, 'reason': "Contains disallowed prefix"}
    if any(new_title_clean.endswith(suffix) for suffix in DISALLOWED_SUFFIXES):
        return {'verified': False, 'probability': 0, 'reason': "Contains disallowed suffix"}
    
    new_vector = vectorizer.transform([new_title_clean]).toarray().astype('float32')
    distances, indices = index.search(new_vector, top_k)
    
    max_similarity = 0
    similar_titles = []
    for dist, idx in zip(distances[0], indices[0]):
        existing_title = df.iloc[idx]['Title Name']
        similarity = fuzz.ratio(new_title_clean, existing_title) / 100
        max_similarity = max(max_similarity, similarity)
        if similarity > 0.8:
            similar_titles.append(existing_title)
        if phonetic_similarity(new_title_clean, existing_title):
            return {'verified': False, 'probability': 0, 'reason': f"Phonetic similarity to {existing_title}"}
    
    if similar_titles:
        return {
            'verified': False,
            'probability': 1 - max_similarity,
            'reason': f"Similar to existing titles: {', '.join(similar_titles)}",
            'similar_titles': similar_titles
        }
    
    return {'verified': True, 'probability': 1 - max_similarity}

@app.route('/verify', methods=['POST'])
def verify_title_endpoint():
    data = request.json
    if 'title' not in data:
        return jsonify({'error': 'No title provided'}), 400
    result = verify_title(data['title'])
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True)
