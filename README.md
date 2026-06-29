# AI Book-to-Movie Adaptation Chatbot 🎬📖

An intelligent, glassmorphic conversational assistant that analyzes the faithfulness of book-to-movie adaptations. Utilizing OMDb, Google Books, and Google's Gemini 2.5 Flash API, the chatbot provides real-time comparisons, plot breakdowns, directing analysis, and dynamically fetches cover art, movie posters, and ratings.

---

## ✨ Features

- 🧠 **Intelligent RAG Comparison**: Dynamic entity extraction queries Google Books and OMDb to extract plot summaries, author/director data, and IMDb ratings to assist Gemini in generating accurate adaptation guides.
- 🎨 **Premium Glassmorphic UI**: Vibrant, responsive layout with floating backdrop glows, sliding form transitions, custom toasts, and dynamic card layouts.
- 🎙️ **Voice Assistant Integration**:
  - **Speech-to-Text (STT)**: Pulsing microphone glows support vocal inputs directly into the chat.
  - **Text-to-Speech (TTS)**: Reads response content aloud, configurable via settings.
- ⚙️ **Functional Profile Dashboard**: Customize user avatars, nicknames, and adjust TTS playback speech rate (speed) and voice pitch.
- 📊 **Dynamic Recommendations Grid**: A dedicated portal displaying handpicked literature-to-cinema adaptations with summary badges and ratings.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/AI-Book-to-Movie.git
   cd AI-Book-to-Movie/AI
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   Create a file named **`Api.env`** in the `/AI` folder and insert your credentials:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_BOOKS_API_KEY=your_google_books_key
   OMDB_API_KEY=your_omdb_api_key
   ```

---

## 🚀 Running the App

Start the Flask server:
```bash
python App.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser!
