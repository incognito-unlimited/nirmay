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

UI_TEXT = {
    "English": {
        "title": "🌿 Nirmay: Rural Health Report Simplifier",
        "description": "Upload your medical report and let Nirmay help you understand it simply and gently.",
        "lang_settings": "🌐 Language Settings",
        "select_lang": "Select your language / अपनी भाषा चुनें:",
        "reset_session": "Reset Session",
        "upload_report": "Upload your Medical Report (PDF)",
        "reading": "Reading & simplifying your report... Please wait.",
        "read_error": "We couldn't read any text from this file. Please try a clearer document.",
        "success": "Report successfully processed!",
        "ask_question": "Ask a question in English...",
        "voice_input": "🗣️ Voice Input",
        "transcribing": "Transcribing audio...",
        "audio_error": "Audio recording requires the Groq Cloud API key to be active.",
        "typing": "Nirmay is typing in English..."
    },
    "Hindi": {
        "title": "🌿 निर्मय: ग्रामीण स्वास्थ्य रिपोर्ट सरलीकृत",
        "description": "अपनी मेडिकल रिपोर्ट अपलोड करें और निर्मय को इसे सरलता और सौम्यता से समझने में आपकी मदद करने दें।",
        "lang_settings": "🌐 भाषा सेटिंग्स",
        "select_lang": "Select your language / अपनी भाषा चुनें:",
        "reset_session": "सत्र रीसेट करें",
        "upload_report": "अपनी मेडिकल रिपोर्ट (PDF) अपलोड करें",
        "reading": "आपकी रिपोर्ट पढ़ी और सरल की जा रही है... कृपया प्रतीक्षा करें।",
        "read_error": "हम इस फ़ाइल से कोई पाठ नहीं पढ़ सके। कृपया अधिक स्पष्ट दस्तावेज़ आज़माएं।",
        "success": "रिपोर्ट सफलतापूर्वक संसाधित हो गई!",
        "ask_question": "हिंदी में कोई प्रश्न पूछें...",
        "voice_input": "🗣️ वॉयस इनपुट",
        "transcribing": "ऑडियो ट्रांसक्राइब किया जा रहा है...",
        "audio_error": "ऑडियो रिकॉर्डिंग के लिए Groq Cloud API कुंजी सक्रिय होनी चाहिए।",
        "typing": "निर्मय हिंदी में टाइप कर रहा है..."
    },
    "Tamil": {
        "title": "🌿 நிர்மெய்: கிராமப்புற சுகாதார அறிக்கை எளிமைப்படுத்தி",
        "description": "உங்கள் மருத்துவ அறிக்கையைப் பதிவேற்றவும், அதை எளிமையாகவும் மென்மையாகவும் புரிந்துகொள்ள நிர்மெய் உங்களுக்கு உதவட்டும்.",
        "lang_settings": "🌐 மொழி அமைப்புகள்",
        "select_lang": "Select your language / अपनी भाषा चुनें:",
        "reset_session": "அமர்வை மீட்டமை",
        "upload_report": "உங்கள் மருத்துவ அறிக்கையை பதிவேற்றவும் (PDF)",
        "reading": "உங்கள் அறிக்கையைப் படித்து எளிமையாக்குகிறது... தயவுசெய்து காத்திருக்கவும்.",
        "read_error": "இந்தக் கோப்பிலிருந்து எங்களால் எந்த உரையையும் படிக்க முடியவில்லை. தெளிவான ஆவணத்தை முயற்சிக்கவும்.",
        "success": "அறிக்கை வெற்றிகரமாகச் செயலாக்கப்பட்டது!",
        "ask_question": "தமிழில் ஒரு கேள்வி கேளுங்கள்...",
        "voice_input": "🗣️ குரல் உள்ளீடு",
        "transcribing": "ஆடியோ டிரான்ஸ்கிரைப் செய்யப்படுகிறது...",
        "audio_error": "ஆடியோ பதிவுக்கு Groq கிளவுட் API விசை செயலில் இருக்க வேண்டும்.",
        "typing": "நிர்மெய் தமிழில் தட்டச்சு செய்கிறார்..."
    },
    "Telugu": {
        "title": "🌿 నిర్మయ్: గ్రామీణ ఆరోగ్య నివేదిక సరళీకృత",
        "description": "మీ వైద్య నివేదికను అప్‌లోడ్ చేయండి మరియు దాన్ని సరళంగా మరియు సున్నితంగా అర్థం చేసుకోవడంలో నిర్మయ్ మీకు సహాయం చేయనివ్వండి.",
        "lang_settings": "🌐 భాష సెట్టింగులు",
        "select_lang": "Select your language / अपनी भाषा चुनें:",
        "reset_session": "సెషన్‌ను రీసెట్ చేయండి",
        "upload_report": "మీ వైద్య నివేదికను అప్‌లోడ్ చేయండి (PDF)",
        "reading": "మీ నివేదికను చదువుతోంది మరియు సరళీకృతం చేస్తోంది... దయచేసి వేచి ఉండండి.",
        "read_error": "మేము ఈ ఫైల్ నుండి ఏ వచానాన్ని చదవలేకపోయాము. దయచేసి స్పష్టమైన పత్రాన్ని ప్రయత్నించండి.",
        "success": "నివేదిక విజయవంతంగా ప్రాసెస్ చేయబడింది!",
        "ask_question": "తెలుగులో ఒక ప్రశ్న అడగండి...",
        "voice_input": "🗣️ వాయిస్ ఇన్‌పుట్",
        "transcribing": "ఆడియో ట్రాన్స్‌క్రైబ్ చేయబడుతోంది...",
        "audio_error": "ఆడియో రికార్డింగ్‌కు Groq క్లౌడ్ API కీ చురుకుగా ఉండాలి.",
        "typing": "నిర్మయ్ తెలుగులో టైప్ చేస్తున్నారు..."
    },
    "Bengali": {
        "title": "🌿 নির্মেয়: গ্রামীণ স্বাস্থ্য প্রতিবেদন সরলীকৃত",
        "description": "আপনার মেডিকেল রিপোর্ট আপলোড করুন এবং নির্মেয় আপনাকে এটি সহজ ও নম্রভাবে বুঝতে সাহায্য করুক।",
        "lang_settings": "🌐 ভাষা সেটিংস",
        "select_lang": "Select your language / अपनी भाषा चुनें:",
        "reset_session": "সেশন রিসেট করুন",
        "upload_report": "আপনার মেডিকেল রিপোর্ট আপলোড করুন (PDF)",
        "reading": "আপনার প্রতিবেদন পড়া এবং সহজ করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।",
        "read_error": "আমরা এই ফাইল থেকে কোনো লেখা পড়তে পারিনি। অনুগ্রহ করে একটি পরিষ্কার নথি চেষ্টা করুন।",
        "success": "প্রতিবেদন সফলভাবে প্রক্রিয়া করা হয়েছে!",
        "ask_question": "বাংলায় একটি প্রশ্ন জিজ্ঞাসা করুন...",
        "voice_input": "🗣️ ভয়েস ইনপুট",
        "transcribing": "অডিও প্রতিলিপি করা হচ্ছে...",
        "audio_error": "অডিও রেকর্ডিংয়ের জন্য গ্রোক ক্লাউড এপিআই কী সক্রিয় থাকতে হবে।",
        "typing": "নির্মেয় বাংলায় টাইপ করছে..."
    }
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
    # Clean messages (Remove raw bytes like TTS audio before sending to JSON-based LLM APIs)
    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    # Attempt Primary Engine: Local Ollama (llama3.1:8b)
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "llama3.1:8b",
                "messages": clean_messages,
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
                messages=clean_messages,
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
    # Set default language temporarily until sidebar renders
    current_ui = st.session_state.get('current_ui', UI_TEXT["English"])
    
    st.title(current_ui["title"])
    st.markdown(current_ui["description"])
    
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
        st.header(current_ui["lang_settings"])
        selected_lang = st.selectbox(
            current_ui["select_lang"], 
            options=list(LANG_MAP.keys()), 
            index=list(LANG_MAP.keys()).index(st.session_state.get('current_lang', "English"))
        )
        current_ui = UI_TEXT[selected_lang]
        st.session_state.current_ui = current_ui
        
        st.divider()
        st.header(current_ui["voice_input"])
        audio_input = audio_recorder(text="🎙️", recording_color="#cc0000", neutral_color="#0066cc", icon_size="2x")
        
        st.divider()
        # Reset conversation
        if st.button(current_ui["reset_session"]) and st.session_state.get('report_processed', False):

            st.session_state.messages = [{"role": "system", "content": get_system_prompt(selected_lang)}]
            st.session_state.report_processed = False
            st.rerun()

    # Initialize session state variables
    if "current_lang" not in st.session_state or st.session_state.current_lang != selected_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.current_ui = current_ui
        # If language changes, update the system prompt but keep conversation if active?
        # Better to reset conversation if language fundamentally changes, or just let future messages translate.
        if "messages" not in st.session_state or not st.session_state.get("report_processed", False):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(selected_lang)}]
        else:
            # Update the very first message silently so instructions update for follow-ups
            st.session_state.messages[0] = {"role": "system", "content": get_system_prompt(selected_lang)}
        st.rerun()

    if "report_processed" not in st.session_state:
        st.session_state.report_processed = False

    # --- File Upload Section ---
    if not st.session_state.report_processed:
        uploaded_file = st.file_uploader(current_ui["upload_report"], type=["pdf"])
        
        if uploaded_file is not None:
            with st.spinner(current_ui["reading"]):
                report_text = extract_text_from_pdf(uploaded_file)
                
                if not report_text:
                    st.error(current_ui["read_error"])
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
        st.success(current_ui["success"])
        
        # Display chat history (skipping the underlying system prompt and initial raw injection)
        for message in st.session_state.messages[2:]: # Skip system prompt and the raw OCR insertion
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("audio"):
                    st.audio(message["audio"], format="audio/mp3")

        # Accept follow-up user input via text
        text_prompt = st.chat_input(current_ui["ask_question"])
            
        final_prompt = None
        
        # Voice transcription via Groq Whisper Fallback (Requires Groq Key)
        if audio_input and groq_key:
            with st.spinner(current_ui["transcribing"]):
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
            st.error(current_ui["audio_error"])

        if text_prompt:
            final_prompt = text_prompt

        if final_prompt:
            st.session_state.messages.append({"role": "user", "content": final_prompt})
            
            with st.chat_message("user"):
                st.markdown(final_prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(current_ui["typing"]):
                    response = query_llm(st.session_state.messages, groq_key)
                    st.markdown(response)
                    
                    audio_bytes = generate_tts(response, LANG_MAP[selected_lang])
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                        
            st.session_state.messages.append({"role": "assistant", "content": response, "audio": audio_bytes})

if __name__ == "__main__":
    main()
