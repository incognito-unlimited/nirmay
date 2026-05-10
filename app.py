import streamlit as st
import os
import io
import requests
import PyPDF2
from pdf2image import convert_from_bytes
import pytesseract
from groq import Groq
from dotenv import load_dotenv
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder

# Load environment variables
load_dotenv(override=True)

# Set up Streamlit page configuration
st.set_page_config(page_title="Nirmay: Rural Health Report Simplifier", page_icon="🌿", layout="wide")

LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Bengali": "bn"
}

# --- System Prompt Definition ---
def get_system_prompt(language="English"):
    return f"""
You are 'Nirmay', a compassionate and highly knowledgeable Medical Interpreter designed to help rural and low-literacy populations understand their medical reports. 

CRITICAL RULE: You MUST communicate entirely in {language}. All your responses, summaries, and answers must be translated fluently to {language}.

You will be provided with raw text extracted via OCR from a user's medical document (e.g., blood test, prescription, or diagnostic report). 

Your workflow is as follows:
1. SUMMARY: Provide a highly simplified, jargon-free summary of what the report is about (maximum 3 sentences).
2. KEY METRICS: Identify any flagged anomalies or important metrics. Explain them in plain, non-alarming language. Do NOT diagnose the user.
3. NEXT STEPS: Suggest 3 simple, specific questions the user should ask their doctor at their next visit.

Tone & Constraints: 
- Be incredibly empathetic, calm, and reassuring.
- Use simple vocabulary. Avoid complex medical terminology unless you are defining it immediately.
- Always include a disclaimer stating you are an AI assistant and they must consult a human doctor for medical advice.
- When the user asks follow-up questions in the chat, answer them directly based ONLY on the provided OCR context.
"""

