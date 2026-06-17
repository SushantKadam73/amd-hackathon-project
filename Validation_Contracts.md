# Validation Assertions for GRC Platform MVP

**Date:** June 17, 2026
**Scope:** NIST SP 800-53 controls (PE-03, AC-02, SC-07, IR-06, RA-05) for datacenter company
**Areas:** Framework & Control Library, Evidence Management, AI Review & Chatbot

---

## Area 1: Framework & Control Library (VAL-LIBRARY-*)

### Assertion VAL-LIBRARY-001: Framework Listing Display
- **Behavior:** When a user navigates to the Framework Library page, the system displays all active frameworks in a table/list showing framework name, version, description, total control count, and last updated date. At minimum, NIST SP 800-53 Rev 5 must be listed.
- **Tool:** Streamlit UI inspection (screenshot or DOM check)
- **Evidence:** Screenshot or HTML snapshot showing the framework list with NIST SP 800-53 visible

### Assertion VAL-LIBRARY-002: Framework Detail View
- **Behavior:** When a user clicks on a framework entry, the system displays the framework detail page showing the framework name, version, version date, description, and a list of all controls belonging to that framework with their control IDs, titles, and control families.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of framework detail page showing controls listed

### Assertion VAL-LIBRARY-003: Control Library Complete Listing
- **Behavior:** When a user navigates to the Control Library page, all 5 NIST SP 800-53 controls (PE-03, AC-02, SC-07, IR-06, RA-05) are displayed with their control ID, title, control family, priority level, and mapping status (Fully Mapped / Partially Mapped / Unmapped).
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing all 5 controls listed

### Assertion VAL-LIBRARY-004: Control Detail View - PE-03
- **Behavior:** When a user clicks on PE-03 (Physical Access Control), the system displays: control ID "PE-03", title "Physical Access Control", full description about enforcing physical access authorizations, control family "Physical and Environmental Protection", required artifact types (Policy Documents 15%, Procedures 15%, Access Lists 20%, System Configs 20%, Audit Logs 15%, Training Records 5%, Inspection Reports 10%), and current mapping status.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of PE-03 detail with all artifact types and weightages visible

### Assertion VAL-LIBRARY-005: Control Detail View - AC-02
- **Behavior:** When a user clicks on AC-02 (Account Management), the system displays: control ID "AC-02", title "Account Management", full description about managing information system accounts, control family "Access Control", required artifact types (Policy Documents 15%, Procedures 15%, Account Inventories 20%, Access Reviews 20%, Configuration Records 15%, Audit Logs 10%, Training Records 5%), and current mapping status.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of AC-02 detail with all artifact types and weightages visible

### Assertion VAL-LIBRARY-006: Control Detail View - SC-07
- **Behavior:** When a user clicks on SC-07 (Boundary Protection), the system displays: control ID "SC-07", title "Boundary Protection", full description about monitoring and controlling communications, control family "System and Communications Protection", required artifact types (Network Architecture 20%, Firewall Rules 25%, Segmentation Policies 15%, Monitoring Configs 15%, Audit Logs 15%, Change Records 10%), and current mapping status.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of SC-07 detail with all artifact types and weightages visible

### Assertion VAL-LIBRARY-007: Control Detail View - IR-06
- **Behavior:** When a user clicks on IR-06 (Incident Reporting), the system displays: control ID "IR-06", title "Incident Reporting", full description about reporting suspected security incidents, control family "Incident Response", required artifact types (Policy Documents 15%, IR Plan 20%, Training Records 10%, Incident Records 25%, Communication Logs 15%, Lessons Learned 10%, Contact Lists 5%), and current mapping status.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of IR-06 detail with all artifact types and weightages visible

### Assertion VAL-LIBRARY-008: Control Detail View - RA-05
- **Behavior:** When a user clicks on RA-05 (Vulnerability Scanning), the system displays: control ID "RA-05", title "Vulnerability Scanning", full description about scanning for vulnerabilities, control family "Risk Assessment", required artifact types (Scanning Policies 15%, Tool Configurations 20%, Scan Results 25%, Remediation Records 20%, Validation Reports 10%, Metrics/Reports 10%), and current mapping status.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of RA-05 detail with all artifact types and weightages visible

### Assertion VAL-LIBRARY-009: Control Search Functionality
- **Behavior:** When a user types a search query (e.g., "physical access") into the control search box, the system filters the control library to show only controls whose title, description, or control family matches the query. Searching for "physical" returns PE-03; searching for "account" returns AC-02; searching for "incident" returns IR-06.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered results for at least 3 different search queries

### Assertion VAL-LIBRARY-010: Control Filter by Control Family
- **Behavior:** When a user selects a control family filter (e.g., "Access Control"), the system displays only controls belonging to that family. Selecting "Access Control" shows AC-02; selecting "Physical and Environmental Protection" shows PE-03; selecting "Incident Response" shows IR-06.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered results for each family selection

