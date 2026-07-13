import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime
from gtts import gTTS
import io

# ==========================================
# 0. DATABASE SETUP (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_type TEXT,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_history(input_type, summary_text):
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history (timestamp, input_type, summary) VALUES (?, ?, ?)", 
              (now, input_type, summary_text))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, input_type, summary FROM history ORDER BY id DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize the database file on launch
init_db()

# ==========================================
# 1. APPLICATION SETUP & SECURITY
# ==========================================
st.title("📚 HASHIO_AI: VTU Notes & File Summarizer")
st.write("Welcome, Mohammed! Paste your notes, drop a file, and track your recent session history below.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key missing! Please configure GEMINI_API_KEY in the Streamlit Secrets panel.")
    st.stop()

if "summary" not in st.session_state:
    st.session_state.summary = ""

# ==========================================
# 2. INPUT SELECTION TABS
# ==========================================
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

# ==========================================
# 3. TRIGGER AI ANALYSIS
# ==========================================
if st.button("Generate AI Summary"):
    if not notes_to_analyze.strip():
        st.warning("Please paste some notes or upload a file first!")
    else:
        with st.spinner("AI is analyzing and summarizing your notes..."):
            try:
                model = genai.GenerativeModel('gemini-3.5-flash')
                prompt = (
                    f"You are an expert engineering professor. Summarize the following "
                    f"academic notes or document. Break down the core concepts into clear, concise bullet points "
                    f"that are easy to study for exams. Keep formatting clean:\n\n{notes_to_analyze}"
                )
                response = model.generate_content(prompt)
                st.session_state.summary = response.text
                
                # Save to database
                save_to_history(source_type, response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

# ==========================================
# 4. RENDERING LIVE SUMMARY & AUDIO SPEAKER
# ==========================================
if st.session_state.summary:
    st.write("---")
    st.subheader("📝 AI-Generated Summary:")
    st.success(st.session_state.summary)
    
    st.subheader("🔊 Audio Reader")
    
    with st.spinner("Generating audio track..."):
        try:
            # Clean text slightly for a natural read-out
            speech_text = st.session_state.summary.replace("*", "").replace("-", " ")
            
            # Use gTTS to build the speech track in memory
            tts = gTTS(text=speech_text, lang='en', tld='com')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            # Render Streamlit's beautiful native HTML5 audio bar widget
            st.audio(fp, format="audio/mp3")
            
        except Exception as audio_err:
            st.error(f"Could not generate audio: {audio_err}")

# ==========================================
# 5. RENDERING THE DATABASE HISTORY LOG
# ==========================================
st.write("---")
st.subheader("📜 Recent Summaries Database Log")
records = get_history()

if records:
    for row in records:
        timestamp, input_type, stored_summary = row
        with st.expander(f"🕒 {timestamp} | Source: {input_type}"):
            st.info(stored_summary)
else:
    st.write("No recent summaries saved in this session yet. Try generating one!")
