import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

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

Respond in a structured, clear manner."""

TRANSLATION_PROMPT = """Translate the following text from {source_language} to {target_language}:

{text}

Provide only the translated text, with no additional comments or explanations."""

UI_STRINGS = {
    "en": {
        "title": "🎥 Multilingual YouTube Video Analyzer & Chatbot",
        "settings": "Settings",
        "select_transcript_lang": "Select transcript language:",
        "select_interface_lang": "Select interface language:",
        "enter_url": "Enter YouTube Video Link:",
        "analyze_btn": "Analyze Video",
        "loading_msg": "Fetching transcript and generating analysis...",
        "success_msg": "Video analysis completed successfully!",
        "summary_title": "📌 Comprehensive Video Analysis:",
        "chat_title": "💬 Interactive Video Insights",
        "ask_placeholder": "Ask a detailed question about the video or topic",
        "generating_msg": "Generating comprehensive response..."
    }
}

# Language support - add translations for UI elements as needed
LANGUAGE_OPTIONS = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Japanese': 'ja',
    'Chinese': 'zh',
    'Hindi': 'hi',
    'Arabic': 'ar',
    'Russian': 'ru',
    'Portuguese': 'pt',
    'Korean': 'ko',
    'Italian': 'it'
}

# Add basic UI strings for each language
for lang_code in LANGUAGE_OPTIONS.values():
    if lang_code != 'en' and lang_code not in UI_STRINGS:
        UI_STRINGS[lang_code] = UI_STRINGS['en']  # Default to English

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
            st.error("Invalid YouTube URL")
            return None, None

        # Fetch transcript with language options
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # Try to get the transcript in the requested language
            transcript = transcript_list.find_transcript([language_code])
            st.success(f"Found native transcript in selected language")
        except:
            try:
                # If not available, try to get auto-generated and translate it
                original_transcript = transcript_list.find_generated_transcript(['en'])
                transcript = original_transcript.translate(language_code)
                st.info(f"Using YouTube's translated transcript")
            except Exception as e:
                st.warning(f"Could not find transcript in selected language. Using available transcript.")
                # Get any available transcript
                transcript = next(iter(transcript_list))
        
        transcript_data = transcript.fetch()
        transcript_text = " ".join([item["text"] for item in transcript_data])

        return transcript_text, video_id
    except Exception as e:
        st.error(f"Error extracting transcript: {str(e)}")
        return None, None

# Translate text using Gemini
def translate_with_gemini(text, source_language='en', target_language='en'):
    if not text or source_language == target_language:
        return text
        
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        prompt = TRANSLATION_PROMPT.format(
            source_language=source_language,
            target_language=target_language,
            text=text
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

# Generate summary using Google Gemini AI
def generate_gemini_summary(transcript_text):
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        response = model.generate_content(SUMMARY_PROMPT + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return "Unable to generate summary."

# Enhanced Chatbot AI response function with translation
def get_ai_response(question, summary, target_language='en'):
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        
        # Ensure the question is in English for processing
        question_in_english = question
        if target_language != 'en':
            question_in_english = translate_with_gemini(question, target_language, 'en')
            
        # Ensure the summary is in English for processing
        summary_in_english = summary
        if target_language != 'en':
            summary_in_english = translate_with_gemini(summary, target_language, 'en')
        
        formatted_prompt = QUESTION_PROMPT.format(
            summary=summary_in_english, 
            question=question_in_english
        )
        
        response = model.generate_content(formatted_prompt)
        
        # Translate response if needed
        if target_language != 'en':
            return translate_with_gemini(response.text, 'en', target_language)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Sorry, I couldn't generate a comprehensive response."

# Get localized UI string
def get_ui_string(key, language='en'):
    if language in UI_STRINGS and key in UI_STRINGS[language]:
        return UI_STRINGS[language][key]
    return UI_STRINGS['en'][key]

# Main Streamlit Application
def main():
    # Initialize session state
    init_session_state()
    
    # Get current language
    current_lang = st.session_state.language

    # Main App Title
    st.title(get_ui_string('title', current_lang))
    
    # Sidebar for settings
    with st.sidebar:
        st.header(get_ui_string('settings', current_lang))
        
        # Transcript language selection
        transcript_language = st.selectbox(
            get_ui_string('select_transcript_lang', current_lang),
            options=list(LANGUAGE_OPTIONS.keys()),
            format_func=lambda x: x,
            index=list(LANGUAGE_OPTIONS.keys()).index("English")
        )
        # Store language code in session state
        st.session_state.transcript_language = LANGUAGE_OPTIONS[transcript_language]
        
        # Interface language selection
        interface_language = st.selectbox(
            get_ui_string('select_interface_lang', current_lang),
            options=list(LANGUAGE_OPTIONS.keys()),
            format_func=lambda x: x,
            index=list(LANGUAGE_OPTIONS.keys()).index("English")
        )
        # Store language code in session state
        new_lang = LANGUAGE_OPTIONS[interface_language]
        if new_lang != current_lang:
            st.session_state.language = new_lang
            st.rerun()  # Refresh to update UI language

    # YouTube Link Input
    youtube_link = st.text_input(
        get_ui_string('enter_url', current_lang),
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
    if st.button(get_ui_string('analyze_btn', current_lang)):
        with st.spinner(get_ui_string('loading_msg', current_lang)):
            # Reset chat messages
            st.session_state.chat_messages = []
            
            # Extract transcript with selected language
            transcript_text, video_id = extract_transcript_details(
                youtube_link, 
                st.session_state.transcript_language
            )

            if transcript_text:
                # Generate summary (in English initially)
                summary = generate_gemini_summary(transcript_text)
                
                # Translate summary if interface language is different
                if current_lang != 'en':
                    summary = translate_with_gemini(summary, 'en', current_lang)
                
                # Store summary in session state
                st.session_state.summary = summary
                st.session_state.video_title = f"YouTube Video (ID: {video_id})"
                
                # Success message
                st.success(get_ui_string('success_msg', current_lang))

    # Display Summary
    if st.session_state.summary:
        st.markdown(f"## {get_ui_string('summary_title', current_lang)}")
        st.write(st.session_state.summary)

    # Chat Interface
    if st.session_state.summary:
        st.markdown(f"## {get_ui_string('chat_title', current_lang)}")

        # Display existing chat messages
        for msg in st.session_state.chat_messages:
            st.chat_message("user").write(msg['question'])
            st.chat_message("assistant").write(msg['answer'])

        # Question Input
        current_question = st.chat_input(get_ui_string('ask_placeholder', current_lang))

        # Generate Response when question is asked
        if current_question:
            with st.spinner(get_ui_string('generating_msg', current_lang)):
                # Generate AI response with translation if needed
                ai_response = get_ai_response(
                    current_question, 
                    st.session_state.summary,
                    current_lang
                )

                # Add to chat history
                st.session_state.chat_messages.append({
                    'question': current_question,
                    'answer': ai_response
                })

                # Rerun to display the new message
                st.rerun()

# Run the application
if __name__ == "__main__":
    main()