### Assertion VAL-LIBRARY-011: Control Filter by Mapping Status
- **Behavior:** When a user filters controls by mapping status (e.g., "Unmapped"), only controls with that status are displayed. When a control has no evidence mapped, its status is "Unmapped". When some evidence is mapped but not all artifact types are covered, status is "Partially Mapped". When all artifact types have valid evidence, status is "Fully Mapped".
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered results for each status

### Assertion VAL-LIBRARY-012: Mapping Status Auto-Calculation
- **Behavior:** When evidence artifacts are mapped to a control, the mapping status auto-recalculates: if 0% of required artifact types are covered, status is "Unmapped"; if 50-89% of artifact types are covered with valid evidence, status is "Partially Mapped"; if 90%+ of artifact types are covered with current (within 12 months) and validated evidence, status is "Fully Mapped".
- **Tool:** API test (POST evidence mapping, then GET control status)
- **Evidence:** API response showing status transition from Unmapped to Partially Mapped to Fully Mapped

### Assertion VAL-LIBRARY-013: Control Family Grouping
- **Behavior:** The control library groups controls by their control family. The 5 controls span 5 families: Physical and Environmental Protection (PE-03), Access Control (AC-02), System and Communications Protection (SC-07), Incident Response (IR-06), Risk Assessment (RA-05). Each family header shows the family name and the count of controls within it.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing all 5 families with their controls grouped

### Assertion VAL-LIBRARY-014: Empty Control Library State
- **Behavior:** When no frameworks have been loaded into the system, the control library displays an empty state message (e.g., "No frameworks loaded. Please add a framework to begin.") with no error or crash. The UI remains functional.
- **Tool:** Streamlit UI inspection with empty database
- **Evidence:** Screenshot showing empty state message

### Assertion VAL-LIBRARY-015: Control Priority Display
- **Behavior:** Each control displays its priority level (high, medium, low) with visual differentiation (e.g., color coding or icons). Priority is stored and retrievable from the database.
- **Tool:** Streamlit UI inspection + API check
- **Evidence:** Screenshot showing priority indicators on control cards

### Assertion VAL-LIBRARY-016: Cross-Framework Mapping Display
- **Behavior:** When a user views a control (e.g., PE-03), the system displays its cross-framework mappings to other frameworks (NIST CSF 2.0, CIS Controls v8, PCI DSS v4.0.1) as defined in the mapping matrix. PE-03 maps to PR.AA-06 (NIST CSF), CIS 6 (CIS), PCI 9.2/9.3 (PCI DSS).
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing cross-framework mapping relationships for at least one control

### Assertion VAL-LIBRARY-017: Artifact Type Weightage Display
- **Behavior:** On each control detail page, the required artifact types are displayed with their percentage weightage. The total of all artifact type weightages for a control sums to 100%. For PE-03: 15+15+20+20+15+5+10 = 100%.
- **Tool:** Streamlit UI inspection + manual calculation
- **Evidence:** Screenshot showing weightage breakdown with visible percentages

### Assertion VAL-LIBRARY-018: Evidence Coverage Visualization per Control
- **Behavior:** On each control detail page, a visual indicator (e.g., progress bar or pie chart) shows how much of the required evidence has been mapped. For a control with no evidence, the coverage shows 0%. For a control with 3 of 7 artifact types covered, coverage shows ~43%.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing coverage visualization for a control with partial evidence

### Assertion VAL-LIBRARY-019: Control Description Rich Text
- **Behavior:** Control descriptions are displayed with proper formatting (line breaks, paragraphs) rather than raw text. Long descriptions do not overflow their container and are scrollable or truncated with expand option.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing properly formatted control description

### Assertion VAL-LIBRARY-020: Framework Version Display
- **Behavior:** The framework detail page shows the version string (e.g., "Rev 5") and version date for the loaded framework. This information is consistent between the list view and detail view.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing version info in both list and detail views

---

## Area 2: Evidence Management (VAL-EVIDENCE-*)

### Assertion VAL-EVIDENCE-001: Evidence Upload Form Display
- **Behavior:** When a user navigates to the Evidence Upload page, a form is displayed with fields for: file selection (file picker), evidence name/title, artifact type (dropdown matching control requirements), target control (dropdown of all 5 controls), description (text area), and an upload button.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot of evidence upload form with all fields visible

### Assertion VAL-EVIDENCE-002: Supported File Types - PDF Upload
- **Behavior:** When a user selects a PDF file (e.g., "Physical_Security_Policy.pdf") for upload, the system accepts the file, stores it, and creates an evidence artifact record with file_type "PDF".
- **Tool:** Streamlit UI interaction + API verification
- **Evidence:** Screenshot of upload success + API GET response showing file_type "PDF"

### Assertion VAL-EVIDENCE-003: Supported File Types - Image Upload
- **Behavior:** When a user selects an image file (PNG or JPG, e.g., "badge_reader_config.png") for upload, the system accepts the file, stores it, and creates an evidence artifact record with file_type "PNG" or "JPG".
- **Tool:** Streamlit UI interaction + API verification
- **Evidence:** Screenshot of upload success + API response

