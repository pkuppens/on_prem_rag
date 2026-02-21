# Healthcare Clinical Guidelines — Source Curation

Created: 2026-02-21  
Updated: 2026-02-21

Curated sources for the healthcare clinical guideline assistant demo (#82). Documents are **retrieved by reference** — URLs are documented here; PDFs are downloaded to a local `.gitignored` directory.

## NHG-Standaarden (Dutch, drug prescriptions)

**Source:** [richtlijnen.nhg.org](https://richtlijnen.nhg.org)  
**Access:** Public PDFs, no subscription required.  
**Rationale:** Drug-prescription guidelines; supports prescription recommendation / ATC violation projects; multi-lingual (Dutch).

### Topic clusters (multiple documents per topic)

| Cluster       | Documents              | Drug focus                          |
|---------------|------------------------|-------------------------------------|
| Uro/gyn       | Urineweginfecties, Fluor vaginalis | Nitrofurantoïne, trimethoprim, antifungals |
| Mental health | Depressie, Angst, Slaapproblemen   | Antidepressants, anxiolytics        |
| GI            | Maagklachten, Acute diarree, Obstipatie | PPI, loperamide, laxatives       |
| Respiratory   | Acuut hoesten, Acute rhinosinusitis, Acute keelpijn | Antibiotics (narrow spectrum) |

### PDF URLs (verified)

| Title              | URL | Est. pages |
|--------------------|-----|------------|
| Urineweginfecties  | https://richtlijnen.nhg.org/files/pdf/9428_Urineweginfecties_december-2025.pdf | ~25 |
| Fluor vaginalis    | https://richtlijnen.nhg.org/files/pdf/3202_Fluor%20vaginalis_januari-2024.pdf | ~15 |
| Depressie          | https://richtlijnen.nhg.org/files/pdf/6020_Depressie_januari-2024.pdf | ~25 |
| Angst              | https://richtlijnen.nhg.org/files/pdf/3509_Angst_september-2025.pdf | ~25 |
| Slaapproblemen     | https://richtlijnen.nhg.org/files/pdf/6215_Slaapproblemen_januari-2026.pdf | ~20 |
| Maagklachten       | https://richtlijnen.nhg.org/files/pdf/10271_Maagklachten_april-2025.pdf | ~25 |
| Acute diarree      | https://richtlijnen.nhg.org/files/pdf/4201_Acute%20diarree_mei-2024.pdf | ~15 |
| Obstipatie         | https://richtlijnen.nhg.org/files/pdf/6101_Obstipatie%20_september-2010.pdf | ~12 |
| Acuut hoesten      | https://richtlijnen.nhg.org/files/pdf/7880_Acuut%20hoesten_juli-2025.pdf | ~25 |
| Acute rhinosinusitis | https://richtlijnen.nhg.org/files/pdf/4254_Acute%20rhinosinusitis_mei-2024.pdf | ~15 |
| Acute keelpijn     | https://richtlijnen.nhg.org/files/pdf/5806_Acute%20keelpijn_augustus-2015.pdf | ~12 |

**Total:** 10–11 documents, ~100–200 pages.

## Ingestion flow

1. **Fetch PDFs** (run once, or to refresh):
   ```bash
   uv run python -m scripts.fetch_healthcare_guidelines
   ```
   Downloads to `tmp/healthcare_guidelines/` (gitignored). Reports location and count.

2. **Ingest into RAG** (uses local ChromaDB + embedding; no API server):
   ```bash
   uv run python -m scripts.upload_documents --direct --filenameonly tmp/healthcare_guidelines
   ```
   Windows: use directory path (glob does not expand in PowerShell).

## English sources (optional)

- **NICE:** [nice.org.uk/guidance](https://www.nice.org.uk/guidance) — e.g. NG222 Depression, NG246 Obesity
- **WHO:** [who.int/publications](https://www.who.int/publications) — e.g. Influenza, Malaria

## Related

- [HEALTHCARE_DEMO.md](../HEALTHCARE_DEMO.md) — On-premises rationale, source attribution, limitations

## Future refinements (TODO)

- **MMR ranking:** Favor chunks from different documents for cross-checking reliability.
- **Language filtering:** Filter by language at retrieval; English for Dutch readers OK.
