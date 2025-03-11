import streamlit as st
import google.generativeai as genai
from prompts import SUMMARY_PROMPT, QUESTION_PROMPT

def generate_gemini_summary(transcript_text):
    """
    Generate summary using Google Gemini AI
    
    Args:
        transcript_text (str): Video transcript
    
    Returns:
        str: Generated summary
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        response = model.generate_content(SUMMARY_PROMPT + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return "Unable to generate summary."

def get_ai_response(question, summary):
    """
    Generate comprehensive AI response
    
    Args:
        question (str): User's question
        summary (str): Video summary
    
    Returns:
        str: AI-generated response
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        formatted_prompt = QUESTION_PROMPT.format(summary=summary, question=question)
        response = model.generate_content(formatted_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Sorry, I couldn't generate a comprehensive response."