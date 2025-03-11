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

# Get transcript from YouTube
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            st.error("Invalid YouTube URL")
            return None, None

        # Fetch transcript
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_data])

        # Attempt to get video title (this might require YouTube Data API, which is not implemented here)
        video_title = "YouTube Video"

        return transcript, video_title
    except Exception as e:
        st.error(f"Error extracting transcript: {str(e)}")
        return None, None

# Generate summary using Google Gemini AI
def generate_gemini_summary(transcript_text):
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        response = model.generate_content(SUMMARY_PROMPT + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return "Unable to generate summary."

# Enhanced Chatbot AI response function
def get_ai_response(question, summary):
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        formatted_prompt = QUESTION_PROMPT.format(summary=summary, question=question)
        response = model.generate_content(formatted_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Sorry, I couldn't generate a comprehensive response."

# Main Streamlit Application
def main():
    # Initialize session state
    init_session_state()

    # Main App Title
    st.title("🎥 Advanced YouTube Video Analyzer & Chatbot")

    # YouTube Link Input
    youtube_link = st.text_input("Enter YouTube Video Link:", 
                                 value=st.session_state.video_link, 
                                 key="youtube_link_input")
    
    # Store the video link in session state
    st.session_state.video_link = youtube_link

    # Display YouTube Thumbnail
    if youtube_link:
        video_id = extract_video_id(youtube_link)
        if video_id:
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

    # Generate Summary Button
    if st.button("Analyze Video"):
        with st.spinner("Fetching transcript and generating comprehensive analysis..."):
            # Reset chat messages
            st.session_state.chat_messages = []
            
            # Extract transcript
            transcript_text, video_title = extract_transcript_details(youtube_link)

            if transcript_text:
                # Generate summary
                summary = generate_gemini_summary(transcript_text)
                
                # Store summary in session state
                st.session_state.summary = summary
                st.session_state.video_title = video_title
                
                # Success message
                st.success("Video analysis completed successfully!")

    # Display Summary
    if st.session_state.summary:
        st.markdown("## 📌 Comprehensive Video Analysis:")
        st.write(st.session_state.summary)

    # Chat Interface
    if st.session_state.summary:
        st.markdown("## 💬 Interactive Video Insights")

        # Display existing chat messages
        for msg in st.session_state.chat_messages:
            st.chat_message("user").write(msg['question'])
            st.chat_message("assistant").write(msg['answer'])

        # Question Input
        current_question = st.chat_input("Ask a detailed question about the video or topic")

        # Generate Response when question is asked
        if current_question:
            with st.spinner("Generating comprehensive response..."):
                # Generate AI response
                ai_response = get_ai_response(current_question, st.session_state.summary)

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