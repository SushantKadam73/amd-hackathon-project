"""GRC Platform - Chatbot Interface Page.

Provides an interactive chat interface for GRC compliance questions.
Features:
- Chat interface with message input, send button, and chat history
- Welcome message describing capabilities and 5 in-scope controls
- User messages right-aligned, chatbot responses left-aligned with timestamps
- Loading/typing indicator while processing
- Multi-turn conversation with context via session_id
- Session persistence to agent_sessions table
- Empty query and unrelated question handling
"""

from datetime import datetime
from typing import Any, Optional

import streamlit as st
from app.api_client import send_chat_message, get_agent_session

# Page configuration
st.set_page_config(
    page_title="AI Chatbot - GRC Platform",
    page_icon="🤖",
    layout="wide",
)

# =============================================================================
# Constants
# =============================================================================

WELCOME_MESSAGE = (
    "👋 **Welcome to the GRC Compliance Chatbot!**\n\n"
    "I can help you with NIST SP 800-53 compliance questions for datacenter companies. "
    "Here's what I can do:\n\n"
    "📋 **Explain Controls** — Ask about any of the 5 in-scope controls:\n"
    "   • **PE-03** (Physical Access Control)\n"
    "   • **AC-02** (Account Management)\n"
    "   • **SC-07** (Boundary Protection)\n"
    "   • **IR-06** (Incident Reporting)\n"
    "   • **RA-05** (Vulnerability Scanning)\n\n"
    "📎 **Evidence Guidance** — Ask what evidence you need for any control\n"
    "📊 **Gap Analysis** — Ask about your compliance gaps\n"
    "✅ **Recommendations** — Get actionable compliance improvement tips\n\n"
    "Just type your question below to get started!"
)

UNRELATED_KEYWORDS = [
    "weather", "sports", "game", "movie", "recipe", "cooking",
    "music", "song", "celebrity", "news today", "politics",
    "stock price", "cryptocurrency", "bitcoin", "joke", "poem",
    "story", "dance", "fashion",
]

# =============================================================================
# Custom CSS for Chat Styling
# =============================================================================

CUSTOM_CSS = """
<style>
    .chat-timestamp-user {
        font-size: 0.7rem;
        color: #aaa;
        text-align: right;
        margin-top: 0.1rem;
    }
    .chat-timestamp-assistant {
        font-size: 0.7rem;
        color: #aaa;
        text-align: left;
        margin-top: 0.1rem;
    }
    .welcome-card {
        background-color: #f0f7ff;
        border: 1px solid #d0e3ff;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
"""


# =============================================================================
# Session State Initialization
# =============================================================================


def init_session_state() -> None:
    """Initialize the chat session state variables."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "chat_session_id" not in st.session_state:
        params = st.query_params
        st.session_state.chat_session_id = params.get("session_id", None)

    if "chat_processing" not in st.session_state:
        st.session_state.chat_processing = False

    # Load session messages when resuming (only on first load)
    if (
        st.session_state.chat_session_id
        and not st.session_state.chat_messages
    ):
        _load_session_messages(st.session_state.chat_session_id)


def _load_session_messages(session_id: str) -> None:
    """Load previous messages from a session when resuming.

    Args:
        session_id: The session UUID to load messages for.
    """
    try:
        session_data = get_agent_session(session_id)
        if session_data:
            messages = session_data.get("messages", [])
            # Parse stored messages into chat format
            for msg in messages:
                role = msg.get("role", "assistant")
                content = msg.get("content", "")
                ts_str = msg.get("timestamp")
                timestamp: Optional[datetime] = None
                if ts_str:
                    try:
                        timestamp = datetime.fromisoformat(
                            str(ts_str).replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        timestamp = None

                st.session_state.chat_messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                })
    except Exception:
        # Silently fail - user can start fresh
        pass


# =============================================================================
# Helper Functions
# =============================================================================


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime for display in chat.

    Args:
        dt: Datetime object to format.

    Returns:
        Formatted time string like "2:30 PM" or "Yesterday 2:30 PM".
    """
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%I:%M %p")
    elif (now - dt).days == 1:
        return f"Yesterday {dt.strftime('%I:%M %p')}"
    else:
        return dt.strftime("%b %d, %I:%M %p")


