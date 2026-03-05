# Voortgang WBSO-AICM-2025-01 — Q4 2025 (oktober–december)

**Project:** WBSO-AICM-2025-01 – AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving  
**Periode:** 2025-10-01 t/m 2025-12-31  
**Opsteller:** Pieter Kuppens  
**Datum:** 2026-03-05

## Onderzochte onderwerpen

Integratie, RBAC en productie-voorbereiding:

- **Rolgebaseerde toegangscontrole (RBAC)**: Implementatie rol-context-model; toetsing aan datatoegang.
- **Datacorruptie-preventie**: Classificatiemodule voor read-only vs. muterende queries; blokkade van risicovolle operaties.
- **LLM-integratie**: Uitbreiding naar LiteLLM; modelwisseling via configuratie.
- **Frontend**: React/MUI; Chainlit UI voor agent-interactie.
- **AI Agent orkestratie**: Verdere integratie componenten; end-to-end testen.
- **Evaluatieframework**: RAG-evaluatie met retrieval metrics (NDCG, MAP); benchmark-datasets.

## Technische uitdagingen en oplossingsrichtingen

- **RBAC-granulariteit**: Balans tussen fijnmazige rechten en bruikbaarheid; rolhiërarchie onderzocht.
- **Evaluatiemetrices**: Keuze voor retrieval-first (ragas-achtig) i.p.v. end-to-end LLM-evaluatie; kosten/tijd overweging.

## Conclusies en afwijkingen

- RBAC, datacorruptie-preventie en frontend geïntegreerd; evaluatieframework operationeel.
- **Afwijkingen**:
  1. **State-of-the-art**: Knowledge-graph augmented RAG en advanced ragas-metrics onderzocht maar nog niet geïmplementeerd; gedocumenteerd als future work.
  2. **Risicomitigatie**: WBSO dekt de technische onzekerheden (chunking, modelkeuze, hybrid retrieval); werk is systematisch uitgevoerd en gedocumenteerd.
