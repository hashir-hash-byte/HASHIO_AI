import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

# 1. Setup the Title and Description
st.title("📚 HASHIO_AI: VTU Notes & File Summarizer")
st.write("Welcome, Mohammed! Paste your notes or drop a file below to get an intelligent AI summary.")

# 2. Automatically load the API Key from Streamlit's secure vault
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key missing! Please configure GEMINI_API_KEY in the Streamlit Secrets panel.")
    st.stop()

# Initialize Session State memory fields so data stays on screen
if "summary" not in st.session_state:
    st.session_state.summary = ""

# 3. Create two tabs: One for text input, one for file uploads
tab1, tab2 = st.tabs(["📝 Paste Text", "📁 Upload File"])

notes_to_analyze = ""

with tab1:
    user_notes = st.text_area("Paste your VTU Notes here:", height=250, key="text_input")
    if user_notes:
        notes_to_analyze = user_notes

with tab2:
    uploaded_file = st.file_uploader("Upload a text file (.txt):", type=["txt"])
    if uploaded_file is not None:
        file_contents = uploaded_file.read().decode("utf-8")
        st.success(f"Successfully loaded: {uploaded_file.name}")
        with st.expander("Preview uploaded file content"):
            st.code(file_contents[:500] + "...", language="text")
        notes_to_analyze = file_contents

# 4. Trigger the AI analysis
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
                
                # Save the summary into our page memory!
                st.session_state.summary = response.text
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

# 5. Display the summary and voice buttons permanently if they exist in memory
if st.session_state.summary:
    st.write("---")
    st.subheader("📝 AI-Generated Summary:")
    st.success(st.session_state.summary)
    
    st.subheader("🔊 Audio Reader")
    
    # Clean up text specifically for the JavaScript execution string
    clean_text = st.session_state.summary.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    
    # HTML and JavaScript to tap into the browser's native text-to-speech engine
    tts_html = f"""
    <div style="display: flex; gap: 10px; font-family: sans-serif;">
        <button onclick="speak()" style="background-color: #2e7d32; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">▶ Play Audio</button>
        <button onclick="stop()" style="background-color: #d32f2f; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">⏹ Stop</button>
    </div>

    <script>
        var msg = new SpeechSynthesisUtterance();
        msg.text = "{clean_text}";
        msg.rate = 1.0; 
        
        function speak() {{
            window.speechSynthesis.cancel(); 
            window.speechSynthesis.speak(msg);
        }}
        
        function stop() {{
            window.speechSynthesis.cancel();
        }}
    </script>
    """
    # Render the speaker component safely outside the temporary button conditional
    components.html(tts_html, height=70)
