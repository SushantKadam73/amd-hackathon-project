"""GRC Platform - Review Workflow Page.

Provides:
1. Review queue with pending reviews sorted by submission date (oldest first)
2. Approve button (blocked for self-approval with error message)
3. Reject button with mandatory review notes field
4. Review history tab with filtering by decision, entity type, date range
5. Review detail panel with entity context, submission notes, approve/reject
"""

from datetime import date, datetime, timezone
from typing import Any, Optional

import streamlit as st

from app.api_client import (
    approve_review,
    get_evidence_detail,
    get_mapping_detail,
    get_pending_review_count,
    get_review,
    get_reviews,
    get_users,
    reject_review,
    submit_for_review,
)

# Page configuration
st.set_page_config(
    page_title="Review Workflow - GRC Platform",
    page_icon="📋",
    layout="wide",
)


# =============================================================================
# Constants
# =============================================================================

ENTITY_TYPE_LABELS = {
    "evidence_artifact": "📎 Evidence Artifact",
    "evidence_control_mapping": "🔗 Evidence Mapping",
}

ENTITY_TYPE_OPTIONS = [
    "All Types",
    "evidence_artifact",
    "evidence_control_mapping",
]

DECISION_OPTIONS = ["All Decisions", "approved", "rejected"]

STATUS_COLORS = {
    "pending": "#ffaa00",
    "approved": "#00cc66",
    "rejected": "#ff3333",
}

STATUS_BG_COLORS = {
    "pending": "#fff8e6",
    "approved": "#e6ffe6",
    "rejected": "#ffe6e6",
}


# =============================================================================
# Helper Functions
# =============================================================================


def _get_status_color(status: str) -> str:
    """Get display color for a workflow status.

    Args:
        status: Workflow status string.

    Returns:
        CSS color string.
    """
    return STATUS_COLORS.get(status, "#999999")


def _get_entity_type_display(entity_type: str) -> str:
    """Get a human-readable label for an entity type.

    Args:
        entity_type: Raw entity type string.

    Returns:
        Formatted display label.
    """
    return ENTITY_TYPE_LABELS.get(entity_type, entity_type.replace("_", " ").title())


def _resolve_entity_name(
    entity_type: str,
    entity_id: str,
) -> str:
    """Resolve the display name for a reviewed entity.

    Args:
        entity_type: Type of entity (e.g., 'evidence_artifact').
        entity_id: UUID of the entity.

    Returns:
        Human-readable name/title of the entity.
    """
    try:
        if entity_type == "evidence_artifact":
            evidence = get_evidence_detail(entity_id)
            if evidence:
                return evidence.get("name", entity_id[:8] + "...")
        elif entity_type == "evidence_control_mapping":
            mapping = get_mapping_detail(entity_id)
            if mapping:
                ctrl_ref = mapping.get("control_ref_id", "")
                artifact_type = mapping.get("artifact_type", "")
                if ctrl_ref and artifact_type:
                    return f"{ctrl_ref} - {artifact_type}"
                elif ctrl_ref:
                    return ctrl_ref
                return mapping.get("id", entity_id[:8] + "...")
    except Exception:
        pass
    return entity_id[:8] + "..."


def _format_datetime(dt_str: Optional[str]) -> str:
    """Format an ISO datetime string for display.

    Args:
        dt_str: ISO format datetime string or None.

    Returns:
        Formatted display string.
    """
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return dt_str[:16] if dt_str and len(dt_str) >= 16 else dt_str or "—"


def _get_current_user() -> tuple[str, str]:
    """Get the current user's ID and username from session state.

    Returns:
        Tuple of (user_id, username).
    """
    user_id = st.session_state.get("current_user_id", "")
    username = st.session_state.get("current_user_name", "")
    return user_id, username


# =============================================================================
# Render Functions
# =============================================================================


