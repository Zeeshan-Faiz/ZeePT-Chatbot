import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface

st.markdown(
    """
    <style>
    @media (prefers-color-scheme: dark) {
        .themed-box {
            border: 1px solid #4F8BF9;
            background-color: #1e1e2f;
            color: #e0e0e0;
        }
    }

    @media (prefers-color-scheme: light) {
        .themed-box {
            border: 1px solid #cce0ff;
            background-color: #f5faff;
            color: #333333;
        }
    }
    </style>

    <div class="themed-box" style='
        border-radius: 30px;
        padding: 10px 20px;
        margin-bottom: 10px;
        text-align: center;
    '>
        <h1 style='font-family: "Segoe UI", sans-serif;'>ZeePT AI Assistant 🤖</h1>
        <p style='font-size:16px;'>Upload files, ask questions and get accurate answers that are fast, secure and always reliable. </p>
    </div>
    """,
    unsafe_allow_html=True
)


# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Display the sidebar
display_sidebar()

# Display the chat interface
display_chat_interface()