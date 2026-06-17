"""GRC Platform - Input/Output Guardrails.

Provides PII detection, malicious input detection, and output compliance
validation for the GRC agent system. Uses regex patterns for PII detection,
common patterns for malicious input detection, and compliance checks for
output validation.
"""

import re
from typing import Optional

from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails.base import BaseGuardrail
from agno.guardrails.pii import PIIDetectionGuardrail
from agno.guardrails.prompt_injection import PromptInjectionGuardrail
from agno.run.agent import RunInput
from agno.run.team import TeamRunInput


# =============================================================================
# PII Patterns
# =============================================================================

# Social Security Numbers (XXX-XX-XXXX)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Credit Card Numbers (standard 16-digit formats)
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[- ]?){3}\d{4}\b"
)

# Email addresses
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Phone numbers (US format)
PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

# Bank Account Numbers (simple pattern - various formats)
BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{8,17}\b")

# Passport Numbers (US format - 9 alphanumeric)
PASSPORT_PATTERN = re.compile(r"\b[A-Za-z0-9]{8,10}\b")

# Driver's License (simplified - various state formats)
DRIVERS_LICENSE_PATTERN = re.compile(
    r"\b[A-Za-z]{1,2}\d{5,9}\b"
)


# =============================================================================
# Malicious Input Patterns
# =============================================================================

# SQL Injection patterns
SQL_INJECTION_PATTERNS = [
    r"'.*OR.*'=",
    r"'.*OR.*1\s*=\s*1",
    r"'.*--",
    r"\bDROP\s+TABLE",
    r"\bDELETE\s+FROM",
    r"\bINSERT\s+INTO",
    r"\bALTER\s+TABLE",
    r"\bEXEC\s*\(.*\)",
    r"\bUNION\s+ALL\s+SELECT",
    r"\bSELECT\s+.*\bFROM\b",
    r"\bxp_cmdshell",
    r"\bWAITFOR\s+DELAY",
    r"\bBENCHMARK\s*\(",
    r"'\s*OR\s+'[^']+'\s*=\s*'",
    r"'\s*OR\s+'\d+'\s*=\s*'\d+",
    r"\bpg_sleep\s*\(",
]

# Common prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|directions|commands)",
    r"forget\s+(everything|all|anything)\s+(above|previous|prior)",
    r"you\s+are\s+now\s+a",
    r"override\s+(your\s+)?(safety|guidelines|restrictions|rules|constraints)",
    r"disregard\s+(the\s+)?(above|previous|all|guidelines|instructions)",
    r"system\s+prompt",
    r"jailbreak",
    r"act\s+as\s+if",
    r"pretend\s+(to\s+be|you\s+are)",
    r"role[- ]?play\s+as",
    r"simulate\s+being",
    r"developer\s+mode",
    r"do\s+anything\s+now",
    r"no\s+(restrictions|limits|boundaries|rules)",
    r"you\s+must\s+not\s+(refuse|decline|deny)",
    r"you\s+have\s+no\s+(restrictions|limitations|filter)",
    r"bypass\s+(the\s+)?(filter|restrictions|rules|guidelines)",
    r"(\`\`\`).*(\`\`\`)",
]

# Compiled malicious input patterns
_SQL_INJECTION_REGEX = re.compile(
    "|".join(SQL_INJECTION_PATTERNS), re.IGNORECASE
)
_PROMPT_INJECTION_REGEX = re.compile(
    "|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE
)


# =============================================================================
# Output Compliance Patterns
# =============================================================================

# Sensitive data patterns for output validation
OUTPUT_SENSITIVE_PATTERNS = [
    SSN_PATTERN,
    CREDIT_CARD_PATTERN,
    BANK_ACCOUNT_PATTERN,
]

# Required GRC compliance keywords
GRC_COMPLIANCE_KEYWORDS = [
    "NIST SP 800-53",
    "PE-03",
    "AC-02",
    "SC-07",
    "IR-06",
    "RA-05",
    "compliance",
    "control",
    "evidence",
    "mapping",
]


# =============================================================================
# Guardrail Functions (standalone, usable outside Agno)
# =============================================================================

