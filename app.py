# app.py
from flask import Flask, render_template, request
from recommender import recommend

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    query = ''
    if request.method == 'POST':
        query = request.form['query']
        recommendations = recommend(query)
    return render_template('index.html', recommendations=recommendations, query=query)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