# --- Helper Functions ---

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts text from a PDF file, falling back to OCR if no selectable text is found."""
    text = ""
    pdf_bytes = pdf_file.read()
    
    try:
        # First attempt: Direct text extraction using PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # If sufficient text was found, we assume it's a text-based PDF
        if len(text.strip()) > 50:
            return text.strip()
            
    except Exception as e:
        st.warning(f"Failed to read as digital PDF format. Attempting OCR... Error: {str(e)}")

    # Fallback attempt: OCR for scanned PDFs
    try:
        images = convert_from_bytes(pdf_bytes)
        for i, image in enumerate(images):
            text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        st.error(f"OCR Processing failed. Please ensure 'tesseract' and 'poppler' are installed on your system. Error: {str(e)}")
        
    return text.strip()

def query_llm(messages, groq_api_key):
    """
    Hybrid LLM querying workflow: Try local Ollama first, fallback to Groq.
    """
    # Attempt Primary Engine: Local Ollama (llama3.1:8b)
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "llama3.1:8b",

                "messages": messages,
                "stream": False
            },
            timeout=5 # Short timeout for local check
        )
        response.raise_for_status()
        data = response.json()
        
        st.session_state.engine_status = "Primary Engine (Local Ollama)"
        return data["message"]["content"]
        
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Local model unavailable, fallback to cloud if API key exists
        if not groq_api_key:
            return "Error: Local Ollama is unreachable, and no Groq API key was provided for the fallback engine."
        
        try:
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            
            st.session_state.engine_status = "Fallback Engine (Groq Cloud)"
            return completion.choices[0].message.content
            
        except Exception as groq_error:
            return f"Error: Failed to reach both local Ollama and Groq fallback. Details: {str(groq_error)}"

def generate_tts(text, lang_code):
    """Generates Text-to-Speech audio bytes."""
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception:
        return None

# --- Main App Logic ---

def main():
    st.title("🌿 Nirmay: Rural Health Report Simplifier")
    st.markdown("Upload your medical report and let Nirmay help you understand it simply and gently.")
    
    # --- Sidebar Styling & Configurations ---
    # Read the API key securely from environment variable
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        try:
            from dotenv import dotenv_values
            env_vals = dotenv_values(".env")
            groq_key = env_vals.get("GROQ_API_KEY", "")
        except Exception:
            groq_key = ""

    with st.sidebar:
        st.header("🌐 Language Settings")
        selected_lang = st.selectbox(
            "Select your language / अपनी भाषा चुनें:", 
            options=list(LANG_MAP.keys()), 
            index=0
        )
        
        st.divider()
        # Reset conversation
        if st.button("Reset Session") and st.session_state.get('report_processed', False):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(selected_lang)}]
            st.session_state.report_processed = False
            st.rerun()

    # Initialize session state variables
    if "current_lang" not in st.session_state or st.session_state.current_lang != selected_lang:
        st.session_state.current_lang = selected_lang
        # If language changes, update the system prompt but keep conversation if active?
        # Better to reset conversation if language fundamentally changes, or just let future messages translate.
        if "messages" not in st.session_state or not st.session_state.get("report_processed", False):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(selected_lang)}]
        else:
            # Update the very first message silently so instructions update for follow-ups
            st.session_state.messages[0] = {"role": "system", "content": get_system_prompt(selected_lang)}

    if "report_processed" not in st.session_state:
        st.session_state.report_processed = False
    if "engine_status" not in st.session_state:
        st.session_state.engine_status = "Checking availability..."


            st.session_state.report_processed = False
            st.rerun()

    # --- File Upload Section ---
    if not st.session_state.report_processed:
        uploaded_file = st.file_uploader("Upload your Medical Report (PDF)", type=["pdf"])
        
        if uploaded_file is not None:
            with st.spinner("Reading & simplifying your report... Please wait."):
                report_text = extract_text_from_pdf(uploaded_file)
                
                if not report_text:
                    st.error("We couldn't read any text from this file. Please try a clearer document.")
                    return
                
                # Create initial prompt merging text and system instructions
                user_initial_prompt = f"Here is the OCR extracted text from the patient's medical report:\n\n{report_text}\n\nPlease proceed with the SUMMARY, KEY METRICS, and NEXT STEPS as per your instructions."
                
                st.session_state.messages.append({"role": "user", "content": user_initial_prompt})
                
                # Process the LLM query
                assistant_response = query_llm(st.session_state.messages, groq_key)
                
                # Generate TTS for initial summary
                audio_bytes = generate_tts(assistant_response, LANG_MAP[selected_lang])
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response, "audio": audio_bytes})
                st.session_state.report_processed = True
                st.rerun()

    # --- Interactive Chat Interface ---
    if st.session_state.report_processed:
        st.success("Report successfully processed!")
        
        # Display chat history (skipping the underlying system prompt and initial raw injection)
        for message in st.session_state.messages[2:]: # Skip system prompt and the raw OCR insertion
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("audio"):
                    st.audio(message["audio"], format="audio/mp3")

        # Accept follow-up user input via text or voice
        col1, col2 = st.columns([1, 6])
        with col1:
            audio_input = audio_recorder(text="🎙️", recording_color="#cc0000", neutral_color="#0066cc", icon_size="2x")
        with col2:
            text_prompt = st.chat_input(f"Ask a question in {selected_lang}...")
            
        final_prompt = None
        
        # Voice transcription via Groq Whisper Fallback (Requires Groq Key)
        if audio_input and groq_key:
            with st.spinner("Transcribing audio..."):
                client = Groq(api_key=groq_key)
                try:
                    transcription = client.audio.transcriptions.create(
                      file=("audio.wav", audio_input),
                      model="whisper-large-v3",
                    )
                    final_prompt = transcription.text
                except Exception as e:
                    st.error(f"Speech recognition failed: {str(e)}")
        elif audio_input and not groq_key:
            st.error("Audio recording requires the Groq Cloud API key to be active.")

        if text_prompt:
            final_prompt = text_prompt

        if final_prompt:
            st.session_state.messages.append({"role": "user", "content": final_prompt})
            
            with st.chat_message("user"):
                st.markdown(final_prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(f"Nirmay is typing in {selected_lang}..."):
                    response = query_llm(st.session_state.messages, groq_key)
                    st.markdown(response)
                    
                    audio_bytes = generate_tts(response, LANG_MAP[selected_lang])
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                        
            st.session_state.messages.append({"role": "assistant", "content": response, "audio": audio_bytes})

if __name__ == "__main__":
    main()
