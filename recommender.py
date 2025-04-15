# recommender.py
import nltk
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
from nltk.corpus import stopwords
nltk.download('stopwords')

# Load and preprocess data
def preprocess(text):
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = [word for word in text.split() if word not in stop_words and word.isalpha()]
    return ' '.join(tokens)

news_data = fetch_20newsgroups(subset='all', remove=('headers', 'footers', 'quotes'))
processed_docs = [preprocess(doc) for doc in news_data.data]

vectorizer = TfidfVectorizer(max_features=5000)
X_tfidf = vectorizer.fit_transform(processed_docs)

# Recommendation function
def recommend(query, top_n=5):
    query_vec = vectorizer.transform([preprocess(query)])
    similarity = cosine_similarity(query_vec, X_tfidf).flatten()
    indices = similarity.argsort()[-top_n:][::-1]
    recommendations = [(news_data.data[idx], similarity[idx]) for idx in indices]
    return recommendations
