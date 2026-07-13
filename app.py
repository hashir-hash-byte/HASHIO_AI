import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime
from gtts import gTTS
import io

# ==========================================
# 0. DATABASE & SECURITY SETUP (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    # 1. Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    ''')
    # 2. Create History Table safely
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            input_type TEXT,
            summary TEXT
        )
    ''')
    
    # 3. SCHEMA MIGRATION: Forcefully add username column to old tables if missing
    try:
        c.execute("ALTER TABLE history ADD COLUMN username TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # If the column already exists, SQLite throws an error, which we safely ignore here
        pass
        
    conn.commit()
    conn.close()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (username, make_hash(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def login_user(username, password):
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", 
              (username, make_hash(password)))
    data = c.fetchall()
    conn.close()
    return len(data) > 0

def save_to_history(username, input_type, summary_text):
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history (username, timestamp, input_type, summary) VALUES (?, ?, ?, ?)", 
              (username, now, input_type, summary_text))
    conn.commit()
    conn.close()

def get_user_history(username):
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, input_type, summary FROM history WHERE username = ? ORDER BY id DESC LIMIT 5", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# ==========================================
# 1. SIDEBAR AUTHENTICATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
# Chat message logs stored globally for the session
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("🔑 HASHIO_AI Portal")
    
    if not st.session_state.logged_in:
        auth_mode = st.radio("Choose Action:", ["Login", "Sign Up"])
        auth_user = st.text_input("Username:").strip()
        auth_pass = st.text_input("Password:", type="password")
        
        if auth_mode == "Login":
            if st.button("Sign In"):
                if login_user(auth_user, auth_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = auth_user
                    # Seed chat greeting
                    st.session_state.messages = [{"role": "assistant", "content": f"Hi {auth_user}! I'm ready. Paste your engineering notes, drop a file, or ask me a direct question!"}]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        else:
            if st.button("Register Account"):
                if auth_user == "" or auth_pass == "":
                    st.warning("Please fill out both fields.")
                elif create_user(auth_user, auth_pass):
                    st.success("Account created! You can now log in.")
                else:
                    st.error("Username already taken.")
    else:
        st.write(f"Logged in as: **{st.session_state.username}**")
        
        # Display Personal User History from DB inside the Sidebar to save room
        st.write("---")
        st.subheader("📜 Your Recent Logs")
        records = get_user_history(st.session_state.username)
        if records:
            for row in records:
                timestamp, input_type, stored_summary = row
                with st.expander(f"🕒 {timestamp} | {input_type}"):
                    st.caption(stored_summary[:100] + "...")
        else:
            st.caption("No history saved yet.")

        st.write("---")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = []
            st.rerun()

# ==========================================
# 2. CHAT MODE INTERFACE (PROTECTED)
# ==========================================
st.title("💬 HASHIO_AI: Interactive Companion")

if not st.session_state.logged_in:
    st.info("Please Log In or Sign Up using the sidebar menu to open the chat window.")
else:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    except Exception:
        st.error("API Key missing from Streamlit secrets.")
        st.stop()

    # Optional File Uploader attachment widget right at the top
    uploaded_file = st.file_uploader("📎 Optional: Attach a text file (.txt) to analyze in the conversation", type=["txt"])
    file_payload = ""
    if uploaded_file is not None:
        file_payload = uploaded_file.read().decode("utf-8")
        st.success(f"Attached file: {uploaded_file.name}")

    st.write("---")

    # Render rolling history of conversational logs on screen
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Look for active inputs at the bottom row (Like ChatGPT)
    if user_prompt := st.chat_input("Ask HASHIO_AI anything..."):
        
        # Display human bubble
        with st.chat_message("user"):
            st.write(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # Process context package (Merge text inputs with attached file data if present)
        final_prompt = user_prompt
        source_label = "Direct Query"
        if file_payload:
            final_prompt = f"Context file contents:\n{file_payload}\n\nUser Question:\n{user_prompt}"
            source_label = f"File Context: {uploaded_file.name}"

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    model = genai.GenerativeModel('gemini-3.5-flash')
                    
                    # Feed the full conversational chain to simulate actual memory
                    system_context = "You are an expert engineering mentor. Answer clearly and split dense technical explanations into easy-to-read bullet points.\n\n"
                    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
                    
                    full_payload = f"{system_context}{history_context}\nuser: {final_prompt}"
                    
                    response = model.generate_content(full_payload)
                    ai_response = response.text
                    
                    st.write(ai_response)
                    
                    # Text to Speech Generator
                    st.write("🔊 **Listen to reply:**")
                    speech_text = ai_response.replace("*", "").replace("-", " ")
                    tts = gTTS(text=speech_text, lang='en', tld='com')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    st.audio(fp, format="audio/mp3")

                    # Log the turn inside the SQLite Database
                    save_to_history(st.session_state.username, source_label, ai_response[:150] + "...")
                    
                    # Update rolling memory array
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    st.error(f"Error communicating with AI: {e}")
