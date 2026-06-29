import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Helper to load key-value pairs from Api.env
def load_env():
    env = {}
    env_path = os.path.join(os.path.dirname(__file__), "Api.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

# Initialize configuration
env_vars = load_env()
GEMINI_API_KEY = env_vars.get("GEMINI_API_KEY", "")
GOOGLE_BOOKS_API_KEY = env_vars.get("GOOGLE_BOOKS_API_KEY", "")
OMDB_API_KEY = env_vars.get("OMDB_API_KEY", "")

# ----------------- Helper API Integrations -----------------

def call_gemini(prompt, system_instruction=None, history=None):
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not configured.")
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    if history:
        # History format: [{"role": "user", "text": "..."}, {"role": "bot", "text": "..."}]
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("text", "")}]
            })
            
    # Append the current prompt
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })
    
    body = {
        "contents": contents
    }
    
    if system_instruction:
        body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        if response.status_code == 429:
            try:
                err_data = response.json()
                err_msg = err_data.get("error", {}).get("message", "")
                if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                    return f"ERROR_QUOTA: {err_msg}"
            except Exception:
                pass
        response.raise_for_status()
        data = response.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini API Request Failed:", e)
    return None

def extract_entities(user_message):
    system_prompt = (
        "You are a movie and book entity extractor. Analyze the user's query and extract:\n"
        "1. 'book_title': The name of any book mentioned. If none, output null.\n"
        "2. 'movie_title': The name of any movie mentioned. If none, output null.\n"
        "Provide your output strictly in JSON format matching this schema:\n"
        "{\n"
        "  \"book_title\": string or null,\n"
        "  \"movie_title\": string or null\n"
        "}\n"
        "Do not include any extra explanation or markdown block (like ```json). Return raw JSON."
    )
    result = call_gemini(user_message, system_instruction=system_prompt)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception as e:
            print("Failed to parse entity JSON:", e, "Raw response:", result)
    return {"book_title": None, "movie_title": None}

def get_book_details(title):
    if not title:
        return None
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"intitle:{title}",
        "maxResults": 1
    }
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY
        
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if "items" in data and len(data["items"]) > 0:
            volume_info = data["items"][0]["volumeInfo"]
            return {
                "title": volume_info.get("title"),
                "authors": volume_info.get("authors", []),
                "publisher": volume_info.get("publisher"),
                "publishedDate": volume_info.get("publishedDate"),
                "description": volume_info.get("description", "No description available."),
                "rating": volume_info.get("averageRating", "N/A"),
                "ratingCount": volume_info.get("ratingsCount", 0),
                "image": volume_info.get("imageLinks", {}).get("thumbnail")
            }
    except Exception as e:
        print("Google Books API Error for title", title, ":", e)
    return None

