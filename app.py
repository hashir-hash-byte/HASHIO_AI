import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime

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
                    f"that are easy to study for exams. Avoid complex markdown symbols like asterisks inside the text:\n\n{notes_to_analyze}"
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
    
    clean_text = (
        st.session_state.summary
        .replace("\\", " ")
        .replace("'", " ")
        .replace('"', ' ')
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )
    
    tts_html = f"""
    <div style="display: flex; gap: 10px; font-family: sans-serif;">
        <button onclick="speak()" style="background-color: #2e7d32; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; box-shadow: 0px 2px 4px rgba(0,0,0,0.2);">▶ Play Audio</button>
        <button onclick="stop()" style="background-color: #d32f2f; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; box-shadow: 0px 2px 4px rgba(0,0,0,0.2);">⏹ Stop</button>
    </div>
    
    <script>
        var msg = null;
        function speak() {{
            try {{
                window.speechSynthesis.cancel(); 
                msg = new SpeechSynthesisUtterance();
                msg.text = "{clean_text}";
                msg.rate = 1.0; 
                msg.lang = 'en-US';
                window.speechSynthesis.speak(msg);
            }} catch(err) {{
                alert("Speech error: " + err.message);
            }}
        }}
        function stop() {{
            window.speechSynthesis.cancel();
        }}
    </script>
    """
    st.html(tts_html)

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
