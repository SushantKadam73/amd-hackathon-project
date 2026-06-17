"""GRC Platform - Evidence Management Page.

Provides:
1. Evidence upload form with file picker, name, artifact type, target control, description
2. Upload button with progress feedback and success/error messages
3. Evidence list table with search and filter controls
4. Empty state for no uploaded evidence
"""

from typing import Any, Optional

import streamlit as st

from app.api_client import (
    get_compliance_status,
    get_controls,
    get_evidence_list,
    get_evidence_mappings,
    get_frameworks,
    map_evidence_to_control,
    upload_evidence,
)

# Page configuration
st.set_page_config(
    page_title="Evidence Management - GRC Platform",
    page_icon="📎",
    layout="wide",
)

# Supported file types for upload
SUPPORTED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg", ".docx"]
SUPPORTED_EXTENSIONS_STR = ", ".join(SUPPORTED_EXTENSIONS)


def _get_mapping_status_color(status: str) -> str:
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
    }
    return colors.get(status, "gray")


def _get_artifact_types_for_control(
    controls: list[dict[str, Any]],
    control_id: str,
) -> list[dict[str, Any]]:
    """Get artifact requirements for a specific control.

    Args:
        controls: List of control dicts.
        control_id: UUID or control_ref_id of the target control.

    Returns:
        List of artifact requirement dicts with type, weightage, description.
    """
    for ctrl in controls:
        if ctrl.get("id") == control_id or ctrl.get("control_id") == control_id:
            return ctrl.get("artifact_requirements", [])
    return []


def _get_weightage_for_type(
    artifact_types: list[dict[str, Any]],
    artifact_type: str,
) -> float:
    """Get the weightage for a specific artifact type from a control's requirements.

    Args:
        artifact_types: List of artifact requirement dicts.
        artifact_type: The artifact type name.

    Returns:
        Weightage percentage as float.
    """
    for req in artifact_types:
        if req.get("type") == artifact_type:
            return float(req.get("weightage", 0))
    return 0.0


