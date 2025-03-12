import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from googletrans import Translator
import time

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Enhanced AI Prompts
SUMMARY_PROMPT = """You are a comprehensive YouTube video summarizer. 
Provide a detailed summary of the transcript, including:
1. Key main points
2. Important details
3. Context of the video
4. Potential insights or implications

Transcript text: """

QUESTION_PROMPT = """You are an advanced AI assistant designed to provide comprehensive answers about a YouTube video topic.

Context:
- Video Summary: {summary}
- User Question: {question}

Task: Generate a multi-faceted response that includes:
1. A direct answer based on the video summary
2. Additional contextual information from broader knowledge
3. Relevant insights, background, or related information
4. Potential follow-up areas of exploration

Guidelines:
- Use the video summary as a primary reference
- Expand beyond the summary with credible, relevant information
- Provide a well-rounded, informative response
- If the summary lacks sufficient information, clearly indicate this
- Ensure the response is coherent, informative, and engaging

Response Format:
A. Direct Video Summary Response
B. Expanded Context
C. Additional Insights
D. Potential Further Exploration

Respond in a structured, clear manner in the {language} language."""

# Language support
LANGUAGE_OPTIONS = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Japanese': 'ja',
    'Chinese (Simplified)': 'zh-cn',
    'Hindi': 'hi',
    'Arabic': 'ar',
    'Russian': 'ru',
    'Portuguese': 'pt',
    'Korean': 'ko',
    'Italian': 'it'
}

# Map of language codes to full language names
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ja': 'Japanese',
    'zh-cn': 'Chinese',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'ru': 'Russian',
    'pt': 'Portuguese',
    'ko': 'Korean',
    'it': 'Italian'
}

# Initialize the translator with retry mechanism
def get_translator():
    for _ in range(3):
        try:
            return Translator(service_urls=[
                'translate.google.com',
                'translate.google.co.kr',
                'translate.google.co.jp'
            ])
        except:
            time.sleep(1)
    # Fallback
    return Translator()

translator = get_translator()

# Initialize session state
def init_session_state():
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "video_link" not in st.session_state:
        st.session_state.video_link = ""
    if "video_title" not in st.session_state:
        st.session_state.video_title = ""
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "transcript_language" not in st.session_state:
        st.session_state.transcript_language = "en"
    if "translation_cache" not in st.session_state:
        st.session_state.translation_cache = {}
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = ""

# Extract YouTube Video ID from URL
def extract_video_id(youtube_url):
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]
        elif parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            return parse_qs(parsed_url.query).get("v", [None])[0]
        return None
    except Exception:
        return None

# Get transcript from YouTube with language support
def extract_transcript_details(youtube_video_url, language_code='en'):
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            error_msg = "Invalid YouTube URL"
            st.error(translate_ui_text(error_msg, st.session_state.language))
            return None, None

        # Fetch transcript with language options
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # Try to get the transcript in the requested language
            transcript = transcript_list.find_transcript([language_code])
            success_msg = f"Found native transcript in selected language"
            st.success(translate_ui_text(success_msg, st.session_state.language))
        except:
            try:
                # If not available, try to get auto-generated and translate it
                original_transcript = transcript_list.find_generated_transcript(['en'])
                transcript = original_transcript.translate(language_code)
                info_msg = f"Using YouTube's translated transcript"
                st.info(translate_ui_text(info_msg, st.session_state.language))
            except Exception as e:
                warning_msg = f"Could not find transcript in selected language. Using available transcript."
                st.warning(translate_ui_text(warning_msg, st.session_state.language))
                # Get any available transcript
                transcript = next(iter(transcript_list))
        
        transcript_data = transcript.fetch()
        transcript_text = " ".join([item["text"] for item in transcript_data])

        return transcript_text, video_id
    except Exception as e:
        error_msg = f"Error extracting transcript: {str(e)}"
        st.error(translate_ui_text(error_msg, st.session_state.language))
        return None, None

# More robust language detection
def is_english(text):
    if not text or len(text) < 10:
        return True
        
    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use a sample of the text for faster detection
                sample = text[:150] if len(text) > 150 else text
                detected = translator.detect(sample)
                return detected.lang == 'en'
            except Exception:
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
    except:
        return False

# Translate text using googletrans with caching and retry
def translate_text(text, target_language='en'):
    # Skip translation if not needed
    if not text or target_language == 'en' and is_english(text):
        return text
    
    # Check cache first
    cache_key = f"{text[:50]}_{target_language}"  # Use first 50 chars as key to avoid huge keys
    if cache_key in st.session_state.translation_cache:
        return st.session_state.translation_cache[cache_key]
        
    try:
        # Retry mechanism for more reliable translations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = translator.translate(text, dest=target_language)
                translated_text = result.text
                # Save to cache
                st.session_state.translation_cache[cache_key] = translated_text
                return translated_text
            except Exception:
                if attempt == max_retries - 1:
                    # Last attempt failed, return original
                    return text
                # Wait before retrying with exponential backoff
                time.sleep(1 * (attempt + 1))
    except Exception:
        return text  # Return original text if translation fails

# Helper function to translate UI text
def translate_ui_text(text, target_language='en'):
    if target_language == 'en':
        return text
    
    # Check cache
    cache_key = f"ui_{text}_{target_language}"
    if cache_key in st.session_state.translation_cache:
        return st.session_state.translation_cache[cache_key]
    
    try:
        translated = translator.translate(text, dest=target_language).text
        st.session_state.translation_cache[cache_key] = translated
        return translated
    except:
        return text

