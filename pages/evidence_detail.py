"""GRC Platform - Evidence Detail Page.

Displays full evidence artifact metadata including:
1. Full metadata (name, file type, file size, upload date)
2. Content text preview (first 500 characters)
3. Checksum
4. All control mappings with their statuses
"""

from typing import Any, Optional

import streamlit as st

from app.api_client import (
    get_evidence_detail,
    get_evidence_mappings,
    analyze_evidence_ai,
    suggest_mapping_ai,
)

# Page configuration
st.set_page_config(
    page_title="Evidence Detail - GRC Platform",
    page_icon="📎",
    layout="wide",
)


def _get_status_color(status: str) -> str:
    """Get display color for a mapping status.

    Args:
        status: Mapping status string.

    Returns:
        CSS color string.
    """
    colors = {
        "approved": "green",
        "pending": "orange",
        "rejected": "red",
        "unmapped": "gray",
    }
    return colors.get(status, "gray")


def _get_relevance_color(score: float) -> str:
    """Get display color for a relevance score (0-100).

    Args:
        score: Relevance score from 0 to 100.

    Returns:
        CSS color string: green for >70, yellow for 40-70, red for <40.
    """
    if score > 70:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"


def _format_file_size(size_bytes: Optional[int]) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted size string (e.g., '1.5 MB').
    """
    if size_bytes is None:
        return "Unknown"

    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _render_metadata_section(evidence: dict[str, Any]) -> None:
    """Render the evidence artifact metadata section.

    Args:
        evidence: Evidence artifact dict from API.
    """
    st.subheader("📋 Metadata")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Name", evidence.get("name", "—"))
        st.metric("File Type", evidence.get("file_type", "—").upper())

    with col2:
        file_size = evidence.get("file_size")
        st.metric("File Size", _format_file_size(file_size))
        uploaded_at = evidence.get("uploaded_at", "")
        if uploaded_at:
            st.metric("Upload Date", uploaded_at[:10])
        else:
            st.metric("Upload Date", "—")

    with col3:
        st.metric(
            "Evidence ID",
            evidence.get("id", "—")[:8] + "...",
            help=f"Full ID: {evidence.get('id', '')}",
        )
        uploaded_by = evidence.get("uploaded_by")
        if uploaded_by:
            st.metric("Uploaded By", uploaded_by[:8] + "...")
        else:
            st.metric("Uploaded By", "System")


def _render_content_preview(evidence: dict[str, Any]) -> None:
    """Render the content text preview (first 500 chars).

    Args:
        evidence: Evidence artifact dict from API.
    """
    st.subheader("📝 Content Preview")

    content_text = evidence.get("content_text")

    if content_text:
        preview = content_text[:500]
        st.text_area(
            "Extracted text content (first 500 characters)",
            value=preview,
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )
        if len(content_text) > 500:
            st.caption(
                f"*Showing first 500 of {len(content_text)} characters*"
            )
    else:
        file_type = evidence.get("file_type", "").lower()
        if file_type in ("png", "jpg", "jpeg"):
            st.info(
                "Content text extraction is not available for image files. "
                "OCR text extraction can be enabled with pytesseract.",
                icon="🖼️",
            )
        else:
            st.info(
                "No content text was extracted from this file. "
                "This may occur with scanned documents or "
                "encrypted files.",
                icon="ℹ️",
            )


def _render_checksum_section(evidence: dict[str, Any]) -> None:
    """Render the file checksum section.

    Args:
        evidence: Evidence artifact dict from API.
    """
    st.subheader("🔐 File Checksum")

    checksum = evidence.get("checksum")
    if checksum:
        st.code(checksum, language="text")
        st.caption("SHA-256 checksum for file integrity verification")
    else:
        st.info("No checksum computed for this artifact.", icon="ℹ️")


def _render_mappings_section(
    evidence_id: str,
    mappings: list[dict[str, Any]],
) -> None:
    """Render the control mappings section.

    Args:
        evidence_id: UUID of the evidence artifact.
        mappings: List of mapping dicts.
    """
    st.subheader("🔗 Control Mappings")

    if not mappings:
        st.info(
            "This evidence artifact has not been mapped to any controls. "
            "Go to the evidence library to create mappings.",
            icon="🔗",
        )
        return

    for mapping in mappings:
        status = mapping.get("mapping_status", "pending")
        status_color = _get_status_color(status)

        with st.container(border=True):
            cols = st.columns([2, 2, 1.5, 1, 1])

            with cols[0]:
                control_ref = mapping.get("control_ref_id", "")
                control_title = mapping.get("control_title", "")
                st.markdown(f"**{control_ref}**")
                st.caption(control_title)
            with cols[1]:
                st.markdown(f"**Artifact Type:** {mapping.get('artifact_type', '—')}")
            with cols[2]:
                st.markdown(
                    f"**Weightage:** {mapping.get('weightage', 0):.1f}%"
                )
            with cols[3]:
                st.markdown(
                    f"<span style='color:{status_color};font-weight:bold;'>"
                    f"{status.title()}</span>",
                    unsafe_allow_html=True,
                )
            with cols[4]:
                mapped_at = mapping.get("mapped_at", "")
                if mapped_at:
                    st.caption(mapped_at[:10])
                else:
                    st.caption("—")

        # Show mapping ID for reference
        st.caption(f"Mapping ID: `{mapping.get('id', '')[:8]}...`")


def _render_ai_analysis_section(
    evidence_id: str,
    evidence: dict[str, Any],
) -> None:
    """Render the AI analysis section with Analyze button and results.

    Args:
        evidence_id: UUID of the evidence artifact.
        evidence: Evidence artifact dict from API.
    """
    st.subheader("🤖 AI Analysis")

    # Analyze button
    if st.button(
        "🔍 Analyze with AI",
        key="analyze_evidence_btn",
        help="Run AI analysis to assess control relevance and quality",
        type="primary",
    ):
        with st.spinner("Running AI analysis..."):
            analysis = analyze_evidence_ai(evidence_id)

        if analysis:
            st.session_state["ai_analysis"] = analysis

    # Display results if available (either just computed or from session state)
    analysis = st.session_state.get("ai_analysis")

    if analysis:
        # Requires Review indicator
        if analysis.get("requires_review", True):
            st.warning(
                "⚠️ **Requires Review** - This analysis has low confidence "
                f"({analysis.get('confidence', 0):.0%}) and needs human verification."
            )
        else:
            st.success(
                f"✅ Analysis complete (confidence: {analysis.get('confidence', 0):.0%})"
            )

        # Control Relevance Scores
        st.markdown("#### Control Relevance Scores")
        relevance_scores = analysis.get("relevance_scores", [])

        cols = st.columns(len(relevance_scores) if relevance_scores else 1)
        for idx, score_data in enumerate(relevance_scores):
            control_id = score_data.get("control_id", "")
            score = score_data.get("score", 0)
            color = _get_relevance_color(score)

            with cols[idx]:
                st.metric(
                    label=control_id,
                    value=f"{score:.0f}/100",
                )
                # Color bar indicator
                st.markdown(
                    f"<div style='background-color:{color};height:8px;"
                    f"border-radius:4px;margin-top:4px;'></div>",
                    unsafe_allow_html=True,
                )

        st.divider()

        # Artifact Type & Quality Assessment
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"**Suggested Artifact Type:** "
                f"{analysis.get('suggested_artifact_type', '—')}"
            )
        with col2:
            st.markdown(
                f"**Quality Assessment:** "
                f"{analysis.get('quality_assessment', '—')}"
            )

        # Currency Check
        currency = analysis.get("currency", {})
        currency_status = currency.get("status", "unknown")
        currency_detail = currency.get("detail", "")

        if currency_status == "stale":
            st.warning(
                f"📅 **Document Currency: Stale** - {currency_detail}"
            )
        elif currency_status == "current":
            st.info(f"📅 **Document Currency: Current** - {currency_detail}")
        else:
            st.info(f"📅 **Document Currency: Unknown** - {currency_detail}")

        # Most relevant control
        most_relevant = analysis.get("most_relevant_control", "—")
        st.info(f"🎯 **Most Relevant Control:** {most_relevant}")

    else:
        st.info(
            "Click 'Analyze with AI' to assess control relevance, "
            "artifact type, and document quality.",
            icon="ℹ️",
        )


def _render_mapping_suggestion_section(
    evidence_id: str,
    evidence: dict[str, Any],
) -> None:
    """Render the mapping suggestion section.

    Args:
        evidence_id: UUID of the evidence artifact.
        evidence: Evidence artifact dict from API.
    """
    st.subheader("💡 Mapping Suggestions")

    if st.button(
        "🔮 Suggest Mappings",
        key="suggest_mapping_btn",
        help="Get AI-suggested control mappings with confidence scores",
    ):
        with st.spinner("Generating mapping suggestions..."):
            suggestions = suggest_mapping_ai(evidence_id)

        if suggestions:
            st.session_state["mapping_suggestions"] = suggestions

    # Display suggestions if available
    suggestions_data = st.session_state.get("mapping_suggestions")

    if suggestions_data:
        suggestions = suggestions_data.get("suggestions", [])

        if not suggestions:
            st.info(
                "No mapping suggestions were found for this evidence artifact.",
                icon="ℹ️",
            )
        else:
            for suggestion in suggestions:
                control_id = suggestion.get("control_id", "")
                title = suggestion.get("title", "")
                confidence = suggestion.get("confidence", 0)
                artifact_type = suggestion.get("suggested_artifact_type", "")

                # Determine color based on confidence
                if confidence >= 70:
                    badge_color = "green"
                elif confidence >= 40:
                    badge_color = "orange"
                else:
                    badge_color = "red"

                with st.container(border=True):
                    cols = st.columns([2, 1.5, 1.5])

                    with cols[0]:
                        st.markdown(f"**{control_id}**")
                        st.caption(title)

                    with cols[1]:
                        st.markdown(f"**Confidence:** {confidence:.1f}%")
                        st.markdown(
                            f"<div style='background-color:{badge_color};"
                            f"height:6px;border-radius:3px;margin-top:4px;"
                            f"width:{confidence}%;'></div>",
                            unsafe_allow_html=True,
                        )

                    with cols[2]:
                        st.markdown(f"**Artifact Type:** {artifact_type}")
    else:
        st.info(
            "Click 'Suggest Mappings' to get AI-powered control mapping "
            "recommendations with confidence scores.",
            icon="ℹ️",
        )


def main() -> None:
    """Main entry point for the Evidence Detail page."""
    st.title("📎 Evidence Detail")

    # Read query parameters
    query_params = st.query_params
    evidence_id = query_params.get("evidence_id", "")

    if not evidence_id:
        st.warning(
            "No evidence artifact specified. "
            "Navigate from the Evidence Library to view details.",
            icon="ℹ️",
        )
        st.page_link(
            "pages/evidence_library.py",
            label="← Go to Evidence Library",
        )
        return

    # Fetch evidence detail
    evidence = get_evidence_detail(evidence_id)

    if not evidence:
        st.error(
            f"Evidence artifact with ID '{evidence_id}' not found. "
            "It may have been deleted or the ID is invalid.",
            icon="❌",
        )
        st.page_link(
            "pages/evidence_library.py",
            label="← Back to Evidence Library",
        )
        return

    # Fetch mappings
    mappings = get_evidence_mappings(evidence_id)

    # --- Breadcrumb navigation ---
    st.markdown(
        "<small>"
        "<a href='/evidence_library' target='_self'>Evidence Library</a>"
        f" &gt; {evidence.get('name', 'Detail')}</small>",
        unsafe_allow_html=True,
    )

    # --- Evidence Name Header ---
    st.markdown(f"### {evidence.get('name', 'Evidence Artifact')}")

    # --- Divider ---
    st.divider()

    # --- Metadata Section ---
    _render_metadata_section(evidence)

    st.divider()

    # --- Content Preview Section ---
    _render_content_preview(evidence)

    st.divider()

    # --- Checksum Section ---
    _render_checksum_section(evidence)

    st.divider()

    # --- Control Mappings Section ---
    _render_mappings_section(evidence_id, mappings)

    st.divider()

    # --- AI Analysis Section ---
    _render_ai_analysis_section(evidence_id, evidence)

    st.divider()

    # --- Mapping Suggestion Section ---
    _render_mapping_suggestion_section(evidence_id, evidence)

    # --- Navigation ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.page_link(
            "pages/evidence_library.py",
            label="← Back to Evidence Library",
        )


if __name__ == "__main__":
    main()
