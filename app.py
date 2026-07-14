import cohere  # Add this import at the very top of your app.py

# ... inside your chat generation block in app.py ...
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = None
                
                # --- TRY COHERE TRIAL API FIRST ---
                try:
                    # Look for the Cohere Key in your Streamlit secrets dashboard
                    cohere_key = st.secrets.get("COHERE_API_KEY", None)
                    
                    if cohere_key:
                        # Initialize the official Cohere client (v2 architecture)
                        co_client = cohere.ClientV2(api_key=cohere_key)
                        
                        system_context = "You are an expert engineering mentor. Answer clearly and split dense technical explanations into easy-to-read bullet points."
                        
                        # Format the chat history safely for Cohere's chat tool layout
                        messages_payload = [{"role": "system", "content": system_context}]
                        for m in st.session_state.messages[:-1]:
                            # Map 'assistant' role to what Cohere expects if needed, or leave as standard
                            messages_payload.append({"role": m["role"], "content": m["content"]})
                        messages_payload.append({"role": "user", "content": final_prompt})
                        
                        # Query Cohere's premier flagship model
                        response = co_client.chat(
                            model="command-r-plus",
                            messages=messages_payload
                        )
                        
                        ai_response = response.message.content
                        
                except Exception as co_err:
                    # If you hit the 20-request-per-minute cap or run out of monthly slots, trigger backup
                    st.warning("Cohere trial limit reached or hit an error. Switching to backup engine...")
                
                # --- BACKUP FALLBACK: GOOGLE GEMINI ---
                if not ai_response:
                    try:
                        model = genai.GenerativeModel('gemini-3.5-flash')
                        system_context = "You are an expert engineering mentor. Answer clearly and split dense technical explanations into easy-to-read bullet points.\n\n"
                        history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
                        full_payload = f"{system_context}{history_context}\nuser: {final_prompt}"
                        
                        response = model.generate_content(full_payload)
                        ai_response = response.text
                    except Exception as e:
                        st.error(f"Critical System Failure: Both AI engines are down. Details: {e}")
                
                # --- DISPLAY AND OUTPUT LOGS ---
                if ai_response:
                    st.write(ai_response)
                    
                    # On-demand Audio Engine to keep the initial response fast!
                    button_key = f"audio_{datetime.now().strftime('%H%M%S')}"
                    if st.button("🔊 Generate Audio Track", key=button_key):
                        with st.spinner("Converting text to speech..."):
                            speech_text = ai_response.replace("*", "").replace("-", " ")
                            tts = gTTS(text=speech_text, lang='en', tld='com')
                            fp = io.BytesIO()
                            tts.write_to_fp(fp)
                            fp.seek(0)
                            st.audio(fp, format="audio/mp3")

                    # Log inside the persistent SQLite system
                    save_to_history(st.session_state.username, source_label, ai_response[:150] + "...")
                    
                    # Save into rolling visual memory array
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
