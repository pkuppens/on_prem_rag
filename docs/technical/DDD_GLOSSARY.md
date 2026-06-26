# Ubiquitous Language Glossary

> **Date:** 2026-06-26  
> **Purpose:** Establish a shared, consistent vocabulary across the project  
> **Scope:** All bounded contexts in `src/backend/`  
> **Target BCs:** As defined in `DDD_TARGET_ARCHITECTURE.md`

---

## A

### AccessDecision
- **Definition:** Result of an access control evaluation — whether permission is granted or denied, with reason.
- **Bounded Context:** Access Control
- **Synonyms:** Permission check result, authorization verdict
- **See also:** DataScope, Permission

### ActorReference
- **Definition:** Privacy-safe reference to a user/actor using a hashed user ID (not the actual ID).
- **Bounded Context:** Audit Trail
- **Synonyms:** Hashed actor identity, pseudonymous actor

### AgentInstance
- **Definition:** A configured CrewAI agent within the medical analysis pipeline, with a specific role (preprocessor, clinical extractor, etc.).
- **Bounded Context:** Medical Agents
- **Synonyms:** CrewAI agent, analysis agent

### AgentMemory
- **Definition:** Aggregate root for three-tier memory system: short-term (session), long-term (vector), structured (entity).
- **Bounded Context:** Memory
- **Synonyms:** Memory system, memory management

### AnalysisJob
- **Definition:** Aggregate root for medical document analysis — tracks the lifecycle of one analysis run through all CrewAI agents.
- **Bounded Context:** Medical Agents
- **Synonyms:** Analysis run, document analysis

### AnalysisResult
- **Definition:** Output of a medical document analysis, including preprocessing, language assessment, clinical extraction, summarization, and quality scores.
- **Bounded Context:** Medical Agents
- **Synonyms:** Analysis output, medical report

### AnonymizedText
- **Definition:** Text with PII replaced by placeholder tokens, plus audit metadata. This is what gets sent to cloud LLMs.
- **Bounded Context:** Privacy Guard
- **Synonyms:** Sanitized text, PII-free text, anonymized query
- **WBSO:** Primary evidence that no PII reaches the cloud

### Answer
- **Definition:** LLM-generated response to a user query, including text content and optional citation metadata.
- **Bounded Context:** Query Service
- **Synonyms:** Response, LLM output, generated text
- **See also:** Citation, Confidence, Query

### AuditEvent
- **Definition:** Published language event schema emitted by any BC to log an auditable action.
- **Bounded Context:** Audit Trail
- **Synonyms:** Audit record, log entry

### AuditMetadata
- **Definition:** Non-sensitive operational metadata for audit entries — latency, PII categories, confidence scores.
- **Bounded Context:** Audit Trail
- **Synonyms:** Audit context, operational metadata

---

## C

### Chunk
- **Definition:** A text segment resulting from splitting a document page into smaller pieces suitable for embedding and retrieval.
- **Bounded Context:** Ingestion
- **Synonyms:** Text segment, fragment, node (avoid — LlamaIndex term)
- **See also:** ChunkMetadata, ChunkingStrategy

### ChunkMetadata
- **Definition:** Metadata attached to a chunk: chunk_index, document_id, page_number, page_label, content_hash, source path.
- **Bounded Context:** Ingestion
- **Synonyms:** Chunk attributes, chunk header

### ChunkingResult
- **Definition:** Result value object from a chunking operation — contains the list of chunks plus statistics (counts, filtering stats, file hash).
- **Bounded Context:** Ingestion
- **Synonyms:** Chunking output, processed chunks

### ChunkingStrategy
- **Definition:** Strategy pattern for chunking: character-based, semantic (sentence boundary), recursive (paragraph→line→word).
- **Bounded Context:** Ingestion
- **Synonyms:** Split strategy, text division method

### Citation
- **Definition:** Reference to a source document chunk included in an answer, with document_name, page_number, similarity_score, and text preview.
- **Bounded Context:** Query Service
- **Synonyms:** Source reference, document citation
- **See also:** Answer

