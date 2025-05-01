import nltk
import pandas as pd
import spacy
from rank_bm25 import BM25Okapi
import requests

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load your cleaned CSV file
df = pd.read_csv('Data/20newsgroups_data.csv')

# Ensure there are no missing values in the 'text' column
df = df.dropna(subset=['text'])

# Use the 'text' column as your corpus
limited_docs = df['text'].tolist()  # Adjust slicing if needed, e.g., df['text'][:1000].tolist()

# Preprocess documents: lowercased and tokenized
processed_docs = [doc.lower() for doc in limited_docs]
tokenized_corpus = [doc.split() for doc in processed_docs]

# Initialize BM25 with the tokenized corpus
bm25 = BM25Okapi(tokenized_corpus, k1=2.0, b=1.2)

# Process user query: extract important keywords using spaCy NLP
def process_query(query):
    doc = nlp(query)
    keywords = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
    return keywords

# Intelligent recommender using BM25
def recommend_intelligent(query, top_n=5):
    keywords = process_query(query)
    scores = bm25.get_scores(keywords)
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    recommendations = [(limited_docs[idx], scores[idx], keywords) for idx in indices]
    return recommendations

# 🔥 LIVE NEWS FETCH FUNCTION
NEWS_API_KEY = 'd3cf11b7508e4a5886bdc0a0971eb3ab'  # <--- Replace with your key!

def fetch_live_news(topic='technology'):
    url = f'https://newsapi.org/v2/top-headlines?q={topic}&language=en&pageSize=5&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'ok':
        articles = data['articles']
        return [(article['title'], article['description'], article['url']) for article in articles]
    else:
        return []
