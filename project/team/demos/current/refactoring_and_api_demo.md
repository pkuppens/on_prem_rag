# Demo Playbook: Refactoring and API-Driven Workflow

**Date**: 2025-07-05
**Presenter**: Gemini

## 1. Introduction

This demonstration showcases the successful refactoring of the RAG pipeline into a modular, extensible architecture. We will demonstrate the new, clear separation of concerns between agents and tasks, and show how this new architecture is exposed through a clean, easy-to-use API.

## 2. What We Will Demonstrate

- **Modular Codebase**: A walkthrough of the new `agents` and `tasks` packages, highlighting the clear separation of responsibilities.
- **API-Driven Workflow**: A live demonstration of the new `/api/query/process_conversation` endpoint, showing how the refactored pipeline can be triggered with a simple API call.
- **End-to-End Validation**: Proof that the refactored system works as expected, from API request to a final, processed result.

## 3. Demonstration Steps

### Step 1: Showcase the New Code Structure (5 minutes)

1.  **Open the `src/backend/rag_pipeline` directory.**
2.  **Navigate to the `agents` package.**
    - Explain that each file now represents a specific agent with a clear role (e.g., `preprocessing_agent.py`, `clinical_extractor.py`).
    - Open `preprocessing_agent.py` and `__init__.py` to show the new class-based structure and the `create_medical_crew` function.
3.  **Navigate to the `tasks` package.**
    - Explain that each file now represents a specific task, corresponding to an agent's function.
    - Open `preprocess_task.py` to show the new task class.
4.  **Contrast with the (now removed) old, monolithic `agents.py` and `tasks.py` files.**

### Step 2: Demonstrate the API Endpoint (10 minutes)

1.  **Ensure the backend server is running.**
    ```bash
    uv run start-backend
    ```
2.  **Use a tool like `curl` or a REST client (e.g., Postman, VS Code REST Client) to send a POST request to the new endpoint.**

    **Request:**

    We'll use the FastAPI docs "Try it" feature:
    http://localhost:8000/docs#/query/process_conversation_endpoint_api_query_process_conversation_post

    with "text": "The patient is a 45-year-old male with a history of hypertension. He presents with a persistent cough and fever. Recent lab results show elevated white blood cell count."

3.  **Show the JSON response from the API.**
    - Explain that this response is the result of the entire RAG pipeline being executed, orchestrated by the `Crew` in the new `main.py`.
    - Highlight that the complex workflow is now abstracted behind a simple, clean API call.

### Step 3: Walk Through the Code Execution (5 minutes)

1.  **Open `src/backend/rag_pipeline/api/query.py`.**
    - Show the `process_conversation_endpoint` and how it calls `process_medical_conversation`.
2.  **Open `src/backend/rag_pipeline/main.py`.**
    - Trace the `process_medical_conversation` function.
    - Show how the `create_medical_crew` function is called to assemble the agents.
    - Show how the tasks are instantiated and assigned to the agents.
    - Explain how the `Crew` is created and kicked off.

## 4. Conclusion

This refactoring has significantly improved the maintainability, extensibility, and testability of the RAG pipeline. By moving to a modular, API-driven architecture, we have laid a solid foundation for future development and made the system easier to integrate with other services.