### CloudEligibility
- **Definition:** Result of determining whether a query can be sent to a cloud LLM — approved, denied (PII remains), or denied (policy).
- **Bounded Context:** Privacy Guard
- **Synonyms:** Cloud safety clearance, routing decision
- **WBSO:** Evidence that cloud routing is safe

### CloudQueryAuditEntry
- **Definition:** Audit record of a query sent to a cloud LLM — stores the anonymized query text for auditor inspection.
- **Bounded Context:** Audit Trail
- **Synonyms:** Cloud LLM audit record, WBSO evidence entry
- **WBSO:** Primary evidence artifact for Knelpunt 2 (AVG-veilig)

### CloudSafety
- **Definition:** Classification of data types for cloud transmission safety: NEVER (must never go to cloud), AFTER_TRANSFORM (safe after anonymization), SAFE (can go as-is).
- **Bounded Context:** Privacy Guard
- **Synonyms:** Cloud safety level, cloud eligibility class

### Completion
- **Definition:** The result of an LLM generation call — the generated text content.
- **Bounded Context:** LLM Gateway
- **Synonyms:** LLM response, generated text, model output
- **See also:** Prompt

### Confidence
- **Definition:** Measure of answer reliability based on average similarity score of retrieved chunks: high (>0.8), medium (>0.6), low (≤0.6).
- **Bounded Context:** Query Service
- **Synonyms:** Answer confidence, reliability score

### Conversation
- **Definition:** Aggregate root for a multi-turn Q&A session between a user and the system.
- **Bounded Context:** Query Service
- **Synonyms:** Chat session, dialogue, Q&A thread

### ConversationContext
- **Definition:** Entity tracking participating agents, summary, and status of a conversation session.
- **Bounded Context:** Memory
- **Synonyms:** Session context, chat context

---

## D

### DataScope
- **Definition:** Value object defining the boundary of accessible data for a query — user_id, role, and optional patient_filter for data isolation.
- **Bounded Context:** Access Control
- **Synonyms:** Access scope, data boundary
- **WBSO:** Core concept for Knelpunt 1 (patient data isolation)

### Document (Domain)
- **Definition:** An uploaded file with metadata (id, filename, type, size, upload_time) and processing status. Distinguished from LlamaIndex Document.
- **Bounded Context:** Ingestion, Query Service
- **Synonyms:** Source file, uploaded document
- **Note:** Avoid using this term interchangeably with LlamaIndex's `Document` type.

### DocumentLoader
- **Definition:** Application service that validates files and extracts text using format-specific processors (PDF, DOCX, MD, TXT, HTML).
- **Bounded Context:** Ingestion
- **Synonyms:** File reader, document parser, text extractor

### DocumentMetadata
- **Definition:** Metadata for a processed document: file_path, file_hash, file_type, file_size, num_pages (for PDFs), section_headings.
- **Bounded Context:** Ingestion
- **Synonyms:** File metadata, document info

---

## E

### Embedding
- **Definition:** Vector representation of a text chunk generated by an embedding model (e.g., HuggingFace sentence transformers).
- **Bounded Context:** Ingestion, Retrieval, LLM Gateway
- **Synonyms:** Vector embedding, text embedding, feature vector

### EmbeddingProvider
- **Definition:** Port interface for generating text embeddings, implemented by HuggingFace or other models.
- **Bounded Context:** LLM Gateway
- **Synonyms:** Embedding model, text encoder

### EvaluationReport
- **Definition:** Output of a RAG pipeline evaluation run — metrics on retrieval quality, answer quality, latency.
- **Bounded Context:** Evaluation
- **Synonyms:** Benchmark report, test results

---

## F

### FileContentHash
- **Definition:** SHA-256 hash of raw file bytes used for exact duplicate detection before document loading.
- **Bounded Context:** Ingestion
- **Synonyms:** File hash, content fingerprint, dedup key

