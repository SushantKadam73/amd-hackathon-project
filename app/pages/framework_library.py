"""GRC Platform - Framework & Control Library Page.

Displays:
1. A framework listing table showing NIST SP 800-53 Rev 5
2. A control library view grouped by control family
3. Search and filter capabilities
4. Empty state handling
"""

from typing import Any, Optional

import streamlit as st
import plotly.graph_objects as go

from app.api_client import get_frameworks, get_controls, get_compliance_status

# Page configuration
st.set_page_config(
    page_title="Framework & Control Library - GRC Platform",
    page_icon="📚",
    layout="wide",
)


def _get_mapping_status(score: float) -> str:
    """Determine mapping status from a compliance score.

    Args:
        score: Compliance score (0-100).

    Returns:
        Mapping status string.
    """
    if score >= 90.0:
        return "Fully Mapped"
    elif score >= 50.0:
        return "Partially Mapped"
    return "Unmapped"


def _get_status_color(status: str) -> str:
    """Get a display color for a mapping status.

    Args:
        status: Mapping status string.

    Returns:
        CSS color string.
    """
    colors = {
        "Fully Mapped": "green",
        "Partially Mapped": "orange",
        "Unmapped": "red",
    }
    return colors.get(status, "gray")


def _render_empty_state() -> None:
    """Render an empty state when no frameworks are loaded."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            "### No frameworks loaded\n\n"
            "The framework library is empty. Please seed the database first:\n\n"
            "```bash\npython scripts/seed_data.py\n```\n\n"
            "This will populate the database with NIST SP 800-53 Rev 5 "
            "and its controls. The control library will then be available "
            "for browsing, searching, and mapping evidence.\n\n"
            "**Expected controls:** PE-03, AC-02, SC-07, IR-06, RA-05",
            icon="📚",
        )


def _render_framework_section(frameworks: list[dict[str, Any]]) -> None:
    """Render the framework listing section.

    Args:
        frameworks: List of framework dicts.
    """
    st.subheader("Compliance Frameworks")

    for fw in frameworks:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"### {fw['name']}")
                if fw.get("version"):
                    st.markdown(f"**Version:** {fw['version']}")
            with cols[1]:
                st.markdown("**Controls**")
                st.markdown(
                    f"<h2 style='margin:0; color:#0066cc;'>5</h2>",
                    unsafe_allow_html=True,
                )
            with cols[2]:
                st.markdown("**Status**")
                st.markdown(
                    "<span style='color:green;'>● Active</span>",
                    unsafe_allow_html=True,
                )

            if fw.get("description"):
                st.markdown(fw["description"])

            st.markdown(f"**Framework ID:** `{fw['id']}`")


def _get_control_mapping_status(
    control_id: str,
    compliance_data: Optional[dict[str, Any]],
) -> tuple[str, float]:
    """Get the mapping status for a specific control.

    Args:
        control_id: The human-readable control ID (e.g., 'PE-03').
        compliance_data: Compliance status from the API.

    Returns:
        Tuple of (status_string, score_percentage).
    """
    if not compliance_data:
        return "Unmapped", 0.0

    for ctrl in compliance_data.get("controls", []):
        if ctrl.get("control_id") == control_id:
            score = ctrl.get("score", 0.0)
            status = ctrl.get("status", _get_mapping_status(score))
            return status, score

    return "Unmapped", 0.0


def _render_control_library(
    controls: list[dict[str, Any]],
    compliance_data: Optional[dict[str, Any]],
) -> None:
    """Render the control library with search and filters.

    Args:
        controls: List of control dicts.
        compliance_data: Compliance status data for mapping statuses.
    """
    st.subheader("Control Library")

    if not controls:
        st.info("No controls found for this framework.", icon="📋")
        return

    # Gather distinct families and statuses for filters
    families = sorted(
        set(
            ctrl.get("control_family", "Unknown")
            for ctrl in controls
        )
    )
    statuses = ["Unmapped", "Partially Mapped", "Fully Mapped"]

    # --- Search and Filter Bar ---
    col_search, col_family, col_status = st.columns([3, 2, 2])

    with col_search:
        search_query = st.text_input(
            "🔍 Search controls",
            placeholder="Search by title, description, or family...",
            label_visibility="collapsed",
        )

    with col_family:
        family_filter = st.selectbox(
            "Control Family",
            options=["All"] + families,
            index=0,
            label_visibility="collapsed",
        )

    with col_status:
        status_filter = st.selectbox(
            "Mapping Status",
            options=["All"] + statuses,
            index=0,
            label_visibility="collapsed",
        )

    # --- Apply filters ---
    filtered: list[dict[str, Any]] = []
    for ctrl in controls:
        ctrl_status, _ = _get_control_mapping_status(
            ctrl["control_id"], compliance_data
        )

        # Search filter (by title, description, family)
        if search_query:
            q = search_query.lower()
            title = (ctrl.get("title") or "").lower()
            description = (ctrl.get("description") or "").lower()
            family = (ctrl.get("control_family") or "").lower()
            if q not in title and q not in description and q not in family:
                continue

        # Family filter
        if family_filter != "All" and ctrl.get("control_family") != family_filter:
            continue

        # Status filter
        if status_filter != "All" and ctrl_status != status_filter:
            continue

        filtered.append(ctrl)

    # --- Results info ---
    st.markdown(
        f"*Showing {len(filtered)} of {len(controls)} controls*"
    )

    if not filtered:
        st.info(
            "No controls match your search or filter criteria. "
            "Try adjusting your search terms or clearing filters.",
            icon="🔍",
        )
        return

    # --- Group controls by family ---
    grouped: dict[str, list[dict[str, Any]]] = {}
    for ctrl in filtered:
        family = ctrl.get("control_family", "Other")
        if family not in grouped:
            grouped[family] = []
        grouped[family].append(ctrl)

    # --- Render grouped controls ---
    for family_name, family_controls in grouped.items():
        with st.expander(f"**{family_name}** ({len(family_controls)} controls)", expanded=True):
            for ctrl in family_controls:
                ctrl_status, ctrl_score = _get_control_mapping_status(
                    ctrl["control_id"], compliance_data
                )
                status_color = _get_status_color(ctrl_status)

                with st.container(border=True):
                    cols = st.columns([1, 3, 1, 1, 1.5])

                    with cols[0]:
                        st.markdown(
                            f"**{ctrl['control_id']}**",
                        )
                    with cols[1]:
                        st.markdown(ctrl.get("title", ""))
                    with cols[2]:
                        priority = ctrl.get("priority", "medium")
                        priority_colors = {
                            "high": "🔴",
                            "medium": "🟡",
                            "low": "🟢",
                        }
                        st.markdown(
                            f"{priority_colors.get(priority, '⚪')} {priority.title()}"
                        )
                    with cols[3]:
                        st.markdown(ctrl.get("control_family", ""))
                    with cols[4]:
                        st.markdown(
                            f"<span style='color:{status_color};font-weight:bold;'>"
                            f"{ctrl_status}</span>",
                            unsafe_allow_html=True,
                        )

                    # View details button
                    detail_url = (
                        f"/control_detail?control_id={ctrl['control_id']}"
                        f"&framework_id={ctrl.get('framework_id', '')}"
                    )
                    st.markdown(
                        f"[📖 View Details]({detail_url})",
                    )


def main() -> None:
    """Main entry point for the Framework & Control Library page."""
    st.title("📚 Framework & Control Library")
    st.markdown(
        "Browse compliance frameworks and explore controls with "
        "their requirements, artifact types, and cross-framework mappings."
    )

    # Fetch frameworks
    frameworks = get_frameworks()

    if not frameworks:
        _render_empty_state()
        return

    # --- Tabbed layout ---
    tab_frameworks, tab_controls = st.tabs([
        "📋 Framework Overview",
        "🛡️ Control Library",
    ])

    with tab_frameworks:
        _render_framework_section(frameworks)

    with tab_controls:
        # Use the first framework (NIST SP 800-53) for controls
        framework_id = frameworks[0]["id"]
        controls = get_controls(framework_id)
        compliance_data = get_compliance_status()
        _render_control_library(controls, compliance_data)


if __name__ == "__main__":
    main()
