"""Anti-Corruption Layer adapters for the Query Service.

Each adapter translates between the Query Service domain types and
the other bounded context's types:
- access_control.py: ACL to AccessControl BC
- privacy_guard.py: ACL to PrivacyGuard BC
- retrieval.py: Adapter to Retrieval BC
- audit.py: Adapter to AuditTrail BC
- llm.py: Adapter to LLM Gateway BC
"""
