from urllib.parse import urlparse, parse_qs
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(youtube_url):
    """
    Extract YouTube video ID from a given URL
    
    Args:
        youtube_url (str): YouTube video URL
    
    Returns:
        str or None: Video ID if valid, None otherwise
    """
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]
        elif parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            return parse_qs(parsed_url.query).get("v", [None])[0]
        return None
    except Exception:
        return None

def extract_transcript_details(youtube_video_url):
    """
    Extract transcript from a YouTube video
    
    Args:
        youtube_video_url (str): YouTube video URL
    
    Returns:
        tuple: (transcript_text, video_id) or (None, None)
    """
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            st.error("Invalid YouTube URL")
            return None, None

        # Fetch transcript
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_data])

        return transcript, video_id
    except Exception as e:
        st.error(f"Error extracting transcript: {str(e)}")
        return None, None