"""GRC Platform - Knowledge Loader.

Functions to ingest compliance documents into pgvector and manage
the pre-loaded knowledge base. Contains pre-loaded knowledge for:
- NIST SP 800-53 control descriptions and requirements (PE-03, AC-02, SC-07, IR-06, RA-05)
- Artifact type requirements and weightages
- Cross-framework mapping definitions
- Compliance best practices for datacenter companies
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from config import get_config
from rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
config = get_config()


# =============================================================================
# Pre-loaded Knowledge Data
# =============================================================================

def get_preloaded_knowledge() -> list[dict[str, Any]]:
    """Return the pre-loaded compliance knowledge entries.

    Contains structured information about NIST SP 800-53 controls,
    artifact requirements, cross-framework mappings, and compliance
    best practices for datacenter companies.

    Returns:
        list[dict]: List of knowledge entries with title, content, source,
                   and metadata fields.
    """
    return [
        # =====================================================================
        # PE-03: Physical Access Control
        # =====================================================================
        {
            "title": "PE-03: Physical Access Control - Description",
            "content": (
                "PE-03 (Physical Access Control) is a NIST SP 800-53 control "
                "in the Physical and Environmental Protection family. It requires "
                "organizations to enforce physical access authorizations at facility "
                "entry and exit points by verifying individual access authorizations "
                "before granting access and controlling the flow of visitors. "
                "For datacenter companies, this includes server room access, cage "
                "security, rack locks, biometric enrollment records, and cage key "
                "inventory management."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 0,
            "metadata": {
                "control_id": "PE-03",
                "control_family": "Physical and Environmental Protection",
                "framework": "NIST SP 800-53",
                "category": "control_description",
                "keywords": ["physical access", "badge", "visitor", "access control", "facility"],
            },
        },
        {
            "title": "PE-03: Physical Access Control - Requirements",
            "content": (
                "PE-03 requires: (a) Enforcing physical access authorizations at "
                "all facility entry and exit points; (b) Verifying individual access "
                "authorizations before granting access; (c) Controlling the flow of "
                "visitors and maintaining visitor logs; (d) Monitoring physical access "
                "to the facility; (e) Maintaining audit logs of physical access events; "
                "(f) Reviewing physical access logs periodically. Required evidence "
                "includes: Physical Security Policy, Visitor Access Procedures, "
                "Authorized Personnel Lists, Badge Reader Configurations, Access Logs, "
                "Security Training Records, and Physical Security Inspection Reports."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 1,
            "metadata": {
                "control_id": "PE-03",
                "control_family": "Physical and Environmental Protection",
                "framework": "NIST SP 800-53",
                "category": "requirements",
                "keywords": ["access authorization", "visitor", "badge", "audit log", "monitoring"],
            },
        },
        {
            "title": "PE-03: Artifact Type Requirements and Weightages",
            "content": (
                "For PE-03 (Physical Access Control), the required artifact types "
                "and their weightages are: Policy Documents 15%, Procedures 15%, "
                "Access Lists 20%, System Configurations 20%, Audit Logs 15%, "
                "Training Records 5%, Inspection Reports 10%. Total weightage sums "
                "to 100%. Fully Mapped requires >=90% of artifacts present, current "
                "(within 12 months), and validated. Partially Mapped is 50-89%. "
                "Unmapped is <50% or missing critical artifacts."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "PE-03",
                "framework": "GRC Platform",
                "category": "artifact_requirements",
                "keywords": ["weightage", "artifact", "evidence", "policy", "audit log", "training"],
            },
        },
        {
            "title": "PE-03: Cross-Framework Mappings",
            "content": (
                "PE-03 (Physical Access Control) maps to the following frameworks: "
                "NIST CSF 2.0 - PR.AA-06 (Physical access to assets managed, "
                "monitored, and enforced); CIS Controls v8 - CIS 6 (Access Control "
                "Management); PCI DSS v4.0.1 - 9.2 (Physical access controls) and "
                "9.3 (Badge systems). If PE-03 is fully satisfied, then PR.AA-06, "
                "CIS 6, and PCI 9.2/9.3 are automatically satisfied."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "PE-03",
                "framework": "Cross-Framework",
                "category": "cross_framework_mappings",
                "keywords": ["NIST CSF", "CIS", "PCI DSS", "mapping", "PR.AA-06"],
            },
        },
        # =====================================================================
        # AC-02: Account Management
        # =====================================================================
        {
            "title": "AC-02: Account Management - Description",
            "content": (
                "AC-02 (Account Management) is a NIST SP 800-53 control in the "
                "Access Control family. It requires organizations to manage information "
                "system accounts including establishing, activating, modifying, "
                "reviewing, disabling, and removing accounts. It enforces principles "
                "of least privilege and separation of duties. For datacenter companies, "
                "this includes customer admin access management, NOC operator access "
                "provisioning, and break-glass emergency access procedures."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 0,
            "metadata": {
                "control_id": "AC-02",
                "control_family": "Access Control",
                "framework": "NIST SP 800-53",
                "category": "control_description",
                "keywords": ["account management", "least privilege", "separation of duties", "IAM"],
            },
        },
        {
            "title": "AC-02: Account Management - Requirements",
            "content": (
                "AC-02 requires: (a) Establishing and documenting account types and "
                "authorization procedures; (b) Activating accounts with proper "
                "authorization; (c) Disabling accounts after inactivity; (d) Removing "
                "accounts when no longer needed; (e) Reviewing accounts quarterly; "
                "(f) Enforcing least privilege and separation of duties. Required "
                "evidence includes: Account Management Policy, Account Creation/"
                "Termination Procedures, Active Account Lists, Quarterly Access "
                "Review Records, IAM System Configurations, MFA Settings, Account "
                "Activity Logs, and Admin Training Documentation."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 1,
            "metadata": {
                "control_id": "AC-02",
                "control_family": "Access Control",
                "framework": "NIST SP 800-53",
                "category": "requirements",
                "keywords": ["account", "authentication", "privilege", "review", "least privilege"],
            },
        },
        {
            "title": "AC-02: Artifact Type Requirements and Weightages",
            "content": (
                "For AC-02 (Account Management), the required artifact types "
                "and their weightages are: Policy Documents 15%, Procedures 15%, "
                "Account Inventories 20%, Access Reviews 20%, Configuration Records "
                "15%, Audit Logs 10%, Training Records 5%. Total weightage sums to "
                "100%. Fully Mapped requires >=90% of artifacts present, current "
                "(within 12 months), and validated. Partially Mapped is 50-89%. "
                "Unmapped is <50% or missing critical artifacts."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "AC-02",
                "framework": "GRC Platform",
                "category": "artifact_requirements",
                "keywords": ["weightage", "artifact", "account inventory", "access review"],
            },
        },
        {
            "title": "AC-02: Cross-Framework Mappings",
            "content": (
                "AC-02 (Account Management) maps to the following frameworks: "
                "NIST CSF 2.0 - PR.AA-05 (Identity management, authentication, "
                "and access control enforced); CIS Controls v8 - CIS 5 (Account "
                "Management) and CIS 6 (Access Control Management); PCI DSS v4.0.1 "
                "- 2.2 (System accounts) and 7.2 (Access assignment). If AC-02 is "
                "fully satisfied, then PR.AA-05, CIS 5/6, and PCI 2.2/7.2 are "
                "automatically satisfied."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "AC-02",
                "framework": "Cross-Framework",
                "category": "cross_framework_mappings",
                "keywords": ["NIST CSF", "CIS", "PCI DSS", "mapping", "PR.AA-05"],
            },
        },
        # =====================================================================
        # SC-07: Boundary Protection
        # =====================================================================
        {
            "title": "SC-07: Boundary Protection - Description",
            "content": (
                "SC-07 (Boundary Protection) is a NIST SP 800-53 control in the "
                "System and Communications Protection family. It requires organizations "
                "to monitor and control communications at external managed interfaces "
                "to the system and at key internal managed interfaces within the "
                "system. It also requires implementing subnetworks for publicly "
                "accessible system components. For datacenter companies, this includes "
                "network segmentation between customer VLANs, DDoS protection, "
                "multi-tenant network isolation, and inter-VLAN routing policies."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 0,
            "metadata": {
                "control_id": "SC-07",
                "control_family": "System and Communications Protection",
                "framework": "NIST SP 800-53",
                "category": "control_description",
                "keywords": ["boundary protection", "network", "firewall", "segmentation", "DMZ"],
            },
        },
        {
            "title": "SC-07: Boundary Protection - Requirements",
            "content": (
                "SC-07 requires: (a) Monitoring and controlling communications at "
                "external and key internal managed interfaces; (b) Implementing "
                "subnetworks for publicly accessible system components; (c) Blocking "
                "network traffic by default and allowing access by exception; "
                "(d) Preventing unauthorized information transfer via shared resources; "
                "(e) Managing connections to external networks. Required evidence "
                "includes: Network Architecture Diagrams, Firewall Rule Sets, Network "
                "Segmentation Policies, IDS/IPS Configurations, Network Traffic Logs, "
                "Blocked Connection Logs, and Change Management Records."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 1,
            "metadata": {
                "control_id": "SC-07",
                "control_family": "System and Communications Protection",
                "framework": "NIST SP 800-53",
                "category": "requirements",
                "keywords": ["network", "firewall", "segmentation", "interface", "subnet"],
            },
        },
        {
            "title": "SC-07: Artifact Type Requirements and Weightages",
            "content": (
                "For SC-07 (Boundary Protection), the required artifact types "
                "and their weightages are: Network Architecture 20%, Firewall Rules "
                "25%, Segmentation Policies 15%, Monitoring Configurations 15%, "
                "Audit Logs 15%, Change Records 10%. Total weightage sums to 100%. "
                "Fully Mapped requires >=90% of artifacts present, current (within "
                "12 months), and validated. Partially Mapped is 50-89%. Unmapped "
                "is <50% or missing critical artifacts."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "SC-07",
                "framework": "GRC Platform",
                "category": "artifact_requirements",
                "keywords": ["weightage", "artifact", "network", "firewall", "segmentation"],
            },
        },
        {
            "title": "SC-07: Cross-Framework Mappings",
            "content": (
                "SC-07 (Boundary Protection) maps to the following frameworks: "
                "NIST CSF 2.0 - PR.IR-01 (Networks and environments are protected); "
                "CIS Controls v8 - CIS 13 (Network Monitoring and Defense) and "
                "CIS 9 (Email and Browser Protections); PCI DSS v4.0.1 - 1.2 "
                "(Firewall/network controls) and 1.3 (DMZ). If SC-07 is fully "
                "satisfied, then PR.IR-01, CIS 13/9, and PCI 1.2/1.3 are "
                "automatically satisfied."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "SC-07",
                "framework": "Cross-Framework",
                "category": "cross_framework_mappings",
                "keywords": ["NIST CSF", "CIS", "PCI DSS", "mapping", "PR.IR-01"],
            },
        },
        # =====================================================================
        # IR-06: Incident Reporting
        # =====================================================================
        {
            "title": "IR-06: Incident Reporting - Description",
            "content": (
                "IR-06 (Incident Reporting) is a NIST SP 800-53 control in the "
                "Incident Response family. It requires organizations to require "
                "personnel to report suspected security incidents to the organizational "
                "incident response capability within an organization-defined time "
                "period, and report incidents to designated organizations or external "
                "parties. For datacenter companies, this includes customer breach "
                "notification procedures, SLA escalation processes, and incident "
                "notification templates."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 0,
            "metadata": {
                "control_id": "IR-06",
                "control_family": "Incident Response",
                "framework": "NIST SP 800-53",
                "category": "control_description",
                "keywords": ["incident", "reporting", "breach", "notification", "response"],
            },
        },
        {
            "title": "IR-06: Incident Reporting - Requirements",
            "content": (
                "IR-06 requires: (a) Requiring personnel to report suspected "
                "security incidents within the organization-defined time period; "
                "(b) Reporting incidents to the organizational incident response "
                "capability; (c) Reporting incidents to designated external "
                "organizations and parties; (d) Providing incident reports to "
                "affected stakeholders. Required evidence includes: Incident "
                "Response Policy, Incident Response Plan, Escalation Procedures, "
                "IR Training Materials, Incident Tickets, Investigation Reports, "
                "Notification Records, Post-Incident Reports, Improvement Action "
                "Items, and Emergency Contact Lists."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 1,
            "metadata": {
                "control_id": "IR-06",
                "control_family": "Incident Response",
                "framework": "NIST SP 800-53",
                "category": "requirements",
                "keywords": ["incident", "breach", "report", "notification", "escalation"],
            },
        },
        {
            "title": "IR-06: Artifact Type Requirements and Weightages",
            "content": (
                "For IR-06 (Incident Reporting), the required artifact types "
                "and their weightages are: Policy Documents 15%, IR Plan 20%, "
                "Training Records 10%, Incident Records 25%, Communication Logs "
                "15%, Lessons Learned 10%, Contact Lists 5%. Total weightage sums "
                "to 100%. Fully Mapped requires >=90% of artifacts present, current "
                "(within 12 months), and validated. Partially Mapped is 50-89%. "
                "Unmapped is <50% or missing critical artifacts."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "IR-06",
                "framework": "GRC Platform",
                "category": "artifact_requirements",
                "keywords": ["weightage", "artifact", "incident", "response", "IR plan"],
            },
        },
        {
            "title": "IR-06: Cross-Framework Mappings",
            "content": (
                "IR-06 (Incident Reporting) maps to the following frameworks: "
                "NIST CSF 2.0 - RS.CO-02 (Incidents are reported to designated "
                "internal and external stakeholders); CIS Controls v8 - CIS 17 "
                "(Incident Response Management); PCI DSS v4.0.1 - 12.10 (Incident "
                "response plan). If IR-06 is fully satisfied, then RS.CO-02, "
                "CIS 17, and PCI 12.10 are automatically satisfied."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "IR-06",
                "framework": "Cross-Framework",
                "category": "cross_framework_mappings",
                "keywords": ["NIST CSF", "CIS", "PCI DSS", "mapping", "RS.CO-02"],
            },
        },
        # =====================================================================
        # RA-05: Vulnerability Scanning
        # =====================================================================
        {
            "title": "RA-05: Vulnerability Scanning - Description",
            "content": (
                "RA-05 (Vulnerability Scanning) is a NIST SP 800-53 control in the "
                "Risk Assessment family. It requires organizations to scan for "
                "vulnerabilities in organizational information systems and system "
                "components at an organization-defined frequency, and report findings. "
                "For datacenter companies, this includes infrastructure vulnerability "
                "scanning, hypervisor scanning, scanning scope documentation, and "
                "scan exclusion approvals."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 0,
            "metadata": {
                "control_id": "RA-05",
                "control_family": "Risk Assessment",
                "framework": "NIST SP 800-53",
                "category": "control_description",
                "keywords": ["vulnerability", "scanning", "patch", "risk assessment", "remediation"],
            },
        },
        {
            "title": "RA-05: Vulnerability Scanning - Requirements",
            "content": (
                "RA-05 requires: (a) Scanning for vulnerabilities in the information "
                "system and hosted applications at organization-defined frequency; "
                "(b) Using vulnerability scanning tools and techniques that promote "
                "interoperability; (c) Analyzing scan reports and remediation; "
                "(d) Remediating legitimate vulnerabilities; (e) Sharing information "
                "about the content and results of vulnerability scans. Required "
                "evidence includes: Vulnerability Scanning Policy, Scanner "
                "Configurations, Scan Profiles, Vulnerability Reports, Patch Records, "
                "Remediation Tickets, Exception Approvals, Rescan Verification, "
                "False Positive Analysis, and Vulnerability Trend Reports."
            ),
            "source": "NIST SP 800-53 Rev 5",
            "chunk_index": 1,
            "metadata": {
                "control_id": "RA-05",
                "control_family": "Risk Assessment",
                "framework": "NIST SP 800-53",
                "category": "requirements",
                "keywords": ["vulnerability", "scan", "patch", "remediation", "risk"],
            },
        },
        {
            "title": "RA-05: Artifact Type Requirements and Weightages",
            "content": (
                "For RA-05 (Vulnerability Scanning), the required artifact types "
                "and their weightages are: Scanning Policies 15%, Tool Configurations "
                "20%, Scan Results 25%, Remediation Records 20%, Validation Reports "
                "10%, Metrics/Reports 10%. Total weightage sums to 100%. Fully Mapped "
                "requires >=90% of artifacts present, current (within 12 months), and "
                "validated. Partially Mapped is 50-89%. Unmapped is <50% or missing "
                "critical artifacts."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "RA-05",
                "framework": "GRC Platform",
                "category": "artifact_requirements",
                "keywords": ["weightage", "artifact", "vulnerability", "scan", "remediation"],
            },
        },
        {
            "title": "RA-05: Cross-Framework Mappings",
            "content": (
                "RA-05 (Vulnerability Scanning) maps to the following frameworks: "
                "NIST CSF 2.0 - ID.RA-01 (Vulnerabilities are identified, validated, "
                "and recorded); CIS Controls v8 - CIS 7 (Continuous Vulnerability "
                "Management); PCI DSS v4.0.1 - 11.3 (External vulnerability scans) "
                "and 6.3 (Secure development). If RA-05 is fully satisfied, then "
                "ID.RA-01, CIS 7, and PCI 11.3/6.3 are automatically satisfied."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "control_id": "RA-05",
                "framework": "Cross-Framework",
                "category": "cross_framework_mappings",
                "keywords": ["NIST CSF", "CIS", "PCI DSS", "mapping", "ID.RA-01"],
            },
        },
        # =====================================================================
        # Compliance Best Practices for Datacenter Companies
        # =====================================================================
        {
            "title": "Compliance Best Practices - Evidence Collection Priorities",
            "content": (
                "Recommended evidence collection priorities for datacenter "
                "compliance: Priority 1 - System Configurations (20-25% weightage): "
                "Direct technical proof of control implementation. Priority 2 - "
                "Policy/Procedures (15-20% weightage): Foundational governance "
                "documentation. Priority 3 - Audit Logs/Monitoring (15-20% weightage): "
                "Continuous evidence of control operation. Priority 4 - Access "
                "Reviews/Lists (15-20% weightage): Periodic validation of control "
                "effectiveness. Priority 5 - Training Records (5-10% weightage): "
                "Supporting evidence of awareness. Priority 6 - Incident/Change "
                "Records (10-15% weightage): Operational evidence of control response."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "category": "best_practices",
                "keywords": ["evidence", "collection", "priority", "artifact", "best practice"],
            },
        },
        {
            "title": "Compliance Best Practices - Certification Readiness Checklist",
            "content": (
                "Datacenter certification readiness checklist: PE-03: Physical "
                "access logs exported for last 12 months. PE-03: Badge reader system "
                "configuration documented. PE-03: Visitor access procedures current "
                "and approved. AC-02: Account inventory with last 90-day review "
                "timestamp. AC-02: Service account inventory with ownership "
                "documentation. AC-02: Privileged access review records (quarterly "
                "minimum). SC-07: Network architecture diagram (current version). "
                "SC-07: Firewall rule documentation with business justification. "
                "SC-07: Network segmentation validation testing results. IR-06: "
                "Incident response plan (approved within 12 months). IR-06: Incident "
                "notification templates for all stakeholders. RA-05: Vulnerability "
                "scan schedule and execution records. RA-05: Remediation tracking "
                "with SLA compliance metrics."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 1,
            "metadata": {
                "category": "best_practices",
                "keywords": ["certification", "readiness", "checklist", "datacenter", "compliance"],
            },
        },
        {
            "title": "Compliance Best Practices - Mapping Status Assessment",
            "content": (
                "Mapping status assessment criteria: Fully Mapped requires >=90% "
                "of required artifacts present, current (within 12 months), and "
                "validated by independent review with all artifact types documented "
                "with validation. Partially Mapped requires 50-89% of required "
                "artifacts present with some gaps identified, most artifact types "
                "present and documented remediation plan for gaps. Unmapped is <50% "
                "of required artifacts present or critical artifacts missing with "
                "documented gap analysis and remediation roadmap."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 2,
            "metadata": {
                "category": "best_practices",
                "keywords": ["mapping", "status", "assessment", "fully mapped", "partially mapped", "unmapped"],
            },
        },
        {
            "title": "Datacenter-Specific Compliance - Critical Controls",
            "content": (
                "Critical datacenter controls with additional considerations: "
                "PE-03 - Server room access, cage security, rack locks. Additional "
                "artifacts: Biometric enrollment records, cage key inventory. "
                "SC-07 - Network segmentation between customer VLANs, DDoS protection. "
                "Additional artifacts: Multi-tenant network diagrams, inter-VLAN "
                "routing policies. AC-02 - Customer admin access, NOC operator access. "
                "Additional artifacts: Customer access provisioning records, break-glass "
                "procedures. RA-05 - Infrastructure vulnerability scanning, hypervisor "
                "scanning. Additional artifacts: Scanning scope documentation, scan "
                "exclusion approvals. IR-06 - Customer breach notification, SLA "
                "escalation. Additional artifacts: Customer notification templates, "
                "SLA compliance reports."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 3,
            "metadata": {
                "category": "best_practices",
                "keywords": ["datacenter", "critical", "controls", "PE-03", "SC-07", "AC-02", "RA-05", "IR-06"],
            },
        },
        {
            "title": "Cross-Framework Mapping Matrix Overview",
            "content": (
                "Cross-framework mapping relationships: PE-03 maps to PR.AA-06 "
                "(NIST CSF), CIS 6 (CIS), PCI 9.2/9.3 (PCI DSS). AC-02 maps to "
                "PR.AA-05 (NIST CSF), CIS 5/6 (CIS), PCI 2.2/7.2 (PCI DSS). "
                "SC-07 maps to PR.IR-01 (NIST CSF), CIS 13/9 (CIS), PCI 1.2/1.3 "
                "(PCI DSS). IR-06 maps to RS.CO-02 (NIST CSF), CIS 17 (CIS), "
                "PCI 12.10 (PCI DSS). RA-05 maps to ID.RA-01 (NIST CSF), CIS 7 "
                "(CIS), PCI 11.3/6.3 (PCI DSS). Overlap categories: High overlap "
                "(all 4 frameworks) for PE-03, AC-02, SC-07 where a single evidence "
                "set satisfies multiple frameworks."
            ),
            "source": "GRC Platform Framework Research",
            "chunk_index": 0,
            "metadata": {
                "category": "cross_framework_mappings",
                "keywords": ["mapping", "matrix", "NIST CSF", "CIS", "PCI DSS", "overlap"],
            },
        },
    ]


# =============================================================================
# Chunking Helpers
# =============================================================================

def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split a large text into overlapping chunks for embedding.

    Args:
        text: The text to split into chunks.
        max_chunk_size: Maximum characters per chunk (default 1000).
        overlap: Overlap between consecutive chunks in characters (default 100).

    Returns:
        list[str]: List of text chunks.
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Try to split at a sentence boundary near the limit
        split_at = text.rfind(". ", start, end)
        if split_at == -1 or split_at < start + max_chunk_size // 2:
            split_at = text.rfind(" ", start, end)
        if split_at == -1 or split_at < start + max_chunk_size // 2:
            split_at = end
        else:
            split_at += 1  # Include the period/space

        chunks.append(text[start:split_at])
        start = split_at - overlap

    return chunks


# =============================================================================
# Database Operations
# =============================================================================

def ingest_document(
    title: str,
    content: str,
    source: str = "user_upload",
    metadata: Optional[dict[str, Any]] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Ingest a document into the knowledge base.

    Splits the document into chunks, generates embeddings for each chunk,
    and stores them in the knowledge_base table.

    Args:
        title: Document title.
        content: Document text content.
        source: Source identifier (default "user_upload").
        metadata: Optional metadata dict.
        user_id: Optional user ID for audit logging.
        ip_address: Optional IP address for audit logging.

    Returns:
        dict: Result with document_id, chunk_count, and chunks info.

    Raises:
        RuntimeError: If database operations fail.
    """
    from api.database import create_knowledge_entry  # noqa: WPS433

    metadata = metadata or {}
    chunks_text = chunk_text(content)
    embedding_service = EmbeddingService()

    # Generate embeddings for all chunks
    embeddings = embedding_service.embed_batch(chunks_text)

    chunk_records: list[dict[str, Any]] = []
    for idx, (chunk_text_content, embedding_vector) in enumerate(
        zip(chunks_text, embeddings)
    ):
        entry = create_knowledge_entry(
            title=f"{title} (chunk {idx + 1})" if len(chunks_text) > 1 else title,
            content=chunk_text_content,
            source=source,
            chunk_index=idx,
            embedding_vector=embedding_vector,
            metadata=metadata,
            user_id=user_id,
            ip_address=ip_address,
        )
        chunk_records.append(entry)

    return {
        "document_id": chunk_records[0]["id"] if chunk_records else None,
        "title": title,
        "chunk_count": len(chunk_records),
        "chunks": chunk_records,
    }