### Assertion VAL-EVIDENCE-004: Supported File Types - DOCX Upload
- **Behavior:** When a user selects a Word document (e.g., "Incident_Response_Plan.docx") for upload, the system accepts the file, stores it, and creates an evidence artifact record with file_type "DOCX".
- **Tool:** Streamlit UI interaction + API verification
- **Evidence:** Screenshot of upload success + API response

### Assertion VAL-EVIDENCE-005: Unsupported File Type Rejection
- **Behavior:** When a user attempts to upload an unsupported file type (e.g., .exe, .bat, .scr), the system rejects the upload with a clear error message indicating the file type is not supported and listing acceptable types (PDF, PNG, JPG, DOCX).
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing error message for rejected file type

### Assertion VAL-EVIDENCE-006: File Size Limit Enforcement
- **Behavior:** When a user attempts to upload a file exceeding the maximum size (50MB in dev, 500MB in prod), the system rejects the upload with an error message indicating the file exceeds the maximum allowed size.
- **Tool:** Streamlit UI interaction test with oversized file
- **Evidence:** Screenshot showing error message for oversized file

### Assertion VAL-EVIDENCE-007: Empty File Upload Rejection
- **Behavior:** When a user attempts to upload a file with 0 bytes, the system rejects the upload with an error message indicating the file is empty.
- **Tool:** Streamlit UI interaction test with empty file
- **Evidence:** Screenshot showing error message for empty file

### Assertion VAL-EVIDENCE-008: Post-Upload Processing - Text Extraction
- **Behavior:** After a PDF or DOCX file is uploaded, the system automatically extracts text content from the document and stores it in the evidence artifact's content_text field. This text is available for RAG search.
- **Tool:** API test (upload file, then GET evidence detail)
- **Evidence:** API response showing content_text is populated with extracted text

### Assertion VAL-EVIDENCE-009: Post-Upload Processing - Embedding Generation
- **Behavior:** After a file is uploaded and text is extracted, the system generates a vector embedding (1024-dimensional) using the NVIDIA Llama Nemotron Embed model and stores it in the embedding_vector field for similarity search.
- **Tool:** API test (upload file, then GET evidence detail)
- **Evidence:** API response showing embedding_vector is populated (non-null)

### Assertion VAL-EVIDENCE-010: Post-Upload Processing - Checksum Calculation
- **Behavior:** After a file is uploaded, the system calculates and stores a checksum (SHA-256 or MD5) of the file content in the checksum field for integrity verification.
- **Tool:** API test (upload file, then GET evidence detail)
- **Evidence:** API response showing checksum is populated

### Assertion VAL-EVIDENCE-011: Post-Upload Processing - File Metadata
- **Behavior:** After a file is uploaded, the system stores the file_size (in bytes), file_type (extension), and uploaded_at (timestamp) in the evidence artifact record.
- **Tool:** API test
- **Evidence:** API response showing file_size, file_type, and uploaded_at are populated

### Assertion VAL-EVIDENCE-012: Evidence to Control Mapping
- **Behavior:** When a user maps an evidence artifact to a control, the system creates an evidence_control_mapping record with: evidence_id, control_id, weightage (user-specified or auto-calculated), mapping_status "pending", and the mapped_by user reference.
- **Tool:** API test (POST map-to-control, then GET mappings)
- **Evidence:** API response showing new mapping record created

### Assertion VAL-EVIDENCE-013: Evidence Mapping Weightage Assignment
- **Behavior:** When mapping evidence to a control, the weightage field reflects the artifact type's required percentage as defined in the framework. For example, mapping a "Policy Document" to PE-03 sets weightage to 15.00. The weightage can be overridden by the user but must remain between 0 and 100.
- **Tool:** API test
- **Evidence:** API response showing weightage matches artifact type requirement

### Assertion VAL-EVIDENCE-014: Evidence Mapping Weightage Validation
- **Behavior:** When a user attempts to set a weightage value outside 0-100 range (e.g., -5 or 150), the system rejects the update with a validation error message.
- **Tool:** API test with invalid weightage values
- **Evidence:** API error response for weightage < 0 and > 100

### Assertion VAL-EVIDENCE-015: Evidence List View
- **Behavior:** When a user navigates to the Evidence Library page, all uploaded evidence artifacts are displayed in a table/list showing: name, file type, file size, target control, artifact type, mapping status, weightage, uploaded date, and uploaded by.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing evidence list with all columns visible

### Assertion VAL-EVIDENCE-016: Evidence Detail View
- **Behavior:** When a user clicks on an evidence artifact, the system displays full details: name, file type, file size, checksum, upload date, uploaded by, description, content text preview (first 500 characters), and all control mappings with their statuses and weightages.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing evidence detail page

