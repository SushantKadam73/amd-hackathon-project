"""GRC Platform MVP - Streamlit Frontend Entry Point.

Run with:
    streamlit run app.py --server.port 8501
"""

import streamlit as st
from app.api_client import get_frameworks, get_compliance_status, get_pending_review_count

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="GRC Platform MVP",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar() -> None:
    """Render the sidebar navigation with links to all pages."""
    st.sidebar.title("🛡️ GRC Platform")
    st.sidebar.markdown(
        "Governance, Risk, and Compliance Management"
    )
    st.sidebar.divider()

    st.sidebar.page_link("app.py", label="🏠 Home", use_container_width=True)
    st.sidebar.page_link(
        "pages/dashboard.py",
        label="📊 Dashboard",
        use_container_width=True,
    )
    st.sidebar.page_link(
        "pages/framework_library.py",
        label="📚 Framework & Control Library",
        use_container_width=True,
    )
    st.sidebar.page_link(
        "pages/evidence_library.py",
        label="📎 Evidence Management",
        use_container_width=True,
    )

    # Reviews link with notification badge
    pending_count = get_pending_review_count()
    if pending_count > 0:
        review_label = f"📋 Reviews  🔴 {pending_count}"
    else:
        review_label = "📋 Reviews"
    st.sidebar.page_link(
        "pages/reviews.py",
        label=review_label,
        use_container_width=True,
    )

    st.sidebar.page_link(
        "pages/chat.py",
        label="🤖 AI Chatbot",
        use_container_width=True,
    )
    st.sidebar.page_link(
        "pages/sessions.py",
        label="📋 Chat Sessions",
        use_container_width=True,
    )

    st.sidebar.divider()

    st.sidebar.page_link(
        "pages/audit_logs.py",
        label="📋 Audit Log",
        use_container_width=True,
    )

    st.sidebar.divider()
    st.sidebar.markdown("### System Status")

    # Fetch basic stats for sidebar
    frameworks = get_frameworks()
    framework_count = len(frameworks)

    compliance = get_compliance_status()
    if compliance:
        score = compliance.get("overall_score", 0)
        status = compliance.get("overall_status", "Not Started")
    else:
        score = 0
        status = "Not Started"

    st.sidebar.metric("Frameworks", framework_count)
    st.sidebar.metric("Compliance Score", f"{score:.1f}%", delta=status)
    st.sidebar.caption("Status shown on load")

    st.sidebar.divider()
    st.sidebar.caption("GRC Platform MVP v0.1.0")


def main() -> None:
    """Main entry point for the Streamlit frontend."""
    render_sidebar()

    st.title("🛡️ GRC Platform MVP")
    st.markdown(
        "Governance, Risk, and Compliance Management for Datacenter Companies"
    )

    # Welcome banner
    st.info(
        "Welcome to the GRC Platform MVP. "
        "This platform helps manage NIST SP 800-53 compliance "
        "for datacenter organizations. "
        "Use the sidebar to navigate between sections.",
        icon="ℹ️",
    )

    # Overview metrics
    frameworks = get_frameworks()
    framework_count = len(frameworks)
    control_count = 0

    if frameworks:
        from app.api_client import get_controls
        controls = get_controls(frameworks[0]["id"])
        control_count = len(controls)

    compliance = get_compliance_status()

    col1, col2, col3 = st.columns(3)
    with col1:
        if framework_count > 0:
            fw = frameworks[0]
            delta = f"{fw.get('name', 'NIST SP 800-53')} {fw.get('version', 'Rev 5')}"
        else:
            delta = "Not loaded"
        st.metric(label="Frameworks", value=framework_count, delta=delta)

    with col2:
        st.metric(label="Controls", value=control_count)

    with col3:
        if compliance:
            score = compliance.get("overall_score", 0)
            status = compliance.get("overall_status", "Not Started")
            st.metric(
                label="Compliance Score",
                value=f"{score:.1f}%",
                delta=status,
            )
        else:
            st.metric(label="Compliance Score", value="N/A", delta="No data")

    # Quick actions
    st.divider()
    st.subheader("Quick Actions")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.page_link(
            "pages/dashboard.py",
            label="📊 Full Dashboard",
            use_container_width=True,
        )
    with col_b:
        st.page_link(
            "pages/framework_library.py",
            label="📚 Browse Control Library",
            use_container_width=True,
        )
    with col_c:
        st.page_link(
            "pages/evidence_library.py",
            label="📎 Upload Evidence",
            use_container_width=True,
        )
    with col_d:
        st.markdown(
            "<a href='/control_detail?control_id=PE-03' target='_self' "
            "style='display:block; padding:0.5rem 1rem; "
            "background:#f0f2f6; border-radius:0.5rem; "
            "text-align:center; text-decoration:none; color:inherit; "
            "font-weight:500;'>"
            "🛡️ View PE-03 Details</a>",
            unsafe_allow_html=True,
        )

    if framework_count == 0:
        st.warning(
            "No frameworks loaded. "
            "Run `python scripts/seed_data.py` to populate the database with "
            "NIST SP 800-53 Rev 5 and its controls.",
            icon="⚠️",
        )


if __name__ == "__main__":
    main()
