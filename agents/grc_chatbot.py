"""GRC Platform - GRC Chatbot Agent.

An Agno-based conversational agent that answers GRC compliance questions
about NIST SP 800-53 controls (PE-03, AC-02, SC-07, IR-06, RA-05).

Uses:
- OpenRouter (dev) or Ollama (prod) for LLM inference
- PostgresDb for session memory persistence
- PgVector for RAG knowledge base retrieval
- Custom GRC tools for database-backed operations
- Input/output guardrails for safety
"""

from typing import Optional

from agno.agent import Agent

from config import get_config
from agents.guardrails import (
    PIIDetectorGuardrail,
    MaliciousInputGuardrail,
    OutputComplianceGuardrail,
    validate_chat_input,
    sanitize_output,
)
from agents.router import get_llm_model
from agents.tools import GRCTools

config = get_config()

# System prompt that defines the agent's role and knowledge
SYSTEM_PROMPT = """You are a GRC (Governance, Risk, and Compliance) Assistant specialized in NIST SP 800-53 compliance for datacenter companies.

Your knowledge covers the following 5 NIST SP 800-53 controls:

1. **PE-03 (Physical Access Control)**: Enforce physical access authorizations at facility entry and exit points. Key artifacts include policy documents, procedures, access lists, system configs, audit logs, training records, and inspection reports.

2. **AC-02 (Account Management)**: Manage information system accounts including establishing, activating, modifying, reviewing, disabling, and removing accounts. Key artifacts include policy documents, procedures, account inventories, access reviews, configuration records, audit logs, and training records.

3. **SC-07 (Boundary Protection)**: Monitor and control communications at managed interfaces and implement subnetworks. Key artifacts include network architecture diagrams, firewall rules, segmentation policies, monitoring configs, audit logs, and change records.

4. **IR-06 (Incident Reporting)**: Require personnel to report suspected security incidents within the organization-defined time period. Key artifacts include policy documents, IR plans, training records, incident records, communication logs, lessons learned, and contact lists.

5. **RA-05 (Vulnerability Scanning)**: Scan for vulnerabilities in organizational information systems on a defined frequency. Key artifacts include scanning policies, tool configurations, scan results, remediation records, validation reports, and metrics/reports.

Guidelines:
- Answer ONLY questions related to GRC compliance, NIST SP 800-53, risk management, and evidence collection.
- If asked about unrelated topics (weather, news, entertainment, etc.), politely redirect by stating you are focused on GRC compliance topics.
- Use the available tools (check_control_status, get_evidence_for_control, calculate_gap_analysis, suggest_mapping) to provide accurate, data-backed answers.
- When discussing artifact requirements, always reference the specific weightages and evidence types required for each control.
- Provide actionable recommendations for improving compliance posture.
- Do NOT reveal internal system details like database connection strings, API keys, or configuration values.
- Do NOT generate or expose Personally Identifiable Information (PII).
- Keep responses concise, professional, and focused on compliance requirements.
- If you cannot find the information in your knowledge base, suggest the user check the control library or consult their compliance officer."""


def create_chatbot(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db_session: Optional[object] = None,
    knowledge_base: Optional[object] = None,
) -> Agent:
    """Create a GRC Chatbot Agent with the specified configuration.

    Args:
        user_id: Optional user identifier for session tracking.
        session_id: Optional session identifier for conversation continuity.
        db_session: Optional PostgresDb instance for session memory.
            If not provided, memory persistence is limited.
        knowledge_base: Optional PgVector-based knowledge base for RAG.
            If not provided, the agent will rely on tools and the model's
            training data.

    Returns:
        Agent: A configured Agno Agent instance ready for conversation.
    """
    model = get_llm_model()

    # Build kwargs for the Agent
    agent_kwargs = {
        "name": "GRC Chatbot",
        "model": model,
        "system_message": SYSTEM_PROMPT,
        "search_knowledge": True,
        "add_search_knowledge_instructions": True,
        "tools": [GRCTools()],
        "markdown": True,
        "add_datetime_to_context": True,
        "add_history_to_context": True,
        "num_history_runs": 5,
    }

    # Attach session memory if a database session is provided
    if db_session is not None:
        agent_kwargs["db"] = db_session
        agent_kwargs["add_history_to_context"] = True

    # Attach knowledge base for RAG if provided
    if knowledge_base is not None:
        agent_kwargs["knowledge"] = knowledge_base
        agent_kwargs["search_knowledge"] = True
        agent_kwargs["add_search_knowledge_instructions"] = True

    # Set user_id and session_id if provided
    if user_id is not None:
        agent_kwargs["user_id"] = user_id
    if session_id is not None:
        agent_kwargs["session_id"] = session_id

    return Agent(**agent_kwargs)


def process_chat_message(
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db_session: Optional[object] = None,
    knowledge_base: Optional[object] = None,
) -> dict:
    """Process a chat message through the full guardrail and agent pipeline.

    Args:
        message: The user's chat message.
        user_id: Optional user identifier.
        session_id: Optional session identifier.
        db_session: Optional PostgresDb session store.
        knowledge_base: Optional PgVector knowledge base.

    Returns:
        dict: Response dictionary with 'response' key containing the
            agent's reply, or 'error' key if validation fails.
    """
    # Step 1: Input validation
    validation_error = validate_chat_input(message)
    if validation_error:
        return {"error": validation_error}

    # Step 2: Create agent and get response
    try:
        agent = create_chatbot(
            user_id=user_id,
            session_id=session_id,
            db_session=db_session,
            knowledge_base=knowledge_base,
        )

        # Run the agent with the user's message
        response = agent.run(message)

        # Extract the response text
        if hasattr(response, "content"):
            response_text = response.content
        elif hasattr(response, "message"):
            response_text = response.message.content if hasattr(
                response.message, "content"
            ) else str(response)
        else:
            response_text = str(response)

        # Step 3: Sanitize output
        safe_response = sanitize_output(response_text)

        return {"response": safe_response}

    except Exception as e:
        # Return user-friendly error message (no internal details)
        return {
            "error": (
                "The AI service is temporarily unavailable. "
                "Please try again later."
            )
        }