def _render_user_selector() -> None:
    """Render a user selector in the sidebar for simulating different users."""
    st.sidebar.divider()
    st.sidebar.markdown("### 👤 Current User")

    # Fetch users from API
    users = get_users()

    if not users:
        # Fallback to default user
        st.sidebar.info("No users found in database.", icon="👤")
        st.session_state.current_user_id = "00000000-0000-0000-0000-000000000000"
        st.session_state.current_user_name = "System"
        st.sidebar.caption(
            f"Logged in as: **{st.session_state.get('current_user_name', 'Unknown')}**"
        )
        return

    # Build display options
    user_display = [
        f"{u.get('username', 'user')} ({u.get('full_name', '')})"
        for u in users
    ]

    # Find current selection index
    current_id = st.session_state.get("current_user_id", users[0]["id"])
    current_idx = 0
    for i, u in enumerate(users):
        if u["id"] == current_id:
            current_idx = i
            break

    selected_display = st.sidebar.selectbox(
        "Simulate as",
        options=user_display,
        index=current_idx,
        key="user_selector",
        label_visibility="collapsed",
    )

    # Update session state
    selected_idx = user_display.index(selected_display)
    selected_user = users[selected_idx]
    st.session_state.current_user_id = selected_user["id"]
    st.session_state.current_user_name = selected_user.get("full_name", selected_user.get("username", "Unknown"))

    st.sidebar.caption(
        f"Logged in as: **{st.session_state.get('current_user_name', 'Unknown')}**"
    )