### Assertion VAL-EVIDENCE-017: Evidence to Multiple Controls Mapping
- **Behavior:** When a user maps a single evidence artifact to multiple controls (e.g., a "Physical Security Policy" to both PE-03 and AC-02), separate evidence_control_mapping records are created for each control with appropriate weightages.
- **Tool:** API test
- **Evidence:** API response showing two distinct mapping records for one evidence artifact

### Assertion VAL-EVIDENCE-018: Evidence Mapping Status Transitions
- **Behavior:** Evidence mapping status transitions follow the workflow: pending (initial) -> approved (after review) or rejected (after review). A mapping cannot go from approved back to pending without a new submission.
- **Tool:** API test (create mapping, approve, verify status)
- **Evidence:** API responses showing status transitions: pending -> approved

### Assertion VAL-EVIDENCE-019: Evidence Mapping Rejection
- **Behavior:** When a reviewer rejects an evidence mapping, the mapping_status changes to "rejected" and review_notes are required. The rejected mapping does not count toward the control's mapping status calculation.
- **Tool:** API test
- **Evidence:** API response showing rejected status and review_notes

### Assertion VAL-EVIDENCE-020: Evidence Deletion
- **Behavior:** When a user deletes an evidence artifact, the artifact record is removed (or soft-deleted), and all associated evidence_control_mapping records are also removed. The file is removed from storage.
- **Tool:** API test (delete evidence, verify mappings removed)
- **Evidence:** API response confirming deletion + subsequent GET returning 404

### Assertion VAL-EVIDENCE-021: Empty Evidence Library State
- **Behavior:** When no evidence has been uploaded, the Evidence Library page displays an empty state message (e.g., "No evidence artifacts uploaded yet. Upload evidence to begin mapping.") with no error or crash.
- **Tool:** Streamlit UI inspection with empty database
- **Evidence:** Screenshot showing empty state message

### Assertion VAL-EVIDENCE-022: Duplicate Evidence Upload Handling
- **Behavior:** When a user uploads a file with the same name and checksum as an existing evidence artifact, the system handles it gracefully (either rejects with a "duplicate detected" message or allows upload with a warning and creates a separate record).
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing system response to duplicate upload

### Assertion VAL-EVIDENCE-023: Evidence Upload Progress Feedback
- **Behavior:** During evidence upload, the system provides visual feedback (e.g., progress indicator, loading spinner) while the file is being processed (uploaded, text extracted, embedding generated). The user is not left without feedback.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing progress indicator during upload

### Assertion VAL-EVIDENCE-024: Evidence Upload Success Confirmation
- **Behavior:** After a successful evidence upload, the system displays a success confirmation message with the evidence artifact name and provides a link/button to view the uploaded artifact or upload another.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing success confirmation

### Assertion VAL-EVIDENCE-025: Evidence Weightage Calculation Aggregation
- **Behavior:** For a given control, the sum of all approved evidence mapping weightages reflects the coverage of required artifact types. For PE-03, if Policy Documents (15%) and Audit Logs (15%) are mapped and approved, the aggregate weightage is 30% and the control is 30% covered.
- **Tool:** API test (map multiple evidence, check aggregated weightage)
- **Evidence:** API response showing correct aggregate weightage calculation

### Assertion VAL-EVIDENCE-026: Evidence Artifact Type Selection
- **Behavior:** When mapping evidence to a control, the artifact type dropdown only shows artifact types relevant to the selected control. For PE-03: Policy Documents, Procedures, Access Lists, System Configs, Audit Logs, Training Records, Inspection Reports. For AC-02: Policy Documents, Procedures, Account Inventories, Access Reviews, Configuration Records, Audit Logs, Training Records.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing artifact type dropdown filtered by control

### Assertion VAL-EVIDENCE-027: Evidence Search Functionality
- **Behavior:** When a user searches the evidence library by name, the system filters results to show only evidence artifacts whose name matches the search query. Searching for "policy" shows evidence with "policy" in the name.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered evidence results

### Assertion VAL-EVIDENCE-028: Evidence Filter by Control
- **Behavior:** When a user filters the evidence library by target control (e.g., "PE-03"), only evidence artifacts mapped to that control are displayed.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered evidence list

### Assertion VAL-EVIDENCE-029: Evidence Filter by Mapping Status
- **Behavior:** When a user filters the evidence library by mapping status (e.g., "pending"), only evidence artifacts with that mapping status are displayed.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing filtered evidence list

### Assertion VAL-EVIDENCE-030: Evidence Upload Audit Trail
- **Behavior:** When a user uploads evidence, an audit log entry is created recording: user_id, action "evidence_upload", entity_type "evidence_artifact", entity_id, new_values (artifact metadata), timestamp, IP address, and user agent.
- **Tool:** API test (upload evidence, then GET audit logs)
- **Evidence:** API response showing audit log entry for upload

### Assertion VAL-EVIDENCE-031: Large File Upload Handling
- **Behavior:** When a user uploads a file near the size limit (e.g., 49MB in dev environment), the upload completes successfully and the file_size field accurately reflects the actual file size.
- **Tool:** Streamlit UI interaction + API verification
- **Evidence:** Screenshot of successful upload + API response with correct file_size

