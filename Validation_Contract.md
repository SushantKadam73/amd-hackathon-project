# GRC Platform MVP - Validation Assertions
# Areas: Dashboard & Reporting, Review Workflow, Audit Logging, Cross-Area Flows
# NIST SP 800-53 Controls: PE-03, AC-02, SC-07, IR-06, RA-05

---

## AREA 1: Dashboard & Reporting

### VAL-DASHBOARD-001: Overall Compliance Score Display
- **Behavioral description:** The dashboard displays a single aggregate compliance score (0-100%) computed as the weighted average of all 5 controls (PE-03, AC-02, SC-07, IR-06, RA-05). The score must reflect the current state of evidence mappings and validations. On first visit with no data, the score shows 0% with an informational message indicating no evidence has been uploaded.
- **Tool:** Streamlit UI inspection + API response validation
- **Evidence:** Screenshot of dashboard widget; API response from `/api/v1/reports/compliance-status` showing score field; calculation verification against evidence_control_mappings table

### VAL-DASHBOARD-002: Per-Control Compliance Status Cards
- **Behavioral description:** The dashboard renders exactly 5 control status cards, one for each NIST SP 800-53 control (PE-03, AC-02, SC-07, IR-06, RA-05). Each card displays: control ID, control title, compliance status (Fully Mapped / Partially Mapped / Unmapped), the evidence count mapped, and the weightage coverage percentage. Status is determined by: Fully Mapped >= 90% artifacts present and validated; Partially Mapped 50-89%; Unmapped < 50% or critical artifacts missing.
- **Tool:** Streamlit UI inspection + DB query verification
- **Evidence:** Screenshot of 5 cards; SQL query on evidence_control_mappings joined with controls showing matching status values

### VAL-DASHBOARD-003: Risk Heatmap Visualization
- **Behavioral description:** The dashboard renders a risk heatmap matrix (control vs. risk level) where each cell is color-coded: green (low risk / fully mapped), yellow (medium risk / partially mapped), red (high risk / unmapped). The heatmap must include all 5 controls on one axis and risk levels (low, medium, high, critical) on the other. Tooltip on hover shows the exact risk score and gap count for that cell.
- **Tool:** Streamlit UI inspection (st.plotly_chart or st.altair_chart)
- **Evidence:** Screenshot of heatmap; API response from `/api/v1/reports/risk-heatmap` with data points for all 5 controls

### VAL-DASHBOARD-004: Gap Summary Report Widget
- **Behavioral description:** The dashboard displays a gap summary widget showing: total open gaps, gaps by severity (critical, high, medium, low), and the oldest open gap age. The widget updates in real-time when new gaps are created or resolved. When no gaps exist, it displays "No open gaps" with a green indicator.
- **Tool:** Streamlit UI inspection + API call to `/api/v1/reports/gap-summary`
- **Evidence:** Screenshot of gap summary; API response with gap_counts by severity; verification that creating a new gap immediately reflects in the widget after page refresh

### VAL-DASHBOARD-005: Evidence Upload Progress Tracker
- **Behavioral description:** The dashboard shows an evidence collection progress tracker for each control family, displaying the number of uploaded artifacts vs. required artifact types (e.g., "3/6 artifact types for PE-03"). Progress bars are color-coded: green >= 80%, yellow 50-79%, red < 50%. Artifact type categories match the framework research: Policy Documents, Procedures, Access Lists, System Configs, Audit Logs, Training Records, Inspection Reports (varying by control).
- **Tool:** Streamlit UI inspection + evidence_artifacts table query
- **Evidence:** Screenshot of progress tracker; DB query counting evidence_artifacts grouped by control_id and file_type; verification that upload count matches displayed value

### VAL-DASHBOARD-006: Framework Comparison View
- **Behavioral description:** The dashboard provides a comparison view showing how the 5 NIST SP 800-53 controls map to equivalent controls in NIST CSF 2.0, CIS Controls v8, and PCI DSS v4.0.1. The view displays at least the direct mappings defined in the cross-framework matrix (e.g., PE-03 -> PR.AA-06, CIS 6, PCI 9.2/9.3). Missing mappings show "No mapping defined."
- **Tool:** Streamlit UI inspection + control_mappings table query
- **Evidence:** Screenshot of comparison view; DB query on control_mappings showing at least 5 direct mappings

