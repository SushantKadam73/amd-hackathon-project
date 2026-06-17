"""GRC Platform - Evidence Analysis Agent.

An Agno-based agent that analyzes uploaded evidence artifacts for:
- Control relevance scoring (0-100) for each of the 5 NIST SP 800-53 controls
- Suggested artifact type classification
- Quality and currency assessment (stale warnings for documents > 12 months)
- Low-confidence result flagging for human review
"""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from agno.agent import Agent

from config import get_config
from agents.guardrails import sanitize_output
from agents.router import get_llm_model

config = get_config()

# Analysis prompt for the evidence analyzer agent
ANALYSIS_PROMPT = """You are an Evidence Analysis Agent for a GRC (Governance, Risk, and Compliance) platform. Your role is to analyze uploaded evidence artifacts and determine their relevance to NIST SP 800-53 controls.

For each piece of evidence, you must evaluate:

1. **Control Relevance Scores (0-100)**: How relevant is this evidence to each control?
   - PE-03 (Physical Access Control): Physical security policies, badge systems, access logs
   - AC-02 (Account Management): Account policies, IAM configs, access reviews
   - SC-07 (Boundary Protection): Network diagrams, firewall rules, segmentation
   - IR-06 (Incident Reporting): Incident plans, response procedures, communication logs
   - RA-05 (Vulnerability Scanning): Scan results, remediation records, vulnerability policies

2. **Suggested Artifact Type**: Classify the evidence into the most appropriate artifact type based on the control's requirements.

3. **Quality Assessment**: Evaluate document quality, completeness, and currency.

4. **Currency Check**: Flag documents older than 12 months as potentially stale.

5. **Confidence Level**: Rate your overall assessment confidence (0.0 to 1.0).

Provide your analysis in a structured format."""


# Control-specific keyword signatures for rule-based analysis
_CONTROL_KEYWORDS: dict[str, list[str]] = {
    "PE-03": [
        "physical access", "badge", "visitor", "door", "gate", "perimeter",
        "facility", "security guard", "mantrap", "biometric", "cage",
        "server room", "key card", "access control system",
    ],
    "AC-02": [
        "account", "password", "user", "authentication", "authorization",
        "privilege", "iam", "identity", "active directory", "ldap",
        "mfa", "login", "access review", "provisioning",
    ],
    "SC-07": [
        "network", "firewall", "boundary", "segmentation", "vlan",
        "dmz", "ids", "ips", "traffic", "subnet", "acl", "vpc",
        "router", "switch", "microsegmentation",
    ],
    "IR-06": [
        "incident", "response", "breach", "reporting", "escalation",
        "emergency", "compromise", "crisis", "notification", "containment",
        "eradication", "recovery", "post-incident",
    ],
    "RA-05": [
        "vulnerability", "scan", "remediation", "patch", "nessus",
        "qualys", "cve", "risk assessment", "penetration test",
        "vulnerability management", "scan result",
    ],
}


def _analyze_by_keywords(
    content_text: str,
    name: str,
    file_type: str,
) -> dict[str, Any]:
    """Perform a keyword-based analysis of evidence content.

    Used as a fallback when the LLM is unavailable, or to provide
    a fast initial assessment.

    Args:
        content_text: The extracted text content of the evidence.
        name: The original filename.
        file_type: The file extension.

    Returns:
        dict: Analysis results with relevance scores, suggested type,
            quality assessment, and confidence level.
    """
    content_lower = (content_text or "").lower()
    name_lower = (name or "").lower()
    combined = f"{name_lower} {content_lower}"

    # Calculate relevance scores based on keyword matches
    total_keywords = 0
    control_matches: dict[str, int] = {}
    control_totals: dict[str, int] = {}

    for control_id, keywords in _CONTROL_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in combined)
        control_matches[control_id] = matches
        control_totals[control_id] = len(keywords)
        total_keywords += len(keywords)

    relevance_scores: dict[str, float] = {}
    for control_id in _CONTROL_KEYWORDS:
        total = control_totals[control_id]
        matches = control_matches[control_id]
        score = min((matches / total) * 100, 100) if total > 0 else 0
        relevance_scores[control_id] = round(score, 1)

    # Determine most relevant control
    best_control = max(
        relevance_scores, key=lambda c: relevance_scores[c]
    )
    best_score = relevance_scores[best_control]

    # Suggest artifact type based on content
    suggested_artifact_type = _suggest_artifact_type(
        combined, best_control
    )

    # Currency check
    currency_assessment = _check_currency(content_text)

    # Quality assessment based on content length and keywords
    word_count = len(content_lower.split()) if content_lower else 0
    if word_count > 500:
        quality = "Good"
    elif word_count > 100:
        quality = "Fair"
    else:
        quality = "Poor"

    # Confidence level
    if best_score >= 50 and word_count > 200:
        confidence = min(best_score / 100, 0.85)
    elif best_score >= 25:
        confidence = min(best_score / 100, 0.6)
    else:
        confidence = 0.3

    requires_review = confidence < 0.5

    return {
        "relevance_scores": relevance_scores,
        "most_relevant_control": best_control,
        "suggested_artifact_type": suggested_artifact_type,
        "quality_assessment": quality,
        "currency": currency_assessment,
        "confidence": round(confidence, 2),
        "requires_review": requires_review,
        "analysis_method": "keyword",
    }


