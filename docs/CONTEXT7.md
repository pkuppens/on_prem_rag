# Context7: A Unified Context Server for AI Coding Assistants

## What is Context7?

Context7 is a powerful concept representing a **unified, real-time context server** for AI coding assistants like **Cursor**, **Gemini**, **Claude**, and others. Instead of just serving static documentation, a Context7 server exposes your **entire project directory**—including source code, documentation, and configuration—through a local web server.

This approach transforms your project into a browsable, API-accessible resource for your AI assistant. It allows the AI to fetch not only high-level documentation but also to read specific source files, check configuration, and understand the codebase directly. This bridges the gap between the AI's general knowledge and the specific, real-time state of your project.

The "7" in Context7 refers to the seven key areas of context it is designed to serve, now expanded to include the full project:

1.  **Live Source Code**: Direct access to `.py`, `.ts`, `.java`, etc., files.
2.  **Project & Architectural Documentation**: `README.md`, `ARCHITECTURE.md`, C4 models.
3.  **Coding Standards & Conventions**: Style guides and linter configurations (`.ruff.toml`, `.prettierrc`).
4.  **API & Schema Definitions**: OpenAPI specs, GraphQL schemas, and database schemas, whether in docs or generated from code.
5.  **Operational Procedures & Configuration**: `Dockerfile`, `docker-compose.yml`, CI/CD pipeline files (`.github/workflows`).
6.  **Historical Context & Decision Logs**: Architectural Decision Records (ADRs).
7.  **Business Logic & Domain Knowledge**: Glossaries, process flows, and core business rules.

By exposing the entire project via a local endpoint, you give your AI a single, comprehensive source of truth, ensuring its suggestions are radically relevant and perfectly aligned.

## How to Set Up Your Context7 Server

Setting up a Context7 server is fast and can be done in several ways, from simple one-liners to more robust Docker setups.

### Step 1: Choose Your Server Method

#### Option A: Quick Start with NPX (Recommended)

For a zero-installation approach, you can use `npx` with the `http-server` package. This is the fastest way to get started.

1.  **Run the Server from Your Project Root**:
    Open a terminal in your project's root directory and run:
    ```bash
    # Serve the current directory on port 8077 with CORS enabled
    npx http-server . -p 8077 --cors
    ```
2.  Keep this server running in the background. Your entire project is now available at `http://localhost:8077`.

#### Option B: Using Docker

If you prefer a containerized, isolated environment, Docker is an excellent choice.

1.  **Run the Docker Command**:
    From your project's root directory, execute the following command:
    ```bash
    # Mount the current directory and serve it using a standard nginx image
    docker run --rm -v .:/usr/share/nginx/html:ro -p 8077:80 nginx
    ```
    This command serves your project files read-only (`:ro`), which is a good security practice.

#### Option C: Using Python

If you have Python installed, you can use its built-in HTTP server.

1.  **Run the Server**:
    From your project root, run this one-liner:
    ```bash
    # For Python 3
    python -m http.server 8077
    ```

### Step 2: Configure Your AI Assistant

Point your AI assistant to the running Context7 server. The key is to treat `http://localhost:8077` as the root of your project.

**Example**: To ask your AI to read `src/backend/main.py`, you would refer it to `http://localhost:8077/src/backend/main.py`.

---

### For Gemini & Claude

These assistants work well with URLs in prompts.

**Example Prompt**:

> "My project's context is served at `http://localhost:8077`. Please review the main application entrypoint at `/src/backend/main.py` and the database schema described in `/docs/SCHEMA.md`. Based on this, suggest a refactoring of the main startup event."

---

### For Cursor

Cursor's "Add Docs" feature is perfect for this.

1.  Open the AI chat and use the `@` symbol.
2.  Select **"Add a new doc"** -> **"URL"**.
3.  Enter the root URL: `http://localhost:8077`
4.  Give it a name like `@project`.

**Example Prompt**:

> "@project Please read `/pyproject.toml` and tell me which dependencies are used for testing."

---

## Managing Multiple Projects & Shared Documentation

Context7 excels when you work on multiple projects with shared standards.

### The Strategy: Layered Context

Run multiple Context7 servers on different ports:
1.  **Shared Context Server** (e.g., on port `8078`): Serves a directory containing company-wide documentation, such as coding standards, design system assets, and architectural principles.
2.  **Project Context Server** (e.g., on port `8077`): Serves your specific project's root directory.

### Example Multi-Context Prompt

Now, you can provide both URLs to your AI assistant to give it layered context.

> "I am working on a project served at `http://localhost:8077`. My company's shared coding standards and architectural principles are available at `http://localhost:8078`.
>
> Please review the shared standards for Python REST APIs from the shared context. Then, review my project's code at `/src/backend/api/routes.py`.
>
> Suggest improvements to my project's code to better align it with the company standards."

This layered approach ensures the AI has access to both the micro (project-specific) and macro (company-wide) context, leading to highly accurate and compliant suggestions.