### VAL-DASHBOARD-007: Dashboard Filter Controls
- **Behavioral description:** The dashboard provides filters for: (1) Framework selector (default: NIST SP 800-53), (2) Status filter (All, Fully Mapped, Partially Mapped, Unmapped), (3) Risk level filter (All, Critical, High, Medium, Low), (4) Date range picker for evidence upload date. Applying any filter immediately refreshes all dashboard widgets to show only matching data. Filters are combinable (AND logic).
- **Tool:** Streamlit UI interaction (selectbox, multiselect, date_input)
- **Evidence:** Screenshot of filter panel; video recording of filter application causing widget refresh; API response showing filtered results

### VAL-DASHBOARD-008: First Visit Empty State
- **Behavioral description:** On first visit with no uploaded evidence and no controls configured, the dashboard displays an onboarding/empty state message guiding the user to: (1) Upload evidence artifacts, (2) Map evidence to controls, (3) Run gap analysis. No error messages or broken visualizations appear. All widgets gracefully handle empty data with placeholder content.
- **Tool:** Streamlit UI inspection (fresh database)
- **Evidence:** Screenshot of empty state dashboard; verification that no JavaScript errors or Streamlit exceptions are thrown

### VAL-DASHBOARD-009: Dashboard Data Freshness Indicator
- **Behavioral description:** The dashboard displays a "Last updated" timestamp showing when dashboard data was last refreshed. A manual "Refresh" button forces immediate recalculation of all metrics. The timestamp updates to current time after refresh. Auto-refresh occurs at minimum every 5 minutes if the page remains open.
- **Tool:** Streamlit UI inspection + timer verification
- **Evidence:** Screenshot showing timestamp; recording of clicking refresh and timestamp updating; verification of auto-refresh after 5-minute wait

### VAL-DASHBOARD-010: Compliance Score Calculation Consistency
- **Behavioral description:** The aggregate compliance score displayed on the dashboard exactly matches a manual calculation: sum of (per-control score * control weight) / total weight across all 5 controls. Per-control score = (validated evidence weightage sum / total required weightage for that control) * 100. The score must never exceed 100% or go below 0%.
- **Tool:** API response validation + manual calculation
- **Evidence:** API response from `/api/v1/reports/compliance-status` with per-control breakdown; manual calculation spreadsheet matching displayed aggregate score

### VAL-DASHBOARD-011: Control Detail Drill-Down Link
- **Behavioral description:** Each control status card on the dashboard is clickable and navigates to the detailed control view page. The navigation preserves the selected filter context. The detail page shows: full control description, all mapped evidence, mapping status, gap analyses, review status, and activity timeline.
- **Tool:** Streamlit page navigation + URL verification
- **Evidence:** Recording of clicking PE-03 card and arriving at control detail page showing PE-03's full description and mapped evidence list

### VAL-DASHBOARD-012: Report Export Functionality
- **Behavioral description:** The dashboard provides an "Export Report" button that generates a downloadable report in PDF and Excel formats. The export includes: compliance scores, per-control status, gap summary, evidence list, and risk heatmap. The export must complete within 30 seconds and produce a valid, non-corrupted file.
- **Tool:** File download verification + content validation
- **Evidence:** Downloaded PDF and Excel files; verification that PDF opens correctly and contains all sections; Excel file has correct sheet names and data

---

## AREA 2: Review Workflow

### VAL-REVIEW-001: Submit Evidence for Review
- **Behavioral description:** When a user clicks "Submit for Review" on an evidence artifact, a review workflow record is created with status "pending", the current user as submitted_by, and a timestamp. The evidence artifact's mapping_status in evidence_control_mappings changes from "pending" to "pending_review". The submission is recorded in the audit log with action "SUBMIT_FOR_REVIEW".
- **Tool:** API call to POST `/api/v1/reviews` + DB verification
- **Evidence:** API response with review ID; audit_logs table showing SUBMIT_FOR_REVIEW entry; evidence_control_mappings showing updated status

### VAL-REVIEW-002: Submit Mapping for Review
- **Behavioral description:** When a user submits a control mapping (evidence-to-control association) for review, a review workflow record is created with entity_type="mapping". The review record references the specific evidence_control_mapping ID. The reviewer receives the submission with full context: evidence name, target control, weightage, and submission notes.
- **Tool:** API call to POST `/api/v1/reviews` with entity_type="mapping" + UI verification
- **Evidence:** Review workflow record in DB; UI showing review queue with mapping context details