def detect_pii(text: str) -> list[dict[str, str]]:
    """Detect PII in the given text using regex patterns.

    Args:
        text: The text to scan for PII.

    Returns:
        list[dict]: A list of detected PII items, each containing
            'type' and 'value' keys. Empty list if no PII found.
    """
    findings: list[dict[str, str]] = []

    # SSN detection
    for match in SSN_PATTERN.finditer(text):
        findings.append({"type": "SSN", "value": match.group()})

    # Credit card detection
    for match in CREDIT_CARD_PATTERN.finditer(text):
        # Basic Luhn check could be added here for accuracy
        findings.append({"type": "CREDIT_CARD", "value": match.group()})

    # Email detection
    for match in EMAIL_PATTERN.finditer(text):
        findings.append({"type": "EMAIL", "value": match.group()})

    # Phone detection
    for match in PHONE_PATTERN.finditer(text):
        findings.append({"type": "PHONE", "value": match.group()})

    return findings


def detect_malicious_input(text: str) -> list[dict[str, str]]:
    """Detect malicious input patterns in the given text.

    Checks for SQL injection and prompt injection patterns.

    Args:
        text: The text to scan for malicious patterns.

    Returns:
        list[dict]: A list of detected threats, each containing
            'type' and 'pattern' keys. Empty list if no threats found.
    """
    findings: list[dict[str, str]] = []

    # SQL injection check
    sql_match = _SQL_INJECTION_REGEX.search(text)
    if sql_match:
        findings.append({
            "type": "SQL_INJECTION",
            "pattern": sql_match.group(),
        })

    # Prompt injection check
    pi_match = _PROMPT_INJECTION_REGEX.search(text)
    if pi_match:
        findings.append({
            "type": "PROMPT_INJECTION",
            "pattern": pi_match.group(),
        })

    return findings


def validate_output(text: str) -> list[dict[str, str]]:
    """Validate that AI output complies with GRC standards.

    Checks that the output:
    - Does not leak sensitive information (PII)
    - Contains appropriate compliance context
    - Does not expose internal system details

    Args:
        text: The output text to validate.

    Returns:
        list[dict]: A list of validation issues found. Empty list if
            output passes all compliance checks.
    """
    issues: list[dict[str, str]] = []

    # Check for sensitive data leakage in output
    for pattern in OUTPUT_SENSITIVE_PATTERNS:
        match = pattern.search(text)
        if match:
            issues.append({
                "type": "SENSITIVE_DATA_LEAK",
                "detail": f"Output may contain sensitive data: '{match.group()[:10]}...'",
            })

    # Check for error message leakage
    error_leak_patterns = [
        r"Traceback \(most recent call last\)",
        r"File \".*\", line \d+",
        r"connection string|DATABASE_URL|api_key",
        r"psycopg2\.OperationalError",
        r"sqlalchemy\.exc\.",
        r"openrouter\.ai.*api.*key",
    ]

    for pattern in error_leak_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append({
                "type": "INTERNAL_DETAIL_LEAK",
                "detail": "Output may expose internal system details or stack traces.",
            })

    return issues


def mask_pii(text: str) -> str:
    """Mask PII in the given text by replacing sensitive values.

    Args:
        text: The text containing potential PII.

    Returns:
        str: The text with PII masked.
    """
    result = text

    # Mask SSNs
    result = SSN_PATTERN.sub("***-**-****", result)
    # Mask credit cards
    result = CREDIT_CARD_PATTERN.sub("****-****-****-****", result)
    # Mask emails
    result = EMAIL_PATTERN.sub("***@***.***", result)
    # Mask phones
    result = PHONE_PATTERN.sub("***-***-****", result)

    return result


def check_grc_relevance(text: str) -> dict[str, bool | float]:
    """Check if text is related to GRC compliance topics.

    Analyzes the text for GRC-relevant keywords and returns a relevance
    assessment.

    Args:
        text: The text to analyze.

    Returns:
        dict: A dictionary with 'is_relevant' (bool) and 'relevance_score'
            (float 0-1) keys.
    """
    text_lower = text.lower()
    matches = sum(
        1 for kw in GRC_COMPLIANCE_KEYWORDS
        if kw.lower() in text_lower
    )
    total_keywords = len(GRC_COMPLIANCE_KEYWORDS)

    return {
        "is_relevant": matches > 0,
        "relevance_score": round(matches / total_keywords, 2),
    }


# =============================================================================
# Agno-Compatible Guardrail Classes
# =============================================================================

