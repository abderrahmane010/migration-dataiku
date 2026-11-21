"""Reader based on the Dataiku public API (``dataikuapi``) — interface only.

Phase 1 defines the interface; the implementation will come once an API access
is available. It will rely on:

- ``DSSClient.list_project_keys()`` / ``list_projects()``;
- ``project.get_flow().get_graph()`` for the flow;
- ``dataset.get_settings()`` / ``recipe.get_settings()`` for definitions;
- ``recipe_settings.get_payload()`` / ``get_json_payload()`` for payloads;
- ``recipe.get_status().get_selected_engine_details()`` for the engine.

Credentials come from environment variables, never from code (CLAUDE.md, rule 4).
"""

from __future__ import annotations

from dku2dbx.model.ir import Project

API_HOST_ENV = "DKU_DSS_URL"
API_KEY_ENV = "DKU_API_KEY"  # name of an environment variable, not a secret


class DataikuApiReader:
    """``ProjectReader`` backed by a live DSS instance (not implemented yet)."""

    def __init__(self, host_env: str = API_HOST_ENV, api_key_env: str = API_KEY_ENV) -> None:
        self.host_env = host_env
        self.api_key_env = api_key_env

    def list_projects(self) -> list[str]:
        raise NotImplementedError("DataikuApiReader: en attente d'un accès à l'API Dataiku")

    def read_project(self, project_key: str) -> Project:
        raise NotImplementedError("DataikuApiReader: en attente d'un accès à l'API Dataiku")
