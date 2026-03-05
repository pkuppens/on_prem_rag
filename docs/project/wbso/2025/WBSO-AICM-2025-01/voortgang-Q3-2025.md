# Voortgang WBSO-AICM-2025-01 — Q3 2025 (juli–september)

**Project:** WBSO-AICM-2025-01 – AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving  
**Periode:** 2025-07-01 t/m 2025-09-30  
**Opsteller:** Pieter Kuppens  
**Datum:** 2026-03-05

## Onderzochte onderwerpen

Uitbreiding naar privacy, audit en toegangscontrole:

- **AVG/toestemmingsverificatie**: Beslisregels wanneer data wel/niet naar cloud mag; screeninglaag concept.
- **Vector database**: ChromaDB-optimalisatie; document retrieval en context-aggregatie.
- **Encryptie**: Beveiligingsmechanismen voor data-at-rest en in transit.
- **Privacyvriendelijke auditlog**: Ontwerp logstructuur met veilige referenties (geen PII in logs).
- **Systeemarchitectuur**: Bounded-context scheiding; modulaire componenten.
- **Intentieherkenning**: Semantische interpretatie van natuurlijke taalvragen.
- **Authenticatie en sessiebeheer**: OAuth2/JWT-integratie.
- **Data-anonimisering/pseudonimisering**: Onderzoek welke bewerkingen per datatype nodig zijn.
- **Cloud-waardigheid**: Beslisregels welke queries lokaal vs. cloud worden verwerkt.
- **Query-classificatie**: Lees vs. bewerk- classificatie om datacorruptie te voorkomen.
- **Backend API**: FastAPI-endpoints voor RAG, auth en document-upload.

## Technische uitdagingen en oplossingsrichtingen

- **Chunking-strategie**: Getest fixed-size (512 chars, 50 overlap); semantische chunking onderzocht maar vereist extra research voor productie (zie afwijkingen).
- **Multilingualiteit**: Kleine lokale modellen (7B–13B) tonen zwakkere multi-lingual understanding dan cloud-modellen; beperking geaccepteerd voor MVP (zie afwijkingen).
- **Hybrid retrieval (BM25 + vector)**: Literatuur bestudeerd; implementatie uitgesteld wegens prioritering core RAG (zie afwijkingen).

## Conclusies en afwijkingen

- Auditlog-, encryptie- en toegangscontrole-architectuur ontworpen en geïmplementeerd.
- **Afwijkingen**:
  1. **Chunking/hybrid retrieval**: Conclusie dat meer onderzoek nodig is; huidige fixed-size strategie voldoet voor pilot.
  2. **Kleine modellen**: Beperkte multi-lingualiteit is bekend; cloud-fallback (met screening) blijft onderzoeksonderwerp.
  3. **Solo-preneur**: Tempo van state-of-the-art (ragas, knowledge graphs) moeilijk bij te houden; gefocust op stabiele basis.
