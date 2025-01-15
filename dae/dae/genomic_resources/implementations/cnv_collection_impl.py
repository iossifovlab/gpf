from __future__ import annotations

import logging
from typing import Any

from dae.genomic_resources.implementations.genomic_scores_impl import (
    GenomicScoreImplementation,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class CnvCollectionImplementation(GenomicScoreImplementation):
    """Assists in the management of resource of type cnv_collection."""
    # pylint: disable=useless-parent-delegation

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph,
        **kwargs: str,
    ) -> list[Task]:
        return super().add_statistics_build_tasks(task_graph, **kwargs)

    def calc_info_hash(self) -> bytes:
        return super().calc_info_hash()

    def calc_statistics_hash(self) -> bytes:
        return super().calc_statistics_hash()

    def get_info(self, **kwargs: Any) -> str:
        return super().get_info(**kwargs)

    def get_statistics_info(self, **kwargs: Any) -> str:
        return super().get_statistics_info(**kwargs)