### Assertion VAL-EVIDENCE-032: Evidence File Integrity Verification
- **Behavior:** When evidence is uploaded and a checksum is generated, the checksum can be used to verify file integrity. Re-calculating the checksum of the stored file produces the same value as the stored checksum.
- **Tool:** API test + checksum recalculation script
- **Evidence:** Script output showing checksum match

---

## Area 3: AI Review & Chatbot (VAL-AI-*)

### Assertion VAL-AI-001: Chatbot Interface Display
- **Behavior:** When a user navigates to the Chat page, a chat interface is displayed with: a message input text area, a send button, and a chat history area. The interface shows a welcome message (e.g., "Welcome to the GRC Assistant. Ask me about compliance controls, evidence requirements, or framework mappings.").
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing chat interface with welcome message

### Assertion VAL-AI-002: Chatbot - Control Explanation Query
- **Behavior:** When a user asks "What is PE-03?", the chatbot responds with a clear explanation of the Physical Access Control control, including its purpose (enforcing physical access authorizations), control family, and key requirements. The response is sourced from the NIST SP 800-53 knowledge base via RAG.
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response about PE-03

### Assertion VAL-AI-003: Chatbot - Evidence Requirements Query
- **Behavior:** When a user asks "What evidence do I need for AC-02?", the chatbot responds with the required artifact types for AC-02 (Policy Documents, Procedures, Account Inventories, Access Reviews, Configuration Records, Audit Logs, Training Records) along with their weightages.
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response listing AC-02 evidence requirements

### Assertion VAL-AI-004: Chatbot - Framework Mapping Query
- **Behavior:** When a user asks "What does SC-07 map to in PCI DSS?", the chatbot responds with the cross-framework mapping information showing SC-07 maps to PCI DSS 1.2, 1.3 (Firewall/network controls, DMZ).
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response about SC-07 to PCI DSS mapping

### Assertion VAL-AI-005: Chatbot - Compliance Status Query
- **Behavior:** When a user asks "What is my compliance status for PE-03?", the chatbot retrieves the current mapping status and evidence coverage for PE-03 and responds with the status (Unmapped / Partially Mapped / Fully Mapped) and the percentage of evidence covered.
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response with compliance status

### Assertion VAL-AI-006: Chatbot - Gap Analysis Query
- **Behavior:** When a user asks "What are my gaps for IR-06?", the chatbot analyzes the evidence coverage for IR-06 against required artifact types, identifies missing artifact types, and responds with a list of gaps (e.g., "You are missing: Training Records (10%), Lessons Learned (10%)").
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response listing gaps

### Assertion VAL-AI-007: Chatbot - Recommendation Query
- **Behavior:** When a user asks "How can I improve my RA-05 compliance?", the chatbot analyzes current evidence coverage for RA-05, identifies gaps, and provides actionable recommendations (e.g., "Upload vulnerability scan reports (25% weightage) and remediation tracking records (20% weightage) to improve compliance").
- **Tool:** Streamlit UI interaction + chat response verification
- **Evidence:** Screenshot showing user query and chatbot response with recommendations

### Assertion VAL-AI-008: Chatbot - Multi-Turn Conversation
- **Behavior:** When a user has a multi-turn conversation (e.g., "What is PE-03?" -> "What evidence do I need?" -> "Do I have any of that evidence?"), the chatbot maintains conversation context across turns and provides coherent, context-aware responses.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing 3-turn conversation with coherent responses

### Assertion VAL-AI-009: Chatbot - Session Persistence
- **Behavior:** When a user sends messages in a chatbot session, the conversation is stored in the agent_sessions table with the session_type "chat", user_id, started_at, and context (conversation history). When the user returns, previous sessions are accessible.
- **Tool:** API test (send messages, then GET sessions)
- **Evidence:** API response showing session record with conversation context

### Assertion VAL-AI-010: Chatbot - Unrelated Query Handling
- **Behavior:** When a user asks a question unrelated to GRC (e.g., "What is the weather today?"), the chatbot responds with a polite redirect (e.g., "I'm focused on GRC compliance. Please ask about controls, evidence, or framework mappings.") rather than providing irrelevant information.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing chatbot redirect for unrelated query

### Assertion VAL-AI-011: Chatbot - Empty Query Handling
- **Behavior:** When a user sends an empty message (clicks send with no text), the chatbot does not crash and displays a message indicating the user should type a question.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing empty query handling

### Assertion VAL-AI-012: Chatbot - Loading/Typing Indicator
- **Behavior:** While the chatbot is processing a query, a loading indicator (e.g., typing animation, spinner) is displayed so the user knows the system is working. The indicator disappears when the response is ready.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing typing indicator during processing

