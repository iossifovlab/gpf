from __future__ import annotations

import json
import logging
import textwrap
from collections import defaultdict
from dataclasses import asdict, dataclass
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
    ResourceStatistics,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


@dataclass
class StatisticsData:
    """Class for storing gene models statistics."""

    transcript_number: int
    protein_coding_transcript_number: int
    gene_number: int
    protein_coding_gene_number: int


class GeneModelsStatistics(ResourceStatistics):
    """Class for accessing reference genome statistics."""

    def __init__(
            self, resource_id: str,
            chromosome_count: int,
            global_statistic: StatisticsData,
            chrom_statistics: dict[str, StatisticsData]):
        super().__init__(resource_id)
        self.chromosome_count = chromosome_count
        self.global_statistic = global_statistic
        self.chrom_statistics = chrom_statistics

    def serialize(self) -> str:
        """Serialize gene models statistics."""
        result: dict[str, Any] = {}
        result["resource_id"] = self.resource_id
        result["chromosome_count"] = self.chromosome_count
        result["global"] = asdict(self.global_statistic)
        result["chromosomes"] = {
            chrom: asdict(stat)
            for chrom, stat in self.chrom_statistics.items()
        }
        return yaml.dump(result, sort_keys=False)

    @staticmethod
    def deserialize(data: str) -> GeneModelsStatistics:
        """Deserialize gene models statistics."""
        result = yaml.safe_load(data)
        return GeneModelsStatistics(
            result["resource_id"],
            result["chromosome_count"],
            StatisticsData(**result["global"]),
            {
                chrom: StatisticsData(**stat)
                for chrom, stat in result["chromosomes"].items()
            },
        )


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
            {% block extra_styles %}
            #chromosomes-table {
                border-collapse: separate;
                border-spacing: 0;
            }
            #chromosomes-table th {
                border-top: 1px solid;
                border-bottom: 1px solid;
                border-right: 1px solid;
            }
            #chromosomes-table td {
                border-bottom: 1px solid;
                border-right: 1px solid;
            }
            #chromosomes-table th:first-child,
            #chromosomes-table td:first-child {
                border-left: 1px solid;
            }
            #chromosomes-table thead tr:nth-of-type(2) th {
                border-top: none;
            }
            #chromosomes-table thead {
                position: sticky; top: 0; background-color: white;
            }
            {% endblock %}

            {% block content %}
            <h1>Configuration</h1>
                Gene models file:
                <p><a href="{{ data.config.filename }}">
                {{ data.config.filename }}
                </a></p>

                <p>Format: {{ data.config.format }}</p>
            <h1>Statistics</h1>
                <h2>Chromosome statistics</h2>
                <div style="max-height: 50%; overflow-y: auto; width: fit-content">
                    <table id="chromosomes-table">
                        <thead>
                            <tr>
                                <th></th>
                                <th>Transcript number</th>
                                <th>Protein coding transcript number</th>
                                <th>Gene number</th>
                                <th>Protein coding gene number</th>
                            </tr>
                            <tr>
                                <th>Global</th>
                                <td>{{ '{:,}'.format(data.stats.global_statistic.transcript_number)}}</td>
                                <td>{{ '{:,}'.format(data.stats.global_statistic.protein_coding_transcript_number)}}</td>
                                <td>{{ '{:,}'.format(data.stats.global_statistic.gene_number)}}</td>
                                <td>{{ '{:,}'.format(data.stats.global_statistic.protein_coding_gene_number)}}</td>
                            </tr>
                        </thead>
                        {% for chrom, stat in data.stats.chrom_statistics.items() %}
                            <tr>
                                <td>{{ chrom }}</td>
                                <td>{{ '{:,}'.format(stat.transcript_number)}}</td>
                                <td>{{ '{:,}'.format(stat.protein_coding_transcript_number)}}</td>
                                <td>{{ '{:,}'.format(stat.gene_number)}}</td>
                                <td>{{ '{:,}'.format(stat.protein_coding_gene_number)}}</td>
                            </tr>
                        {% endfor %}
                    </table>
                </div>
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
    def _do_statistics(resource: GenomicResource) -> GeneModelsStatistics:
        gene_models = build_gene_models_from_resource(resource).load()

        coding_transcripts = [
            tm
            for tm in gene_models.transcript_models.values()
            if tm.is_coding()
        ]
        global_stats = StatisticsData(
            len(gene_models.transcript_models),
            len(coding_transcripts),
            len(gene_models.gene_names()),
            len({tm.gene for tm in coding_transcripts}),
        )

        tm_by_chrom: dict[str, list[TranscriptModel]] = defaultdict(list)
        for trm in gene_models.transcript_models.values():
            tm_by_chrom[trm.chrom].append(trm)
        chromosome_stats: dict[str, StatisticsData] = {}
        for chrom, tms in tm_by_chrom.items():
            chrom_coding_transcripts = [
                tm
                for tm in tms
                if tm.is_coding()
            ]
            chromosome_stats[chrom] = StatisticsData(
                len(tms),
                len(chrom_coding_transcripts),
                len({tm.gene for tm in tms}),
                len({tm.gene for tm in chrom_coding_transcripts}),
            )
        gene_models_stats = GeneModelsStatistics(
            resource.resource_id,
            len(tm_by_chrom),
            global_stats,
            chromosome_stats,
        )
        with resource.proto.open_raw_file(
                resource, "statistics/stats.yaml", "wt") as stats_file:
            stats_file.write(gene_models_stats.serialize())
        return gene_models_stats

    @lru_cache(maxsize=64)  # noqa: B019
    def get_statistics(self) -> Optional[GeneModelsStatistics]:  # type: ignore
        try:
            with self.resource.proto.open_raw_file(
                    self.resource, "statistics/stats.yaml", "rt") as stats_file:
                return GeneModelsStatistics.deserialize(
                    stats_file.read())
        except FileExistsError:
            return None
