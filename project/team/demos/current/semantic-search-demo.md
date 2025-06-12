# Semantic Search Demo - Sprint Review

## Demo Information

- **Sprint**: Sprint 1
- **Date**: TBD
- **Duration**: 15 minutes
- **Audience**: Stakeholders, Product Management, Development Team

## Demo Goal

Our goal is to make finding information in documents easier and faster. Users can search with normal words and phrases, and the
system will find the right documents and sections - even if they use different words to describe the same thing.

### How we do this:

- Users can upload multiple documents (at once)
- The system chunks the documents into smaller sections
- The system attaches a meaning to the sections by creating 'embeddings', and stores them in a database
- We can then search the system for keywords
- The system finds relevant sections by matching the keywords to embeddings in the database, not just exact word matches
- The system returns a sorted list of document sections that match the keywords the best
- This is the first step towards a system that can answer questions about the documents

## Story Coverage

List of stories being demonstrated:

- [ ] **[STORY-002: Document Processing Pipeline](../../../team/stories/STORY-002.md)**: Ingest PDF, DOCX, and TXT files and generate vector embeddings
- [ ] **[STORY-003: Basic Q&A Interface](../../../team/stories/STORY-003.md)**: Ask questions about uploaded documents
- [ ] **[STORY-004: Containerized Deployment](../../../team/stories/STORY-004.md)**: Containerized services for consistent deployment

## Feature Alignment

Related features from Program Board:

- **[FEAT-001: Technical Foundation & MVP](../../../program/features/FEAT-001.md)**: Core RAG capabilities for document processing and question-answering
- **[FEAT-002: Enterprise User Interface](../../../program/features/FEAT-002.md)**: Modern web interface for document upload and interactive Q&A

## Demo Overview

Demonstration of containerized semantic search application for uploaded documents, showcasing our initial implementation of the on-premises RAG solution.

## Technical Scope

1. Document Processing Pipeline

   - Upload interface
   - Multiple format support
   - Chunking strategy
   - Embedding generation

2. Semantic Search Engine

   - Natural language processing
   - Vector similarity search
   - Result ranking
   - Context preservation

3. Containerized Environment
   - Docker deployment
   - Resource management
   - Configuration system

## Demo Flow

1. **Setup & Configuration** (2 min)

   - *Introduction*: quick recap of our containerized semantic search stack and what the audience will see
   - *Container startup*: start the docker compose stack from the desktop terminal – see [docs/TEST_DOCKER.md](../../../docs/TEST_DOCKER.md) for build details
   - *Configuration walkthrough*: highlight the UI settings, especially the embedding mode selector (**Fast** vs **Precise**) – model options are documented in [docs/EMBEDDING_MODEL_SETUP.md](../../../docs/EMBEDDING_MODEL_SETUP.md)
   - *Resource monitoring*: show a brief `docker stats` output to confirm CPU and memory usage

2. **Document Management** (3 min)

   - Document upload workflow – open a file browser and drag four curated files into the upload area
   - Processing pipeline visualization – show a simple Mermaid diagram while the documents process
   - Chunking strategy explanation – reference [docs/technical/CHUNKING.md](../../../docs/technical/CHUNKING.md)
   - Embedding generation display – watch the progress indicator as vectors are created

3. **Search Demonstration** (5 min)

   - Keyword search examples – simple term search to show baseline behavior
   - Semantic query capabilities – ask a natural language question and highlight matched snippets
   - Result ranking demonstration – explain why the top result is most relevant
   - Context preservation showcase – open the document section to show surrounding text

4. **Technical Deep-Dive** (5 min)
   - Architecture overview – diagram of backend, vector store, and UI (see [docs/DOCKER_TECHNICAL.md](../../../docs/DOCKER_TECHNICAL.md))
   - Security implementation – login screen and placeholder auth, roadmap for improved controls
   - Performance metrics – share baseline response times from container logs
   - Scaling capabilities – discuss testing with 100+ documents and multiple concurrent users

## Success Criteria

Maps to story acceptance criteria:

- [ ] Document upload successfully processes multiple formats
- [ ] Search results show high relevance to queries
- [ ] System performance meets response time targets
- [ ] Container deployment works consistently
- [ ] Security measures are properly implemented

## Known Limitations

- Document size constraints
- Supported file formats
- Processing time for large documents
- Resource requirements

## Questions & Answers

Prepare for common questions:

- How does the system handle large documents?
- What security measures are in place?
- How can the system be scaled?
- What's the deployment process?

## Demo Resources

- Sample documents (various formats)
- Prepared search queries
- Performance dashboard
- Container monitoring tools

## Notes

- Focus on real-world use cases
- Emphasize security features
- Show performance metrics
- Highlight deployment simplicity

## Next Steps

- [ ] Performance optimization (STORY-004)
- [ ] Additional file format support (STORY-005)
- [ ] Enhanced security features (STORY-006)
- [ ] Improved result visualization (STORY-007)

## Demo Best Practices

- Use the [sprint-demo template](../templates/sprint-demo.md) for consistent structure
- Update this document throughout the sprint and finalize it one day before presenting
- Keep language concise and link to related stories, features, and technical docs
- Run `pre-commit run --files <file>` before committing changes
- Manage dependencies with `uv add` as described in [AGENTS.md](../../../AGENTS.md)