### FileSource
- **Definition:** Entity representing a single file queued for or being processed in an ingestion job.
- **Bounded Context:** Ingestion
- **Synonyms:** Source file, input file

---

## G

### GuardrailEventEntry
- **Definition:** Audit record of a guardrail activation — what guardrail triggered, what action was taken, and relevant metrics.
- **Bounded Context:** Audit Trail
- **Synonyms:** Guardrail audit record, safety event

### GuardrailsResult
- **Definition:** Combined result of all guardrails checks — whether input/output is allowed, with detailed validation results.
- **Bounded Context:** Guardrails
- **Synonyms:** Safety check result, validation outcome

---

## I

### Index
- **Definition:** Aggregate root representing a searchable collection of embedded chunks, supporting dense, sparse, and hybrid search.
- **Bounded Context:** Retrieval
- **Synonyms:** Search index, vector index, collection

### IngestionDocument
- **Definition:** Domain document type used within the Ingestion BC — the project's own type rather than LlamaIndex's Document.
- **Bounded Context:** Ingestion
- **Synonyms:** Internal document, ingested document
- **Note:** Created to decouple from LlamaIndex's Document type

### IngestionJob
- **Definition:** Aggregate root for tracking a batch of document processing — from upload through loading, chunking, embedding, and storage.
- **Bounded Context:** Ingestion
- **Synonyms:** Processing job, ingest task, upload batch

### IngestionResult
- **Definition:** Value object recording the outcome of a document ingestion — chunks processed, records stored, and any errors.
- **Bounded Context:** Ingestion
- **Synonyms:** Processing result, ingest stats

---

## L

### LLMConfig
- **Definition:** Resolved LLM configuration from environment variables — backend, model, LiteLLM model string, API base URL.
- **Bounded Context:** LLM Gateway
- **Synonyms:** LLM settings, model configuration

### LLMProvider
- **Definition:** Port interface for LLM text generation — generate, generate_stream, health_check. Implemented by Ollama, LiteLLM, HuggingFace, etc.
- **Bounded Context:** LLM Gateway
- **Synonyms:** LLM backend, text generation service, model provider

---

## M

### MedicalCrewOrchestrator
- **Definition:** Application service that coordinates CrewAI agents in sequential or hierarchical workflows for medical text analysis.
- **Bounded Context:** Medical Agents
- **Synonyms:** Agent orchestrator, crew coordinator

### MemoryDocument
- **Definition:** Value object representing a document stored in long-term vector memory — content, agent_role, session_id, memory_type, importance.
- **Bounded Context:** Memory
- **Synonyms:** Memory entry, stored memory

### MemoryEntry
- **Definition:** Entity in the structured memory store, containing agent_role, session_id, content, memory_type, timestamps.
- **Bounded Context:** Memory
- **Synonyms:** Memory record, agent memory

### MemoryType
- **Definition:** Classification of memory content: "fact", "observation", "result", "context", "entity_source".
- **Bounded Context:** Memory
- **Synonyms:** Memory category, memory classification

### ModelIdentifier
- **Definition:** Value object identifying an LLM or embedding model — provider prefix + model name (e.g., "ollama/mistral", "openai/gpt-4.1-mini").
- **Bounded Context:** LLM Gateway
- **Synonyms:** Model ID, model spec, model reference

---

## P

### Permission
- **Definition:** Enum of atomic permissions (READ_OWN_RECORDS, QUERY_CLOUD_LLM, MANAGE_USERS, etc.) that can be assigned to roles.
- **Bounded Context:** Access Control
- **Synonyms:** Right, privilege, capability

### PIICategory
- **Definition:** Classification of PII types: direct identifiers (NAME, BSN, DOB_EXACT) and quasi-identifiers (AGE_EXACT, POSTAL_CODE).
- **Bounded Context:** Privacy Guard
- **Synonyms:** PII type, data category
- **WBSO:** Taxonomy used for Knelpunt 2

### PIIDetection
- **Definition:** Value object capturing a detected PII instance — category, original_value, start/end position, confidence.
- **Bounded Context:** Privacy Guard
- **Synonyms:** PII match, detection result

