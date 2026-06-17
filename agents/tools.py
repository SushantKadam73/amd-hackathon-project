"""GRC Platform - Custom Agno Tools.

Provides Agno-compatible tool functions for querying control status,
evidence, gap analysis, and mapping suggestions. These tools are
registered with Agno agents to enable database-backed GRC operations.
"""

from typing import Any, Optional

from agno.tools import Toolkit

from api.database import (
    get_control,
    list_controls_by_framework,
    list_mappings_by_control,
    list_evidence,
    get_evidence,
    calculate_compliance_score,
    get_gap_summary,
)


class GRCTools(Toolkit):
    """Toolkit of GRC-related functions for Agno agents.

    Registers the following tools:
        - check_control_status: Get compliance status for a control
        - get_evidence_for_control: List evidence mapped to a control
        - calculate_gap_analysis: Get a full gap analysis across all controls
        - suggest_mapping: Suggest evidence-to-control mapping candidates
    """

    def __init__(self):
        super().__init__(name="grc_tools")

        self.register(self.check_control_status)
        self.register(self.get_evidence_for_control)
        self.register(self.calculate_gap_analysis)
        self.register(self.suggest_mapping)

    @staticmethod
    def check_control_status(control_ref_id: str) -> str:
        """Get the compliance status for a specified control.

        Looks up the control by its reference ID (e.g., 'PE-03', 'AC-02')
        and returns its current compliance score, mapping status, and
        artifact coverage details.

        Args:
            control_ref_id: The control reference ID (e.g., 'PE-03', 'AC-02',
                'SC-07', 'IR-06', 'RA-05').

        Returns:
            str: A formatted string describing the control's compliance
                status including score, coverage, and evidence count.
        """
        try:
            # Find the control by reference ID across frameworks
            # For simplicity, query the database directly for the control
            from api.database import get_cursor

            with get_cursor() as cur:
                cur.execute(
                    "SELECT id, control_id, title, description, "
                    "control_family, artifact_requirements "
                    "FROM controls WHERE control_id = %s",
                    (control_ref_id,),
                )
                ctrl = cur.fetchone()

            if not ctrl:
                return (
                    f"Control '{control_ref_id}' not found. "
                    f"Available controls: PE-03, AC-02, SC-07, IR-06, RA-05."
                )

            ctrl_id = ctrl["id"]
            requirements = ctrl.get("artifact_requirements") or []

            # Calculate total required weightage
            total_required = sum(
                float(req.get("weightage", 0)) for req in requirements
            )

            # Get approved mappings
            with get_cursor() as cur2:
                cur2.execute(
                    "SELECT weightage, artifact_type FROM evidence_control_mappings "
                    "WHERE control_id = %s AND mapping_status = 'approved'",
                    (ctrl_id,),
                )
                approved = cur2.fetchall()

            validated_weightage = sum(
                float(m["weightage"]) for m in approved
            )

            # Get all mappings (any status)
            with get_cursor() as cur3:
                cur3.execute(
                    "SELECT COUNT(DISTINCT evidence_id) as cnt "
                    "FROM evidence_control_mappings WHERE control_id = %s",
                    (ctrl_id,),
                )
                evidence_count = cur3.fetchone()["cnt"] or 0

            if total_required > 0:
                score = min(
                    (validated_weightage / total_required) * 100, 100.0
                )
            else:
                score = 0.0

            if score >= 90.0:
                status = "Fully Mapped"
            elif score >= 50.0:
                status = "Partially Mapped"
            else:
                status = "Unmapped"

            return (
                f"**{ctrl['control_id']}**: {ctrl['title']}\n"
                f"- **Family**: {ctrl.get('control_family', 'N/A')}\n"
                f"- **Status**: {status}\n"
                f"- **Compliance Score**: {round(score, 1)}%\n"
                f"- **Validated Weightage**: {round(validated_weightage, 1)} / {round(total_required, 1)}\n"
                f"- **Evidence Artifacts Mapped**: {evidence_count}\n"
                f"- **Description**: {ctrl.get('description', 'N/A')[:200]}"
            )

        except Exception as e:
            return f"Error checking control status: {str(e)}"

    @staticmethod
    def get_evidence_for_control(control_ref_id: str) -> str:
        """List all evidence artifacts mapped to a specified control.

        Retrieves evidence mappings for the given control reference ID
        (e.g., 'PE-03') and returns details of each mapped artifact
        including its type, weightage, and mapping status.

        Args:
            control_ref_id: The control reference ID (e.g., 'PE-03', 'AC-02',
                'SC-07', 'IR-06', 'RA-05').

        Returns:
            str: A formatted string listing all evidence artifacts mapped
                to the control with their details.
        """
        try:
            from api.database import get_cursor

            with get_cursor() as cur:
                cur.execute(
                    "SELECT id FROM controls WHERE control_id = %s",
                    (control_ref_id,),
                )
                ctrl = cur.fetchone()

            if not ctrl:
                return (
                    f"Control '{control_ref_id}' not found. "
                    f"Available controls: PE-03, AC-02, SC-07, IR-06, RA-05."
                )

            mappings = list_mappings_by_control(str(ctrl["id"]))

            if not mappings:
                return (
                    f"No evidence artifacts mapped to {control_ref_id} yet."
                )

            lines = [f"**Evidence mapped to {control_ref_id}:**"]
            for m in mappings:
                lines.append(
                    f"- **{m.get('evidence_name', 'Unknown')}** "
                    f"({m.get('file_type', 'N/A')})\n"
                    f"  - Artifact Type: {m.get('artifact_type', 'N/A')}\n"
                    f"  - Weightage: {m.get('weightage', 0)}%\n"
                    f"  - Status: {m.get('mapping_status', 'N/A')}"
                )

            return "\n".join(lines)

        except Exception as e:
            return f"Error retrieving evidence: {str(e)}"

    @staticmethod
    def calculate_gap_analysis() -> str:
        """Perform a full gap analysis across all GRC controls.

        Analyzes the current evidence coverage for each control and
        identifies missing artifact types, their weightage impact,
        and severity levels.

        Returns:
            str: A formatted string with the complete gap analysis
                including total gaps, severity breakdown, and
                per-control details.
        """
        try:
            compliance = calculate_compliance_score()
            gaps = get_gap_summary()

            lines = [
                "## Gap Analysis Summary\n",
                f"**Overall Compliance Score**: {compliance['overall_score']}% "
                f"({compliance['overall_status']})",
                f"**Total Open Gaps**: {gaps['total_open_gaps']}",
                "",
                "### Gaps by Severity:",
            ]

            severity_colors = {
                "critical": "🔴 Critical",
                "high": "🟠 High",
                "medium": "🟡 Medium",
                "low": "🟢 Low",
            }

            for sev, label in severity_colors.items():
                count = gaps["gaps_by_severity"].get(sev, 0)
                lines.append(f"- {label}: {count}")

            lines.append("")
            lines.append("### Per-Control Status:")

            for ctrl in compliance["controls"]:
                lines.append(
                    f"- **{ctrl['control_id']}**: {ctrl['score']}% "
                    f"({ctrl['status']}) - "
                    f"{ctrl['evidence_count']} evidence items"
                )

            return "\n".join(lines)

        except Exception as e:
            return f"Error calculating gap analysis: {str(e)}"

    @staticmethod
    def suggest_mapping(evidence_id: str) -> str:
        """Suggest control mappings for a given evidence artifact.

        Analyzes the evidence artifact and recommends which controls
        it could be mapped to, along with suggested artifact types
        and confidence levels.

        Args:
            evidence_id: The UUID of the evidence artifact to analyze
                for potential control mappings.

        Returns:
            str: A formatted string with suggested mapping candidates
                including control IDs, artifact types, and confidence
                assessments.
        """
        try:
            evidence = get_evidence(evidence_id)
            if not evidence:
                return f"Evidence artifact with ID '{evidence_id}' not found."

            from api.database import get_cursor

            with get_cursor() as cur:
                cur.execute(
                    "SELECT id, control_id, title, artifact_requirements "
                    "FROM controls ORDER BY control_id"
                )
                all_controls = cur.fetchall()

            evidence_name = evidence.get("name", "Unknown")
            content_text = evidence.get("content_text", "") or ""

            # Simple keyword-based mapping suggestion
            keyword_map = {
                "PE-03": [
                    "physical", "access", "badge", "visitor", "security",
                    "door", "entry", "exit", "perimeter", "facility",
                ],
                "AC-02": [
                    "account", "password", "user", "authentication",
                    "privilege", "iam", "identity", "active directory",
                    "ldap", "mfa", "login",
                ],
                "SC-07": [
                    "network", "firewall", "boundary", "segmentation",
                    "vlan", "dmz", "ids", "ips", "traffic", "subnet",
                ],
                "IR-06": [
                    "incident", "response", "breach", "reporting",
                    "escalation", "emergency", "compromise", "crisis",
                ],
                "RA-05": [
                    "vulnerability", "scan", "remediation", "patch",
                    "nessus", "cve", "risk assessment", "audit",
                ],
            }

            content_lower = content_text.lower()
            suggestions = []

            for ctrl in all_controls:
                ctrl_ref = ctrl["control_id"]
                keywords = keyword_map.get(ctrl_ref, [])
                matches = sum(
                    1 for kw in keywords if kw in content_lower
                )

                if matches > 0:
                    confidence = min(matches / len(keywords) * 100, 95)
                    requirements = ctrl.get("artifact_requirements") or []

                    suggested_type = "Documentation"
                    if requirements:
                        suggested_type = requirements[0].get("type", "Documentation")

                    suggestions.append({
                        "control_id": ctrl_ref,
                        "title": ctrl["title"],
                        "confidence": round(confidence, 1),
                        "suggested_artifact_type": suggested_type,
                    })

            if not suggestions:
                return (
                    f"**{evidence_name}** does not strongly match any "
                    f"control based on content analysis. Consider manual "
                    f"review to determine the appropriate mapping."
                )

            lines = [
                f"## Suggested Mappings for: {evidence_name}\n"
            ]
            for s in sorted(
                suggestions, key=lambda x: x["confidence"], reverse=True
            ):
                confidence_label = (
                    "High" if s["confidence"] >= 70
                    else "Medium" if s["confidence"] >= 40
                    else "Low"
                )
                lines.append(
                    f"- **{s['control_id']}** ({s['title']})\n"
                    f"  - Confidence: **{confidence_label}** ({s['confidence']}%)\n"
                    f"  - Suggested Artifact Type: {s['suggested_artifact_type']}"
                )

            lines.append(
                "\n*Note: These are AI-suggested mappings and should be "
                "reviewed before approval.*"
            )

            return "\n".join(lines)

        except Exception as e:
            return f"Error suggesting mapping: {str(e)}"