def _build_evidence_rows(
    evidence_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build display rows with mapping data joined for each evidence item.

    For each evidence artifact, fetches its control mappings and creates
    display rows. Evidence with no mappings shows a single unmapped row.

    Args:
        evidence_items: List of evidence artifact dicts.

    Returns:
        List of display-ready row dicts.
    """
    rows: list[dict[str, Any]] = []
    for item in evidence_items:
        mappings = get_evidence_mappings(item["id"])
        if mappings:
            for m in mappings:
                rows.append({
                    "id": item["id"],
                    "name": item["name"],
                    "file_type": item.get("file_type", ""),
                    "target_control": m.get("control_ref_id", ""),
                    "artifact_type": m.get("artifact_type", ""),
                    "mapping_status": m.get("mapping_status", "unmapped"),
                    "weightage": f"{m.get('weightage', 0):.1f}%",
                    "uploaded_at": item.get("uploaded_at", ""),
                    "_has_mappings": True,
                })
        else:
            # Unmapped evidence
            rows.append({
                "id": item["id"],
                "name": item["name"],
                "file_type": item.get("file_type", ""),
                "target_control": "—",
                "artifact_type": "—",
                "mapping_status": "unmapped",
                "weightage": "—",
                "uploaded_at": item.get("uploaded_at", ""),
                "_has_mappings": False,
            })
    return rows


def _render_upload_tab() -> None:
    """Render the evidence upload form."""
    st.subheader("📤 Upload Evidence Artifact")

    st.markdown(
        "Upload compliance evidence documents to support control mappings. "
        "Accepted file types: **PDF, PNG, JPG, DOCX**."
    )

    # Fetch frameworks and controls for dropdowns
    frameworks = get_frameworks()
    controls_list: list[dict[str, Any]] = []
    if frameworks:
        controls_list = get_controls(frameworks[0]["id"])

    # --- Upload Form ---
    with st.form("upload_evidence_form", clear_on_submit=False):
        # File picker
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=SUPPORTED_EXTENSIONS,
            help=f"Accepted formats: {SUPPORTED_EXTENSIONS_STR}",
        )

        col1, col2 = st.columns(2)

        with col1:
            # Evidence name (pre-filled from filename)
            default_name = ""
            if uploaded_file is not None:
                default_name = uploaded_file.name

            evidence_name = st.text_input(
                "Evidence Name",
                value=default_name,
                placeholder="Enter a descriptive name for this evidence",
                help="A human-readable name for this evidence artifact",
            )

            # Target control dropdown
            control_options = []
            control_id_map: dict[str, str] = {}
            if controls_list:
                for ctrl in controls_list:
                    label = f"{ctrl.get('control_id', '')} - {ctrl.get('title', '')}"
                    control_options.append(label)
                    control_id_map[label] = ctrl.get("id", "")

            selected_control_label = st.selectbox(
                "Target Control (optional)",
                options=["None"] + control_options,
                index=0,
                help="Select the control this evidence maps to",
            )

        with col2:
            # Artifact type dropdown (filtered by selected control)
            artifact_types_list: list[str] = []
            artifact_types_data: list[dict[str, Any]] = []

            if selected_control_label != "None" and controls_list:
                # Find the control UUID
                ctrl_uuid = control_id_map.get(selected_control_label, "")
                artifact_types_data = _get_artifact_types_for_control(
                    controls_list,
                    ctrl_uuid,
                )
                artifact_types_list = [
                    req.get("type", "") for req in artifact_types_data
                ]

            if artifact_types_list:
                selected_artifact_type = st.selectbox(
                    "Artifact Type (optional)",
                    options=[""] + artifact_types_list,
                    index=0,
                    help="Type of evidence artifact for the selected control",
                )
                # Show weightage for selected type
                if selected_artifact_type:
                    weight = _get_weightage_for_type(
                        artifact_types_data, selected_artifact_type
                    )
                    st.caption(f"Weightage: {weight:.1f}%")
            else:
                selected_artifact_type = st.selectbox(
                    "Artifact Type (optional)",
                    options=[""],
                    index=0,
                    disabled=True,
                    help="Select a target control first to see artifact types",
                )
                st.caption("Select a target control to see available artifact types")

            # Description field
            description = st.text_area(
                "Description (optional)",
                placeholder="Additional context about this evidence...",
                height=80,
            )

        # Upload button
        submitted = st.form_submit_button(
            "📤 Upload Evidence",
            type="primary",
            use_container_width=True,
            disabled=uploaded_file is None,
        )

    # --- Handle form submission ---
    if submitted:
        if uploaded_file is None:
            st.warning("Please select a file to upload.", icon="⚠️")
            return

        if not evidence_name.strip():
            st.warning("Please enter an evidence name.", icon="⚠️")
            return

        # Check file extension
        file_ext = _get_extension(uploaded_file.name)
        if file_ext.lower() not in SUPPORTED_EXTENSIONS:
            st.error(
                f"Unsupported file type '{file_ext}'. "
                f"Accepted types: {SUPPORTED_EXTENSIONS_STR}.",
                icon="❌",
            )
            return

        # Upload file with progress indicator
        with st.status("Uploading evidence...", expanded=True) as status:
            st.write(f"📄 Uploading **{evidence_name}**...")

            file_bytes = uploaded_file.getvalue()

            # Use the evidence name as the filename sent to the API
            upload_filename = f"{evidence_name}{file_ext}"

            result = upload_evidence(
                file_content=file_bytes,
                filename=upload_filename,
            )

            if result:
                st.write("✅ File uploaded successfully!")
                evidence_id = result.get("id", "")

                # If target control and artifact type selected, create mapping
                if (
                    selected_control_label != "None"
                    and selected_artifact_type
                    and evidence_id
                ):
                    ctrl_uuid = control_id_map.get(selected_control_label, "")
                    weight = _get_weightage_for_type(
                        artifact_types_data, selected_artifact_type
                    )

                    st.write(f"🔄 Mapping to **{selected_control_label}**...")

                    mapping_result = map_evidence_to_control(
                        evidence_id=evidence_id,
                        control_id=ctrl_uuid,
                        weightage=weight,
                        artifact_type=selected_artifact_type,
                    )

                    if mapping_result:
                        st.write(
                            f"✅ Mapped to {selected_control_label} "
                            f"as '{selected_artifact_type}' "
                            f"({weight:.1f}% weightage)"
                        )

                status.update(
                    label="✅ Upload complete!",
                    state="complete",
                    expanded=False,
                )
                st.success(
                    f"**{evidence_name}** uploaded successfully!",
                    icon="🎉",
                )
                st.rerun()
            else:
                status.update(
                    label="❌ Upload failed",
                    state="error",
                    expanded=True,
                )


def _get_extension(filename: str) -> str:
    """Get the file extension from a filename.

    Args:
        filename: The file name.

    Returns:
        File extension with leading dot.
    """
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _render_evidence_list_tab() -> None:
    """Render the evidence library table with search and filter controls."""
    st.subheader("📋 Evidence Library")

    # Fetch evidence
    evidence_items = get_evidence_list()

    if not evidence_items:
        _render_empty_state()
        return

    # Build display rows with mapping data
    all_rows = _build_evidence_rows(evidence_items)

    # --- Search and Filter Controls ---
    col_search, col_control, col_status = st.columns([3, 2, 2])

    with col_search:
        search_query = st.text_input(
            "🔍 Search by name",
            placeholder="Type to filter evidence...",
            label_visibility="collapsed",
        )

    with col_control:
        # Get distinct control ref IDs from rows
        control_options = sorted(
            set(
                row["target_control"]
                for row in all_rows
                if row["target_control"] != "—"
            )
        )
        control_filter = st.selectbox(
            "Filter by Control",
            options=["All Controls"] + control_options,
            index=0,
            label_visibility="collapsed",
        )

    with col_status:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All Statuses", "approved", "pending", "rejected", "unmapped"],
            index=0,
            label_visibility="collapsed",
        )

    # --- Apply filters ---
    filtered_rows = all_rows
    if search_query:
        q = search_query.lower()
        filtered_rows = [
            row for row in filtered_rows if q in row["name"].lower()
        ]

    if control_filter != "All Controls":
        filtered_rows = [
            row for row in filtered_rows
            if row["target_control"] == control_filter
        ]

    if status_filter != "All Statuses":
        filtered_rows = [
            row for row in filtered_rows
            if row["mapping_status"] == status_filter
        ]

    # --- Results count ---
    st.markdown(f"*Showing {len(filtered_rows)} of {len(evidence_items)} artifacts*")

    if not filtered_rows:
        st.info(
            "No evidence matches your search or filter criteria. "
            "Try adjusting your search terms or clearing filters.",
            icon="🔍",
        )
        return

    # --- Evidence Table ---
    # Group rows by evidence ID for display
    displayed_ids: set[str] = set()
    for row in filtered_rows:
        eid = row["id"]
        if eid in displayed_ids:
            # This is a duplicate evidence (multiple mappings), show as additional row
            pass
        displayed_ids.add(eid)

        status_color = _get_mapping_status_color(row["mapping_status"])

        with st.container(border=True):
            cols = st.columns([2.5, 1, 1.5, 1.5, 1, 1, 1.5])

            with cols[0]:
                # Name with link to detail page
                detail_url = f"/evidence_detail?evidence_id={eid}"
                st.markdown(
                    f"<a href='{detail_url}' target='_self' "
                    f"style='text-decoration:none;font-weight:bold;'>"
                    f"{row['name']}</a>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.markdown(f"`{row['file_type']}`")
            with cols[2]:
                st.markdown(f"**{row['target_control']}**")
            with cols[3]:
                st.markdown(row["artifact_type"])
            with cols[4]:
                st.markdown(
                    f"<span style='color:{status_color};font-weight:bold;'>"
                    f"{row['mapping_status'].title()}</span>",
                    unsafe_allow_html=True,
                )
            with cols[5]:
                st.markdown(row["weightage"])
            with cols[6]:
                uploaded = row.get("uploaded_at", "")
                if uploaded:
                    # Show date part only
                    st.text(uploaded[:10] if len(uploaded) >= 10 else uploaded)
                else:
                    st.text("—")

    # Column headers hint
    st.caption(
        "Columns: Name | File Type | Target Control | Artifact Type | "
        "Mapping Status | Weightage | Upload Date"
    )


def _render_empty_state() -> None:
    """Render an empty state when no evidence has been uploaded."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            "### 📎 No Evidence Uploaded\n\n"
            "Your evidence library is empty. Upload compliance documents "
            "and map them to controls to track your compliance status.\n\n"
            "**Getting Started:**\n"
            "1. Go to the **Upload Evidence** tab\n"
            "2. Select a file (PDF, PNG, JPG, or DOCX)\n"
            "3. Choose a target control and artifact type\n"
            "4. Click **Upload Evidence**\n\n"
            "**Supported file types:** PDF, PNG, JPG, DOCX",
            icon="📎",
        )


def _render_column_headers() -> None:
    """Render column headers for the evidence list table."""
    cols = st.columns([2.5, 1, 1.5, 1.5, 1, 1, 1.5])
    headers = [
        "Name",
        "File Type",
        "Target Control",
        "Artifact Type",
        "Status",
        "Weightage",
        "Upload Date",
    ]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")


def main() -> None:
    """Main entry point for the Evidence Management page."""
    st.title("📎 Evidence Management")
    st.markdown(
        "Upload, view, and manage compliance evidence artifacts. "
        "Map evidence to NIST SP 800-53 controls to track compliance status."
    )

    # Tabbed layout: Upload | Evidence Library
    tab_upload, tab_library = st.tabs([
        "📤 Upload Evidence",
        "📋 Evidence Library",
    ])

    with tab_upload:
        _render_upload_tab()

    with tab_library:
        _render_evidence_list_tab()


if __name__ == "__main__":
    main()
