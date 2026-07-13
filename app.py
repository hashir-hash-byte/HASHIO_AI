# ==========================================
# 4. RENDERING LIVE SUMMARY & AUDIO SPEAKER
# ==========================================
if st.session_state.summary:
    st.write("---")
    st.subheader("📝 AI-Generated Summary:")
    st.success(st.session_state.summary)
    
    st.subheader("🔊 Audio Reader")
    
    # Advanced cleaning: strip out backslashes, quotes, and line breaks that destroy JS strings
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
                // Stop anything currently speaking
                window.speechSynthesis.cancel(); 
                
                // Re-initialize the utterance object fresh on click
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
