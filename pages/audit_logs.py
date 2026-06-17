"""GRC Platform - Audit Log Viewer Page.

Provides:
1. Audit log table in reverse chronological order with columns:
   timestamp, user, action, entity type, entity ID, IP address
2. Expandable rows showing full old_values and new_values JSON
3. Multi-select filter for action types
4. User selector filter and date range picker
5. Search field for entity IDs
6. Export button for filtered logs as CSV
7. Pagination with 50 entries per page
"""

import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Optional

import streamlit as st

from app.api_client import get_audit_logs, get_users

# Page configuration
st.set_page_config(
    page_title="Audit Log - GRC Platform",
    page_icon="📋",
    layout="wide",
)

# =============================================================================
# Constants
# =============================================================================

# Known action types matching the audit log data
ACTION_TYPE_OPTIONS = [
    "CREATE_EVIDENCE",
    "MAP_EVIDENCE",
    "SUBMIT_FOR_REVIEW",
    "APPROVE_REVIEW",
    "REJECT_REVIEW",
    "AGENT_CHAT",
    "AGENT_ANALYZE",
]

# Friendly display labels for action types
ACTION_TYPE_LABELS: dict[str, str] = {
    "CREATE_EVIDENCE": "📄 UPLOAD_EVIDENCE",
    "MAP_EVIDENCE": "🔗 MAP_EVIDENCE",
    "SUBMIT_FOR_REVIEW": "📤 SUBMIT_FOR_REVIEW",
    "APPROVE_REVIEW": "✅ APPROVE_REVIEW",
    "REJECT_REVIEW": "❌ REJECT_REVIEW",
    "AGENT_CHAT": "💬 AGENT_CHAT",
    "AGENT_ANALYZE": "🤖 AGENT_ANALYZE",
}

# Map display labels back to action values
DISPLAY_TO_ACTION: dict[str, str] = {
    v: k for k, v in ACTION_TYPE_LABELS.items()
}

PAGE_SIZE = 50

ACTION_COLORS: dict[str, str] = {
    "CREATE_EVIDENCE": "#2196F3",
    "UPLOAD_EVIDENCE": "#2196F3",
    "MAP_EVIDENCE": "#9C27B0",
    "SUBMIT_FOR_REVIEW": "#FF9800",
    "APPROVE_REVIEW": "#4CAF50",
    "REJECT_REVIEW": "#F44336",
    "AGENT_CHAT": "#00BCD4",
    "AGENT_ANALYZE": "#607D8B",
}

ACTION_BG_COLORS: dict[str, str] = {
    "CREATE_EVIDENCE": "#E3F2FD",
    "UPLOAD_EVIDENCE": "#E3F2FD",
    "MAP_EVIDENCE": "#F3E5F5",
    "SUBMIT_FOR_REVIEW": "#FFF3E0",
    "APPROVE_REVIEW": "#E8F5E9",
    "REJECT_REVIEW": "#FFEBEE",
    "AGENT_CHAT": "#E0F7FA",
    "AGENT_ANALYZE": "#ECEFF1",
}


# =============================================================================
# Helper Functions
# =============================================================================


def _get_action_color(action: str) -> str:
    """Get display color for an action type.

    Args:
        action: Action type string.

    Returns:
        CSS color string.
    """
    return ACTION_COLORS.get(action, "#999999")


def _get_action_bg_color(action: str) -> str:
    """Get background color for an action type badge.

    Args:
        action: Action type string.

    Returns:
        CSS background color string.
    """
    return ACTION_BG_COLORS.get(action, "#F5F5F5")


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
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return dt_str[:19] if dt_str and len(dt_str) >= 19 else dt_str or "—"


