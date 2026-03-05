# Voortgang WBSO-AICM-2025-01 — Q2 2025 (juni)

**Project:** WBSO-AICM-2025-01 – AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving  
**Periode:** 2025-06-01 t/m 2025-06-30  
**Opsteller:** Pieter Kuppens  
**Datum:** 2026-03-05

## Onderzochte onderwerpen

Projectstart 1 juni 2025. Eerste maand gericht op opzet AI-agent framework, LLM-integratie en modelselectie voor on-premises RAG.

- **LLM-integratie**: Onderzoek naar Ollama vs. HuggingFace vs. LiteLLM voor lokale inferentie; configuratie via omgevingsvariabelen.
- **Modelselectie**: Evaluatie van embed-modellen (multilingual-E5-large-instruct) en instruct-modellen voor NL-vragen.
- **AI Agent orkestratie**: Eerste opzet agent-architectuur met LangChain/CrewAI-patterns; intentie-routing.

## Technische uitdagingen en oplossingsrichtingen

- **Tokenlimieten**: Lokale modellen (7B–13B) hebben beperkte context; overlap in chunking (50 token) getest voor retrievalkwaliteit.
- **Prompt engineering**: Eerste jailbreak-detectie regels onderzocht; conclusie dat robuuste detectie meer research vergt (zie afwijkingen).
- **Vector database**: ChromaDB gekozen voor embedded vector store; eerste implementatie document indexing.

## Conclusies en afwijkingen

- Framework-basis staat; RAG-pipeline functioneel voor PDF-query’s.
- **Afwijking**: Jailbreak-detectie is complexer dan voorzien; meerdere prompt-varianten nodig voor betrouwbare classificatie. Vervolgonderzoek gepland.