def load_preloaded_knowledge(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Load the pre-defined knowledge entries into the database.

    Processes all pre-loaded compliance knowledge entries and ingests
    them into the knowledge_base table.

    Args:
        user_id: Optional user ID for audit logging.
        ip_address: Optional IP address for audit logging.

    Returns:
        dict: Summary of the loading operation.
    """
    entries = get_preloaded_knowledge()
    embedding_service = EmbeddingService()

    from api.database import create_knowledge_entry  # noqa: WPS433

    loaded_count = 0
    skip_count = 0
    error_count = 0
    errors: list[str] = []

    for entry in entries:
        try:
            content = entry["content"]
            embedding = embedding_service.embed_text(content)

            create_knowledge_entry(
                title=entry["title"],
                content=content,
                source=entry.get("source", "Pre-loaded"),
                chunk_index=entry.get("chunk_index", 0),
                embedding_vector=embedding,
                metadata=entry.get("metadata", {}),
                user_id=user_id,
                ip_address=ip_address,
            )
            loaded_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"Failed to load '{entry.get('title', 'unknown')}': {e}")
            logger.error(f"Error loading knowledge entry '{entry['title']}': {e}")

    return {
        "total_entries": len(entries),
        "loaded_count": loaded_count,
        "skip_count": skip_count,
        "error_count": error_count,
        "errors": errors,
    }
