"""Common interface of the project readers (ZIP export, Dataiku API)."""

from __future__ import annotations

from typing import Protocol

from dku2dbx.model.ir import Project


class ProjectReader(Protocol):
    """Source of Dataiku projects, turned into the internal representation."""

    def list_projects(self) -> list[str]:
        """Keys of the projects this source can read."""
        ...

    def read_project(self, project_key: str) -> Project:
        """Read one project into the IR. Raises ``KeyError`` for an unknown key."""
        ...
