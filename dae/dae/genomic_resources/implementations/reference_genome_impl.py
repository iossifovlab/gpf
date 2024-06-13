from __future__ import annotations

import copy
import itertools
import json
import logging
import os
import textwrap
from typing import Any, Optional

import yaml
from jinja2 import Template

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceStatistics,
)
from dae.genomic_resources.statistics.base_statistic import Statistic
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class GenomeStatisticsMixin:
    """Mixin for reference genome statistics access."""

    @staticmethod
    def get_global_statistic_file() -> str:
        return "reference_genome_statistic.yaml"

    @staticmethod
    def get_chrom_file(chrom: str) -> str:
        return f"{chrom}_statistic.yaml"


class ReferenceGenomeStatistics(
    ResourceStatistics,
    GenomeStatisticsMixin,
):
    """Class for accessing reference genome statistics."""

    def __init__(
            self, resource_id: str,
            global_statistic: GenomeStatistic,
            chrom_statistics: dict[str, ChromosomeStatistic]):
        super().__init__(resource_id)
        self.global_statistic = global_statistic
        self.chrom_statistics = chrom_statistics

    @staticmethod
    def build_statistics(
        genomic_resource: GenomicResource,
    ) -> Optional[ReferenceGenomeStatistics]:
        """Load reference genome statistics."""
        chrom_statistics = {}
        try:
            global_stat_filepath = os.path.join(
                ReferenceGenomeStatistics.get_statistics_folder(),
                ReferenceGenomeStatistics.get_global_statistic_file(),
            )
            with genomic_resource.open_raw_file(
                    global_stat_filepath, mode="r") as infile:
                global_statistic = GenomeStatistic.deserialize(infile.read())
            for chrom in global_statistic.chromosomes:
                chrom_stat_filepath = os.path.join(
                    ReferenceGenomeStatistics.get_statistics_folder(),
                    ReferenceGenomeStatistics.get_chrom_file(chrom),
                )
                with genomic_resource.open_raw_file(
                        chrom_stat_filepath, mode="r") as infile:
                    chrom_statistics[chrom] = ChromosomeStatistic.deserialize(
                        infile.read(),
                    )
        except FileNotFoundError:
            logger.exception(
                "Couldn't load statistics of %s", genomic_resource.resource_id,
            )
            return None
        return ReferenceGenomeStatistics(
            genomic_resource.resource_id,
            global_statistic,
            chrom_statistics,
        )


class ChromosomeStatistic(Statistic):
    """Class for individual chromosome statistics."""

    def __init__(
        self, chromosome: str, length: int = 0,
        nucleotide_counts: Optional[dict[str, int]] = None,
        nucleotide_pair_counts: Optional[dict[str, int]] = None,
    ):
        super().__init__(chromosome, "Reference genome chromosome stats")
        if nucleotide_counts is None:
            self.nucleotide_counts = {
                "A": 0,
                "G": 0,
                "C": 0,
                "T": 0,
                "N": 0,
            }
        else:
            assert set(
                nucleotide_counts.keys(),
            ) == {"A", "G", "C", "T", "N"}
            self.nucleotide_counts = nucleotide_counts

        nucleotides = ["A", "G", "C", "T", "N"]
        pairs = map("".join, itertools.product(nucleotides, nucleotides))
        if nucleotide_pair_counts is None:
            self.nucleotide_pair_counts = dict.fromkeys(pairs, 0)
        else:
            assert set(nucleotide_pair_counts.keys()) == set(pairs)
            self.nucleotide_pair_counts = nucleotide_pair_counts

        self.nucleotide_distribution: dict[str, float] = {}
        self.bi_nucleotide_distribution: dict[str, float] = {}
        self.last_nuc = ""
        self.length = length

    def _add_nucleotide(self, nuc: str) -> None:
        assert nuc is not None
        if nuc not in self.nucleotide_counts:
            logger.warning(
                "unexpected nucleotide <%s> in chromosome <%s>",
                nuc, self.statistic_id)
            return

        self.nucleotide_counts[nuc] += 1
        self.length += 1

    def _add_nucleotide_tuple(
            self, nuc1: Optional[str], nuc2: str) -> None:
        if nuc1 is None:
            return

        assert nuc1 is not None
        assert nuc2 is not None

        pair = f"{nuc1}{nuc2}"
        if pair not in self.nucleotide_pair_counts:
            return
        self.nucleotide_pair_counts[pair] += 1

    def add_value(self, value: tuple[Optional[str], str]) -> None:
        prev, current = value
        self._add_nucleotide(current)
        self._add_nucleotide_tuple(prev, current)

    def merge(self, other: Statistic) -> None:
        assert isinstance(other, ChromosomeStatistic)

        local_keys = set(self.nucleotide_counts.keys())
        other_keys = set(other.nucleotide_counts.keys())
        matching_keys = local_keys.intersection(other_keys)
        missing_keys = other_keys.difference(local_keys)
        for k in matching_keys:
            self.nucleotide_counts[k] += other.nucleotide_counts[k]
        for k in missing_keys:
            self.nucleotide_counts[k] = other.nucleotide_counts[k]

        local_keys = set(self.nucleotide_pair_counts.keys())
        other_keys = set(other.nucleotide_pair_counts.keys())
        matching_keys = local_keys.intersection(other_keys)
        missing_keys = other_keys.difference(local_keys)
        for k in matching_keys:
            self.nucleotide_pair_counts[k] += other.nucleotide_pair_counts[k]
        for k in missing_keys:
            self.nucleotide_pair_counts[k] = other.nucleotide_pair_counts[k]

        self.length += other.length

    def finish(self) -> None:
        for nucleotide, count in self.nucleotide_counts.items():
            self.nucleotide_distribution[nucleotide] = \
                count / self.length * 100

        total_pairs = sum(self.nucleotide_pair_counts.values())
        for pair, count in self.nucleotide_pair_counts.items():
            if total_pairs == 0:
                self.bi_nucleotide_distribution[pair] = 0.0
            else:
                self.bi_nucleotide_distribution[pair] = \
                    count * 100.0 / total_pairs

    def serialize(self) -> str:
        return yaml.dump(
            {
                "chrom": self.statistic_id,
                "length": self.length,
                "nucleotide_counts": self.nucleotide_counts,
                "nucleotide_pair_counts": self.nucleotide_pair_counts,
            },
        )

    @staticmethod
    def deserialize(content: str) -> ChromosomeStatistic:
        res = yaml.safe_load(content)
        stat = ChromosomeStatistic(
            res["chrom"],
            length=res.get("length"),
            nucleotide_counts=res.get("nucleotide_counts"),
            nucleotide_pair_counts=res.get("nucleotide_pair_counts"),
        )
        stat.finish()
        return stat


class GenomeStatistic(Statistic):
    """Class for the global reference genome statistic."""

    def __init__(
            self, chromosomes: list[str], length: int = 0,
            nucleotide_distribution: Optional[dict[str, float]] = None,
            bi_nucleotide_distribution: Optional[dict[str, float]] = None,
            chromosome_statistics: Optional[
                dict[str, ChromosomeStatistic]] = None,
    ):
        super().__init__("global", "")
        self.chromosomes = chromosomes
        self.length = 0

        if chromosome_statistics is not None:
            self.chromosome_statistics = chromosome_statistics
            self.nucleotide_distribution: dict[str, Any] = {}
            self.bi_nucleotide_distribution: dict[str, Any] = {}
            self.finish()
        else:
            self.chromosome_statistics = {}
            if nucleotide_distribution is None:
                self.nucleotide_distribution = {}
            else:
                self.nucleotide_distribution = nucleotide_distribution

            if bi_nucleotide_distribution is None:
                self.bi_nucleotide_distribution = {}
            else:
                self.bi_nucleotide_distribution = bi_nucleotide_distribution

        self.length = length

    @property
    def chrom_count(self) -> int:
        return len(self.chromosomes)

    def add_value(self, value: Any) -> None:
        assert isinstance(value, ChromosomeStatistic)
        self.chromosome_statistics[value.statistic_id] = value

    def finish(self) -> None:
        total_nucs = 0
        total_nucleotide_counts = {
            "A": 0,
            "G": 0,
            "C": 0,
            "T": 0,
            "N": 0,
        }
        nucleotides = ["A", "G", "C", "T", "N"]
        pairs = map("".join, itertools.product(nucleotides, nucleotides))
        total_pair_counts = dict.fromkeys(pairs, 0)
        total_pairs = 0
        for statistic in self.chromosome_statistics.values():
            total_nucs += statistic.length
            for nuc, count in statistic.nucleotide_counts.items():
                total_nucleotide_counts[nuc] += count
            for pair, count in statistic.nucleotide_pair_counts.items():
                total_pairs += count
                total_pair_counts[pair] += count

        self.length = total_nucs

        for nuc, count in total_nucleotide_counts.items():
            self.nucleotide_distribution[nuc] = count / total_nucs * 100

        for pair, count in total_pair_counts.items():
            self.bi_nucleotide_distribution[pair] = count / total_pairs * 100

    def merge(self, other: Statistic) -> None:  # noqa: ARG002
        return

    def serialize(self) -> str:
        return yaml.dump({
            "chromosomes": self.chromosomes,
            "length": self.length,
            "nucleotide_distribution": self.nucleotide_distribution,
            "bi_nucleotide_distribution": self.bi_nucleotide_distribution,
        })

    @staticmethod
    def deserialize(content: str) -> GenomeStatistic:
        res = yaml.safe_load(content)
        return GenomeStatistic(
            res["chromosomes"],
            length=res.get("length"),
            nucleotide_distribution=res.get("nucleotide_distribution"),
            bi_nucleotide_distribution=res.get("bi_nucleotide_distribution"),
        )


class ReferenceGenomeImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Resource implementation for reference genome."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        self.reference_genome = build_reference_genome_from_resource(resource)

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}

            {% if data["chrom_prefix"] %}
            <p>chrom prefix: {{ data["chrom_prefix"] }}</p>
            {% endif %}

            {% if data["PARS"] %}
            <h3>Pseudoautosomal regions:</h6>
            {% if data["PARS"]["X"] %}
            <p>X chromosome:</p>
            <ul>
            {% for region in data["PARS"]["X"] %}
            <li>{{region}}</li>
            {% endfor %}
            </ul>
            {% endif %}

            {% if data["PARS"]["Y"] %}
            <p>Y chromosome: </p>
            <ul>
            {% for region in data["PARS"]["Y"] %}
            <li>{{region}}</li>
            {% endfor %}
            </ul>
            {% endif %}
            {% endif %}

            <h3>Genome statistics:</h3>
            {% if data["global_statistic"] %}
                <h4>
                    Length: {{ '{:,}'.format(data["global_statistic"]["length"]) }}
                </h4>

                <h4>Nucleotide distribution:</h4>
                {%
                    for nucleotide, prc in
                    data["global_statistic"]["nuc_distribution"].items()
                %}
                    <div>{{ nucleotide }}: {{ "%0.2f%%" % prc }}</div>
                {% endfor %}

                <h4>Bi-Nucleotide distribution:</h4>
                <table border="1">
                    <tr>
                        <th>{{ nucleotide }}</th>
                        {% for nucleotide in
                            data["global_statistic"]["nuc_distribution"].keys() %}
                            <th>{{ nucleotide }}</th>
                        {% endfor %}
                    </tr>
                    {% for first_nucleotide in
                        data["global_statistic"]["nuc_distribution"].keys() %}
                        <tr>
                            <td>{{ first_nucleotide }}</td>
                            {% for second_nucleotide in
                            data["global_statistic"]["nuc_distribution"].keys() %}
                                <td>{{ "%0.2f%%" %  data["global_statistic"]["bi_nuc_distribution"].get(first_nucleotide + second_nucleotide) }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </table>
            {% endif %}

            <h3>{{ "Chromosomes ({0}):".format(data["chromosomes"]|length) }}</h3>
            <div style="max-height: 50%; overflow-y: auto; width: fit-content">
                <table border="1" >
                    <tr>
                        <th>Chrom</th>
                        <th>Length</th>
                        {% for nucleotide in
                            data["global_statistic"]["nuc_distribution"].keys()|sort %}
                            <th>{{ nucleotide }}</th>
                        {% endfor %}
                    </tr>
                    {%- for chrom, length in data["chromosomes"] -%}
                        <tr>
                            <td>{{ chrom }}</td>
                            <td>{{ '{:,}'.format(length) }}</td>
                            {% for nucleotide in
                                data["global_statistic"]["nuc_distribution"].keys()|sort %}
                                {% if data["chrom_statistics"].get(chrom) %}
                                    <td>{{ "%0.2f%%" % data["chrom_statistics"].get(chrom).nucleotide_distribution.get(nucleotide) }}</td>
                                {% else %}
                                    <td></td>
                                {% endif %}
                            {% endfor %}
                        </tr>
                    {%- endfor -%}
                </table>
            </div>
            {% endblock %}
        """))  # noqa: E501

    def _get_template_data(self) -> dict[str, Any]:
        info = copy.deepcopy(self.config)
        info["chromosomes"] = self.reference_genome.get_all_chrom_lengths()
        info["global_statistic"] = {}
        info["chrom_statistics"] = {}
        statistics = self.get_statistics()
        if statistics is None:
            info["global_statistic"]["length"] = None
            info["global_statistic"]["nuc_distribution"] = None
            info["global_statistic"]["bi_nuc_distribution"] = None
            info["global_statistic"]["chromosome_statistics"] = None
        else:
            global_statistic = statistics.global_statistic

            info["global_statistic"]["length"] = global_statistic.length
            info["global_statistic"]["nuc_distribution"] = \
                global_statistic.nucleotide_distribution
            info["global_statistic"]["bi_nuc_distribution"] = \
                global_statistic.bi_nucleotide_distribution
            info["chrom_statistics"] = statistics.chrom_statistics

        return info

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        manifest = self.resource.get_manifest()
        config = self.get_config()
        genome_filename = config["filename"]
        return json.dumps({
            "score_file": manifest[genome_filename].md5,
        }, sort_keys=True, indent=2).encode()

    def add_statistics_build_tasks(
            self, task_graph: TaskGraph, **kwargs: Any) -> list[Task]:
        tasks = []

        region_size = kwargs.get("region_size", 1_000_000)

        chrom_save_tasks = []
        with self.reference_genome.open():
            for chrom in self.reference_genome.chromosomes:
                _, _, chrom_save_task = self._add_chrom_stats_tasks(
                    task_graph, chrom, region_size,
                )
                chrom_save_tasks.append(chrom_save_task)

        tasks.extend(chrom_save_tasks)

        tasks.append(self._add_global_stat_task(task_graph, chrom_save_tasks))
        return tasks

    def _add_chrom_stats_tasks(
        self, task_graph: TaskGraph, chrom: str, region_size: int,
    ) -> tuple[list[Task], Task, Task]:
        chrom_tasks = []
        regions = self.reference_genome.split_into_regions(region_size, chrom)
        chrom_tasks = [
            task_graph.create_task(
                f"{self.resource.resource_id}_count_nucleotides_"
                f"{reg}",
                ReferenceGenomeImplementation._do_chrom_statistic,
                [self.resource, reg.chrom, reg.start, reg.end],
                [],
            )
            for reg in regions
        ]

        merge_task = task_graph.create_task(
            f"{self.resource.resource_id}_merge_chrom_statistics_{chrom}",
            ReferenceGenomeImplementation._merge_chrom_statistics,
            [*chrom_tasks],
            chrom_tasks,
        )
        save_task = task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics_{chrom}",
            ReferenceGenomeImplementation._save_chrom_statistic,
            [self.resource, chrom, merge_task],
            [merge_task],
        )

        return chrom_tasks, merge_task, save_task

    def _add_global_stat_task(
        self, task_graph: TaskGraph, chrom_stats_save_tasks: list[Task],
    ) -> Task:
        return task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics",
            ReferenceGenomeImplementation._do_global_statistic,
            [self.resource, *chrom_stats_save_tasks],
            chrom_stats_save_tasks,
        )

    @staticmethod
    def _do_chrom_statistic(
        resource: GenomicResource, chrom: str, start: int, end: Optional[int],
    ) -> ChromosomeStatistic:
        impl = build_reference_genome_from_resource(resource)
        statistic = ChromosomeStatistic(chrom)
        with impl.open():
            if start == 1:
                prev: Optional[str] = None
            else:
                prev = impl.get_sequence(chrom, start - 1, start)
            for nuc in impl.fetch(chrom, start, end):
                statistic.add_value((prev, nuc))
                prev = nuc

        statistic.finish()
        return statistic

    @staticmethod
    def _merge_chrom_statistics(
        *chrom_tasks: ChromosomeStatistic,
    ) -> ChromosomeStatistic:
        final_statistic: Optional[ChromosomeStatistic] = None
        for chrom_task_result in chrom_tasks:
            if final_statistic is None:
                final_statistic = chrom_task_result
            else:
                final_statistic.merge(chrom_task_result)
        assert final_statistic is not None
        return final_statistic

    @staticmethod
    def _save_chrom_statistic(
        resource: GenomicResource, chrom: str,
        merged_statistic: ChromosomeStatistic,
    ) -> ChromosomeStatistic:
        proto = resource.proto
        if merged_statistic is None:
            logger.warning("Chrom statistic for %s is None", chrom)
            return {chrom: None}
        with proto.open_raw_file(
            resource,
            f"{ReferenceGenomeStatistics.get_statistics_folder()}"
            f"/{ReferenceGenomeStatistics.get_chrom_file(chrom)}",
            mode="wt",
        ) as outfile:
            outfile.write(merged_statistic.serialize())
        return merged_statistic

    @staticmethod
    def _do_global_statistic(
        resource: GenomicResource, *chrom_save_tasks: ChromosomeStatistic,
    ) -> GenomeStatistic:
        impl = build_reference_genome_from_resource(resource)
        with impl.open():
            statistic = GenomeStatistic(impl.chromosomes)
            for chrom_statistic in chrom_save_tasks:
                statistic.add_value(chrom_statistic)

            statistic.finish()

        proto = resource.proto
        with proto.open_raw_file(
            resource,
            f"{ReferenceGenomeStatistics.get_statistics_folder()}"
            f"/{ReferenceGenomeStatistics.get_global_statistic_file()}",
            mode="wt",
        ) as outfile:
            outfile.write(statistic.serialize())
        return statistic

    def get_statistics(self) -> Optional[ReferenceGenomeStatistics]:
        return ReferenceGenomeStatistics.build_statistics(self.resource)