### VAL-REVIEW-003: Approve Review Action
- **Behavioral description:** When a reviewer clicks "Approve" on a pending review: (1) review_workflow status changes to "approved", (2) reviewed_by is set to the current reviewer, (3) reviewed_at is set to current timestamp, (4) the underlying entity (evidence mapping) status changes to "approved", (5) the approval is logged in audit_logs with action "APPROVE_REVIEW", (6) a notification badge count decrements for the reviewer. Approvals by the original submitter are blocked (same user cannot approve their own submission).
- **Tool:** API call to PUT `/api/v1/reviews/{id}/approve` + DB verification
- **Evidence:** review_workflows record with status="approved"; evidence_control_mappings with status="approved"; audit_logs entry; notification count change

### VAL-REVIEW-004: Reject Review Action
- **Behavioral description:** When a reviewer clicks "Reject" on a pending review: (1) review_workflow status changes to "rejected", (2) review_notes are required (empty notes cause a validation error with HTTP 422), (3) the underlying entity status changes to "rejected", (4) rejection is logged in audit_logs with action "REJECT_REVIEW", (5) the original submitter can see the rejection reason and resubmit.
- **Tool:** API call to PUT `/api/v1/reviews/{id}/reject` + DB verification + validation error test
- **Evidence:** review_workflows record with status="rejected" and review_notes; evidence_control_mappings with status="rejected"; audit_logs entry; API returning 422 when notes are empty

### VAL-REVIEW-005: Review Queue Display
- **Behavioral description:** The review queue page shows all pending reviews sorted by submission date (oldest first). Each queue item displays: entity type (evidence/mapping), entity name, submitted by, submitted at, and a brief description. The queue shows exactly the pending reviews assigned to or visible to the current user based on their role. Reviewers see all pending reviews; analysts see only their own submissions' status.
- **Tool:** Streamlit UI inspection + API call to GET `/api/v1/reviews/my-pending`
- **Evidence:** Screenshot of review queue; API response with pending reviews; role-based filtering verification with different user accounts

### VAL-REVIEW-006: Review History Tab
- **Behavioral description:** The review history page shows all completed reviews (approved and rejected) with: reviewer name, decision, timestamp, review notes, and link to the reviewed entity. History is filterable by: decision (approved/rejected), entity type, date range, and reviewer. Pagination shows 20 items per page with navigation controls.
- **Tool:** Streamlit UI inspection + API call to GET `/api/v1/reviews` with status filter
- **Evidence:** Screenshot of review history; API response with completed reviews; filter application changing displayed results

### VAL-REVIEW-007: Review State Transition Validity
- **Behavioral description:** Review workflows follow strict state transitions: pending -> approved OR pending -> rejected. Any attempt to approve/reject an already-approved or already-rejected review returns HTTP 409 Conflict. An attempt to approve a review that is no longer pending returns an error message. State can only move forward (no reverting approved/rejected back to pending without creating a new review).
- **Tool:** API calls attempting invalid state transitions
- **Evidence:** HTTP 409 response when approving an already-approved review; HTTP 409 response when rejecting an already-rejected review; DB showing no state regression

### VAL-REVIEW-008: Self-Approval Prevention
- **Behavioral description:** A user who submitted an evidence artifact or mapping for review cannot approve their own submission. The approve endpoint checks submitted_by against the current user and returns HTTP 403 Forbidden with message "Cannot approve your own submission" when they match.
- **Tool:** API call attempting self-approval
- **Evidence:** HTTP 403 response from PUT `/api/v1/reviews/{id}/approve` when reviewer ID matches submitted_by; audit_logs showing no self-approval recorded

### VAL-REVIEW-009: Notification Badge Count
- **Behavioral description:** The navigation bar displays a notification badge showing the count of pending reviews visible to the current user. The count updates in real-time (within 5 seconds) when: a new review is submitted, a review is approved/rejected, or the user navigates to the review page. Clicking the badge navigates to the review queue.
- **Tool:** Streamlit UI inspection + real-time state change
- **Evidence:** Screenshot showing badge; recording of badge count changing from 2 to 3 after new submission; recording of badge count decreasing after approval

