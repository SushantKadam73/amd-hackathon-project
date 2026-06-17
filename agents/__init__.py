"""GRC Platform - AI Agents Package (Agno).

Provides the complete Agno-based agent system including:
- GRC Chatbot Agent for compliance Q&A
- Evidence Analysis Agent for document relevance scoring
- Input/output guardrails for safety
- Custom GRC tools for database-backed operations
- LLM model router (OpenRouter dev / Ollama prod)
"""

from agents.grc_chatbot import create_chatbot, process_chat_message
from agents.evidence_analyzer import analyze_evidence, get_artifact_type_options
from agents.guardrails import (
    PIIDetectorGuardrail,
    MaliciousInputGuardrail,
    OutputComplianceGuardrail,
    detect_pii,
    detect_malicious_input,
    validate_output,
    validate_chat_input,
    sanitize_output,
)
from agents.router import get_llm_model, get_llm_model_for_tools
from agents.tools import GRCTools

__all__ = [
    # Chatbot
    "create_chatbot",
    "process_chat_message",
    # Evidence Analyzer
    "analyze_evidence",
    "get_artifact_type_options",
    # Guardrails
    "PIIDetectorGuardrail",
    "MaliciousInputGuardrail",
    "OutputComplianceGuardrail",
    "detect_pii",
    "detect_malicious_input",
    "validate_output",
    "validate_chat_input",
    "sanitize_output",
    # Router
    "get_llm_model",
    "get_llm_model_for_tools",
    # Tools
    "GRCTools",
]
