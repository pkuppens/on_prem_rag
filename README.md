# On-Premises Retrieval-Augmented Generation (RAG) Solution

_Talk with your documents and data using LLM's without the Cloud privacy and confidentiality concerns_

## Introduction

### Objective

Build an on-premises Retrieval-Augmented Generation (RAG) system that organizations can run entirely offline.
The system will ingest large collections of documents (PDFs, Word files), enable interactive Q&A via a web GUI with role-based access control (RBAC).
All components will operate locally (using local vector stores and on-prem LLM inference) to ensure data privacy and compliance.

Optionally, it will also support natural language queries over databases and be extensible to multiple Large Language Models (LLMs) of varying sizes.

### Key Features:
* Document Knowledge Base: Ingest and index PDFs/Word docs into a vector database for retrieval-augmented Q&A.
* Interactive Q&A Interface: A user-friendly GUI (web interface) for querying documents, with authentication and RBAC to restrict access.
* Offline Deployment: All operations run on-premises with no external calls. Models, embeddings, and data stores run locally (with GPU acceleration if available), and access to the system is via secure LAN/VPN only.
* Security: Robust RBAC implementation, admin panel for user and document management, app-level authorization checks, and network-level isolation to protect sensitive data.

### Optional Enhancements
* Database Q&A: Ability to answer natural language questions using company databases (initially PostgreSQL and MS SQL Server) by converting questions into SQL queries and returning answers (data security and integrity are serious concerns).
* Multi-LLM Support: Pluggable support for different LLMs (e.g. Mistral 7B, LLaMA 3, Phi-3) that are commercially usable, ensuring flexibility in speed vs. accuracy.
* Mix with cloud LLM's: only curated questions that do not leak PII and confidential information could be asked to Cloud models.

## Project Plan:

The following sections break down the project plan by business goals, with tasks, subtasks, and implementation steps for each.
We also outline the documentation structure, tool choices (with rationale for each), deployment setup, and security considerations.
This plan is written in clear, concise language for both technical and business readers.

## Goal 1: Full Project Plan with Task Breakdown

### 1.1 Initialize Project Environment
- **Task:** Set up Python environment
  - Subtask: Install tooling
    - Run:
        pip install uv ruff pre-commit
  - Subtask: Create `pyproject.toml` with base dependencies
    - Example:
        [tool.poetry.dependencies]
        python = "^3.10"
        langchain = "*"
        llama-index = "*"
        chromadb = "*"
        fastapi = "*"
        uvicorn = "*"
        streamlit = "*"
  - Subtask: Add pre-commit config
    - `.pre-commit-config.yaml`:
        repos:
          - repo: https://github.com/charliermarsh/ruff-pre-commit
            rev: v0.4.1
            hooks:
              - id: ruff
    - Run:
        pre-commit install

### 1.2 Containerized Environment
- **Task:** Set up Docker environment
  - Files:
    - `Dockerfile`
    - `docker-compose.yml`
  - Base `docker-compose.yml`:
        version: '3.8'
        services:
          app:
            build: .
            volumes:
              - .:/app
            ports:
              - "8000:8000"
            depends_on:
              - vectordb
          vectordb:
            image: chromadb/chroma
            ports:
              - "8001:8000"
          ollama:
            image: ollama/ollama
            volumes:
              - ollama:/root/.ollama
            ports:
              - "11434:11434"
        volumes:
          ollama:

### 1.3 RAG Pipeline MVP
- **Task:** Create file ingestion + vectorization
  - Use LangChain `DirectoryLoader`, `PDFLoader`, `DocxLoader`
  - Convert to embeddings using `HuggingFaceEmbeddings`
  - Store in ChromaDB
  - Example:
        from langchain.document_loaders import DirectoryLoader, PDFLoader, DocxLoader
        from langchain.vectorstores import Chroma
        from langchain.embeddings import HuggingFaceEmbeddings

        loader = DirectoryLoader("docs", loader_cls=PDFLoader)
        docs = loader.load()
        embeddings = HuggingFaceEmbeddings()
        db = Chroma.from_documents(docs, embeddings)

- **Task:** Implement Q&A chain
  - Use `RetrievalQA.from_chain_type`
  - Connect to Ollama with `LLM(model="llama3")`

---

## Goal 2: Documentation in B1 English

### 2.1 Create Documentation Tree
- `README.md`: Summary, use cases, structure
- `docs/`
  - `setup.md`: Environment and Docker setup
  - `rag-pipeline.md`: RAG flow (load → embed → store → retrieve)
  - `database-chat.md`: How natural language to SQL works
  - `security.md`: Role-based access, authentication methods

### 2.2 Write in B1 Style
- Use short, clear sentences
- Favor active voice
- Use diagrams like:
    mermaid
      graph TD
        A[User] --> B[Frontend GUI]
        B --> C[FastAPI Backend]
        C --> D[Vector DB]
        C --> E[LLM via Ollama]
        C --> F[SQL DB]

---

## Goal 3: Tool Choices & Rejections

### 3.1 Accepted Tools
| Tool         | Reason                                     |
|--------------|---------------------------------------------|
| LangChain    | Modular, supports RAG, DB, and agents       |
| Ollama       | Local LLMs, efficient GGUF format support   |
| ChromaDB     | Lightweight vector store for local use      |
| Streamlit    | Fast and simple UI prototyping              |

### 3.2 Rejected Tools
| Tool        | Reason                                         |
|-------------|------------------------------------------------|
| LM Studio   | No commercial use license                     |
| GPT4All GUI | GUI too limited and not modular enough        |
| Pinecone    | Cloud-based; not suitable for offline use     |

---

## Goal 4: Python, Docker, and LLM Models

### 4.1 Python + Tooling
- `uv` for dependency management
- `ruff` for linting

### 4.2 Docker Services
- `app-api`: FastAPI service to handle queries
- `frontend`: Streamlit or React-based GUI
- `vectordb`: Chroma container
- `ollama`: Local model inference

### 4.3 Model Selection
| Model         | License     | Reason                        |
|---------------|-------------|-------------------------------|
| Mistral       | Apache 2.0  | Small, performant             |
| LLaMA 3 8B    | Meta        | Commercial use allowed        |
| Gemma         | Non-commercial | Not allowed for production |
| GPT-J         | Obsolete    | Lower quality                 |

---

## Goal 5: GUI with Role-Based Access

### 5.1 GUI Options
- Streamlit: ideal for prototype/demo
- React + FastAPI: preferred for production

### 5.2 User Roles
- Admin: can add users, manage roles
- Editor: upload and label documents
- Viewer: query documents and DB

- Implement with `fastapi_users` or custom RBAC middleware

---

## Goal 6: Security & Access Control

### 6.1 Network Setup
- Access only via VPN or secured LAN
- Run containers on isolated subnet

### 6.2 Application Security
- JWT-based login for API and GUI
- Role-based permission system
- Audit logs for document and DB queries

### 6.3 Optional Auth Providers
- Keycloak for SSO + LDAP
- Otherwise basic login + role config via admin panel

---

## ✅ Next Steps

1. `uv pip install langchain chromadb fastapi streamlit llama-index`
2. Set up `docker-compose.yml` for `ollama`, `vectordb`, and `api`
3. Test LLM queries via FastAPI → Ollama
4. Build file loader and embedder module
5. Prototype GUI in Streamlit
6. Add SQL wrapper with parameterized query validator
7. Harden with RBAC and secure access
```

---

This plan has been reviewed and rewritten after using ChatGPT in Research Mode: https://chatgpt.com/s/dr_6839fabe3c708191a3caf63b6ba6442d