### VAL-REVIEW-010: Review Context Panel
- **Behavioral description:** When viewing a specific review, the detail panel shows: full entity details (evidence file info or mapping details), submission notes from the submitter, the control(s) involved, current evidence coverage for that control, and any related gap analyses. The reviewer has access to approve/reject buttons only when the review status is "pending".
- **Tool:** Streamlit UI inspection on review detail page
- **Evidence:** Screenshot of review detail panel showing entity context; verification that approve/reject buttons are hidden for non-pending reviews

### VAL-REVIEW-011: Bulk Review Operations
- **Behavioral description:** The review queue supports selecting multiple pending reviews via checkboxes and performing bulk approve or bulk reject. Bulk reject requires a shared rejection note. Each item in the bulk operation is processed as an individual transaction; if one fails, the others that succeeded remain approved/rejected (no rollback of entire batch). The user sees a summary of how many succeeded and how many failed.
- **Tool:** Streamlit UI interaction + API batch endpoint
- **Evidence:** Recording of selecting 3 reviews and clicking bulk approve; audit_logs showing 3 separate APPROVE_REVIEW entries; UI showing "3 of 3 approved" summary message

### VAL-REVIEW-012: Review Escalation on Timeout
- **Behavioral description:** If a review remains in "pending" status for more than 72 hours, the system flags it as "overdue" and displays an escalation indicator (red badge). Overdue reviews appear at the top of the queue regardless of submission date. The escalation is logged in audit_logs with action "REVIEW_ESCALATED".
- **Tool:** DB update to simulate old pending review + UI verification
- **Evidence:** Audit_logs entry for REVIEW_ESCALATED; UI showing red badge on overdue review; queue ordering showing overdue items first

---

## AREA 3: Audit Logging

### VAL-AUDIT-001: Evidence Upload Logging
- **Behavioral description:** Every evidence artifact upload creates an audit log entry with: action="UPLOAD_EVIDENCE", entity_type="evidence", entity_id=new artifact ID, user_id=uploader, new_values containing {name, file_type, file_size, control_id (if mapped)}, ip_address, and timestamp. The log entry is created atomically with the evidence record insertion.
- **Tool:** API call to POST `/api/v1/evidence` + audit_logs query
- **Evidence:** audit_logs table entry with action="UPLOAD_EVIDENCE"; new_values JSON containing uploaded file metadata; timestamp within 1 second of upload time

### VAL-AUDIT-002: Evidence Mapping Logging
- **Behavioral description:** Every evidence-to-control mapping creation or modification creates an audit log entry with: action="MAP_EVIDENCE" or "UPDATE_EVIDENCE_MAPPING", entity_type="evidence_control_mapping", old_values (for updates), new_values containing {evidence_id, control_id, weightage, mapping_status}. Both the initial mapping and any subsequent weightage or status changes are logged.
- **Tool:** API call to POST `/api/v1/evidence/{id}/map-to-control` + audit_logs query
- **Evidence:** audit_logs entries for mapping creation and update; old_values populated for update operations; new_values containing mapping details

### VAL-AUDIT-003: Review Action Logging
- **Behavioral description:** Every review workflow action creates an audit log entry: submission (action="SUBMIT_FOR_REVIEW"), approval (action="APPROVE_REVIEW"), rejection (action="REJECT_REVIEW"). Each entry includes: entity_type, entity_id, user_id, old_values (previous status), new_values (new status + review_notes for approve/reject), and timestamp.
- **Tool:** Full review lifecycle execution + audit_logs query
- **Evidence:** Three audit log entries for submit->approve cycle; review_notes captured in new_values for rejection; timestamps in chronological order

### VAL-AUDIT-004: Control and Framework Modification Logging
- **Behavioral description:** Any CRUD operation on controls or frameworks creates audit log entries: CREATE_CONTROL, UPDATE_CONTROL, DELETE_CONTROL, CREATE_FRAMEWORK, UPDATE_FRAMEWORK, DELETE_FRAMEWORK. Each entry captures old_values and new_values as JSONB with the changed fields. Soft deletes log the is_active=false change rather than physical deletion.
- **Tool:** API calls to create/update/delete controls + audit_logs query
- **Evidence:** audit_logs entries for each operation type; old_values containing previous state for updates; new_values containing new state

