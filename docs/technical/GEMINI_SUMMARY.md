# Gemini Project Summary: On-Premises RAG Solution

## 1. Project Description

This project aims to deliver an on-premises Retrieval-Augmented Generation (RAG) system that enables organizations to leverage Large Language Models (LLMs) for document analysis and database querying while maintaining complete data sovereignty and regulatory compliance. The solution is designed to be fully operational in an offline environment, eliminating the need for cloud services and addressing the privacy and security concerns of enterprises.

The core of the project is a robust RAG pipeline that can ingest documents, process them into a searchable format, and use an LLM to answer questions based on the document content. The system will also feature a user-friendly web interface for document management and interaction with the Q&A and NL2SQL functionalities.

## 2. Implemented Requirements

Based on the project documentation, the following requirements have been implemented or are in the process of being implemented as part of the MVP:

*   **Technical Foundation (FEAT-001):**
    *   A robust development environment has been set up, with `uv` for package management and `pre-commit` for code quality.
    *   The core RAG pipeline for document ingestion and Q&A is in progress.
    *   Docker-based deployment has been set up with `docker-compose.yml`.
*   **Enterprise User Interface (FEAT-002):**
    *   A basic web interface for proof-of-concept is available.
*   **Flexible LLM Integration (FEAT-003):**
    *   The system is designed with a modular LLM provider system in mind, although the full implementation is pending.
*   **Production Deployment (FEAT-005):**
    *   The project is containerized using Docker for consistent environments.

## 3. Remaining Requirements

The following requirements are planned for future phases of the project:

*   **Enterprise User Interface (FEAT-002):**
    *   Full-featured web UI with advanced upload and chat features.
    *   Role-based access control (RBAC) and multi-user support.
*   **Flexible LLM Integration (FEAT-003):**
    *   Integration with multiple local LLM backends.
*   **Database Query Capabilities (FEAT-004):**
    *   Natural Language to SQL (NL2SQL) functionality.
*   **Production Deployment (FEAT-005):**
    *   Production-ready deployment with monitoring and logging.
*   **Security Framework (FEAT-006):**
    *   Network isolation.
    *   Audit logging.
    *   Encrypted traffic.
    *   Third-party security audit.

## 4. Proposed DDD-Based Architecture

To better align the project with its business objectives and to create a more maintainable and scalable system, a Domain-Driven Design (DDD) approach is proposed. This architecture is organized around Bounded Contexts, each representing a distinct area of the business domain.

### 4.1. Bounded Contexts

The system can be divided into the following Bounded Contexts:

*   **`Ingestion`:** Responsible for everything related to getting documents into the system.
*   **`Knowledge`:** Responsible for storing, managing, and retrieving information from the documents.
*   **`Interaction`:** Responsible for handling user interactions with the system, including Q&A and NL2SQL.
*   **`Orchestration`:** Responsible for coordinating the workflows between the other Bounded Contexts.
*   **`Security`:** Responsible for user authentication, authorization, and other security-related concerns.

### 4.2. Components and Functionality

Here is a breakdown of the components and subcomponents within each Bounded Context, with the project's requirements and functionality grouped at the applicable level:

---

### Bounded Context: `Ingestion`

**Description:** This context is responsible for handling the ingestion of documents from various sources.

**Components:**

*   **`File Upload Component`**
    *   **Subcomponents:**
        *   `File Uploader UI`: A web component for users to upload files.
        *   `File Storage Service`: Stores the uploaded files in a designated location.
    *   **Functionality:**
        *   Allows users to upload documents through a web interface.
        *   Supports various file formats (e.g., PDF, DOCX, TXT).
        *   Stores uploaded files for processing.
    *   **Requirements:**
        *   `FEAT-002`: Enterprise User Interface

*   **`Document Processor Component`**
    *   **Subcomponents:**
        *   `File Parser`: Extracts text and metadata from different file formats.
        *   `Text Chunker`: Splits the extracted text into smaller, manageable chunks.
        *   `Embedding Generator`: Generates vector embeddings for the text chunks.
    *   **Functionality:**
        *   Parses uploaded documents to extract their content.
        *   Divides the document content into smaller chunks for efficient processing.
        *   Creates vector embeddings for each chunk to be used in similarity searches.
    *   **Requirements:**
        *   `FEAT-001`: Technical Foundation

---

### Bounded Context: `Knowledge`

**Description:** This context is responsible for managing the knowledge base of the system.

**Components:**

*   **`Vector Store Component`**
    *   **Subcomponents:**
        *   `Vector Database`: Stores the vector embeddings of the document chunks.
        *   `Vector Index`: Allows for efficient similarity searches on the vector embeddings.
    *   **Functionality:**
        *   Stores and manages the vector embeddings of the document chunks.
        *   Provides an interface for performing similarity searches.
    *   **Requirements:**
        *   `FEAT-001`: Technical Foundation

*   **`Document Store Component`**
    *   **Subcomponents:**
        *   `Document Database`: Stores the original documents and their metadata.
    *   **Functionality:**
        *   Stores the original documents for reference.
        *   Manages document metadata (e.g., filename, upload date, source).
    *   **Requirements:**
        *   `FEAT-001`: Technical Foundation

---

### Bounded Context: `Interaction`

**Description:** This context is responsible for handling all user interactions with the system.

**Components:**

