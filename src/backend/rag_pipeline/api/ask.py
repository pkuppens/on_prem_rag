"""Compatibility shim — delegates to the Query Service API.

Same endpoints as before, but delegates to backend.query_service.api.ask
for the actual implementation.
"""

from backend.query_service.api.ask import router, AskRequest, AskResponse, VoiceAskResponse, ask_question, ask_voice

# Re-export everything for backward compatibility
__all__ = ["router", "AskRequest", "AskResponse", "VoiceAskResponse", "ask_question", "ask_voice"]