def _suggest_artifact_type(
    text: str, control_id: str
) -> str:
    """Suggest the artifact type based on content analysis.

    Args:
        text: The concatenated file name and content.
        control_id: The most relevant control ID.

    Returns:
        str: The suggested artifact type.
    """
    # Map keywords to artifact types
    type_keywords: dict[str, list[str]] = {
        "Policy Documents": [
            "policy", "policies", "standard", "framework",
        ],
        "Procedures": [
            "procedure", "sop", "process", "workflow", "guideline",
        ],
        "Access Lists": [
            "access list", "authorized", "personnel list", "roster",
        ],
        "System Configurations": [
            "config", "configuration", "setting", "setup", "parameter",
        ],
        "Audit Logs": [
            "audit", "log", "logs", "logging", "audit trail",
        ],
        "Training Records": [
            "training", "awareness", "education", "course", "workshop",
        ],
        "Inspection Reports": [
            "inspection", "assessment", "audit report", "review report",
        ],
        "Network Architecture": [
            "network diagram", "architecture", "topology", "layout",
        ],
        "Firewall Rules": [
            "firewall", "acl", "access control list", "rule set",
        ],
        "Scan Results": [
            "scan", "vulnerability", "nessus", "qualys", "cve",
        ],
        "Incident Records": [
            "incident", "breach", "ticket", "investigation",
        ],
        "IR Plan": [
            "incident response plan", "ir plan", "response plan",
        ],
    }

    text_lower = text.lower()
    best_type = "Documentation"
    best_matches = 0

    for artifact_type, keywords in type_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > best_matches:
            best_matches = matches
            best_type = artifact_type

    return best_type


def _check_currency(content_text: Optional[str]) -> dict[str, Any]:
    """Check the currency of the evidence document.

    Looks for date patterns in the content to determine if the
    document is current (within 12 months) or stale.

    Args:
        content_text: The extracted text content.

    Returns:
        dict: Currency assessment with status ('current' or 'stale'),
            and details.
    """
    if not content_text:
        return {
            "status": "unknown",
            "detail": "Unable to determine document date from content.",
        }

    # Look for date patterns like "2024", "2025", "January 2024", etc.
    year_patterns = re.findall(r"\b(20\d{2})\b", content_text)
    month_patterns = re.findall(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+20\d{2}\b",
        content_text,
        re.IGNORECASE,
    )

    now = datetime.now(timezone.utc)

    if year_patterns:
        # Use the most recent date found
        recent_year = max(int(y) for y in year_patterns)
        # Check if more than 12 months old
        if recent_year < now.year - 1:
            return {
                "status": "stale",
                "detail": (
                    f"The document references {recent_year}, which is "
                    f"more than 12 months old. Consider updating this "
                    f"evidence."
                ),
            }
        elif recent_year < now.year:
            # Previous year - check the month
            return {
                "status": "current",
                "detail": f"Document references year {recent_year}.",
            }
        return {
            "status": "current",
            "detail": f"Document references year {recent_year}.",
        }

    return {
        "status": "unknown",
        "detail": "No date information found in document content.",
    }