### VAL-AUDIT-005: Gap Analysis Logging
- **Behavioral description:** Gap analysis creation, updates, and resolution are logged: action="CREATE_GAP" when a gap is identified, action="UPDATE_GAP" when remediation plan or status changes, action="RESOLVE_GAP" when status changes to "closed". Each entry includes risk_level, risk_score changes, and remediation plan text in new_values.
- **Tool:** API calls to gap-analyses endpoints + audit_logs query
- **Evidence:** audit_logs entries for gap lifecycle; risk_score changes captured in old_values/new_values; RESOLVE_GAP entry when status transitions to closed

### VAL-AUDIT-006: AI Agent Action Logging
- **Behavioral description:** AI agent interactions are logged: action="AGENT_CHAT" for chatbot queries, action="AGENT_ANALYZE" for evidence analysis, action="AGENT_SUGGEST" for mapping suggestions. Each entry includes: session_id, input_summary (truncated to 500 chars), output_summary, confidence_score, and model_used. PII is never logged in audit entries.
- **Tool:** Agent interaction execution + audit_logs query
- **Evidence:** audit_logs entries with AGENT_CHAT action; input_summary does not contain PII; model_used field populated; confidence_score present for analysis/suggestion actions

### VAL-AUDIT-007: Audit Log Viewer - List View
- **Behavioral description:** The audit log viewer page displays logs in reverse chronological order (newest first) with columns: timestamp, user, action, entity type, entity ID (linked), and IP address. The viewer loads with pagination (50 entries per page) and displays total entry count. Each row is expandable to show full old_values and new_values JSON.
- **Tool:** Streamlit UI inspection + API call to GET `/api/v1/audit-logs`
- **Evidence:** Screenshot of audit log table; API response with 50 entries; expandable row showing JSON details

### VAL-AUDIT-008: Audit Log Filtering by Action Type
- **Behavioral description:** The audit log viewer provides a multi-select filter for action types (UPLOAD_EVIDENCE, MAP_EVIDENCE, SUBMIT_FOR_REVIEW, APPROVE_REVIEW, etc.). Selecting one or more action types filters the log to show only matching entries. Filter state persists across page navigation within the session.
- **Tool:** Streamlit UI interaction with filter controls
- **Evidence:** Screenshot of filter panel with action type checkboxes; recording of selecting "APPROVE_REVIEW" and seeing only approval entries; verification of filter persistence

### VAL-AUDIT-009: Audit Log Filtering by User and Date Range
- **Behavioral description:** The audit log viewer provides: (1) a user selector dropdown populated from the users table, (2) a date range picker (start date, end date). Applying these filters restricts logs to the selected user's actions within the date range. Filters are combinable with action type filter using AND logic.
- **Tool:** Streamlit UI interaction + API call with filter parameters
- **Evidence:** API response showing filtered results; recording of applying user + date filter and seeing narrowed results

### VAL-AUDIT-010: Audit Log Search by Entity
- **Behavioral description:** The audit log viewer provides a search field that accepts entity IDs (UUIDs) or entity names. Searching for an entity ID shows all audit entries related to that entity across all action types. A dedicated entity history view is accessible by clicking an entity ID link in any audit log row, showing the complete audit trail for that specific entity.
- **Tool:** Streamlit UI search + API call to GET `/api/v1/audit-logs/entity/{type}/{id}`
- **Evidence:** Search results showing all entries for a specific evidence artifact; entity history page showing chronological operations on one entity

### VAL-AUDIT-011: Audit Log Immutability
- **Behavioral description:** Audit log entries cannot be modified or deleted through any user interface or API endpoint. The audit_logs table has no UPDATE or DELETE API endpoints. Attempting to call DELETE on `/api/v1/audit-logs/{id}` returns HTTP 405 Method Not Allowed. Log entries include only INSERT operations with automatic timestamps.
- **Evidence:** HTTP 405 response from DELETE attempt; audit_logs table schema verification showing no soft-delete column; API endpoint list confirming no update/delete endpoints for audit logs

### VAL-AUDIT-012: Audit Log Export
- **Behavioral description:** The audit log viewer provides an "Export" button that downloads filtered logs as CSV. The export includes all visible columns plus full old_values and new_values as JSON strings. The export respects current filters (only exports what is displayed). Export completes within 30 seconds for up to 10,000 entries.
- **Tool:** File download + content validation
- **Evidence:** Downloaded CSV file; verification that CSV contains filtered data only; column headers match displayed columns; JSON values parse correctly

