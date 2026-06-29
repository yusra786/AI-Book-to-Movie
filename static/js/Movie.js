// Redirect to login if not authenticated
if (localStorage.getItem("user_logged_in") !== "true") {
    window.location.href = "/login";
}

let chatHistory = [];
let voiceOutputEnabled = false;
let currentAbortController = null;
let synth = window.speechSynthesis;
let recognition = null;

// DOM Ready
document.addEventListener("DOMContentLoaded", function () {
    console.log("AI Chatbot JS Initialized!");

    // Load custom profile avatar in the header
    const avatar = localStorage.getItem("profile_avatar");
    if (avatar) {
        const picEl = document.querySelector(".profile-pic");
        if (picEl) picEl.src = avatar;
    }

    // Load Voice Output setting
    const savedVoice = localStorage.getItem("voice_output_enabled");
    if (savedVoice !== null) {
        voiceOutputEnabled = savedVoice === "true";
    }
    updateVoiceButtonUI();

    // Load Chat History from LocalStorage
    const savedHistory = localStorage.getItem("ai_chat_history");
    if (savedHistory) {
        try {
            chatHistory = JSON.parse(savedHistory);
            renderChatHistory();
        } catch (e) {
            console.error("Failed to parse chat history:", e);
            chatHistory = [];
        }
    }

    // Speech Recognition Setup
    try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.lang = "en-US";
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = function () {
                const micBtn = document.getElementById("micButton");
                const userInp = document.getElementById("userInput");
                micBtn.classList.add("mic-active");
                userInp.placeholder = "Listening... Speak now!";
            };

            recognition.onresult = function (event) {
                const voiceText = event.results[0][0].transcript;
                document.getElementById("userInput").value = voiceText;
                sendMessage();
            };

            recognition.onerror = function (event) {
                console.error("Speech Recognition Error:", event.error);
                resetMicUI();
            };

            recognition.onend = function () {
                resetMicUI();
            };

            document.getElementById("micButton").addEventListener("click", () => {
                // Cancel speaking when speaking a new question
                if (synth.speaking) {
                    synth.cancel();
                }
                recognition.start();
            });
        } else {
            console.warn("Speech Recognition not supported in this browser.");
            document.getElementById("micButton").style.display = "none";
        }
    } catch (err) {
        console.error("Failed to initialize Speech Recognition:", err);
        document.getElementById("micButton").style.display = "none";
    }
});

function resetMicUI() {
    const micBtn = document.getElementById("micButton");
    const userInp = document.getElementById("userInput");
    if (micBtn) micBtn.classList.remove("mic-active");
    if (userInp) userInp.placeholder = "Ask about any book or movie adaptation...";
}