def _format_json_display(
    value: Optional[Any],
    label: str,
) -> str:
    """Format a JSON value for expandable display.

    Args:
        value: The JSON value (dict, list, or None).
        label: Label for the value section.

    Returns:
        Formatted markdown string.
    """
    if value is None:
        return f"**{label}:** `None`"
    if isinstance(value, dict) or isinstance(value, list):
        import json
        formatted = json.dumps(value, indent=2, default=str)
        return f"**{label}:**\n\n```json\n{formatted}\n```"
    return f"**{label}:** `{value}`"


def _export_to_csv(logs: list[dict[str, Any]]) -> bytes:
    """Export audit log entries to CSV format.

    Args:
        logs: List of audit log entry dicts.

    Returns:
        CSV content as bytes.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Timestamp",
        "User",
        "Action",
        "Entity Type",
        "Entity ID",
        "IP Address",
        "Old Values",
        "New Values",
    ])

    for log in logs:
        import json
        old_vals = json.dumps(log.get("old_values"), default=str) if log.get("old_values") else ""
        new_vals = json.dumps(log.get("new_values"), default=str) if log.get("new_values") else ""

        writer.writerow([
            _format_datetime(log.get("created_at")),
            log.get("user_username") or log.get("user_id", "")[:8] or "System",
            log.get("action", ""),
            log.get("entity_type", ""),
            log.get("entity_id", ""),
            log.get("ip_address", ""),
            old_vals,
            new_vals,
        ])

    return output.getvalue().encode("utf-8-sig")


# =============================================================================
# Main Render Functions
# =============================================================================


def _render_filters() -> tuple[
    Optional[list[str]],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """Render the filter controls for the audit log viewer.

    Returns:
        Tuple of (selected_actions, selected_user_id, date_from_str,
                  date_to_str, entity_id_search).
    """
    st.subheader("🔍 Filters")

    col1, col2 = st.columns([2, 1])
    with col1:
        # Multi-select for action types
        display_options = [ACTION_TYPE_LABELS.get(a, a) for a in ACTION_TYPE_OPTIONS]

        selected_displays = st.multiselect(
            "Action Types",
            options=display_options,
            default=None,
            placeholder="Select action types to filter...",
            help="Filter by one or more action types",
        )

        selected_actions: Optional[list[str]] = None
        if selected_displays:
            selected_actions = [
                DISPLAY_TO_ACTION.get(d, d) for d in selected_displays
            ]

    with col2:
        # Entity ID search
        entity_id_search = st.text_input(
            "🔍 Search Entity ID",
            placeholder="Enter entity ID...",
            help="Search for a specific entity ID (partial match)",
        )
        entity_id_search = entity_id_search.strip() or None

    # Second row: User filter and date range
    col_a, col_b, col_c = st.columns([2, 2, 2])

    with col_a:
        users = get_users()
        user_options: list[tuple[str, str]] = [("", "All Users")]
        for u in users:
            display = u.get("username", "") or u.get("full_name", "") or "Unknown"
            user_options.append((u["id"], f"{display} ({u.get('full_name', '')})"))

        selected_user_id = st.selectbox(
            "👤 User",
            options=[u[0] for u in user_options],
            format_func=lambda x: next(
                (u[1] for u in user_options if u[0] == x), "All Users"
            ),
            index=0,
            key="audit_user_select",
        )
        selected_user_id = selected_user_id or None

    with col_b:
        min_date = date(2024, 1, 1)
        max_date = date.today()
        date_from_val = st.date_input(
            "📅 From Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key="audit_date_from",
        )
        date_from_str: Optional[str] = (
            datetime.combine(date_from_val, datetime.min.time())
            .replace(tzinfo=timezone.utc)
            .isoformat()
            if date_from_val != min_date
            else None
        )

    with col_c:
        date_to_val = st.date_input(
            "📅 To Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key="audit_date_to",
        )
        date_to_str: Optional[str] = (
            datetime.combine(date_to_val, datetime.min.time())
            .replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            .isoformat()
            if date_to_val != max_date
            else None
        )

    return (
        selected_actions,
        selected_user_id,
        date_from_str,
        date_to_str,
        entity_id_search,
    )


def _render_audit_log_table(
    logs: list[dict[str, Any]],
    page: int,
    total_filtered: int,
) -> None:
    """Render the audit log entries table with expandable rows.

    Args:
        logs: List of audit log entries for the current page.
        page: Current page number (0-indexed).
        total_filtered: Total number of matching entries.
    """
    if not logs:
        st.info(
            "No audit log entries match your filter criteria. "
            "Try adjusting your filters or clearing search terms.",
            icon="📋",
        )
        return

    # Column headers
    cols = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1, 0.8])
    headers = ["Timestamp", "User", "Action", "Entity Type", "Entity ID", "IP Address", "Details"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")

    st.divider()

    # Render each log entry
    for i, log in enumerate(logs):
        log_id = log.get("id", f"log_{i}")
        timestamp = _format_datetime(log.get("created_at"))
        username = log.get("user_username") or "System"
        action = log.get("action", "")
        entity_type = log.get("entity_type", "")
        entity_id = log.get("entity_id", "") or "—"
        ip_address = log.get("ip_address", "") or "—"
        old_values = log.get("old_values")
        new_values = log.get("new_values")

        action_color = _get_action_color(action)
        action_bg = _get_action_bg_color(action)

        expand_key = f"expand_audit_{log_id}"

        with st.container(border=True):
            # Main row
            row_cols = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1, 0.8])

            with row_cols[0]:
                st.markdown(
                    f"<span style='font-size:13px; white-space:nowrap;'>{timestamp}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[1]:
                st.markdown(
                    f"<span style='font-size:13px;'>{username}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[2]:
                st.markdown(
                    f"<span style='background:{action_bg};color:{action_color};"
                    f"padding:2px 6px;border-radius:4px;font-size:12px;"
                    f"font-weight:bold;white-space:nowrap;'>{action}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[3]:
                st.markdown(
                    f"<span style='font-size:13px;'>{entity_type}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[4]:
                entity_display = entity_id[:16] + "..." if len(str(entity_id)) > 16 else entity_id
                st.markdown(
                    f"<span style='font-size:12px;font-family:monospace;'>{entity_display}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[5]:
                st.markdown(
                    f"<span style='font-size:12px;font-family:monospace;'>{ip_address}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[6]:
                is_expanded = st.session_state.get(expand_key, False)
                if st.button(
                    "▼" if not is_expanded else "▲",
                    key=f"expand_btn_{log_id}",
                    help="Toggle details",
                    type="secondary",
                    use_container_width=True,
                ):
                    st.session_state[expand_key] = not is_expanded
                    st.rerun()

            # Expanded detail panel showing old_values and new_values JSON
            if st.session_state.get(expand_key, False):
                st.divider()
                st.markdown("### 📋 Full Details")

                # Metadata section
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"**Log ID:** `{log_id}`")
                    st.markdown(f"**Timestamp:** {timestamp}")
                    st.markdown(f"**User:** {username} (ID: `{log.get('user_id', '—')}`)")
                with col_m2:
                    st.markdown(f"**Action:** `{action}`")
                    st.markdown(f"**Entity Type:** `{entity_type}`")
                    st.markdown(f"**Entity ID:** `{entity_id}`")
                    st.markdown(f"**IP Address:** `{ip_address}`")

                st.divider()

                # JSON values in expandable sections
                import json

                jcol1, jcol2 = st.columns(2)
                with jcol1:
                    with st.expander("📦 Old Values", expanded=old_values is not None):
                        if old_values is not None:
                            st.code(
                                json.dumps(old_values, indent=2, default=str),
                                language="json",
                            )
                        else:
                            st.caption("No old values recorded.")

                with jcol2:
                    with st.expander("📦 New Values", expanded=new_values is not None):
                        if new_values is not None:
                            st.code(
                                json.dumps(new_values, indent=2, default=str),
                                language="json",
                            )
                        else:
                            st.caption("No new values recorded.")


def _render_pagination(
    page: int,
    total_filtered: int,
) -> int:
    """Render pagination controls.

    Args:
        page: Current page number (0-indexed).
        total_filtered: Total number of matching entries.

    Returns:
        Updated page number.
    """
    total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

    st.divider()

    col_info, col_prev, col_page_info, col_next, col_gap = st.columns([2, 1, 2, 1, 2])

    with col_info:
        start_idx = page * PAGE_SIZE + 1
        end_idx = min((page + 1) * PAGE_SIZE, total_filtered)
        st.markdown(
            f"*Showing **{start_idx}–{end_idx}** of **{total_filtered}** entries*"
        )

    with col_prev:
        if st.button(
            "◀ Previous",
            key="prev_page",
            disabled=page <= 0,
            use_container_width=True,
            type="secondary",
        ):
            return page - 1

    with col_page_info:
        st.markdown(
            f"<div style='text-align:center;'>Page **{page + 1}** of **{total_pages}**</div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button(
            "Next ▶",
            key="next_page",
            disabled=page >= total_pages - 1,
            use_container_width=True,
            type="secondary",
        ):
            return page + 1

    return page


def _render_export_button(logs: list[dict[str, Any]]) -> None:
    """Render the CSV export button.

    Args:
        logs: Full list of filtered logs to export.
    """
    if not logs:
        return

    csv_bytes = _export_to_csv(logs)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    st.download_button(
        label="📥 Export CSV",
        data=csv_bytes,
        file_name=f"audit_logs_{timestamp_str}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
        help="Download filtered audit logs as a CSV file",
    )


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the Audit Log Viewer page."""
    st.title("📋 Audit Log Viewer")
    st.markdown(
        "View all system audit log entries in reverse chronological order. "
        "Use the filters below to narrow down results by action type, user, "
        "date range, or entity ID."
    )

    # Render filters
    (
        selected_actions,
        selected_user_id,
        date_from_str,
        date_to_str,
        entity_id_search,
    ) = _render_filters()

    # Export section (above table)
    st.divider()

    # Fetch all logs matching filters (with a high limit for export)
    # First get total count with a small limit
    all_logs = get_audit_logs(
        actions=selected_actions,
        user_id=selected_user_id,
        date_from=date_from_str,
        date_to=date_to_str,
        entity_id_search=entity_id_search,
        limit=1000,
        offset=0,
    )

    if all_logs is None:
        st.warning("Unable to load audit logs. Is the API running?")
        return

    total_filtered = len(all_logs)

    # Pagination
    page = st.session_state.get("audit_page", 0)

    # Reset page when filters change
    filter_key = str(selected_actions) + str(selected_user_id) + str(date_from_str) + str(date_to_str) + str(entity_id_search)
    if st.session_state.get("audit_filter_key", "") != filter_key:
        st.session_state.audit_page = 0
        st.session_state.audit_filter_key = filter_key
        page = 0

    total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)
    if page >= total_pages:
        page = total_pages - 1
        st.session_state.audit_page = page

    # Get the slice for current page
    page_start = page * PAGE_SIZE
    page_end = page_start + PAGE_SIZE
    page_logs = all_logs[page_start:page_end]

    # Export button
    export_col, _ = st.columns([1, 5])
    with export_col:
        _render_export_button(all_logs)

    # Summary
    if total_filtered > 0:
        st.markdown(f"*{total_filtered} total log entries*")

    # Render table
    _render_audit_log_table(page_logs, page, total_filtered)

    # Pagination controls
    if total_filtered > PAGE_SIZE:
        new_page = _render_pagination(page, total_filtered)
        if new_page != page:
            st.session_state.audit_page = new_page
            st.rerun()

    # Footer
    st.divider()
    st.caption(
        "GRC Platform MVP v0.1.0 | Audit Log Viewer | "
        "Audit logs are immutable and INSERT-only."
    )


if __name__ == "__main__":
    main()