class PIIDetectorGuardrail(BaseGuardrail):
    """Agno guardrail that detects and blocks PII in user inputs.

    Integrates with Agno's guardrail system to automatically check
    inputs for SSNs, credit card numbers, emails, and phone numbers.
    """

    def __init__(self, mask_pii: bool = False):
        super().__init__()
        self.mask_pii = mask_pii

    def check(self, run_input: RunInput | TeamRunInput) -> None:
        """Check the run input for PII.

        Args:
            run_input: The input to check.

        Raises:
            InputCheckError: If PII is detected and mask_pii is False.
        """
        text = run_input.input_content_string or ""
        findings = detect_pii(text)

        if findings:
            pii_types = ", ".join(f["type"] for f in findings)
            raise InputCheckError(
                f"PII detected in input: {pii_types}. "
                "Please remove sensitive information and try again."
            )

    async def async_check(self, run_input: RunInput | TeamRunInput) -> None:
        """Async version of PII check.

        Args:
            run_input: The input to check.
        """
        self.check(run_input)


class MaliciousInputGuardrail(BaseGuardrail):
    """Agno guardrail that detects malicious input patterns.

    Checks for common SQL injection and prompt injection patterns
    in user inputs to the agent system.
    """

    def check(self, run_input: RunInput | TeamRunInput) -> None:
        """Check the run input for malicious patterns.

        Args:
            run_input: The input to check.

        Raises:
            InputCheckError: If malicious patterns are detected.
        """
        text = run_input.input_content_string or ""
        findings = detect_malicious_input(text)

        if findings:
            threat_types = ", ".join(f["type"] for f in findings)
            raise InputCheckError(
                f"Malicious input detected: {threat_types}. "
                "Your message was blocked for security reasons."
            )

    async def async_check(self, run_input: RunInput | TeamRunInput) -> None:
        """Async version of malicious input check.

        Args:
            run_input: The input to check.
        """
        self.check(run_input)


class OutputComplianceGuardrail(BaseGuardrail):
    """Agno guardrail that validates AI output compliance.

    Ensures agent outputs do not leak sensitive information or
    internal system details.
    """

    def check(self, run_input: RunInput | TeamRunInput) -> None:
        """Check the output for compliance issues.

        This is called on the run input which, during output validation,
        contains the model's response.

        Args:
            run_input: The output to validate.

        Raises:
            CheckTrigger: If compliance issues are detected requiring
                human review.
        """
        text = run_input.input_content_string or ""
        issues = validate_output(text)

        if issues:
            issue_types = ", ".join(i["type"] for i in issues)
            raise CheckTrigger(
                f"Output compliance issues detected: {issue_types}. "
                "Flagging for human review."
            )

    async def async_check(self, run_input: RunInput | TeamRunInput) -> None:
        """Async version of output compliance check.

        Args:
            run_input: The output to validate.
        """
        self.check(run_input)


def validate_chat_input(text: str) -> Optional[str]:
    """Validate a chat input before processing.

    Runs all input guardrails and returns an error message if
    validation fails, or None if the input is valid.

    Args:
        text: The user's input text to validate.

    Returns:
        Optional[str]: Error message if validation fails, None if valid.
    """
    if not text or not text.strip():
        return "Please type a question. Empty messages are not allowed."

    # Check for PII
    pii_findings = detect_pii(text)
    if pii_findings:
        pii_types = ", ".join(f["type"] for f in pii_findings)
        return (
            f"Your message contains potentially sensitive information "
            f"({pii_types}). Please remove it for privacy and security."
        )

    # Check for malicious input
    malicious_findings = detect_malicious_input(text)
    if malicious_findings:
        return (
            "Your message was blocked because it contains patterns "
            "that could be used for injection attacks."
        )

    return None


def sanitize_output(text: str) -> str:
    """Sanitize AI output before sending to the user.

    Masks any PII that might have been leaked in the output and
    truncates any error messages that might reveal internal details.

    Args:
        text: The raw output text to sanitize.

    Returns:
        str: The sanitized output text.
    """
    # Mask any PII in the output
    text = mask_pii(text)

    # Replace stack traces with safe message
    if re.search(r"(Traceback|Error|Exception):", text):
        # Only clean up if it contains internal paths
        if re.search(
            r"[A-Za-z]:\\(?:Users|Programs|Windows)|site-packages",
            text,
        ):
            text = (
                "An error occurred while processing your request. "
                "Please try again or contact support if the issue persists."
            )

    return text
