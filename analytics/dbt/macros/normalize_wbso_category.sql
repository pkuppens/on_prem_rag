{#
  Maps a WBSO activity name (calendar_events.summary) to its reporting category code.
  Single dbt-side source of truth for the activity -> category mapping that the Python side keeps in
  docs/project/hours/config/wbso_activities.json (read by src/wbso/activities.py) and re-derives in
  src/wbso/reporting.py (infer_category_from_repos). Unmapped names become 'UNMAPPED', which the
  accepted_values test on the normalized column turns into a loud failure instead of a silent fall-through.
#}
{% macro normalize_wbso_category(activity_column) -%}
    {%- set mapping = {
      'AI Framework Ontwikkeling': 'AI_FRAMEWORK',
      'LLM Integratie en Model Selectie': 'AI_FRAMEWORK',
      'AI Agent Orkestratie': 'AI_FRAMEWORK',
      'Prompt Engineering en Jailbreak Detectie': 'AI_FRAMEWORK',
      'Natural Language Processing Implementatie': 'AI_FRAMEWORK',
      'Intentieherkenning en Semantische Interpretatie': 'AI_FRAMEWORK',
      'Tekstverwerking en Tokenisatie': 'AI_FRAMEWORK',
      'Vector Store Ontwikkeling': 'AI_FRAMEWORK',
      'Vector Database Implementatie': 'AI_FRAMEWORK',
      'RAG Pipeline Ontwikkeling': 'AI_FRAMEWORK',
      'Document Retrieval en Context Aggregatie': 'AI_FRAMEWORK',
      'Semantische Zoekfunctionaliteit': 'AI_FRAMEWORK',
      'Authenticatie Systeem Ontwikkeling': 'ACCESS_CONTROL',
      'Gebruikersauthenticatie en Sessiebeheer': 'ACCESS_CONTROL',
      'Autorisatie Framework Ontwikkeling': 'ACCESS_CONTROL',
      'Rolgebaseerde Toegangscontrole': 'ACCESS_CONTROL',
      'Context-gebaseerde Toegangscontrole': 'ACCESS_CONTROL',
      'Beveiligingsmechanismen Ontwikkeling': 'ACCESS_CONTROL',
      'Encryptie en Beveiligingsmechanismen': 'ACCESS_CONTROL',
      'Privacy-bewuste Cloud Integratie': 'PRIVACY_CLOUD',
      'Data Anonimisering en Pseudonimisering': 'PRIVACY_CLOUD',
      'Cloud-waardigheid Beslisregels': 'PRIVACY_CLOUD',
      'Data Bescherming Ontwikkeling': 'PRIVACY_CLOUD',
      'AVG Compliance en Toestemmingsverificatie': 'PRIVACY_CLOUD',
      'Audit Logging Systeem Ontwikkeling': 'AUDIT_LOGGING',
      'Privacyvriendelijke Audit Log Structuur': 'AUDIT_LOGGING',
      'Monitoring Oplossingen Ontwikkeling': 'AUDIT_LOGGING',
      'Data Integriteit Bescherming': 'DATA_INTEGRITY',
      'Query Classificatie (Lezen/Bewerken)': 'DATA_INTEGRITY',
      'Datacorruptie Preventie': 'DATA_INTEGRITY',
      'Validatie Frameworks Ontwikkeling': 'DATA_INTEGRITY',
      'API Ontwikkeling en Integratie': 'GENERAL_RD',
      'Backend API Ontwikkeling (FastAPI)': 'GENERAL_RD',
      'Frontend Integratie (React)': 'GENERAL_RD',
      'Database Ontwikkeling en Optimalisatie': 'GENERAL_RD',
      'Test Framework Ontwikkeling': 'GENERAL_RD',
      'Technische Documentatie Ontwikkeling': 'GENERAL_RD',
      'Architectuur Ontwerp en Planning': 'GENERAL_RD',
      'Systeemarchitectuur Ontwerp': 'GENERAL_RD',
      'Performance Optimalisatie': 'GENERAL_RD',
      'Deployment Automatisering': 'GENERAL_RD',
      'Onderzoek en Analyse': 'GENERAL_RD',
      'Algemeen R&D Werk': 'GENERAL_RD',
    } -%}
    case {{ activity_column }}
    {%- for activity, category in mapping.items() %}
        when '{{ activity | replace("'", "''") }}' then '{{ category }}'
    {%- endfor %}
        else 'UNMAPPED'
    end
{%- endmacro %}