def _render_review_queue_tab() -> None:
    """Render the Review Queue tab showing pending reviews."""
    st.subheader("📋 Review Queue")

    # Fetch all reviews
    all_reviews = get_reviews()
    if all_reviews is None:
        st.warning("Unable to load reviews. Is the API running?")
        return

    # Filter to pending only
    pending_reviews = [
        r for r in all_reviews
        if r.get("workflow_status") == "pending"
    ]

    # Sort by submission date (oldest first)
    pending_reviews.sort(
        key=lambda r: r.get("created_at", ""),
    )

    if not pending_reviews:
        st.success(
            "✅ No pending reviews. All reviews have been processed.",
            icon="✅",
        )
        return

    st.markdown(f"*{len(pending_reviews)} pending review(s) awaiting action*")

    # Current user for action buttons
    user_id, username = _get_current_user()
    if not user_id:
        st.info("Please select a user from the sidebar to perform reviews.", icon="👤")
        return

    # Render each pending review
    for review in pending_reviews:
        review_id = review["id"]
        entity_type = review.get("entity_type", "")
        entity_id = review.get("entity_id", "")
        entity_name = _resolve_entity_name(entity_type, entity_id)
        submitted_by = review.get("submitted_by_username") or review.get("submitted_by", "Unknown")[:8] + "..."
        submitted_at = _format_datetime(review.get("created_at"))
        submitted_by_id = review.get("submitted_by", "")

        # Check if current user is the submitter (self-approval prevention)
        is_self = submitted_by_id == user_id

        with st.container(border=True):
            # Main row
            row_cols = st.columns([1.2, 2.5, 1.5, 1.5, 1, 1])

            with row_cols[0]:
                st.markdown(
                    f"<span style='font-size:13px;'>"
                    f"{_get_entity_type_display(entity_type)}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[1]:
                st.markdown(f"**{entity_name}**")
            with row_cols[2]:
                st.markdown(f"👤 {submitted_by}")
            with row_cols[3]:
                st.markdown(f"🕐 {submitted_at}")
            with row_cols[4]:
                st.markdown(
                    f"<span style='color:{_get_status_color('pending')};"
                    f"font-weight:bold;'>⏳ Pending</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[5]:
                # Detail toggle button
                expand_key = f"expand_review_{review_id}"
                is_expanded = st.session_state.get(expand_key, False)
                if st.button(
                    "📄 Detail" if not is_expanded else "▲ Close",
                    key=f"detail_btn_{review_id}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state[expand_key] = not is_expanded
                    st.rerun()

            # Expanded detail panel
            if st.session_state.get(expand_key, False):
                st.divider()
                _render_review_detail_panel(review, user_id, is_self)

            # Action buttons row (outside expanded panel, always visible)
            st.divider()
            action_cols = st.columns([3, 2, 2, 3])

            with action_cols[1]:
                # Reject section
                reject_key = f"show_reject_{review_id}"
                show_reject = st.session_state.get(reject_key, False)

                if not show_reject:
                    if st.button(
                        "❌ Reject",
                        key=f"reject_btn_{review_id}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        st.session_state[reject_key] = True
                        st.rerun()
                else:
                    if st.button(
                        "↩️ Cancel",
                        key=f"cancel_reject_{review_id}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        st.session_state[reject_key] = False
                        st.rerun()

            with action_cols[2]:
                if st.button(
                    "✅ Approve",
                    key=f"approve_btn_{review_id}",
                    use_container_width=True,
                    type="primary",
                ):
                    if is_self:
                        st.error(
                            "❌ Cannot approve your own submission. "
                            "Self-approval is not allowed.",
                            icon="🚫",
                        )
                    else:
                        with st.spinner("Approving review..."):
                            result = approve_review(
                                review_id=review_id,
                                reviewer_id=user_id,
                            )
                            if result:
                                st.success(
                                    f"✅ Review approved successfully!",
                                    icon="✅",
                                )
                                st.rerun()

            # Reject notes form (shown when Reject is clicked)
            if st.session_state.get(reject_key, False):
                with st.container(border=True):
                    st.markdown("**Rejection Notes**")
                    notes = st.text_area(
                        "Please provide the reason for rejection",
                        key=f"reject_notes_{review_id}",
                        placeholder="Enter detailed reason for rejection...",
                        height=100,
                        label_visibility="collapsed",
                    )

                    if st.button(
                        "✋ Confirm Rejection",
                        key=f"confirm_reject_{review_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        if not notes or not notes.strip():
                            st.error(
                                "❌ Review notes are required for rejection. "
                                "Please enter the reason.",
                                icon="⚠️",
                            )
                        else:
                            with st.spinner("Rejecting review..."):
                                result = reject_review(
                                    review_id=review_id,
                                    reviewer_id=user_id,
                                    review_notes=notes.strip(),
                                )
                                if result:
                                    st.success(
                                        f"✅ Review rejected successfully!",
                                        icon="✅",
                                    )
                                    # Reset reject state
                                    st.session_state[reject_key] = False
                                    st.rerun()


def _render_review_detail_panel(
    review: dict[str, Any],
    user_id: str,
    is_self: bool,
) -> None:
    """Render the review detail panel showing entity context.

    Args:
        review: Review workflow dict.
        user_id: Current user's UUID.
        is_self: Whether current user is the submitter.
    """
    entity_type = review.get("entity_type", "")
    entity_id = review.get("entity_id", "")
    workflow_status = review.get("workflow_status", "")
    submitted_by_username = review.get("submitted_by_username") or "Unknown"
    review_notes = review.get("review_notes", "")
    created_at = _format_datetime(review.get("created_at"))

    st.markdown("### 📄 Review Details")

    # Entity context section
    st.markdown("**Entity Context**")

    if entity_type == "evidence_artifact":
        evidence = get_evidence_detail(entity_id)
        if evidence:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"**Name:** {evidence.get('name', '—')}")
            with col_b:
                st.markdown(f"**File Type:** {evidence.get('file_type', '—').upper()}")
            with col_c:
                uploaded_at = evidence.get("uploaded_at", "")
                st.markdown(f"**Uploaded:** {_format_datetime(uploaded_at)}")

            content = evidence.get("content_text", "")
            if content:
                with st.expander("📝 Content Preview"):
                    st.text(content[:500])
                    if len(content) > 500:
                        st.caption(f"*Showing first 500 of {len(content)} characters*")
        else:
            st.info(f"Entity details not available (ID: {entity_id[:8]}...)", icon="ℹ️")

    elif entity_type == "evidence_control_mapping":
        mapping = get_mapping_detail(entity_id)
        if mapping:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(
                    f"**Control:** {mapping.get('control_ref_id', '—')}"
                )
            with col_b:
                st.markdown(
                    f"**Artifact Type:** {mapping.get('artifact_type', '—')}"
                )
            with col_c:
                st.markdown(
                    f"**Weightage:** {mapping.get('weightage', 0):.1f}%"
                )

            # Also show associated evidence
            ev_id = mapping.get("evidence_id", "")
            evidence_name = "—"
            if ev_id:
                ev = get_evidence_detail(ev_id)
                if ev:
                    evidence_name = ev.get("name", ev_id[:8] + "...")
            st.markdown(f"**Evidence:** {evidence_name}")
        else:
            st.info(f"Mapping details not available (ID: {entity_id[:8]}...)", icon="ℹ️")
    else:
        st.info(f"Entity type: {entity_type} (ID: {entity_id[:8]}...)", icon="ℹ️")

    st.markdown("---")

    # Submission info
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        st.markdown(f"**Submitted By:** {submitted_by_username}")
    with col_meta2:
        st.markdown(f"**Submitted At:** {created_at}")

    # Submission notes
    if review_notes:
        st.markdown("**Submission Notes:**")
        st.info(review_notes, icon="📝")

    st.markdown("---")

    # Action buttons for pending reviews only
    if workflow_status == "pending":
        st.markdown("**Actions**")
        action_cols = st.columns([1, 2, 2, 1])

        # Reject button
        with action_cols[1]:
            reject_key = f"detail_reject_{review['id']}"
            show_reject = st.session_state.get(reject_key, False)

            if not show_reject:
                if st.button(
                    "❌ Reject",
                    key=f"detail_reject_btn_{review['id']}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state[reject_key] = True
                    st.rerun()
            else:
                if st.button(
                    "↩️ Cancel",
                    key=f"detail_cancel_{review['id']}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state[reject_key] = False
                    st.rerun()

        # Approve button
        with action_cols[2]:
            if st.button(
                "✅ Approve",
                key=f"detail_approve_btn_{review['id']}",
                use_container_width=True,
                type="primary",
            ):
                if is_self:
                    st.error(
                        "❌ Cannot approve your own submission. "
                        "Self-approval is not allowed.",
                        icon="🚫",
                    )
                else:
                    with st.spinner("Approving review..."):
                        result = approve_review(
                            review_id=review["id"],
                            reviewer_id=user_id,
                        )
                        if result:
                            st.success("✅ Review approved successfully!", icon="✅")
                            st.rerun()

        # Reject notes
        if st.session_state.get(reject_key, False):
            st.markdown("---")
            st.markdown("**Rejection Notes**")
            notes = st.text_area(
                "Please provide the reason for rejection",
                key=f"detail_notes_{review['id']}",
                placeholder="Enter detailed reason for rejection...",
                height=100,
                label_visibility="collapsed",
            )
            if st.button(
                "✋ Confirm Rejection",
                key=f"detail_confirm_reject_{review['id']}",
                use_container_width=True,
                type="primary",
            ):
                if not notes or not notes.strip():
                    st.error(
                        "❌ Review notes are required for rejection. "
                        "Please enter the reason.",
                        icon="⚠️",
                    )
                else:
                    with st.spinner("Rejecting review..."):
                        result = reject_review(
                            review_id=review["id"],
                            reviewer_id=user_id,
                            review_notes=notes.strip(),
                        )
                        if result:
                            st.success("✅ Review rejected successfully!", icon="✅")
                            st.session_state[reject_key] = False
                            st.rerun()

    else:
        # Show status for non-pending reviews
        status = workflow_status
        status_color = _get_status_color(status)
        st.markdown(
            f"**Status:** "
            f"<span style='color:{status_color};font-weight:bold;'>"
            f"{status.upper()}</span>",
            unsafe_allow_html=True,
        )


def _render_review_history_tab() -> None:
    """Render the Review History tab with filtering."""
    st.subheader("📜 Review History")

    # Fetch all reviews
    all_reviews = get_reviews()
    if all_reviews is None:
        st.warning("Unable to load review history. Is the API running?")
        return

    # Filter to completed reviews only
    completed_reviews = [
        r for r in all_reviews
        if r.get("workflow_status") in ("approved", "rejected")
    ]

    if not completed_reviews:
        st.info(
            "No review history available. Completed reviews will appear here "
            "after reviews are approved or rejected.",
            icon="📜",
        )
        return

    # --- Filter Controls ---
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])

    with col_f1:
        decision_filter = st.selectbox(
            "Decision",
            options=DECISION_OPTIONS,
            index=0,
        )

    with col_f2:
        entity_type_filter = st.selectbox(
            "Entity Type",
            options=ENTITY_TYPE_OPTIONS,
            index=0,
        )

    with col_f3:
        # Date range: from
        min_date = date(2024, 1, 1)
        max_date = date.today()
        date_from = st.date_input(
            "From Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
        )

    with col_f4:
        # Date range: to
        date_to = st.date_input(
            "To Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
        )

    # --- Apply filters ---
    filtered_reviews = completed_reviews

    if decision_filter != "All Decisions":
        filtered_reviews = [
            r for r in filtered_reviews
            if r.get("workflow_status") == decision_filter
        ]

    if entity_type_filter != "All Types":
        filtered_reviews = [
            r for r in filtered_reviews
            if r.get("entity_type") == entity_type_filter
        ]

    # Date filter
    if date_from:
        dt_from = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        filtered_reviews = [
            r for r in filtered_reviews
            if r.get("updated_at") and datetime.fromisoformat(r["updated_at"]).replace(tzinfo=timezone.utc) >= dt_from
        ]

    if date_to:
        dt_to = datetime.combine(date_to, datetime.min.time()).replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
        filtered_reviews = [
            r for r in filtered_reviews
            if r.get("updated_at") and datetime.fromisoformat(r["updated_at"]).replace(tzinfo=timezone.utc) <= dt_to
        ]

    # Sort by updated_at (newest first)
    filtered_reviews.sort(
        key=lambda r: r.get("updated_at", ""),
        reverse=True,
    )

    st.markdown(
        f"*Showing {len(filtered_reviews)} of {len(completed_reviews)} completed reviews*"
    )

    if not filtered_reviews:
        st.info(
            "No reviews match your filter criteria. "
            "Try adjusting your filters.",
            icon="🔍",
        )
        return

    # --- Render history table ---
    for review in filtered_reviews:
        review_id = review["id"]
        entity_type = review.get("entity_type", "")
        entity_id = review.get("entity_id", "")
        entity_name = _resolve_entity_name(entity_type, entity_id)
        workflow_status = review.get("workflow_status", "")
        reviewed_by = review.get("reviewed_by_username") or "Unknown"
        updated_at = _format_datetime(review.get("updated_at"))
        review_notes = review.get("review_notes", "")

        status_color = _get_status_color(workflow_status)
        status_bg = STATUS_BG_COLORS.get(workflow_status, "#f9f9f9")
        status_label = "✅ Approved" if workflow_status == "approved" else "❌ Rejected"

        with st.container(border=True):
            cols = st.columns([1.2, 2.5, 1.2, 1.2, 1.5, 1])

            with cols[0]:
                st.markdown(
                    _get_entity_type_display(entity_type),
                )
            with cols[1]:
                st.markdown(f"**{entity_name}**")
            with cols[2]:
                st.markdown(
                    f"<span style='color:{status_color};font-weight:bold;'>"
                    f"{status_label}</span>",
                    unsafe_allow_html=True,
                )
            with cols[3]:
                st.markdown(f"👤 {reviewed_by}")
            with cols[4]:
                st.markdown(f"🕐 {updated_at}")
            with cols[5]:
                # Detail toggle
                expand_key = f"expand_history_{review_id}"
                is_expanded = st.session_state.get(expand_key, False)
                if st.button(
                    "📄 Detail" if not is_expanded else "▲ Close",
                    key=f"hist_btn_{review_id}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state[expand_key] = not is_expanded
                    st.rerun()

            # Expanded detail
            if st.session_state.get(expand_key, False):
                st.divider()
                st.markdown("### 📄 Review Details")
                if review_notes:
                    st.markdown("**Review Notes:**")
                    st.info(review_notes, icon="📝")
                else:
                    st.markdown("*No review notes provided.*")

                # Entity context
                with st.expander("📦 Entity Context", expanded=False):
                    if entity_type == "evidence_artifact":
                        evidence = get_evidence_detail(entity_id)
                        if evidence:
                            st.json({
                                "Name": evidence.get("name", ""),
                                "File Type": evidence.get("file_type", ""),
                                "Upload Date": evidence.get("uploaded_at", ""),
                            })
                        else:
                            st.info(f"ID: {entity_id}")
                    elif entity_type == "evidence_control_mapping":
                        mapping = get_mapping_detail(entity_id)
                        if mapping:
                            st.json({
                                "Control": mapping.get("control_ref_id", ""),
                                "Artifact Type": mapping.get("artifact_type", ""),
                                "Weightage": mapping.get("weightage", 0),
                            })
                        else:
                            st.info(f"ID: {entity_id}")
                    else:
                        st.info(f"Entity type: {entity_type}, ID: {entity_id}")


def _render_submit_tab() -> None:
    """Render the Submit for Review tab."""
    st.subheader("📤 Submit for Review")

    # Current user
    user_id, username = _get_current_user()
    if not user_id:
        st.info("Please select a user from the sidebar to submit reviews.", icon="👤")
        return

    st.markdown(
        "Submit an entity for review. This creates a review workflow record "
        "that reviewers can approve or reject."
    )

    with st.form("submit_review_form", clear_on_submit=True):
        entity_type = st.selectbox(
            "Entity Type",
            options=["evidence_artifact", "evidence_control_mapping"],
            help="Select the type of entity to submit for review",
        )

        entity_id = st.text_input(
            "Entity ID",
            placeholder="UUID of the entity (e.g., from the evidence library)",
            help="Paste the UUID of the evidence artifact or mapping",
        )

        review_notes = st.text_area(
            "Submission Notes (optional)",
            placeholder="Add any context or notes for the reviewer...",
            height=100,
        )

        submitted = st.form_submit_button(
            "📤 Submit for Review",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not entity_id.strip():
            st.warning("Please enter an Entity ID.", icon="⚠️")
            return

        with st.spinner("Submitting for review..."):
            result = submit_for_review(
                entity_type=entity_type,
                entity_id=entity_id.strip(),
                review_notes=review_notes.strip() if review_notes.strip() else None,
            )

            if result:
                st.success(
                    f"✅ Review submitted successfully! "
                    f"Review ID: `{result.get('id', '')[:8]}...`",
                    icon="🎉",
                )
                st.rerun()


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the Review Workflow page."""
    # Initialize session state for current user
    if "current_user_id" not in st.session_state:
        # Fetch default first user from API
        users = get_users()
        if users:
            st.session_state.current_user_id = users[0]["id"]
            st.session_state.current_user_name = users[0].get(
                "full_name", users[0].get("username", "Admin")
            )
        else:
            st.session_state.current_user_id = "00000000-0000-0000-0000-000000000000"
            st.session_state.current_user_name = "System"

    st.title("📋 Review Workflow")
    st.markdown(
        "Manage the review process for evidence artifacts and mappings. "
        "Approve or reject pending submissions and track review history."
    )

    # User selector in sidebar
    _render_user_selector()

    # Show pending count in header
    pending_count = get_pending_review_count()
    if pending_count > 0:
        st.info(
            f"📬 You have **{pending_count} pending review(s)** awaiting action.",
            icon="📬",
        )

    # Tabbed layout
    tab_queue, tab_history, tab_submit = st.tabs([
        f"📋 Review Queue ({pending_count})",
        "📜 Review History",
        "📤 Submit for Review",
    ])

    with tab_queue:
        _render_review_queue_tab()

    with tab_history:
        _render_review_history_tab()

    with tab_submit:
        _render_submit_tab()

    st.divider()
    st.caption(
        "GRC Platform MVP v0.1.0 | Review Workflow | "
        "Reviews are processed in the order they are submitted (FIFO)"
    )


if __name__ == "__main__":
    main()
