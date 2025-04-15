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
    app.run(debug=True)