// Render saved conversation history
function renderChatHistory() {
    const chatBox = document.getElementById("chatBox");
    // Clear and put the initial greeting if empty
    chatBox.innerHTML = "";
    if (chatHistory.length === 0) {
        chatBox.innerHTML = `<div class="message bot">Welcome! I am your AI Adaptation Guide. Ask me anything about books and movie adaptations, comparisons, ratings, directors, authors, and recommendations!</div>`;
        return;
    }

    chatHistory.forEach((msg) => {
        appendMessageUI(msg.role, msg.text, msg.book_details, msg.movie_details, false);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Function to toggle voice output
function toggleVoiceOutput() {
    voiceOutputEnabled = !voiceOutputEnabled;
    localStorage.setItem("voice_output_enabled", voiceOutputEnabled);
    updateVoiceButtonUI();
    if (!voiceOutputEnabled && synth.speaking) {
        synth.cancel();
    }
}

function updateVoiceButtonUI() {
    const voiceBtn = document.getElementById("voiceToggleBtn");
    if (voiceBtn) {
        voiceBtn.innerHTML = voiceOutputEnabled ? "🔊" : "🔇";
        voiceBtn.title = voiceOutputEnabled ? "Mute Voice Read Aloud" : "Enable Voice Read Aloud";
        if (voiceOutputEnabled) {
            voiceBtn.style.color = "#00ffcc";
            voiceBtn.style.borderColor = "rgba(0, 255, 204, 0.3)";
        } else {
            voiceBtn.style.color = "#a4b0be";
            voiceBtn.style.borderColor = "rgba(255,255,255,0.1)";
        }
    }
}

// Function to clear chat history
function clearChatHistory() {
    if (confirm("Are you sure you want to clear the conversation history?")) {
        chatHistory = [];
        localStorage.removeItem("ai_chat_history");
        renderChatHistory();
        if (synth.speaking) {
            synth.cancel();
        }
    }
}

// Append message into UI
function appendMessageUI(role, text, bookDetails = null, movieDetails = null, shouldAnimate = true) {
    const chatBox = document.getElementById("chatBox");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", role === "user" ? "user" : "bot");
    
    // Format text with paragraph breaks and lists
    let formattedText = formatMarkdown(text);
    msgDiv.innerHTML = `<div>${formattedText}</div>`;

    // Append Media Cards if available
    if (role === "bot" && (bookDetails || movieDetails)) {
        const container = document.createElement("div");
        container.className = "adaptation-container";

        if (bookDetails) {
            const authorsStr = Array.isArray(bookDetails.authors) ? bookDetails.authors.join(", ") : (bookDetails.authors || "Unknown");
            const bookImg = bookDetails.image || "/static/images/Poster.jpg"; // fallback
            const rating = bookDetails.rating !== "N/A" ? `${bookDetails.rating}★` : "No rating";
            
            container.innerHTML += `
                <div class="media-card">
                    <img src="${bookImg}" alt="${bookDetails.title}" class="media-card-img">
                    <div class="media-card-content">
                        <div class="media-card-title">${bookDetails.title}</div>
                        <div class="media-card-meta">By ${authorsStr}</div>
                        <div class="media-card-desc">${bookDetails.description}</div>
                        <div class="media-card-badges">
                            <span class="media-card-badge blue">📖 Book</span>
                            <span class="media-card-badge">${rating}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        if (movieDetails) {
            const movieImg = movieDetails.poster || "/static/images/Poster.jpg"; // fallback
            const rating = movieDetails.imdbRating !== "N/A" ? `${movieDetails.imdbRating}★` : "No rating";
            
            container.innerHTML += `
                <div class="media-card">
                    <img src="${movieImg}" alt="${movieDetails.title}" class="media-card-img">
                    <div class="media-card-content">
                        <div class="media-card-title">${movieDetails.title} (${movieDetails.year})</div>
                        <div class="media-card-meta">Directed by ${movieDetails.director}</div>
                        <div class="media-card-desc">${movieDetails.plot}</div>
                        <div class="media-card-badges">
                            <span class="media-card-badge blue">🎬 Movie</span>
                            <span class="media-card-badge">${rating}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        msgDiv.appendChild(container);
    }

    // Add action buttons for Bot responses (Copy, Speak)
    if (role === "bot") {
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "message-actions";
        
        const copyBtn = document.createElement("button");
        copyBtn.className = "action-btn";
        copyBtn.innerHTML = "📋 Copy";
        copyBtn.onclick = function () {
            copyToClipboard(text, copyBtn);
        };

        const speakBtn = document.createElement("button");
        speakBtn.className = "action-btn";
        speakBtn.innerHTML = "🔊 Speak";
        speakBtn.onclick = function () {
            speakResponse(text);
        };

        actionsDiv.appendChild(copyBtn);
        actionsDiv.appendChild(speakBtn);
        msgDiv.appendChild(actionsDiv);
    }

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Simple Markdown Formatter for visual excellence
function formatMarkdown(text) {
    if (!text) return "";
    let html = text;
    // Replace bold tags
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Replace bullet points
    html = html.replace(/^\s*[\-\*]\s+(.*)$/gm, '<li>$1</li>');
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    // Replace newlines with breaks if not inside list
    html = html.replace(/\n/g, '<br>');
    return html;
}

// Copy message to clipboard
function copyToClipboard(text, buttonEl) {
    const cleanText = stripHtml(text);
    navigator.clipboard.writeText(cleanText).then(() => {
        const originalText = buttonEl.innerHTML;
        buttonEl.innerHTML = "✅ Copied!";
        buttonEl.style.color = "#00ffcc";
        setTimeout(() => {
            buttonEl.innerHTML = originalText;
            buttonEl.style.color = "";
        }, 1500);
    }).catch(err => {
        console.error("Failed to copy text:", err);
    });
}

// Strip HTML helper
function stripHtml(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return doc.body.textContent || "";
}

// Text-to-Speech reader
function speakResponse(text) {
    if (!synth) return;
    
    // Stop currently playing audio
    synth.cancel();

    const cleanText = stripHtml(text);
    const speech = new SpeechSynthesisUtterance();
    speech.text = cleanText;
    speech.lang = "en-US";
    speech.volume = 1;
    
    // Load custom speed and pitch settings
    const savedRate = parseFloat(localStorage.getItem("profile_speech_rate")) || 1.0;
    const savedPitch = parseFloat(localStorage.getItem("profile_speech_pitch")) || 1.0;
    speech.rate = savedRate;
    speech.pitch = savedPitch;

    synth.speak(speech);
}

// Send Message Flow
async function sendMessage(textOverride = null) {
    const input = document.getElementById("userInput");
    const text = textOverride || input.value.trim();
    if (text === "") return;

    // Reset input
    input.value = "";

    // Cancel any TTS reading if the user asks a new question
    if (synth.speaking) {
        synth.cancel();
    }

    // Abort previous backend call if in progress
    if (currentAbortController) {
        currentAbortController.abort();
    }

    // Append User Message to UI
    appendMessageUI("user", text);

    // Save user message to history array
    chatHistory.push({ role: "user", text: text });
    localStorage.setItem("ai_chat_history", JSON.stringify(chatHistory));

    // Show Typing Indicator
    const chatBox = document.getElementById("chatBox");
    const indicatorMsg = document.createElement("div");
    indicatorMsg.classList.add("message", "bot");
    indicatorMsg.id = "typingIndicator";
    indicatorMsg.innerHTML = `
        <div class="typing-container">
            <span style="font-size: 0.9rem; color: #a4b0be; margin-right: 8px;">AI Guide is thinking</span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    chatBox.appendChild(indicatorMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Set up AbortController
    currentAbortController = new AbortController();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                history: chatHistory.slice(-10) // Send last 10 messages for context
            }),
            signal: currentAbortController.signal
        });

        // Remove typing indicator
        const indicator = document.getElementById("typingIndicator");
        if (indicator) indicator.remove();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Append bot message to UI
        appendMessageUI("bot", data.reply, data.book_details, data.movie_details);

        // Save bot response to history
        chatHistory.push({
            role: "bot",
            text: data.reply,
            book_details: data.book_details,
            movie_details: data.movie_details
        });
        localStorage.setItem("ai_chat_history", JSON.stringify(chatHistory));

        // Read aloud if enabled
        if (voiceOutputEnabled) {
            speakResponse(data.reply);
        }

    } catch (error) {
        if (error.name === "AbortError") {
            console.log("Fetch call was aborted.");
            return;
        }
        
        console.error("Error communicating with backend:", error);
        
        const indicator = document.getElementById("typingIndicator");
        if (indicator) indicator.remove();

        appendMessageUI("bot", "Oops! I ran into an error communicating with my server. Please check your connection and try again.");
    } finally {
        currentAbortController = null;
    }
}

// Enter Key handler
function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}