### PIIType
- **Definition:** Definition of a PII type with detection pattern (regex), cloud safety level, and replacement token.
- **Bounded Context:** Privacy Guard
- **Synonyms:** PII definition, PII pattern

### ProgressEvent
- **Definition:** Domain event published during document processing to report status — file_id, progress percentage, message.
- **Bounded Context:** Ingestion
- **Synonyms:** Progress update, processing status
- **See also:** IngestionJob

### Prompt
- **Definition:** Value object representing a prompt sent to an LLM, composed of system instructions, conversation context, and user question.
- **Bounded Context:** LLM Gateway, Query Service
- **Synonyms:** LLM prompt, query prompt, generation prompt

### PromptBuilder
- **Definition:** Domain service that constructs LLM prompts from retrieved context, conversation history, and user query.
- **Bounded Context:** Query Service
- **Synonyms:** Prompt constructor, prompt assembler

### ProviderType
- **Definition:** Enum of supported LLM backends: ollama, openai, anthropic, azure, huggingface, gemini.
- **Bounded Context:** LLM Gateway
- **Synonyms:** Backend type, model provider

---

## Q

### Query (Domain)
- **Definition:** Value object representing a user's question with its intent classification, sanitized text, and retrieval parameters.
- **Bounded Context:** Query Service
- **Synonyms:** User question, search query, chat message
- **See also:** Answer, QueryIntent

### QueryIntent
- **Definition:** Classification of a query's intent: READ_ONLY or MUTATING, with a risk level (SAFE → BLOCKED).
- **Bounded Context:** Query Service, Guardrails
- **Synonyms:** Intent classification, query purpose

### QueryOrchestrator
- **Definition:** Application service that coordinates the full RAG workflow: access check → PII sanitization → retrieval → LLM generation → audit logging.
- **Bounded Context:** Query Service
- **Synonyms:** RAG coordinator, Q&A pipeline, ask service

### QueryVector
- **Definition:** The embedding vector of a user query, used for similarity search against the index.
- **Bounded Context:** Retrieval
- **Synonyms:** Query embedding, search vector

---

## R

### RAGParams
- **Definition:** Complete parameter set for RAG pipeline — chunking, embedding, LLM, and retrieval parameters. Predefined sets: fast, precise, context_rich, balanced, test.
- **Bounded Context:** Query Service, Ingestion
- **Synonyms:** RAG configuration, pipeline params, parameter set

### RetrievalStrategy
- **Definition:** Strategy for document retrieval: dense (embedding similarity), sparse (BM25 keyword), hybrid (RRF fusion), with optional re-ranking and MMR.
- **Bounded Context:** Retrieval
- **Synonyms:** Search strategy, retrieval method

### Role
- **Definition:** Enum of system roles with distinct permission sets: GP, PATIENT, ADMIN, AUDITOR.
- **Bounded Context:** Access Control
- **Synonyms:** User role, actor type
- **WBSO:** Core concept for Knelpunt 1 (bevoegd datatoegang)

### RolePermissions
- **Definition:** Immutable frozen set of permissions assigned to a role — the "constitution" of the access control system.
- **Bounded Context:** Access Control
- **Synonyms:** Permission set, role rights

---

## S

### SearchResult
- **Definition:** Single chunk match from a retrieval operation — chunk text, similarity_score, document_id, document_name, page_number, record_id.
- **Bounded Context:** Retrieval
- **Synonyms:** Retrieval result, matched chunk, search hit

### Session (Auth)
- **Definition:** Authenticated user session with token, last_active timestamp, and user reference.
- **Bounded Context:** Auth
- **Synonyms:** Auth session, login session, user session

### Session (Memory)
- **Definition:** A conversation session identifier used as the scope for short-term memory storage and access control.
- **Bounded Context:** Memory
- **Synonyms:** Chat session, conversation session

