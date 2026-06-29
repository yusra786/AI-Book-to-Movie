import os
from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys from environment variables (ensure these are set in your .env file)
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

app = Flask(__name__)
CORS(app)

# Home Route
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/chatpage')
def chat_page():
    return render_template('chat.html')

# Recommendations Route
@app.route('/recommendations')
def show_recommendations():
    movies = [
        {"title": "Harry Potter", "book": "J.K. Rowling", "image": url_for('static', filename='images/harry_potter.jpg')},
        {"title": "The Lord of the Rings", "book": "J.R.R. Tolkien", "image": url_for('static', filename='images/lotr.jpg')},
        {"title": "The Hunger Games", "book": "Suzanne Collins", "image": url_for('static', filename='images/hunger_games.jpg')}
    ]
    return render_template('recommendation.html', movies=movies)

# Book-to-Movie Adaptation Checker
@app.route('/book_to_movie', methods=['GET'])
def book_to_movie():
    title = request.args.get('title')
    if not title:
        return jsonify({"error": "Book title is required"}), 400

    try:
        # Google Books API
        book_response = requests.get(GOOGLE_BOOKS_API, params={'q': title, 'key': GOOGLE_BOOKS_API_KEY})
        book_data = book_response.json()

        # OMDB API
        omdb_url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
        movie_response = requests.get(omdb_url)
        movie_data = movie_response.json()

        # Check adaptation
        adaptation = False
        reason = "No clear adaptation link found."
        if 'Writer' in movie_data and 'novel' in movie_data['Writer'].lower():
            adaptation = True
            reason = f"This movie appears to be based on a novel: {movie_data['Writer']}."

        return jsonify({
            "book_info": book_data,
            "movie_info": movie_data,
            "is_adaptation": adaptation,
            "reason": reason
        })

    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

# Chat Route using Gemini API
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    gemini_reply = get_gemini_response(user_message)
    return jsonify({"reply": gemini_reply})

# Gemini API Function
def get_gemini_response(message):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": message}]
        }]
    }
    params = {"key": GEMINI_API_KEY}

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        data = response.json()
        print("Gemini Response:", data)
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0].get('text', 'No response content.')
        else:
            return f"Gemini error: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"Oops! Couldn't fetch a response from Gemini. Error: {str(e)}"


# Health Check Route
@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