# Generate summary using Google Gemini AI
def generate_gemini_summary(transcript_text):
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        response = model.generate_content(SUMMARY_PROMPT + transcript_text)
        return response.text
    except Exception as e:
        error_msg = f"Error generating summary: {str(e)}"
        st.error(translate_ui_text(error_msg, st.session_state.language))
        return translate_ui_text("Unable to generate summary.", st.session_state.language)

# Enhanced Chatbot AI response function with direct language instruction
def get_ai_response(question, summary, target_language='en'):
    try:
        # Add language instruction directly in the prompt
        language_name = LANGUAGE_NAMES.get(target_language, 'English')
        
        # Generate response with explicit language instruction
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        formatted_prompt = QUESTION_PROMPT.format(
            summary=summary, 
            question=question,
            language=language_name
        )
        
        response = model.generate_content(formatted_prompt)
        response_text = response.text
        
        # If response not in target language, force translation
        if target_language != 'en' and is_english(response_text):
            response_text = translate_text(response_text, target_language)
            
        return response_text
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        translated_error = translate_ui_text(error_msg, target_language)
        st.error(translated_error)
        
        sorry_msg = "Sorry, I couldn't generate a comprehensive response."
        translated_sorry = translate_ui_text(sorry_msg, target_language)
        return translated_sorry

# Main Streamlit Application
def main():
    # Initialize session state
    init_session_state()

    # Main App Title
    app_title = "🎥 Multilingual YouTube Video Analyzer & Chatbot"
    st.title(translate_ui_text(app_title, st.session_state.language))
    
    # Sidebar for settings
    with st.sidebar:
        settings_header = "Settings"
        st.header(translate_ui_text(settings_header, st.session_state.language))
        
        # Transcript language selection
        transcript_label = "Select transcript language:"
        transcript_language = st.selectbox(
            translate_ui_text(transcript_label, st.session_state.language),
            options=list(LANGUAGE_OPTIONS.keys()),
            format_func=lambda x: x,
            index=list(LANGUAGE_OPTIONS.keys()).index("English")
        )
        # Store language code in session state
        st.session_state.transcript_language = LANGUAGE_OPTIONS[transcript_language]
        
        # Interface language selection
        interface_label = "Select interface language:"
        interface_language = st.selectbox(
            translate_ui_text(interface_label, st.session_state.language),
            options=list(LANGUAGE_OPTIONS.keys()),
            format_func=lambda x: x,
            index=list(LANGUAGE_OPTIONS.keys()).index("English")
        )
        # Store language code in session state
        st.session_state.language = LANGUAGE_OPTIONS[interface_language]
        
        # Clear cache button
        if st.button(translate_ui_text("Clear Translation Cache", st.session_state.language)):
            st.session_state.translation_cache = {}
            st.success(translate_ui_text("Cache cleared!", st.session_state.language))

    # YouTube Link Input
    youtube_label = "Enter YouTube Video Link:"
    youtube_link = st.text_input(
        translate_ui_text(youtube_label, st.session_state.language),
        value=st.session_state.video_link, 
        key="youtube_link_input"
    )
    
    # Store the video link in session state
    st.session_state.video_link = youtube_link

    # Display YouTube Thumbnail
    if youtube_link:
        video_id = extract_video_id(youtube_link)
        if video_id:
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

    # Generate Summary Button
    analyze_btn_text = "Analyze Video"
    if st.button(translate_ui_text(analyze_btn_text, st.session_state.language)):
        spinner_text = "Fetching transcript and generating analysis..."
        with st.spinner(translate_ui_text(spinner_text, st.session_state.language)):
            # Reset chat messages
            st.session_state.chat_messages = []
            
            # Extract transcript with selected language
            transcript_text, video_id = extract_transcript_details(youtube_link, st.session_state.transcript_language)

            if transcript_text:
                # Generate summary
                summary = generate_gemini_summary(transcript_text)
                
                # Translate summary if interface language is different
                if st.session_state.language != 'en':
                    summary = translate_text(summary, st.session_state.language)
                
                # Store summary in session state
                st.session_state.summary = summary
                st.session_state.video_title = f"YouTube Video (ID: {video_id})"
                
                # Success message
                success_msg = "Video analysis completed successfully!"
                st.success(translate_ui_text(success_msg, st.session_state.language))

    # Display Summary
    if st.session_state.summary:
        summary_title = "📌 Comprehensive Video Analysis:"
        st.markdown(f"## {translate_ui_text(summary_title, st.session_state.language)}")
        st.write(st.session_state.summary)

    # Chat Interface
    if st.session_state.summary:
        chat_title = "💬 Interactive Video Insights"
        st.markdown(f"## {translate_ui_text(chat_title, st.session_state.language)}")

        # Display existing chat messages
        for msg in st.session_state.chat_messages:
            st.chat_message("user").write(msg['question'])
            st.chat_message("assistant").write(msg['answer'])

        # Question Input
        placeholder_text = "Ask a detailed question about the video or topic"
        current_question = st.chat_input(
            translate_ui_text(placeholder_text, st.session_state.language)
        )

        # Generate Response when question is asked
        if current_question:
            # Display the user's question immediately
            st.chat_message("user").write(current_question)
            
            spinner_text = "Generating comprehensive response..."
            with st.spinner(translate_ui_text(spinner_text, st.session_state.language)):
                # Generate AI response using the selected language
                ai_response = get_ai_response(
                    current_question,
                    st.session_state.summary,
                    st.session_state.language
                )

                # Display the response
                st.chat_message("assistant").write(ai_response)

                # Add to chat history
                st.session_state.chat_messages.append({
                    'question': current_question,
                    'answer': ai_response
                })

# Run the application
if __name__ == "__main__":
    main()