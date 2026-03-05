# WBSO Jaarverslag 2025

**Project:** WBSO-AICM-2025-01 – AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving  
**Bedrijf:** pieterkuppens.net (KvK 54225442)  
**Periode:** 2025-06-01 t/m 2025-12-31  
**Opsteller:** Pieter Kuppens  
**Datum:** 2026-03-05

---

## 1. Urenoverzicht

| Kwartaal | S&O-uren | Bron |
|----------|----------|------|
| Q2 2025 (juni) | 169,2 | [uren-samenvatting.md](WBSO-AICM-2025-01/uren-samenvatting.md) |
| Q3 2025 (jul–sep) | 429,0 | idem |
| Q4 2025 (okt–dec) | 365,2 | idem |
| **Totaal** | **964,4** | |

Urenadministratie: [docs/project/hours/](../hours/)

---

## 2. Voortgang en resultaten

### Q2 2025 (juni)

Projectstart. Opzet AI-agent framework, LLM-integratie (Ollama/HuggingFace/LiteLLM), modelselectie voor embeddings en instruct-modellen. Eerste RAG-pipeline voor PDF-query’s; ChromaDB als vector store. Zie [voortgang-Q2-2025.md](WBSO-AICM-2025-01/voortgang-Q2-2025.md).

### Q3 2025 (juli–september)

Uitbreiding privacy, audit en toegangscontrole: AVG-toestemmingsverificatie, privacyvriendelijke auditlog, encryptie, authenticatie (OAuth2/JWT), data-anonimisering, cloud-waardigheidbeslissingen, query-classificatie (lees vs. bewerk), backend FastAPI. Zie [voortgang-Q3-2025.md](WBSO-AICM-2025-01/voortgang-Q3-2025.md).

### Q4 2025 (oktober–december)

RBAC, datacorruptie-preventie, LLM-integratie via LiteLLM, frontend (React/MUI, Chainlit), evaluatieframework voor RAG-retrieval. Zie [voortgang-Q4-2025.md](WBSO-AICM-2025-01/voortgang-Q4-2025.md).

---

## 3. Afwijkingen t.o.v. aanvraag

De RVO accepteert afwijkingen als deze logisch verklaard zijn. De volgende uitkomsten wijken af van de oorspronkelijke verwachtingen:

1. **Chunking en hybrid retrieval**: Conclusie dat semantische chunking en BM25+vector hybrid retrieval meer onderzoek vergen; voor pilot volstaat de huidige fixed-size strategie.
2. **Solo-preneur**: Tempo van state-of-the-art (o.a. knowledge-graph RAG, geavanceerde ragas-metrics) is moeilijk bij te houden; prioriteit gegeven aan een stabiele, werkende basis.
3. **Kleine lokale modellen**: Beperkte multi-lingualiteit van 7B–13B modellen in vergelijking met cloud-modellen; cloud-fallback met screening blijft onderzoeksonderwerp.
4. **Jailbreak-detectie**: Complexer dan voorzien; robuuste detectie vereist vervolgonderzoek.

**Risicomitigatie via WBSO:** Deze onzekerheden rechtvaardigen WBSO; het werk is systematisch uitgevoerd, gedocumenteerd en de conclusies zijn traceerbaar.

---

## 4. Verwijzing naar bewijs

- **Git:** [github.com/pkuppens/on_prem_rag](https://github.com/pkuppens/on_prem_rag) en gerelateerde repos (zie [activity_repo_mapping.md](../hours/output/activity_repo_mapping.md))
- **Issues:** [GitHub Issues](https://github.com/pkuppens/on_prem_rag/issues)
- **Urenbronnen:** [docs/project/hours/](../hours/) – commits, system events, weekly reports