### VAL-AUDIT-013: Audit Log Timestamp Accuracy
- **Behavioral description:** All audit log timestamps are in UTC and accurate to within 1 second of the actual action time. Timestamps are generated server-side (not client-side) and cannot be manipulated by the user. The created_at field uses PostgreSQL's CURRENT_TIMESTAMP default and is never overwritten.
- **Tool:** API call + timestamp comparison with server time
- **Evidence:** audit_logs.created_at within 1 second of curl request timestamp; verification that created_at is server-generated

---

## AREA 4: Cross-Area Flows

### VAL-CROSS-001: Evidence Upload -> Map to Control -> AI Review -> Approve
- **Behavioral description:** The end-to-end flow works as follows: (1) User uploads an evidence artifact via POST `/api/v1/evidence` -> audit log entry created -> artifact appears in evidence list. (2) User maps evidence to PE-03 control via POST `/api/v1/evidence/{id}/map-to-control` with weightage -> audit log entry created -> mapping appears on control detail page. (3) User submits mapping for review via POST `/api/v1/reviews` -> review_workflow record created with status "pending" -> notification badge increments. (4) Reviewer approves via PUT `/api/v1/reviews/{id}/approve` -> mapping status changes to "approved" -> audit log entry created -> compliance score updates. The entire flow produces at least 3 audit log entries and changes the compliance score for PE-03.
- **Tool:** API sequence execution + DB verification + dashboard verification
- **Evidence:** Step-by-step API responses; 3+ audit_logs entries in chronological order; compliance score increase on dashboard; evidence_control_mappings status progression: pending -> pending_review -> approved

### VAL-CROSS-002: Chatbot Query -> Get Answer -> Navigate to Control
- **Behavioral description:** (1) User sends a chatbot query "What evidence is needed for PE-03?" via POST `/api/v1/agent/chat`. (2) The agent responds with a structured answer listing required artifact types for PE-03 and current coverage status. (3) The response includes a clickable link/reference to the PE-03 control detail page. (4) Clicking the link navigates to the control detail page showing PE-03's full requirements, mapped evidence, and gaps. (5) The chatbot session is logged in agent_sessions and audit_logs.
- **Tool:** API call sequence + UI navigation
- **Evidence:** Chatbot response text containing PE-03 artifact types; navigation to control page; agent_sessions record; audit_logs entry with AGENT_CHAT action

### VAL-CROSS-003: Dashboard -> Drill Down to Control -> View Evidence
- **Behavioral description:** (1) User starts on the dashboard and sees PE-03 card showing "Partially Mapped" status. (2) User clicks PE-03 card, navigating to the control detail page. (3) Control detail page shows PE-03 description, all mapped evidence (3 artifacts), unmapped artifact types (3 gaps), and a gap analysis section. (4) User clicks on one evidence artifact name, navigating to the evidence detail page showing file info, content preview, and mapping history. (5) The breadcrumb navigation shows: Dashboard > Controls > PE-03 > Evidence: [name].
- **Tool:** Streamlit page navigation + URL verification
- **Evidence:** Recording of full navigation flow; each page renders correctly; breadcrumb navigation shows correct path; evidence detail page shows file metadata

### VAL-CROSS-004: Gap Detection -> Remediation -> Evidence Upload -> Resolution
- **Behavioral description:** (1) Gap analysis identifies a missing artifact for AC-02 (gap_description: "No account inventory uploaded", risk_level: "high"). (2) Dashboard reflects the gap in the gap summary widget. (3) User uploads the missing evidence (account inventory document). (4) User maps evidence to AC-02 and submits for review. (5) Reviewer approves. (6) Gap status changes to "resolved" (or is auto-resolved when evidence coverage meets threshold). (7) Dashboard compliance score for AC-02 increases. (8) The entire chain produces audit log entries for gap creation, evidence upload, mapping, review, and resolution.
- **Tool:** Multi-step API execution + DB verification
- **Evidence:** Gap record with status="open"; evidence upload and mapping records; review workflow approval; gap record status change; compliance score increase; 5+ audit log entries covering the full lifecycle

### VAL-CROSS-005: Multi-Control Evidence Mapping with Weightage
- **Behavioral description:** A single evidence artifact (e.g., "Physical Security Policy v2.1") is mapped to multiple controls simultaneously: PE-03 (weightage 15%) and AC-02 (weightage 10%). Both mappings appear on the evidence detail page. Both control detail pages show this evidence in their mapped artifacts list. Updating the evidence (re-uploading a new version) reflects on both control pages. The compliance score calculations for both PE-03 and AC-02 account for this shared evidence.
- **Tool:** API calls to map one evidence to two controls + verification
- **Evidence:** evidence_control_mappings table showing 2 records for same evidence_id; both PE-03 and AC-02 detail pages listing the evidence; compliance score calculations including shared weightage

