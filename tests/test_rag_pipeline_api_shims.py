"""Backward-compatibility contract of the `backend.rag_pipeline.api` shims.

Dockerfile, docker-compose, k8s and `start-backend` still run `backend.rag_pipeline.api.app:app`,
so the shims must keep resolving to the Query Service implementation.
"""

import importlib

import pytest

from backend.query_service.api import ask as qs_ask
from backend.query_service.api import chat as qs_chat
from backend.query_service.api import query as qs_query
from backend.query_service.api.app import app as qs_app
from backend.query_service.main import start_server as qs_start_server
from backend.rag_pipeline import api
from backend.rag_pipeline.api import ask as legacy_ask
from backend.rag_pipeline.api import chat as legacy_chat
from backend.rag_pipeline.api import query as legacy_query

# The package re-exports `app` (the FastAPI instance), shadowing the submodule name; import the module explicitly.
legacy_app = importlib.import_module("backend.rag_pipeline.api.app")


def test_app_shim_exposes_query_service_app_and_start_server():
    """As an operator I want the old uvicorn entry point to serve the Query Service app."""
    assert legacy_app.app is qs_app
    assert legacy_app.start_server is qs_start_server


def test_package_exports_query_service_routers():
    """As a developer I want the legacy package-level router names to keep working.

    `api.app` is not asserted: importing the `app` submodule rebinds that attribute to the module.
    """
    assert api.ask_router is qs_ask.router
    assert api.chat_router is qs_chat.router
    assert api.query_router is qs_query.router


@pytest.mark.parametrize(
    ("legacy", "current", "name"),
    [
        (legacy_ask, qs_ask, "router"),
        (legacy_ask, qs_ask, "ask_question"),
        (legacy_chat, qs_chat, "router"),
        (legacy_chat, qs_chat, "chat_stream"),
        (legacy_query, qs_query, "router"),
        (legacy_query, qs_query, "query_documents"),
    ],
    ids=lambda v: getattr(v, "__name__", v),
)
def test_route_shims_reexport_the_same_objects(legacy, current, name):
    """As a developer I want old imports to return the identical Query Service objects."""
    assert getattr(legacy, name) is getattr(current, name)


def test_chat_shim_keeps_qa_system_alias_for_orchestrator():
    """As a developer I want the legacy `qa_system` name to point at the chat orchestrator."""
    assert legacy_chat.qa_system is qs_chat.orchestrator
