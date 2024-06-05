from __future__ import annotations

import json
import logging
import textwrap
from collections import defaultdict
from functools import lru_cache
from typing import Any, Optional

import yaml
from jinja2 import Template

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.gene_models import (
    TranscriptModel,
    build_gene_models_from_resource,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class GeneModelsImpl(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        self.gene_models = build_gene_models_from_resource(resource)

    @property
    def files(self) -> set[str]:
        res = set()
        res.add(self.resource.get_config()["filename"])
        gene_mapping_filename = self.resource.get_config().get("gene_mapping")
        if gene_mapping_filename is not None:
            res.add(gene_mapping_filename)
        return res

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <h1>Configuration</h1>
                Gene models file:
                <p><a href="{{ data.config.filename }}">
                {{ data.config.filename }}
                </a></p>

                <p>Format: {{ data.config.format }}</p>
            <h1>Statistics</h1>
                <table>
                {% for stat, value in data.stats.items() %}
                    <tr><td> {{ stat }} </td><td> {{ value }} </td></tr>
                {% endfor %}
                </table>
            {% endblock %}
        """))

    def _get_template_data(self) -> dict[str, Any]:
        return {"config": self.config,
                "stats": self.get_statistics()}

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        manifest = self.resource.get_manifest()
        return json.dumps({
            "config": {
                "format": self.config.get("format"),
            },
            "files_md5": {
                file_name: manifest[file_name].md5
                for file_name in sorted(self.files)},
        }, indent=2).encode()

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any,  # noqa: ARG002
    ) -> list[Task]:
        task = task_graph.create_task(
            f"{self.resource_id}_cals_stats",
            self._do_statistics,
            [self.resource], [])
        return [task]

    @staticmethod
    def _do_statistics(resource: GenomicResource) -> dict[str, int]:
        gene_models = build_gene_models_from_resource(resource).load()

        coding_transcripts = [tm
                              for tm in gene_models.transcript_models.values()
                              if tm.is_coding()]
        stats = {"transcript number": len(gene_models.transcript_models),
                 "protein coding transcript number": len(coding_transcripts),
                 "gene number": len(gene_models.gene_names()),
                 "protein coding gene number":
                 len({tm.gene for tm in coding_transcripts}),
                 }

        tm_by_chrom: dict[str, list[TranscriptModel]] = defaultdict(list)
        for trm in gene_models.transcript_models.values():
            tm_by_chrom[trm.chrom].append(trm)

        stats["chromosome number"] = len(tm_by_chrom)
        for chrom, tms in tm_by_chrom.items():
            stats[f"{chrom} transcript numbers"] = len(tms)

        with resource.proto.open_raw_file(
                resource, "statistics/stats.yaml", "wt") as stats_file:
            yaml.dump(stats, stats_file, sort_keys=False)
        return stats

    @lru_cache(maxsize=64)  # noqa: B019
    def get_statistics(self) -> Optional[dict[str, int]]:  # type: ignore
        try:
            with self.resource.proto.open_raw_file(
                    self.resource, "statistics/stats.yaml", "rt") as stats_file:
                stats = yaml.safe_load(stats_file)
                if not isinstance(stats, dict):
                    logger.error(
                        "The stats.yaml file for the "
                        "%s is invalid (1).", self.resource)
                    return None
                for stat, value in stats.items():
                    if not isinstance(stat, str):
                        logger.error(
                            "The stats.yaml file for the "
                            "%s is invalid (2. %s).", self.resource, stat)
                        return None
                    if not isinstance(value, int):
                        logger.error(
                            "The stats.yaml file for the "
                            "%s is invalid (3. %s).", self.resource,
                            value)
                        return None
                return stats
        except FileExistsError:
            return None
