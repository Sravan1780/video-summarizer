import streamlit as st

def set_advanced_styling():
    st.markdown("""
    <style>
    /* Global Reset and Base Styling */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    /* Dark Mode Inspired Background */
    .stApp {
        background-color: #0f1117;
        color: #e1e4e8;
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }

    /* Container Styling */
    .main-container {
        background-color: #1e2330;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }

    /* Responsive Typography */
    .main-title {
        font-size: 2.5rem;
        color: #58a6ff;
        text-align: center;
        margin-bottom: 25px;
        font-weight: 700;
        text-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Input Styling */
    .stTextInput > div > div > input {
        background-color: #2c3142;
        color: #e1e4e8;
        border: 2px solid #444c5c;
        border-radius: 10px;
        padding: 12px 15px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #58a6ff;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.2);
    }

    /* Button Styling */
    .stButton > button {
        background-color: #2ea44f;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #2c974b;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* Chat Interface Styling */
    .chat-container {
        background-color: #1e2330;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }

    .user-message {
        background-color: #2c3142;
        color: #e1e4e8;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
    }

    .ai-message {
        background-color: #2c3e50;
        color: #e1e4e8;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
    }

    /* Spinner and Progress Styling */
    .stSpinner > div {
        border-color: #58a6ff transparent #58a6ff transparent;
    }

    /* Responsive Image */
    .stImage {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }

    /* Summary Container */
    .summary-container {
        background-color: #2c3142;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)