### Assertion VAL-AI-013: Chatbot - Response Time
- **Behavior:** The chatbot responds to queries within 10 seconds in the dev environment (OpenRouter) and within 5 seconds in the production environment (Ollama with MI300X GPU). If the response takes longer, a timeout message is displayed.
- **Tool:** Performance test with timer
- **Evidence:** Timing measurement showing response within threshold

### Assertion VAL-AI-014: Evidence Analysis - File Upload Analysis
- **Behavior:** When a user uploads evidence and requests AI analysis (via "Analyze" button or API endpoint POST /api/v1/agent/analyze-evidence), the system analyzes the file content and responds with: identified control relevance (which controls the evidence supports), key topics/keywords extracted, quality assessment (completeness, currency), and suggested artifact type classification.
- **Tool:** API test (upload evidence, then POST analyze-evidence)
- **Evidence:** API response showing analysis results with control relevance, topics, and suggestions

### Assertion VAL-AI-015: Evidence Analysis - Control Relevance Scoring
- **Behavior:** When AI analyzes an evidence artifact, it assigns a relevance score (0-100) for each of the 5 controls. A Physical Security Policy should score high (>70) for PE-03 and low (<30) for RA-05. A Vulnerability Scan Report should score high for RA-05 and low for PE-03.
- **Tool:** API test
- **Evidence:** API response showing relevance scores with expected distribution

### Assertion VAL-AI-016: Evidence Analysis - Artifact Type Suggestion
- **Behavior:** When AI analyzes an evidence artifact, it suggests the most appropriate artifact type from the control's required types. A document containing access control policies should be suggested as "Policy Documents"; a log file should be suggested as "Audit Logs".
- **Tool:** API test
- **Evidence:** API response showing suggested artifact type matching expected classification

### Assertion VAL-AI-017: Evidence Analysis - Quality Assessment
- **Behavior:** When AI analyzes an evidence artifact, it provides a quality assessment including: document currency (is it dated within the last 12 months?), completeness (does it cover the expected scope?), and format quality (is it properly formatted/structured?).
- **Tool:** API test
- **Evidence:** API response showing quality assessment with currency, completeness, and format scores

### Assertion VAL-AI-018: Mapping Suggestion - AI-Powered Mapping
- **Behavior:** When a user requests AI mapping suggestions (POST /api/v1/agent/suggest-mapping) for a control, the system analyzes available evidence artifacts and suggests the most appropriate mappings with confidence scores. Suggestions with confidence > 0.7 are recommended; 0.4-0.7 are optional; < 0.4 are not suggested.
- **Tool:** API test
- **Evidence:** API response showing mapping suggestions with confidence scores

### Assertion VAL-AI-019: Mapping Suggestion - Confidence Threshold Display
- **Behavior:** AI mapping suggestions display confidence scores visually (e.g., high confidence in green, medium in yellow, low in red). The system clearly distinguishes between recommended (>0.7) and optional (0.4-0.7) suggestions.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing mapping suggestions with color-coded confidence scores

### Assertion VAL-AI-020: Guardrails - PII Detection Input
- **Behavior:** When a user sends a chatbot message containing PII (e.g., Social Security numbers, credit card numbers, email addresses), the input guardrail detects the PII and either masks it before processing or blocks the query with a warning message about not sharing sensitive information.
- **Tool:** Streamlit UI interaction test with PII in query
- **Evidence:** Screenshot showing PII detection and response (masking or blocking)

### Assertion VAL-AI-021: Guardrails - Malicious Input Detection
- **Behavior:** When a user sends a chatbot message containing potentially malicious content (e.g., SQL injection attempts, prompt injection, script tags), the input guardrail detects and blocks the query with a security warning message.
- **Tool:** Streamlit UI interaction test with malicious input
- **Evidence:** Screenshot showing malicious input blocked

### Assertion VAL-AI-022: Guardrails - Output Compliance Validation
- **Behavior:** Before displaying AI-generated responses, the output guardrail validates that the response does not contain: false compliance claims, incorrect control descriptions, sensitive data leakage, or hallucinated framework references. Non-compliant responses are flagged for human review or regenerating.
- **Tool:** API test with adversarial queries
- **Evidence:** API response showing output validation results

### Assertion VAL-AI-023: Guardrails - Confidence Score Threshold
- **Behavior:** When an AI analysis produces a confidence score below 0.5 for control relevance, the system flags the result for human review rather than automatically applying it. The user sees a "Requires Review" indicator.
- **Tool:** API test
- **Evidence:** API response showing low-confidence result flagged for review

### Assertion VAL-AI-024: Human-in-the-Loop - Review Queue
- **Behavior:** When AI-generated suggestions (mapping proposals, evidence classifications, gap assessments) are flagged for review, they appear in a review queue accessible to users with reviewer or admin roles. The queue shows: suggestion type, AI confidence, submitted date, and action buttons (approve/reject).
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing review queue with pending AI suggestions