*   **`Q&A Component`**
    *   **Subcomponents:**
        *   `Query Processor`: Processes user queries and converts them into a format suitable for the LLM.
        *   `LLM Gateway`: A modular interface for interacting with different LLMs.
        *   `Response Generator`: Generates a human-readable response based on the LLM output.
    *   **Functionality:**
        *   Allows users to ask questions in natural language.
        *   Retrieves relevant document chunks from the `Knowledge` context.
        *   Uses an LLM to generate an answer based on the retrieved context.
    *   **Requirements:**
        *   `FEAT-001`: Technical Foundation
        *   `FEAT-003`: Flexible LLM Integration

*   **`NL2SQL Component`**
    *   **Subcomponents:**
        *   `SQL Generator`: Converts natural language queries into SQL queries.
        *   `Database Connector`: Connects to the target database to execute the SQL query.
    *   **Functionality:**
        *   Allows users to query a database using natural language.
        *   Translates the user's query into a SQL query.
        *   Executes the SQL query and returns the result.
    *   **Requirements:**
        *   `FEAT-004`: Database Query Capabilities

---

### Bounded Context: `Orchestration`

**Description:** This context is responsible for orchestrating the workflows between the other contexts.

**Components:**

*   **`RAG Pipeline Orchestrator`**
    *   **Functionality:**
        *   Manages the end-to-end RAG pipeline, from document ingestion to Q&A.
        *   Coordinates the interactions between the `Ingestion`, `Knowledge`, and `Interaction` contexts.
    *   **Requirements:**
        *   `FEAT-001`: Technical Foundation

*   **`NL2SQL Pipeline Orchestrator`**
    *   **Functionality:**
        *   Manages the end-to-end NL2SQL pipeline.
        *   Coordinates the interactions between the `Interaction` and `Knowledge` contexts.
    *   **Requirements:**
        *   `FEAT-004`: Database Query Capabilities

---

### Bounded Context: `Security`

**Description:** This context is responsible for all security-related aspects of the system.

**Components:**

*   **`Authentication Component`**
    *   **Functionality:**
        *   Manages user authentication (e.g., username/password, OAuth2).
    *   **Requirements:**
        *   `FEAT-006`: Security Framework

*   **`Authorization Component`**
    *   **Functionality:**
        *   Manages user roles and permissions (RBAC).
    *   **Requirements:**
        *   `FEAT-002`: Enterprise User Interface
        *   `FEAT-006`: Security Framework

*   **`Auditing Component`**
    *   **Functionality:**
        *   Logs all user activities for security and compliance purposes.
    *   **Requirements:**
        *   `FEAT-006`: Security Framework

## 5. Proposed File System Structure for DDD Refactoring

This section outlines a new file system structure based on the proposed DDD architecture. This structure is designed to be modular, scalable, and to clearly reflect the different domains of the application.

```
.
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── file_parser.py        # Adapters for different file formats
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── models.py             # Pydantic models for documents, etc.
│   │   │   └── services.py           # Domain services for ingestion
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── services.py           # Application services for ingestion
│   │       └── tasks.py              # Celery tasks for background processing
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py       # Adapters for different vector stores
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── models.py             # Pydantic models for knowledge base
│   │   │   └── services.py           # Domain services for knowledge
│   │   └── application/
│   │       ├── __init__.py
│   │       └── services.py           # Application services for knowledge
│   │
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── llm_gateway.py        # Adapters for different LLMs
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── models.py             # Pydantic models for queries, responses
│   │   │   └── services.py           # Domain services for interaction
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── services.py           # Application services for interaction
│   │       └── endpoints.py          # FastAPI endpoints for interaction
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── models.py             # Pydantic models for pipelines
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── rag_pipeline.py       # RAG pipeline orchestrator
│   │       └── nl2sql_pipeline.py    # NL2SQL pipeline orchestrator
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── models.py             # Pydantic models for users, roles
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── services.py           # Application services for security
│   │       └── endpoints.py          # FastAPI endpoints for security
│   │
│   └── main.py                       # FastAPI application entry point
│
├── tests/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── test_adapters.py
│   │   ├── test_domain.py
│   │   └── test_application.py
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── test_adapters.py
│   │   ├── test_domain.py
│   │   └── test_application.py
│   │
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── test_adapters.py
│   │   ├── test_domain.py
│   │   └── test_application.py
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── test_rag_pipeline.py
│   │   └── test_nl2sql_pipeline.py
│   │
│   └── security/
│       ├── __init__.py
│       ├── test_domain.py
│       └── test_application.py
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Directory and File Responsibilities

*   **`src/`**: This directory will contain all the source code for the application, organized by Bounded Context.
    *   **`src/<bounded_context>/`**: Each Bounded Context has its own directory.
        *   **`adapters/`**: Contains the code that interacts with external systems, such as databases, file systems, and external APIs.
        *   **`domain/`**: Contains the core business logic of the Bounded Context, including domain models and services. This layer should be independent of any application-specific or infrastructure-specific concerns.
        *   **`application/`**: Contains the application-specific logic, such as use cases, application services, and API endpoints. This layer orchestrates the domain logic to perform specific tasks.
*   **`tests/`**: This directory will contain all the tests for the application, mirroring the structure of the `src/` directory.
*   **`docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `README.md`**: These files will remain at the root of the project.
