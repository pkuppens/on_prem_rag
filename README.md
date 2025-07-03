# On-Premises RAG Solution

_Talk with your documents and data using LLMs without Cloud privacy and confidentiality concerns_

## Executive Summary

This project delivers an **on-premises Retrieval-Augmented Generation (RAG) system** that enables organizations to leverage Large Language Models (LLMs) for document analysis and database querying while maintaining complete data sovereignty and regulatory compliance. The architecture now embraces the **Model‑Context‑Protocol (MCP)** for standardized context exchange between components.

## What We'll Build

![image](https://github.com/user-attachments/assets/2ed5872e-9ab2-49e4-90bf-ca0f774a46e1)

### Business Value Proposition

- **Data Privacy & Compliance**: Zero cloud dependencies ensure sensitive information never leaves your infrastructure
- **Cost Control**: Eliminate per-query API costs and unpredictable cloud billing
- **Regulatory Compliance**: Meet GDPR, HIPAA, SOX, and other regulatory requirements
- **Operational Independence**: No internet dependency for core functionality

## Strategic Goals

Our implementation addresses six core business objectives through a structured SAFe approach:

1. **[Technical Foundation](project/program/features/FEAT-001.md)**: Robust development environment and MVP implementation
2. **[Enterprise User Interface](project/program/features/FEAT-002.md)**: Intuitive GUI with enterprise-grade role-based access control
3. **[Flexible LLM Integration](project/program/features/FEAT-003.md)**: Justified tool selection with clear rationale for choices and rejections
4. **[Database Query Capabilities](project/program/features/FEAT-004.md)**: Natural language to SQL functionality
5. **[Production Deployment](project/program/features/FEAT-005.md)**: Containerized deployment with optimized Python and LLM integration
6. **[Security Framework](project/program/features/FEAT-006.md)**: Comprehensive security and access control implementation

## Repository Overview

This repository contains the complete SAFe project structure under [`docs/`](docs/),
including epics, features, stories, and tasks that guide development. Source
code will be added as the tasks in the `team` folder are implemented. The first
milestone focuses on document question-answering, while database NLP/SQL
capabilities are planned for later phases.

### Authentication Service

A lightweight authentication microservice (`auth_service`) handles username/password
registration and login while exposing placeholder OAuth2 endpoints for Google and Outlook.
Start it with:

```bash
uv run start-auth
```

## Key Business Concerns & Decisions

### Legal & Licensing Considerations

| Concern                      | Status                  | Decision Framework                             |
| ---------------------------- | ----------------------- | ---------------------------------------------- |
| **Commercial LLM Usage**     | ⚠️ Research Phase       | Evaluate Apache 2.0 vs proprietary licenses    |
| **Open Source Dependencies** | ✅ Approved Strategy    | Use permissive licenses (MIT, Apache 2.0) only |
| **Data Governance**          | ⚠️ Policy Required      | Define data retention and access policies      |
| **Liability & Warranty**     | ❌ Pending Legal Review | Establish liability framework for AI outputs   |

### Commercial Considerations

#### Initial Investment

- **Development Time**: 6-8 weeks for MVP, 12-16 weeks for production
- **Infrastructure**: Dedicated GPU server(s) for optimal performance
- **Licensing**: Zero ongoing cloud costs, one-time development investment

#### ROI Drivers

- **Eliminated Cloud Costs**: Typical enterprise saves $50K-200K annually
- **Compliance Risk Mitigation**: Avoid potential regulatory fines
- **Productivity Gains**: 40-60% faster document research and analysis

### Technology Trade-offs

#### Core Decisions Made

- **Local-First Architecture**: Complete offline capability vs. cloud performance
- **Open Source Stack**: Community support vs. enterprise vendor support
- **Modular Design**: Flexibility vs. integration complexity

#### Decisions Pending

- **LLM Model Selection**: Performance vs. resource requirements
- **Authentication Provider**: Built-in vs. enterprise SSO integration
- **Database Scope**: Document-only vs. full database integration

## Implementation Roadmap

The roadmap below intentionally prioritizes document-based question answering
before adding any database NLP/SQL features. A working document pipeline is
critical for validating the overall architecture.

### Phase 1: Foundation (Weeks 1-4)

- Core RAG pipeline with document ingestion
- Document question-answering pipeline
- Basic web interface for proof-of-concept
- Docker-based deployment

## Quick Start with Docker Compose

Clone the repository and run:

```bash
docker-compose up --build
```

This launches ChromaDB, the FastAPI backend, the React frontend and an Ollama
container. Visit the frontend at http://localhost:5173. If you already run an
Ollama container separately, comment out the `ollama` service in
`docker-compose.yml` and set `OLLAMA_BASE_URL` accordingly.

## Local Development Setup

To run the tests or work on the code outside containers, install the Python dependencies using `uv`. Network access is required when installing packages.

```bash
uv venv --python 3.13.2
source .venv/bin/activate
# Install package in editable mode with development dependencies
uv pip install -e .[dev]
pre-commit install
```

**Note**: The project uses editable installation (`-e`) to ensure proper Python module resolution. This allows the test suite to correctly import modules from `src/`, `scripts/`, and `project/` directories using absolute imports.

### Development Standards

- **Import Style**: Use absolute imports (`from scripts import module_name`) instead of relative imports
- **Testing**: All tests must pass before commits. Run tests with: `uv run pytest`
- **Package Management**: Configuration is handled through `pyproject.toml` for portable development environments
- **Dependency Management**:
  - **CRITICAL**: Always use `uv add package-name` for new dependencies - NEVER use `pip install`
  - `pip install` only works locally but fails in fresh environments (CI/CD, containers)
  - Before importing any package, verify it exists in `pyproject.toml` or add it with `uv add`
  - Use `uv sync` to install dependencies in fresh environments

See [docs/SETUP.md](docs/SETUP.md) for additional details.

### Phase 2: Enterprise Features (Weeks 5-8)

- Role-based access control
- Multi-user support
- Security hardening

### Phase 3: Advanced Capabilities (Weeks 9-12)

- Database natural language queries
- Multi-LLM support
- Performance optimization

## Risk Assessment

| Risk Category                | Impact | Mitigation Strategy                               |
| ---------------------------- | ------ | ------------------------------------------------- |
| **Model Performance**        | Medium | Extensive testing with business-relevant datasets |
| **Security Vulnerabilities** | High   | Third-party security audit before production      |
| **Resource Requirements**    | Medium | Scalable deployment architecture                  |
| **User Adoption**            | Low    | Intuitive UI design and comprehensive training    |

## Next Steps for Leadership

1. **Legal Review**: Engage legal team for licensing and liability framework
2. **Infrastructure Planning**: Provision development and production hardware
3. **Stakeholder Alignment**: Define success metrics and acceptance criteria
4. **Security Assessment**: Plan security audit and penetration testing
5. **Change Management**: Develop user training and adoption strategy

---

**Project Documentation**: Detailed SAFe project structure available in [`project/`](project/)
**Strategic Overview**: Complete business case in [`project/SAFe Project Plan.md`](project/SAFe%20Project%20Plan.md)
**Project Status**: Development Phase - MVP in progress
**Last Updated**: 2025-05-31