def is_unrelated_query(text: str) -> bool:
    """Check if a query is clearly unrelated to GRC compliance.

    Args:
        text: The user's input text.

    Returns:
        True if the query appears unrelated.
    """
    text_lower = text.lower().strip()
    for keyword in UNRELATED_KEYWORDS:
        if text_lower == keyword or text_lower.startswith(keyword + " "):
            return True
    return False


def reset_chat() -> None:
    """Clear chat state to start a new conversation."""
    st.session_state.chat_messages = []
    st.session_state.chat_session_id = None
    st.session_state.chat_processing = False
    # Clear query params so next load doesn't resume a session
    st.query_params.clear()
    st.rerun()


# =============================================================================
# Main Chat Interface
# =============================================================================


def main() -> None:
    """Main entry point for the chat page."""
    st.title("🤖 GRC Compliance Chatbot")

    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Initialize session state
    init_session_state()

    # ========================
    # Sidebar
    # ========================
    with st.sidebar:
        st.markdown("### Chat Controls")
        if st.button("🆕 New Chat", use_container_width=True):
            reset_chat()

        st.divider()
        st.markdown("### Previous Sessions")
        st.page_link(
            "pages/sessions.py",
            label="📋 View Session History",
            use_container_width=True,
        )

        st.divider()
        st.markdown("### Quick Questions")
        quick_questions = [
            "What is PE-03?",
            "What evidence do I need for AC-02?",
            "What are my gaps for IR-06?",
            "How can I improve RA-05 compliance?",
        ]
        for q in quick_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                if not st.session_state.chat_processing:
                    st.session_state.chat_processing = True
                    st.session_state._quick_question = q
                    st.rerun()

    # ========================
    # Display chat messages
    # ========================
    if not st.session_state.chat_messages:
        # Show welcome card when no messages exist
        st.markdown(
            f'<div class="welcome-card">{WELCOME_MESSAGE}</div>',
            unsafe_allow_html=True,
        )
    else:
        # Render all existing messages
        for msg in st.session_state.chat_messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            timestamp: Optional[datetime] = msg.get("timestamp")

            with st.chat_message(role):
                st.markdown(content)
                if timestamp:
                    ts_cls = "chat-timestamp-user" if role == "user" else "chat-timestamp-assistant"
                    st.markdown(
                        f'<div class="{ts_cls}">{_format_timestamp(timestamp)}</div>',
                        unsafe_allow_html=True,
                    )

    # ========================
    # Process queued quick question
    # ========================
    if st.session_state.get("_quick_question"):
        question = st.session_state.pop("_quick_question")
        _process_and_display_response(question)

    # ========================
    # Handle processing state (show spinner)
    # ========================
    if st.session_state.chat_processing:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Wait for the processing to complete
                # The response was already added in _process_and_display_response
                pass

    # ========================
    # Chat input
    # ========================
    user_input = st.chat_input(
        "Ask a GRC compliance question...",
        key="chat_input_widget",
        disabled=st.session_state.chat_processing,
    )

    if user_input and not st.session_state.chat_processing:
        _process_and_display_response(user_input)


def _process_and_display_response(user_text: str) -> None:
    """Process a user message: display it, call API, and show response.

    Args:
        user_text: The user's message text.
    """
    if not user_text or not user_text.strip():
        st.warning("Please type a question to get started.")
        st.session_state.chat_processing = False
        return

    trimmed = user_text.strip()

    # Add user message
    now = datetime.now()
    st.session_state.chat_messages.append({
        "role": "user",
        "content": trimmed,
        "timestamp": now,
    })

    # Set processing flag (shows spinner on next render)
    st.session_state.chat_processing = True

    if is_unrelated_query(trimmed):
        # Handle unrelated query locally - polite redirect
        response_msg = (
            "I'm focused on GRC compliance topics related to NIST SP 800-53 "
            "and datacenter security. Please ask me about controls, evidence, "
            "or compliance requirements."
        )
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_msg,
            "timestamp": datetime.now(),
        })
        st.session_state.chat_processing = False
        st.rerun()
        return

    # Call the API
    session_id = st.session_state.chat_session_id
    result = send_chat_message(
        message=trimmed,
        session_id=session_id,
    )

    if result:
        # Save session ID for subsequent messages
        new_sid = result.get("session_id")
        if new_sid:
            st.session_state.chat_session_id = new_sid

        response_text = result.get("response", "")
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(),
        })
    else:
        # API call failed; remove the user message so they can retry
        st.session_state.chat_messages.pop()

    st.session_state.chat_processing = False
    st.rerun()


if __name__ == "__main__":
    main()
