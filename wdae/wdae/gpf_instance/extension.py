from __future__ import annotations

from abc import abstractmethod
from importlib.metadata import entry_points
from typing import Any

from studies.study_wrapper import WDAEAbstractStudy


class GPFExtensionBase:
    """
    Base class for GPF extensions.

    GPF extensions can handle adding new studies and support for various GPF
    tools to an instance.
    """
    def __init__(self, instance: Any):
        tool_entry_points = entry_points(
            group=self._get_tool_entry_point_group(),
        )
        self.instance = instance
        self.dae_config = instance.dae_config
        self._tools: dict[str, GPFTool] = {}
        for entry in tool_entry_points:
            if entry.name in self._tools:
                raise KeyError(
                    f"Entry {entry.name} already defined for "
                    f"{self._get_tool_entry_point_group()}",
                )
            self._tools[entry.name] = entry.load()

        self.setup()

    def setup(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _get_tool_entry_point_group() -> str:
        raise NotImplementedError

    @abstractmethod
    def get_studies(self) -> list[WDAEAbstractStudy]:
        pass

    @abstractmethod
    def get_studies_ids(self) -> list[str]:
        pass

    def get_tool(
        self, study: WDAEAbstractStudy, tool_id: str,
    ) -> GPFTool | None:
        if tool_id not in self._tools:
            return None
        return self._tools[tool_id].make_tool(study)


class GPFTool:
    """
    Base class for implementing GPF tools.

    GPF tools are classes which interact with studies to provide data.
    """
    def __init__(self, tool_id: str):
        self._id = tool_id

    @property
    def tool_id(self) -> str:
        return self._id

    @staticmethod
    @abstractmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError
