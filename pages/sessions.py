"""GRC Platform - Chat Session History Page.

Displays previous chat conversations and allows resuming or deleting them.
"""

from datetime import datetime
from typing import Any

import streamlit as st
from app.api_client import get_agent_sessions, delete_agent_session

# Page configuration
st.set_page_config(
    page_title="Session History - GRC Platform",
    page_icon="📋",
    layout="wide",
)


def format_session_time(iso_str: Any) -> str:
    """Format an ISO datetime string for display.

    Args:
        iso_str: ISO datetime string or None.

    Returns:
        Formatted time string.
    """
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo if dt.tzinfo else None)
        if dt.date() == now.date():
            return f"Today at {dt.strftime('%I:%M %p')}"
        elif (now - dt).days == 1:
            return f"Yesterday at {dt.strftime('%I:%M %p')}"
        else:
            return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return str(iso_str)[:19] if iso_str else "Unknown"


def render_session_row(session: dict[str, Any], index: int) -> None:
    """Render a single session row in the table.

    Args:
        session: Session dict with id, memory_summary, started_at.
        index: Row index for unique key generation.
    """
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    session_id = session.get("id", "")
    summary = session.get("memory_summary", "No summary available")
    started_at = session.get("started_at", "")
    session_type = session.get("session_type", "grc_chatbot")

    # Truncate summary for display
    display_summary = (summary[:80] + "...") if len(summary) > 80 else summary
    if not summary:
        display_summary = "No messages"

    with col1:
        st.markdown(f"**{display_summary}**")

    with col2:
        st.caption(f"Type: {session_type}")

    with col3:
        formatted_time = format_session_time(started_at)
        st.caption(formatted_time)

    with col4:
        # Resume button - set query param then navigate
        resume_key = f"resume_{index}_{session_id}"
        if st.button("▶️ Resume", key=resume_key, use_container_width=True):
            st.query_params["session_id"] = session_id
            st.switch_page("pages/chat.py")

        # Delete button
        delete_key = f"delete_{index}_{session_id}"
        if st.button("🗑️", key=delete_key, help="Delete this session"):
            if delete_agent_session(session_id):
                st.success("Session deleted.")
                st.rerun()
            else:
                st.error("Failed to delete session.")


def main() -> None:
    """Main entry point for the session history page."""
    st.title("📋 Chat Session History")

    # Back to chat button
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown("View and resume your previous chat conversations.")
    with col_right:
        st.page_link("pages/chat.py", label="← Back to Chat", use_container_width=True)

    st.divider()

    # Fetch sessions from API
    with st.spinner("Loading sessions..."):
        sessions = get_agent_sessions(limit=100, offset=0)

    if not sessions:
        # Empty state
        st.info(
            "No chat sessions yet. "
            "Start a conversation with the GRC Compliance Chatbot to see your history here.",
            icon="💬",
        )
        st.page_link("pages/chat.py", label="Start a New Chat →", use_container_width=False)
        return

    # Summary stats
    total = len(sessions)
    st.markdown(f"**{total} session(s)** found")

    # Render sessions
    st.divider()

    for i, session in enumerate(sessions):
        render_session_row(session, i)
        if i < len(sessions) - 1:
            st.divider()


if __name__ == "__main__":
    main()
