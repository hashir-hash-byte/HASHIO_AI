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

# Password hashing utility for security
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
        success = False  # Username already exists
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

# Initialize database tables on startup
init_db()

# ==========================================
# 1. SIDEBAR AUTHENTICATION INTERFACE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

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
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.summary = ""
            st.rerun()

# ==========================================
# 2. APP CODE (PROTECTED BY LOGIN STATE)
# ==========================================
st.title("📚 HASHIO_AI: VTU Notes & File Summarizer")

if not st.session_state.logged_in:
    st.info("Please Log In or Sign Up using the sidebar menu to start using the app.")
else:
    st.write(f"Welcome back, **{st.session_state.username}**! Paste notes or upload a file below.")

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    except Exception:
        st.error("API Key missing from Streamlit secrets.")
        st.stop()

    # Form processing tabs
    tab1, tab2 = st.tabs(["📝 Paste Text", "📁 Upload File"])
    notes_to_analyze = ""
    source_type = "Text Input"

    with tab1:
        user_notes = st.text_area("Paste your VTU Notes here:", height=200, key="text_input")
        if user_notes:
            notes_to_analyze = user_notes
            source_type = "Text Input"

    with tab2:
        uploaded_file = st.file_uploader("Upload a text file (.txt):", type=["txt"])
        if uploaded_file is not None:
            file_contents = uploaded_file.read().decode("utf-8")
            st.success(f"Successfully loaded: {uploaded_file.name}")
            notes_to_analyze = file_contents
            source_type = f"File: {uploaded_file.name}"

    if st.button("Generate AI Summary"):
        if not notes_to_analyze.strip():
            st.warning("Please provide notes or a file first.")
        else:
            with st.spinner("AI is studying your notes..."):
                try:
                    model = genai.GenerativeModel('gemini-3.5-flash')
                    prompt = (
                        f"You are an expert engineering professor. Summarize the following "
                        f"academic notes. Break down core concepts into bullet points for exam preparation:\n\n{notes_to_analyze}"
                    )
                    response = model.generate_content(prompt)
                    st.session_state.summary = response.text
                    
                    # Save history locked to this specific user profile
                    save_to_history(st.session_state.username, source_type, response.text)
                    
                except Exception as e:
                    st.error(f"Error processing content: {e}")

    # Render Summary & Voice
    if st.session_state.summary:
        st.write("---")
        st.subheader("📝 AI-Generated Summary:")
        st.success(st.session_state.summary)
        
        st.subheader("🔊 Audio Reader")
        with st.spinner("Generating audio track..."):
            try:
                speech_text = st.session_state.summary.replace("*", "").replace("-", " ")
                tts = gTTS(text=speech_text, lang='en', tld='com')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format="audio/mp3")
            except Exception as audio_err:
                st.error(f"Audio Generation Error: {audio_err}")

    # Render Personal User History from DB
    st.write("---")
    st.subheader(f"📜 {st.session_state.username}'s History Log")
    records = get_user_history(st.session_state.username)

    if records:
        for row in records:
            timestamp, input_type, stored_summary = row
            with st.expander(f"🕒 {timestamp} | {input_type}"):
                st.info(stored_summary)
    else:
        st.write("No saved summaries in your account history yet.")