### Assertion VAL-AI-025: Human-in-the-Loop - Approval Workflow
- **Behavior:** When a reviewer approves an AI suggestion (e.g., an evidence-to-control mapping), the suggestion is applied (mapping created, status set to "approved"), and the review record is updated with reviewer_id, review timestamp, and optional review notes.
- **Tool:** API test (approve suggestion, verify applied)
- **Evidence:** API responses showing suggestion applied and review record updated

### Assertion VAL-AI-026: Human-in-the-Loop - Rejection Workflow
- **Behavior:** When a reviewer rejects an AI suggestion, the suggestion is not applied, the review record is updated with rejection status and mandatory review notes explaining the rejection reason.
- **Tool:** API test
- **Evidence:** API response showing rejection recorded with notes

### Assertion VAL-AI-027: RAG Knowledge Base Search
- **Behavior:** When the AI agent processes a query, it searches the knowledge base using vector similarity search (pgvector) to retrieve relevant compliance documents, policies, and standards. The retrieval returns the top 5 most relevant chunks with similarity scores.
- **Tool:** API test (POST /api/v1/rag/search)
- **Evidence:** API response showing retrieved knowledge chunks with similarity scores

### Assertion VAL-AI-028: RAG Knowledge Base Ingestion
- **Behavior:** When a document is ingested into the knowledge base (POST /api/v1/rag/ingest), the system splits it into chunks, generates embeddings for each chunk, and stores them with metadata (title, source, content_type, framework_id). The chunks are searchable via vector similarity.
- **Tool:** API test
- **Evidence:** API response confirming ingestion + subsequent search returning the ingested content

### Assertion VAL-AI-029: Chatbot - Error Handling - LLM Unavailable
- **Behavior:** When the LLM service (OpenRouter in dev or Ollama in prod) is unavailable or times out, the chatbot displays a user-friendly error message (e.g., "The AI service is temporarily unavailable. Please try again in a moment.") without exposing internal error details.
- **Tool:** API test with LLM service mocked as unavailable
- **Evidence:** Screenshot showing error message for LLM unavailability

### Assertion VAL-AI-030: Chatbot - Error Handling - Database Unavailable
- **Behavior:** When the database is unavailable, the chatbot handles the error gracefully and displays a message indicating the system is experiencing issues without exposing connection strings or internal details.
- **Tool:** API test with database mocked as unavailable
- **Evidence:** Screenshot showing error message for database unavailability

### Assertion VAL-AI-031: Chatbot - Rate Limiting
- **Behavior:** When a user sends more than a defined threshold of queries (e.g., 30 per minute) to the chatbot, the system applies rate limiting and displays a message asking the user to wait before sending more queries. This prevents abuse and excessive LLM costs.
- **Tool:** API test with rapid query burst
- **Evidence:** API response showing rate limit exceeded message

### Assertion VAL-AI-032: Chatbot - Conversation History Display
- **Behavior:** The chat interface displays the full conversation history in chronological order with clear visual distinction between user messages (right-aligned, one color) and chatbot responses (left-aligned, another color). Timestamps are shown for each message.
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing formatted conversation history

### Assertion VAL-AI-033: Chatbot - Session List
- **Behavior:** When a user navigates to the Sessions page, all previous chatbot sessions are listed showing: session ID, session type, start time, end time, and a summary of the conversation topic. The user can click to resume a session.
- **Tool:** Streamlit UI inspection + API test
- **Evidence:** Screenshot showing session list with entries

### Assertion VAL-AI-034: Chatbot - Resume Session
- **Behavior:** When a user clicks on a previous session, the chat interface loads the conversation history from that session, allowing the user to continue where they left off. The session context is restored.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing resumed session with previous conversation loaded

### Assertion VAL-AI-035: Evidence Analysis - Audit Trail
- **Behavior:** When AI analyzes an evidence artifact, an audit log entry is created recording: user_id, action "evidence_analysis", entity_type "evidence_artifact", entity_id, AI analysis results in new_values, and timestamp.
- **Tool:** API test (analyze evidence, then GET audit logs)
- **Evidence:** API response showing audit log entry for AI analysis

### Assertion VAL-AI-036: Chatbot - Audit Trail
- **Behavior:** Every chatbot interaction creates an audit log entry recording: user_id, action "chat_message", entity_type "agent_session", entity_id, message content (sanitized), and timestamp.
- **Tool:** API test (send message, then GET audit logs)
- **Evidence:** API response showing audit log entry for chat interaction

### Assertion VAL-AI-037: Guardrails - Rate Limiting for AI Analysis
- **Behavior:** When a user requests AI evidence analysis more than the defined threshold (e.g., 10 per hour), the system rate-limits the requests and displays a message about the limit.
- **Tool:** API test with rapid analysis requests
- **Evidence:** API response showing rate limit for AI analysis

### Assertion VAL-AI-038: Chatbot - Multi-Language Handling
- **Behavior:** When a user sends a query in a non-English language, the chatbot either responds in the same language or politely requests the user to ask in English, depending on the configured LLM's capabilities.
- **Tool:** Streamlit UI interaction test
- **Evidence:** Screenshot showing chatbot response to non-English query