def analyze_evidence(
    name: str,
    content_text: Optional[str] = None,
    file_type: Optional[str] = None,
    uploaded_at: Optional[str] = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Analyze an evidence artifact for control relevance and quality.

    Args:
        name: The original filename of the evidence.
        content_text: The extracted text content from the document.
        file_type: The file type/extension.
        uploaded_at: ISO-formatted upload timestamp.
        use_llm: Whether to attempt LLM-based analysis (falls back to
            keyword analysis if LLM is unavailable).

    Returns:
        dict: Analysis results including:
            - relevance_scores: Dict of control_id -> score (0-100)
            - most_relevant_control: The control with the highest score
            - suggested_artifact_type: Best matching artifact type
            - quality_assessment: 'Good', 'Fair', or 'Poor'
            - currency: Currency assessment dict
            - confidence: Overall confidence (0.0-1.0)
            - requires_review: True if confidence < 0.5
    """
    # Always start with keyword analysis as baseline
    keyword_result = _analyze_by_keywords(
        content_text=content_text or "",
        name=name or "",
        file_type=file_type or "",
    )

    # If LLM analysis is requested, attempt it
    if use_llm and config.enable_ai_chat:
        try:
            llm_result = _analyze_with_llm(
                name=name,
                content_text=content_text,
                file_type=file_type,
            )
            if llm_result:
                # Merge LLM results with keyword baseline
                # Use LLM results for relevance and type if confidence is higher
                if llm_result.get("confidence", 0) > keyword_result.get("confidence", 0):
                    return {
                        **llm_result,
                        "analysis_method": "llm",
                    }
                return {
                    **keyword_result,
                    "analysis_method": "keyword_llm_merged",
                }
        except Exception:
            # Fall back to keyword analysis
            pass

    return keyword_result


def _analyze_with_llm(
    name: str,
    content_text: Optional[str] = None,
    file_type: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Analyze evidence using the LLM agent.

    Args:
        name: The filename.
        content_text: The extracted text content.
        file_type: The file type.

    Returns:
        Optional[dict]: Analysis results or None if LLM unavailable.
    """
    try:
        model = get_llm_model()
        agent = Agent(
            name="Evidence Analyzer",
            model=model,
            system_message=ANALYSIS_PROMPT,
            markdown=True,
        )

        evidence_info = (
            f"**File Name**: {name}\n"
            f"**File Type**: {file_type or 'Unknown'}\n"
            f"**Content Preview**:\n"
            f"{(content_text or 'No extractable content')[:2000]}"
        )

        query = (
            f"Analyze this evidence artifact for NIST SP 800-53 relevance:\n\n"
            f"{evidence_info}\n\n"
            f"Provide:\n"
            f"1. Relevance scores (0-100) for PE-03, AC-02, SC-07, IR-06, RA-05\n"
            f"2. Suggested artifact type classification\n"
            f"3. Quality assessment\n"
            f"4. Currency check (is it older than 12 months?)\n"
            f"5. Confidence level (0.0-1.0)\n"
            f"Format as structured data."
        )

        response = agent.run(query)
        response_text = sanitize_output(
            response.content if hasattr(response, "content") else str(response)
        )

        return {
            "relevance_scores": _parse_relevance_from_llm(response_text),
            "most_relevant_control": _find_best_control(
                _parse_relevance_from_llm(response_text)
            ),
            "suggested_artifact_type": _parse_artifact_type(response_text),
            "quality_assessment": _parse_quality(response_text),
            "currency": _parse_currency(response_text),
            "confidence": _parse_confidence(response_text),
            "requires_review": _parse_confidence(response_text) < 0.5,
            "analysis_method": "llm",
            "llm_analysis_text": response_text,
        }

    except Exception:
        return None


def _parse_relevance_from_llm(
    text: str,
) -> dict[str, float]:
    """Parse relevance scores from LLM response text.

    Args:
        text: The LLM's analysis text.

    Returns:
        dict: Control ID to score mapping.
    """
    scores: dict[str, float] = {}
    for control_id in ["PE-03", "AC-02", "SC-07", "IR-06", "RA-05"]:
        # Try to find a score pattern like "PE-03: 85" or "PE-03 - 85"
        patterns = [
            rf"{re.escape(control_id)}[:\s]+(\d+(?:\.\d+)?)",
            rf"{re.escape(control_id)}[:\s-]+(\d+(?:\.\d+)?)\s*[/.]?\s*100",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                scores[control_id] = min(score, 100.0)
                break

        if control_id not in scores:
            scores[control_id] = 0.0

    return scores


def _find_best_control(scores: dict[str, float]) -> str:
    """Find the control with the highest relevance score.

    Args:
        scores: Dict of control_id -> score.

    Returns:
        str: The control ID with the highest score.
    """
    if not scores:
        return "PE-03"
    return max(scores, key=lambda c: scores[c])


def _parse_artifact_type(text: str) -> str:
    """Parse the suggested artifact type from LLM response.

    Args:
        text: The LLM response text.

    Returns:
        str: The suggested artifact type.
    """
    # Look for explicit artifact type mentions
    type_patterns = [
        r"suggested\s+artifact\s+type[:\s-]+(.+)",
        r"artifact\s+type[:\s-]+(.+)",
        r"classification[:\s-]+(.+)",
        r"type[:\s-]+([A-Za-z\s/]+)",
    ]

    for pattern in type_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(".")

    return "Documentation"


def _parse_quality(text: str) -> str:
    """Parse the quality assessment from LLM response.

    Args:
        text: The LLM response text.

    Returns:
        str: 'Good', 'Fair', or 'Poor'.
    """
    text_lower = text.lower()
    if re.search(r"quality[:\s-]*(good|fair|poor)", text_lower):
        match = re.search(
            r"quality[:\s-]*(good|fair|poor)", text_lower
        )
        return match.group(1).capitalize() if match else "Fair"

    # Default based on length
    if len(text) > 500:
        return "Good"
    elif len(text) > 100:
        return "Fair"
    return "Poor"


def _parse_currency(text: str) -> dict[str, str]:
    """Parse the currency assessment from LLM response.

    Args:
        text: The LLM response text.

    Returns:
        dict: Currency status and detail.
    """
    text_lower = text.lower()

    # Check for staleness indicators
    stale_indicators = [
        "stale", "expired", "outdated", "old", "not current",
        "older than 12 months", "more than a year",
    ]

    for indicator in stale_indicators:
        if indicator in text_lower:
            return {
                "status": "stale",
                "detail": "Document appears to be outdated based on content analysis.",
            }

    # Check for current indicators
    current_indicators = [
        "current", "recent", "up to date", "within 12 months",
    ]

    for indicator in current_indicators:
        if indicator in text_lower:
            return {
                "status": "current",
                "detail": "Document appears to be current.",
            }

    return {
        "status": "unknown",
        "detail": "Unable to determine document currency.",
    }


def _parse_confidence(text: str) -> float:
    """Parse the confidence score from LLM response.

    Args:
        text: The LLM response text.

    Returns:
        float: Confidence score between 0.0 and 1.0.
    """
    patterns = [
        r"confidence[:\s-]+(\d+(?:\.\d+)?)",
        r"confidence\s+(?:level|score)[:\s-]+(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            # Normalize to 0.0-1.0 if > 1.0
            if val > 1.0:
                val = val / 100.0
            return max(0.0, min(1.0, val))

    return 0.5


def get_artifact_type_options(control_id: str) -> list[str]:
    """Get the valid artifact type options for a given control.

    Args:
        control_id: The control reference ID (e.g., 'PE-03').

    Returns:
        list[str]: List of valid artifact types for the control.
    """
    from api.database import get_cursor

    with get_cursor() as cur:
        cur.execute(
            "SELECT artifact_requirements FROM controls WHERE control_id = %s",
            (control_id,),
        )
        row = cur.fetchone()

    if not row or not row.get("artifact_requirements"):
        return ["Documentation"]

    requirements = row["artifact_requirements"]
    return [
        req.get("type", "Documentation")
        for req in requirements
        if isinstance(req, dict)
    ]
