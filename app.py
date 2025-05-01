import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from extensions import db, login_manager
from flask_login import login_user, login_required, logout_user, current_user
from recommender import recommend_intelligent, fetch_live_news

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'your_secret_key_here'

# Configure Database: Use instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# ✅ Import models AFTER db initialized
from models import User

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('welcome'))  # ← 🎉 Welcome page here!
        else:
            error = 'Invalid email or password.'

    return render_template('login.html', error=error)

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@app.route('/transition')
@login_required
def transition():
    return render_template('transition.html')


# ---- Home (Protected) ----
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    recommendations = []
    query = ''
    live_news = fetch_live_news()
    keywords_chart_data = {"labels": [], "values": []}

    if request.method == 'POST':
        query = request.form['query']
        recommendations = recommend_intelligent(query)
        live_news = fetch_live_news(query)

# -----✅ Save for tfidf explanation page
        session['last_query'] = query
        session['last_docs'] = [doc for doc, _, _ in recommendations]

    if recommendations:
            all_keywords = recommendations[0][2]
            keywords_chart_data['labels'] = all_keywords[:5]
            keywords_chart_data['values'] = [5 - i for i in range(len(all_keywords[:5]))]

            max_score = max(score for _, score, _ in recommendations)
            if max_score > 0:
                recommendations = [
                    (doc, round((score / max_score) * 100, 2), keywords)
                    for doc, score, keywords in recommendations
                ]

    return render_template(
        'index.html',
        recommendations=recommendations,
        query=query,
        live_news=live_news,
        keywords_chart_data=keywords_chart_data
    )


# ---- Sign Up ----
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('User already exists.', 'error')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))  # << ✅ Must be **inside** the function!!

    return render_template('signup.html')  # << ✅ Also inside the function

# ---- Reset Password ----
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            new_password = request.form['new_password']
            user.set_password(new_password)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return 'No user found with that email.'

    return render_template('reset_password.html')

# ---- Logout ----
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---- Chatbot Page ----
@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

# ---- Chat POST ----
@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.form['message'].lower()
    if 'recommend' in user_message:
        bot_response = "I recommend news based on your query using BM25 and smart keyword analysis."
    elif 'bm25' in user_message:
        bot_response = "BM25 is an advanced algorithm that ranks news articles based on relevance."
    elif 'hello' in user_message or 'hi' in user_message:
        bot_response = "Hello there! I'm your news assistant 🤖. Ask me anything about your news!"
    elif 'suggest' in user_message:
        bot_response = "Try topics like 'Space Exploration', 'AI in Healthcare', or 'Global Politics'."
    else:
        bot_response = "I'm not sure about that, but I'm learning! Try asking about news or recommendations."

    return jsonify({'reply': bot_response})

if __name__ == '__main__':
    app.run(debug=True)

# ---- TF-IDF Explanation Page (Optional Feature) ----
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import session

@app.route('/tfidf-details')
@login_required
def tfidf_details():
    # For demo purposes: Sample documents (normally you'd use your actual data)
    documents = session.get('last_docs', [
        "AI is transforming healthcare and society.",
        "Healthcare applications of AI are expanding rapidly.",
        "News about AI and machine learning in medicine."
    ])
    query = session.get('last_query', "AI in healthcare")

    # Include the query in the corpus to visualize its effect
    corpus = [query] + documents

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    terms = vectorizer.get_feature_names_out()

    result = []
    for i, doc_vector in enumerate(tfidf_matrix.toarray()):
        tfidf_scores = [(term, round(score, 3)) for term, score in zip(terms, doc_vector) if score > 0]
        doc_label = "Query" if i == 0 else f"Doc {i}"
        result.append((doc_label, sorted(tfidf_scores, key=lambda x: -x[1])))

    return render_template("tfidf_details.html", query=query, result=result)