### Assertion VAL-AI-039: Chatbot - Long Query Handling
- **Behavior:** When a user sends a very long query (e.g., 5000+ characters), the system handles it without crashing, processes it (or truncates with a message if too long), and responds appropriately.
- **Tool:** Streamlit UI interaction test with long query
- **Evidence:** Screenshot showing system handling of long query

### Assertion VAL-AI-040: Chatbot - Welcome Message Context
- **Behavior:** The chatbot's welcome message includes context about the system's capabilities: what it can help with (controls, evidence, mappings, compliance status) and the 5 controls in scope (PE-03, AC-02, SC-07, IR-06, RA-05).
- **Tool:** Streamlit UI inspection
- **Evidence:** Screenshot showing welcome message with system capabilities

### Assertion VAL-AI-041: AI Mapping Suggestion - Auto-Suggest Endpoint
- **Behavior:** When the POST /api/v1/control-mappings/auto-suggest endpoint is called with a source control ID, the system analyzes the control description, required artifacts, and available evidence to suggest target control mappings across frameworks with confidence scores.
- **Tool:** API test
- **Evidence:** API response showing auto-suggested mappings with confidence scores

### Assertion VAL-AI-042: AI Gap Detection
- **Behavior:** When the POST /api/v1/gap-analyses/auto-detect endpoint is called for a control, the system analyzes the current evidence coverage against required artifact types, identifies gaps, and creates gap analysis records with risk levels (low/medium/high/critical) based on missing artifact weightages.
- **Tool:** API test
- **Evidence:** API response showing detected gaps with risk levels

### Assertion VAL-AI-043: AI Report Generation
- **Behavior:** When the POST /api/v1/agent/generate-report endpoint is called, the system generates a compliance report that includes: overall compliance status, per-control status breakdown, evidence coverage summary, identified gaps, and recommendations. The report is available in the requested format.
- **Tool:** API test
- **Evidence:** API response showing generated report content

### Assertion VAL-AI-044: LLM Router - Dev/Prod Model Selection
- **Behavior:** In the development environment, the system uses OpenRouter (meta-llama/llama-3-8b-instruct) for LLM inference. In the production environment, it uses Ollama (gemma2:12b) with the MI300X GPU. The active model is indicated in the system configuration endpoint (GET /api/v1/config/ai-models).
- **Tool:** API test (GET config/ai-models in both environments)
- **Evidence:** API responses showing correct model configuration per environment

### Assertion VAL-AI-045: AI Analysis - Evidence Freshness Check
- **Behavior:** When AI analyzes an evidence artifact, it checks the document's date/timestamp. If the evidence is older than 12 months, the analysis includes a "stale" warning recommending the evidence be updated. This affects the control's mapping status calculation.
- **Tool:** API test with old evidence artifact
- **Evidence:** API response showing stale warning in analysis results

---

## Summary

| Area | Prefix | Assertion Count | Key Focus |
|------|--------|----------------|-----------|
| Framework & Control Library | VAL-LIBRARY-001 to VAL-LIBRARY-020 | 20 | Display, search, filter, mapping status, cross-framework mappings, weightages |
| Evidence Management | VAL-EVIDENCE-001 to VAL-EVIDENCE-032 | 32 | Upload flow, file types, processing, mapping, weightage, status transitions, edge cases |
| AI Review & Chatbot | VAL-AI-001 to VAL-AI-045 | 45 | Chatbot queries, evidence analysis, guardrails, human-in-the-loop, RAG, error handling |
| **Total** | | **97** | |

### Coverage by Interaction Type

| Interaction Category | Assertions | Count |
|---------------------|------------|-------|
| Display/Rendering | VAL-LIBRARY-001 to 008, 013, 015-019, VAL-EVIDENCE-001, 015-016, 021, 026, VAL-AI-001, 032-034, 040 | 24 |
| User Actions (Click, Search, Filter) | VAL-LIBRARY-009 to 012, VAL-EVIDENCE-012, 027-029, VAL-AI-008, 033-034 | 11 |
| Upload/Processing | VAL-EVIDENCE-002 to 011, 022-025, 031-032 | 15 |
| AI Processing | VAL-AI-002 to 007, 014-018, 027-028, 041-045 | 18 |
| Guardrails/Security | VAL-AI-010-011, 020-023, 031, 037, 039 | 9 |
| Workflow (Review, Approve) | VAL-EVIDENCE-018-019, VAL-AI-024-026 | 5 |
| Error/Edge Cases | VAL-LIBRARY-014, VAL-EVIDENCE-005-007, 022, VAL-AI-010-011, 029-030, 039 | 10 |
| Audit Trail | VAL-EVIDENCE-030, VAL-AI-035-036 | 3 |
| Data Integrity | VAL-LIBRARY-012, 017, VAL-EVIDENCE-013-014, 025, 032 | 6 |

---

**End of Validation Contracts Document**