### SimilarityScore
- **Definition:** Normalized relevance score for a search result (0.0–1.0) based on cosine similarity or RRF score.
- **Bounded Context:** Retrieval
- **Synonyms:** Relevance score, match confidence

---

## T

### TaskDefinition
- **Definition:** Value object defining a task for a CrewAI agent — description, expected_output, agent_name, dependencies.
- **Bounded Context:** Medical Agents
- **Synonyms:** Agent task, workflow step

### TokenCount
- **Definition:** Value object representing token usage (input, output, total) for an LLM call.
- **Bounded Context:** LLM Gateway
- **Synonyms:** Token usage, token stats, model cost

### Transformation
- **Definition:** Record of a PII transformation applied to text — category, action (removed/replaced/generalized), token_used.
- **Bounded Context:** Privacy Guard
- **Synonyms:** PII transformation, anonymization action

---

## U

### User
- **Definition:** Authenticated actor in the system — has a username, email, password hash (or OAuth2 provider), roles, and sessions.
- **Bounded Context:** Auth
- **Synonyms:** Account, user identity, login account

---

## V

### VectorStoreManager
- **Definition:** Manager for vector database operations — CRUD on embeddings, query, dedup check. Implementations: ChromaDB.
- **Bounded Context:** Ingestion (write), Retrieval (read)
- **Synonyms:** Vector DB manager, embedding store

### ValidationResult
- **Definition:** Result of a single guardrail validation check — check_name, status (PASSED/BLOCKED/WARNING/ERROR/SKIPPED), message, details.
- **Bounded Context:** Guardrails
- **Synonyms:** Check result, validation verdict

---

## W

### WBSOReportGenerator
- **Definition:** Application service that generates WBSO R&D tax credit evidence reports from audit trail data.
- **Bounded Context:** Audit Trail
- **Synonyms:** WBSO evidence report, R&D documentation generator
- **WBSO:** This is the deliverable for WBSO-AICM-2025-01 claims

---

## Cross-Reference: WBSO Knelpunten to Ubiquitous Language

| WBSO Knelpunt | Key Ubiquitous Language | Bounded Context |
|---------------|------------------------|-----------------|
| **Knelpunt 1: Bevoegd datatoegang** | Role, Permission, DataScope, AccessDecision, RolePermissions | Access Control |
| **Knelpunt 2: AVG-veilig (cloud PII)** | PIICategory, PIIType, PIIDetection, CloudSafety, AnonymizedText, CloudEligibility, CloudQueryAuditEntry | Privacy Guard, Audit Trail |
| **Knelpunt 3: Privacyvriendelijke auditlogs** | ActorReference, ResourceReference, AuditMetadata, GuardrailEventEntry, GuardrailEffectivenessReport | Audit Trail |
| **Knelpunt 4: Data-integriteit** | QueryIntent (MUTATING detection), GuardrailEventEntry | Guardrails, Audit Trail |

---

## Deprecated / Avoid Terms

| Term | Why Avoid | Replacement |
|------|-----------|-------------|
| "Node" (LlamaIndex) | Framework-specific, not domain | Chunk |
| "Document" (bare, unqualified) | Ambiguous between domain and LlamaIndex types | IngestionDocument or SourceFile |
| "query" (as generic DB query) | Overloaded with user query | Use specific: "search query", "user question", "vector query" |
| "provider" (bare) | Ambiguous between LLM and file format providers | LLMProvider or FileProcessor |
| "token" (bare) | Three different meanings in the codebase | PII token / JWT token / LLM token |
| "model" (bare without context) | Means embedding model, LLM model, or data model | Specify: "embedding model", "LLM model", "data model" |

---

## How to Evolve This Glossary

1. **When adding a new concept** — Add it to this glossary with its BC, definition, and synonyms
2. **When renaming a concept** — Update all code, then update this glossary. Flag the old term as deprecated for one sprint.
3. **When two BCs use the same term differently** — This is a red flag. Either rename one or create an anti-corruption layer.
4. **Before each extraction phase** — Review this glossary to ensure the BC's language is consistent
