"""GRC Platform - Control Detail Page.

Displays full control details including:
1. Full description of the control
2. Required artifact types with percentage weightages (summing to 100%)
3. Evidence coverage visualization (progress bar)
4. Current mapping status
5. Cross-framework mapping table (NIST CSF, CIS, PCI DSS)
"""

from typing import Any, Optional

import streamlit as st
import plotly.graph_objects as go

from app.api_client import get_frameworks, get_controls, get_compliance_status

# Page configuration
st.set_page_config(
    page_title="Control Detail - GRC Platform",
    page_icon="🛡️",
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


def _render_artifact_requirements(
    requirements: list[dict[str, Any]],
    validated_weightage: float,
) -> None:
    """Render the artifact requirements table with weightages.

    Args:
        requirements: List of artifact requirement dicts with type, weightage, description.
        validated_weightage: Sum of validated evidence weightage.
    """
    st.subheader("📋 Required Artifact Types")

    total_weightage = sum(
        float(req.get("weightage", 0)) for req in requirements
    )

    # Verify weightage sums to 100%
    if abs(total_weightage - 100.0) > 0.01:
        st.warning(
            f"Total weightage ({total_weightage:.1f}%) does not sum to 100%. "
            "This may indicate incomplete configuration.",
            icon="⚠️",
        )

    # Build table data
    table_data = []
    for req in requirements:
        req_type = req.get("type", "Unknown")
        weightage = float(req.get("weightage", 0))
        description = req.get("description", "")

        # Calculate coverage percentage for this artifact type
        # (based on whether evidence is mapped for this type)
        contribution_pct = (weightage / total_weightage * 100) if total_weightage > 0 else 0

        table_data.append({
            "Artifact Type": req_type,
            "Weightage": f"{weightage:.0f}%",
            "Description": description,
        })

    # Display artifact types table
    st.table(table_data)

    # Show weightage summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Required Weightage", f"{total_weightage:.0f}%")
    with col2:
        st.metric("Validated Weightage", f"{validated_weightage:.1f}%")
    with col3:
        gap = max(0, total_weightage - validated_weightage)
        st.metric("Remaining Gap", f"{gap:.1f}%", delta_color="inverse")


def _render_evidence_coverage(
    validated_weightage: float,
    total_required: float,
) -> None:
    """Render the evidence coverage visualization.

    Args:
        validated_weightage: Sum of validated evidence weightage.
        total_required: Total required weightage.
    """
    st.subheader("📊 Evidence Coverage")

    coverage_pct = (
        min(validated_weightage / total_required * 100, 100.0)
        if total_required > 0
        else 0.0
    )

    # Progress bar for coverage
    st.progress(coverage_pct / 100.0, text=f"{coverage_pct:.1f}% coverage")

    # Gauge chart using plotly
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=coverage_pct,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Evidence Coverage"},
        delta={"reference": 100},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#0066cc"},
            "steps": [
                {"range": [0, 50], "color": "#ffcccc"},
                {"range": [50, 90], "color": "#ffebcc"},
                {"range": [90, 100], "color": "#ccffcc"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": coverage_pct,
            },
        },
    ))
    fig.update_layout(
        height=250,
        margin={"t": 30, "b": 0, "l": 0, "r": 0},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_mapping_status_section(
    control_id: str,
    compliance_data: Optional[dict[str, Any]],
) -> tuple[str, float, float]:
    """Render the current mapping status section.

    Args:
        control_id: The human-readable control ID (e.g., 'PE-03').
        compliance_data: Compliance status from the API.

    Returns:
        Tuple of (status_string, validated_weightage, total_required_weightage).
    """
    st.subheader("📌 Current Mapping Status")

    status = "Unmapped"
    validated_weightage = 0.0
    total_required = 0.0
    score = 0.0

    if compliance_data:
        for ctrl in compliance_data.get("controls", []):
            if ctrl.get("control_id") == control_id:
                score = ctrl.get("score", 0.0)
                validated_weightage = ctrl.get("validated_weightage", 0.0)
                total_required = ctrl.get("total_required_weightage", 0.0)
                status = ctrl.get("status", _get_mapping_status(score))
                break

    status_color = _get_status_color(status)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div style='text-align:center; padding:20px; "
            f"background:{status_color}15; border-radius:10px; "
            f"border:2px solid {status_color};'>"
            f"<h3 style='color:{status_color};margin:0;'>{status}</h3>"
            f"<p style='margin:5px 0 0;'>Mapping Status</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.metric("Compliance Score", f"{score:.1f}%")
    with col3:
        if validated_weightage > 0:
            remaining = max(0, total_required - validated_weightage)
            st.metric("Validated Weightage", f"{validated_weightage:.1f}%")
        else:
            st.metric("Validated Weightage", "0.0%")

    return status, validated_weightage, total_required


def _render_cross_framework_mappings(
    mappings: Optional[dict[str, Any]],
) -> None:
    """Render the cross-framework mapping table.

    Args:
        mappings: Dict of cross-framework mappings from the control data.
    """
    st.subheader("🔗 Cross-Framework Mappings")

    if not mappings:
        st.info(
            "No cross-framework mappings defined for this control.",
            icon="ℹ️",
        )
        return

    # Build mapping rows
    mapping_rows = []

    # NIST CSF 2.0
    nist = mappings.get("nist_csf_2_0", {})
    mapping_rows.append({
        "Framework": "NIST CSF 2.0",
        "Mapped Control": nist.get("mapped_to") if nist else "No mapping defined",
        "Description": nist.get("description", "") if nist else "",
    })

    # CIS Controls v8
    cis = mappings.get("cis_controls_v8", {})
    mapping_rows.append({
        "Framework": "CIS Controls v8",
        "Mapped Control": cis.get("mapped_to") if cis else "No mapping defined",
        "Description": cis.get("description", "") if cis else "",
    })

    # PCI DSS v4.0.1
    pci = mappings.get("pci_dss_v4_0_1", {})
    mapping_rows.append({
        "Framework": "PCI DSS v4.0.1",
        "Mapped Control": pci.get("mapped_to") if pci else "No mapping defined",
        "Description": pci.get("description", "") if pci else "",
    })

    for row in mapping_rows:
        with st.container(border=True):
            cols = st.columns([1.5, 2, 3])
            with cols[0]:
                st.markdown(f"**{row['Framework']}**")
            with cols[1]:
                mapped = row["Mapped Control"]
                if mapped and mapped != "No mapping defined":
                    st.markdown(f"`{mapped}`")
                else:
                    st.markdown("*No mapping defined*")
            with cols[2]:
                st.markdown(row["Description"] or "")


def _render_control_not_found(control_id: str) -> None:
    """Render a message when the requested control is not found.

    Args:
        control_id: The control ID that was requested.
    """
    st.error(
        f"Control **{control_id}** not found. "
        "The control may not be loaded in the database. "
        "Please run `python scripts/seed_data.py` to populate controls.",
        icon="❌",
    )
    st.page_link(
        "framework_library.py",
        label="← Back to Control Library",
    )


def main() -> None:
    """Main entry point for the Control Detail page."""
    st.title("🛡️ Control Detail")

    # Read query parameters
    query_params = st.query_params
    control_id = query_params.get("control_id", "")
    framework_id = query_params.get("framework_id", "")

    if not control_id:
        st.warning(
            "No control specified. Navigate from the Control Library to view details.",
            icon="ℹ️",
        )
        st.page_link(
            "framework_library.py",
            label="← Go to Control Library",
        )
        return

    # Fetch frameworks to get the framework_id if not provided
    if not framework_id:
        frameworks = get_frameworks()
        if frameworks:
            framework_id = frameworks[0]["id"]
        else:
            st.warning("No frameworks loaded. Please seed the database.", icon="📚")
            st.page_link(
                "framework_library.py",
                label="← Back to Control Library",
            )
            return

    # Fetch controls and find the matching one
    controls = get_controls(framework_id)

    # Find the control by control_id (e.g., 'PE-03') or by UUID
    control: Optional[dict[str, Any]] = None
    for ctrl in controls:
        if ctrl.get("control_id") == control_id or ctrl.get("id") == control_id:
            control = ctrl
            break

    if not control:
        _render_control_not_found(control_id)
        return

    # Fetch compliance data for mapping status
    compliance_data = get_compliance_status()

    # --- Control Header ---
    ctrl_id = control.get("control_id", "")
    title = control.get("title", "")
    family = control.get("control_family", "")
    priority = control.get("priority", "medium")
    description = control.get("description", "")

    priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    st.markdown(
        f"### {ctrl_id}: {title}"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Control Family:** {family}")
    with col2:
        st.markdown(
            f"**Priority:** {priority_icons.get(priority, '⚪')} {priority.title()}"
        )
    with col3:
        st.markdown(f"**Framework:** NIST SP 800-53 Rev 5")

    # Breadcrumb navigation
    st.markdown(
        "<small>"
        "<a href='/framework_library' target='_self'>Control Library</a>"
        f" &gt; {ctrl_id}</small>",
        unsafe_allow_html=True,
    )

    # --- Full Description ---
    st.subheader("📝 Description")
    st.markdown(description)

    # --- Divider ---
    st.divider()

    # --- Artifact Requirements ---
    requirements = control.get("artifact_requirements", [])
    artifact_requirements: list[dict[str, Any]] = []
    if requirements:
        for req in requirements:
            if isinstance(req, dict):
                artifact_requirements.append(req)
            elif isinstance(req, str):
                # Handle string-encoded requirements (unlikely but defensive)
                pass

    # Get compliance data for this control
    _, validated_weightage, total_required = _render_mapping_status_section(
        ctrl_id, compliance_data
    )

    # Re-calculate from compliance data if available
    if compliance_data:
        for c in compliance_data.get("controls", []):
            if c.get("control_id") == ctrl_id:
                validated_weightage = c.get("validated_weightage", 0.0)
                total_required = c.get("total_required_weightage", 100.0)
                break
    else:
        total_required = sum(
            float(r.get("weightage", 0)) for r in artifact_requirements
        )

    st.divider()

    # Artifact requirements table
    if artifact_requirements:
        _render_artifact_requirements(artifact_requirements, validated_weightage)
    else:
        st.info("No artifact requirements defined for this control.", icon="ℹ️")

    st.divider()

    # Evidence Coverage
    _render_evidence_coverage(validated_weightage, total_required)

    st.divider()

    # Cross-Framework Mappings
    mappings = control.get("cross_framework_mappings")
    _render_cross_framework_mappings(mappings)

    # Back link
    st.divider()
    st.page_link(
        "framework_library.py",
        label="← Back to Control Library",
    )


if __name__ == "__main__":
    main()