def get_movie_details(title):
    if not title or not OMDB_API_KEY:
        return None
    url = "http://www.omdbapi.com/"
    params = {
        "t": title,
        "apikey": OMDB_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("Response") == "True":
            return {
                "title": data.get("Title"),
                "year": data.get("Year"),
                "director": data.get("Director"),
                "writer": data.get("Writer"),
                "actors": data.get("Actors"),
                "plot": data.get("Plot"),
                "imdbRating": data.get("imdbRating", "N/A"),
                "poster": data.get("Poster") if data.get("Poster") != "N/A" else None,
                "genre": data.get("Genre")
            }
    except Exception as e:
        print("OMDb API Error for title", title, ":", e)
    return None

# ----------------- Flask Routes -----------------

@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/chat", methods=["GET"])
def chat_page():
    return render_template("chat.html")

@app.route("/recommendations", methods=["GET"])
def recommendations_page():
    return render_template("Recommendation.html")

@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("Dashboard.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])
    
    if not user_message:
        return jsonify({"reply": "I couldn't understand that. Please send a valid message!"}), 400
        
    # Combine generation and entity extraction into 1 API call to save quota limits (preventing 429)
    system_instruction = (
        "You are the AI Adaptation Guide, an expert chatbot that analyzes book-to-movie adaptations.\n"
        "Answer the user's questions about books, movies, ratings, and differences. "
        "Keep your tone conversational, enthusiastic, and direct. Use markdown bullet points and bold headers to structure your response.\n"
        "IMPORTANT: At the absolute end of your response, append the extracted titles on new lines exactly in this format:\n"
        "EXTRACTED_BOOK: [Book Title or N/A]\n"
        "EXTRACTED_MOVIE: [Movie Title or N/A]"
    )
    
    reply = call_gemini(user_message, system_instruction=system_instruction, history=history)
    if not reply:
        # Fallback message
        return jsonify({
            "reply": "I'm sorry, I had some trouble connecting to my brain. Can you try again?",
            "book_details": None,
            "movie_details": None
        })
        
    if reply.startswith("ERROR_QUOTA:"):
        err_details = reply.split("ERROR_QUOTA:", 1)[1].strip()
        user_msg = (
            "⚠️ **Google Gemini Quota Exceeded!**\n\n"
            "The Google Gemini API Key configured in your `Api.env` file has exhausted its daily request limits.\n\n"
            f"**Google Server Error:**\n`{err_details}`\n\n"
            "**How to Fix This:**\n"
            "1. Open [Google AI Studio](https://aistudio.google.com/) and sign in.\n"
            "2. Create a new API Key (Get API key).\n"
            "3. Open the **`Api.env`** file in your project folder.\n"
            "4. Replace `GEMINI_API_KEY` with your newly created key.\n"
            "5. Refresh the page and try asking your question again!"
        )
        return jsonify({
            "reply": user_msg,
            "book_details": None,
            "movie_details": None
        })
        
    # Parse extracted titles from the response text
    book_title = None
    movie_title = None
    clean_reply_lines = []
    
    for line in reply.split("\n"):
        if line.startswith("EXTRACTED_BOOK:"):
            val = line.split("EXTRACTED_BOOK:", 1)[1].strip()
            if val and val != "N/A" and val != "[Book Title or N/A]":
                book_title = val
        elif line.startswith("EXTRACTED_MOVIE:"):
            val = line.split("EXTRACTED_MOVIE:", 1)[1].strip()
            if val and val != "N/A" and val != "[Movie Title or N/A]":
                movie_title = val
        else:
            clean_reply_lines.append(line)
            
    clean_reply = "\n".join(clean_reply_lines).strip()
    
    # Fetch details for the visual media cards
    book_details = get_book_details(book_title) if book_title else None
    movie_details = get_movie_details(movie_title) if movie_title else None
    
    # Cross-reference search fallbacks
    if book_title and not movie_details:
        movie_details = get_movie_details(book_title)
    if movie_title and not book_details:
        book_details = get_book_details(movie_title)
        
    return jsonify({
        "reply": clean_reply,
        "book_details": book_details,
        "movie_details": movie_details
    })

@app.route("/api/recommendations", methods=["GET"])
def get_recommendations_api():
    recs = [
        {
            "title": "Dune",
            "book": "Frank Herbert",
            "description": "Frank Herbert's sci-fi masterpiece was adapted into a visual triumph by Denis Villeneuve, capturing the complex politics and mysticism of Arrakis.",
            "imdbRating": "8.0",
            "image": "Dune.jpg"
        },
        {
            "title": "The Lord of the Rings",
            "book": "J.R.R. Tolkien",
            "description": "Peter Jackson's legendary trilogy is widely considered one of the greatest book-to-movie adaptations of all time, winning 17 Oscars.",
            "imdbRating": "8.8",
            "image": "Lord of rings.jpg"
        },
        {
            "title": "The Hunger Games",
            "book": "Suzanne Collins",
            "description": "A faithful adaptation of Suzanne Collins' dystopian novel that successfully brought the brutal world of Panem and Katniss Everdeen to life.",
            "imdbRating": "7.2",
            "image": "Hunger games.jpg"
        },
        {
            "title": "Gone Girl",
            "book": "Gillian Flynn",
            "description": "Directed by David Fincher and written by Gillian Flynn herself, this thriller maintains the dark suspense and unreliable narration of the bestseller.",
            "imdbRating": "8.1",
            "image": "Gone Girl.jpg"
        },
        {
            "title": "Ready Player One",
            "book": "Ernest Cline",
            "description": "Steven Spielberg adapted this pop-culture laden novel into a visually dazzling CGI ride, modifying key challenges to fit a cinematic pace.",
            "imdbRating": "7.2",
            "image": "Ready Player One (1_3) Movie Poster.jpg"
        },
        {
            "title": "Sherlock Holmes",
            "book": "Arthur Conan Doyle",
            "description": "Guy Ritchie's adaptation offers a dynamic, action-packed twist on Doyle's detective, featuring a highly charismatic Robert Downey Jr.",
            "imdbRating": "7.6",
            "image": "Sherlock Holmes.jpg"
        }
    ]
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