### VAL-CROSS-006: Notification Propagation Across Areas
- **Behavioral description:** When a user submits evidence for review, the notification propagates correctly: (1) The reviewer's notification badge increments on their next page load. (2) The review queue shows the new pending item. (3) The audit log records the submission. (4) The dashboard's "pending reviews" count updates. All four areas reflect the state change consistently within one page refresh cycle.
- **Tool:** Multi-user UI session + state verification
- **Evidence:** Notification badge count change; review queue showing new item; audit_logs entry; dashboard pending count updated; all within same refresh

### VAL-CROSS-007: AI-Suggested Mapping -> Manual Review -> Approval
- **Behavioral description:** (1) User requests AI mapping suggestions via POST `/api/v1/agent/suggest-mapping` for SC-07 boundary protection. (2) The agent analyzes the evidence and suggests mapping "Firewall_Rule_Set_2024.pdf" to SC-07 with confidence 0.85. (3) User reviews the suggestion and accepts it, creating an evidence_control_mapping. (4) The mapping is submitted for review. (5) A reviewer approves it. (6) The AI suggestion, user acceptance, and reviewer approval are all logged in audit_logs as separate entries with distinct action types.
- **Tool:** API sequence + audit_logs verification
- **Evidence:** AI suggestion response with confidence score; mapping creation record; review workflow record; 3 distinct audit log entries (AGENT_SUGGEST, MAP_EVIDENCE, APPROVE_REVIEW)

### VAL-CROSS-008: Framework Comparison with Evidence Status
- **Behavioral description:** From the dashboard's framework comparison view, a user can see how evidence uploaded for NIST SP 800-53 controls also satisfies mapped controls in NIST CSF 2.0, CIS v8, and PCI DSS. For example, PE-03 evidence mapped as "Fully Mapped" also shows PR.AA-06 (NIST CSF) as satisfied. The cross-framework view reflects real-time evidence status, not static mapping definitions.
- **Tool:** Streamlit UI inspection + API response
- **Evidence:** Framework comparison view showing PE-03 evidence status reflected in PR.AA-06; real-time update when new evidence is uploaded

### VAL-CROSS-009: Concurrent User Activity Consistency
- **Behavioral description:** When two users perform actions simultaneously (User A uploads evidence while User B approves a review), both actions complete successfully and their respective audit log entries are in correct chronological order. The dashboard metrics after both actions reflect both changes. No data corruption or lost updates occur.
- **Tool:** Parallel API calls from two simulated users
- **Evidence:** Both API calls return 200; audit_logs showing both entries with correct timestamps; dashboard showing updated metrics for both actions

### VAL-CROSS-010: Error Handling Across Areas
- **Behavioral description:** When a downstream action fails (e.g., evidence upload succeeds but mapping to control fails due to invalid control_id), the system: (1) Returns an appropriate error response (HTTP 400/404) with a descriptive message. (2) Does NOT create partial state (the evidence exists but no orphaned mapping). (3) Logs the failed action attempt in audit_logs with action="FAILED_MAP_EVIDENCE" and error details in new_values. (4) The dashboard and review queue remain consistent (no phantom entries).
- **Tool:** API call with invalid control_id + state verification
- **Evidence:** HTTP 404 response; no orphaned evidence_control_mappings record; audit_logs entry with FAILED_MAP_EVIDENCE; dashboard state unchanged

---

## Summary Statistics

| Area | Assertion Count | Prefix |
|------|----------------|--------|
| Dashboard & Reporting | 12 | VAL-DASHBOARD-001 to VAL-DASHBOARD-012 |
| Review Workflow | 12 | VAL-REVIEW-001 to VAL-REVIEW-012 |
| Audit Logging | 13 | VAL-AUDIT-001 to VAL-AUDIT-013 |
| Cross-Area Flows | 10 | VAL-CROSS-001 to VAL-CROSS-010 |
| **Total** | **47** | |

---

*Generated for GRC Platform MVP - NIST SP 800-53 Controls: PE-03, AC-02, SC-07, IR-06, RA-05*
