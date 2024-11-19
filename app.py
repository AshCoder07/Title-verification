from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
import jellyfish
from fuzzywuzzy import fuzz
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Load and preprocess the dataset
df = pd.read_csv("dataset.csv", encoding='ISO-8859-1')
print(f"Loaded {len(df)} records")

# Ensure all columns are loaded and processed
df.fillna('', inplace=True)

# Helper function for text cleaning
def clean_text(text):
    return str(text).strip().lower() if pd.notna(text) else ''

# Apply text cleaning to relevant columns
df['Title Name'] = df['Title Name'].apply(clean_text)
df['Hindi Title'] = df['Hindi Title'].apply(clean_text)

# Phonetic encoding for enhanced comparison
df['Title_Soundex'] = df['Title Name'].apply(jellyfish.soundex)
df['Title_Metaphone'] = df['Title Name'].apply(jellyfish.metaphone)

# Process TF-IDF vectors for title similarity
vectorizer = TfidfVectorizer(stop_words='english')
vectors = vectorizer.fit_transform(df['Title Name'] + ' ' + df['Hindi Title']).toarray().astype('float32')

# Initialize FAISS index for nearest neighbor search
dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

# Phonetic similarity function
def phonetic_similarity(new_title, existing_title):
    new_soundex = jellyfish.soundex(new_title)
    existing_soundex = jellyfish.soundex(existing_title)
    new_metaphone = jellyfish.metaphone(new_title)
    existing_metaphone = jellyfish.metaphone(existing_title)
    return (new_soundex == existing_soundex) or (new_metaphone == existing_metaphone)

# Title verification logic
def verify_title(new_title, top_k=10):
    new_title_clean = clean_text(new_title)
    detailed_report = []  # Store comprehensive details about matches
    DISALLOWED_WORDS = {'thief', 'police', 'cid', 'crime', 'corruption', 'army'}

    # Check for title length
    if len(new_title_clean) < 3:
        return {
            'verified': False,
            'probability': 1,
            'reason': "The provided title is too short. Titles should be at least 5 characters long for meaningful verification.",
            'suggestion': "Consider providing a more descriptive and significant title.",
            'detailed_report': detailed_report
        }
    if re.search(r'[^a-zA-Z0-9\s]', new_title_clean):
        return {
            'verified': False,
            'probability': 1,
            'reason': "The title contains special characters, which are not allowed.",
            'suggestion': "Please provide a title using only letters, numbers, and spaces.",
            'detailed_report': detailed_report
        }
    # TF-IDF vectorization and search
    words_in_title = set(new_title_clean.lower().split())
    disallowed_found = DISALLOWED_WORDS.intersection(words_in_title)
    if disallowed_found:
        return {
            'verified': False,
            'probability': 1,
            'reason': f"The title contains disallowed words: {', '.join(disallowed_found)}.",
            'suggestion': "Please avoid using words that relate to crime or restricted domains.",
            'detailed_report': detailed_report
        }

    
    new_vector = vectorizer.transform([new_title_clean]).toarray().astype('float32')
    distances, indices = index.search(new_vector, top_k)

    max_similarity = 0
    similar_titles = []
    for dist, idx in zip(distances[0], indices[0]):
        matched_row = df.iloc[idx]
        existing_title = matched_row['Title Name']
        similarity = fuzz.ratio(new_title_clean, existing_title) / 100
        max_similarity = max(max_similarity, similarity)

        phonetic_match = phonetic_similarity(new_title_clean, existing_title)

        # Append matched record details to the report
        detailed_report.append({
            'Title Name': matched_row['Title Name'],
            'Hindi Title': matched_row['Hindi Title'],
            'Register Serial No': matched_row['Register Serial No'],
            'Regn No.': matched_row['Regn No.'],
            'Owner Name': matched_row['Owner Name'],
            'State': matched_row['State'],
            'Publication City/District': matched_row['Publication City/District'],
            'Periodity': matched_row['Periodity'],
            'Similarity Score': float(similarity),  # Convert to native Python float
            'Phonetic Match': phonetic_match,
            'TF-IDF Distance': float(dist)  # Convert to native Python float
        })

        if similarity > 0.8:
            similar_titles.append(existing_title)

        if phonetic_match:
            return {
                'verified': False,
                'probability': 1,
                'reason': f"Phonetic similarity to {existing_title} which is pre-existing",
                'detailed_report': detailed_report
            }

    if similar_titles:
        return {
            'verified': False,
            'probability': float(1 - max_similarity),  # Convert to native Python float
            'reason': f"Similar to existing titles: {', '.join(similar_titles)}",
            'similar_titles': similar_titles,
            'detailed_report': detailed_report
        }

    return {
        'verified': True,
        'probability': float(1 - max_similarity),  # Convert to native Python float
        'reason': "No significant matches found",
        'detailed_report': detailed_report
    }

# Flask endpoint for title verification
@app.route('/verify', methods=['POST'])
def verify_title_endpoint():
    data = request.json
    if 'title' not in data:
        return jsonify({'error': 'No title provided'}), 400
    result = verify_title(data['title'])
    return jsonify(result)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
