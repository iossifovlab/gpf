"""Defines reference genome class."""
from __future__ import annotations

import os
import logging
import copy
import textwrap
import itertools
import json
from typing import Optional, Any, cast

import yaml

from jinja2 import Template
from cerberus import Validator

from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin, ResourceStatistics
from dae.genomic_resources.statistics.base_statistic import Statistic

from dae.utils.regions import Region
from dae.genomic_resources import GenomicResource
from dae.task_graph.graph import Task


logger = logging.getLogger(__name__)


class GenomeStatisticsMixin:
    """Mixin for reference genome statistics access."""

    @staticmethod
    def get_global_statistic_file():
        return "reference_genome_statistic.yaml"

    @staticmethod
    def get_chrom_file(chrom):
        return f"{chrom}_statistic.yaml"


class ReferenceGenomeStatistics(
    ResourceStatistics,
    GenomeStatisticsMixin
):
    """Class for accessing reference genome statistics."""

    def __init__(self, resource_id, global_statistic, chrom_statistics):
        super().__init__(resource_id)
        self.global_statistic = global_statistic
        self.chrom_statistics = chrom_statistics

    @staticmethod
    def build_statistics(genomic_resource):
        chrom_statistics = {}
        try:
            global_stat_filepath = os.path.join(
                ReferenceGenomeStatistics.get_statistics_folder(),
                ReferenceGenomeStatistics.get_global_statistic_file()
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
                        infile.read()
                    )
        except FileNotFoundError:
            logger.exception(
                "Couldn't load statistics of %s", genomic_resource.resource_id
            )
            return ReferenceGenomeStatistics(genomic_resource, None, {})
        return ReferenceGenomeStatistics(
            genomic_resource,
            global_statistic,
            chrom_statistics
        )


class ChromosomeStatistic(Statistic):
    """Class for individual chromosome statistics."""

    def __init__(
        self, chromosome, length=0,
        nucleotide_counts=None,
        nucleotide_pair_counts=None
    ):
        super().__init__(chromosome, None)
        if nucleotide_counts is None:
            self.nucleotide_counts = {
                "A": 0,
                "G": 0,
                "C": 0,
                "T": 0,
                "N": 0
            }
        else:
            assert set(
                nucleotide_counts.keys()
            ) == set(
                ["A", "G", "C", "T", "N"]
            )
            self.nucleotide_counts = nucleotide_counts

        nucleotides = ["A", "G", "C", "T"]
        pairs = map("".join, itertools.product(nucleotides, nucleotides))
        if nucleotide_pair_counts is None:
            self.nucleotide_pair_counts = {
                k: 0 for k in pairs
            }
        else:
            assert set(nucleotide_pair_counts.keys()) == set(pairs)
            self.nucleotide_pair_counts = nucleotide_pair_counts

        self.nucleotide_distribution = {}
        self.bi_nucleotide_distribution = {}
        self.last_nuc = ""
        self.length = length

    def _add_nucleotide(self, nuc):
        if nuc is None or nuc not in self.nucleotide_counts:
            logger.warning(
                "unexpected nucleotide <%s> in chromosome <%s>",
                nuc, self.statistic_id)
            return

        self.nucleotide_counts[nuc] += 1
        self.length += 1

    def _add_nucleotide_tuple(self, value1, value2):
        if value1 is None or value2 is None:
            return

        pair = f"{value1}{value2}"
        if pair not in self.nucleotide_pair_counts:
            return
        self.nucleotide_pair_counts[pair] += 1

    def add_value(self, value):
        prev, current = value

        self._add_nucleotide(current)

        self._add_nucleotide_tuple(prev, current)

    def merge(self, other):
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

    def finish(self):
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

    def serialize(self):
        return cast(str, yaml.dump(
            {
                "chrom": self.statistic_id,
                "length": self.length,
                "nucleotide_counts": self.nucleotide_counts,
                "nucleotide_pair_counts": self.nucleotide_pair_counts
            }
        ))

    @staticmethod
    def deserialize(data):
        res = yaml.load(data, yaml.Loader)
        stat = ChromosomeStatistic(
            res["chrom"],
            length=res.get("length"),
            nucleotide_counts=res.get("nucleotide_counts"),
            nucleotide_pair_counts=res.get("nucleotide_pair_counts")
        )
        stat.finish()
        return stat


class GenomeStatistic(Statistic):
    """Class for the global reference genome statistic."""

    def __init__(
            self, chromosomes, length=0,
            nucleotide_distribution=None, bi_nucleotide_distribution=None,
            chromosome_statistics=None
    ):
        super().__init__("global", "")
        self.chromosomes = chromosomes

        self.chromosome_statistics = chromosome_statistics

        if self.chromosome_statistics is not None:
            self.nucleotide_distribution: dict[str, Any] = {}
            self.bi_nucleotide_distribution: dict[str, Any] = {}
            self.length = 0
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
    def chrom_count(self):
        return len(self.chromosomes)

    def add_value(self, value):
        assert isinstance(value, ChromosomeStatistic)
        self.chromosome_statistics[value.statistic_id] = value

    def finish(self):
        total_nucs = 0
        total_nucleotide_counts = {
            "A": 0,
            "G": 0,
            "C": 0,
            "T": 0,
            "N": 0
        }
        nucleotides = ["A", "G", "C", "T"]
        pairs = map("".join, itertools.product(nucleotides, nucleotides))
        total_pair_counts = {
            k: 0 for k in pairs
        }
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

    def merge(self, other):
        return self

    def serialize(self):
        return cast(str, yaml.dump({
            "chromosomes": self.chromosomes,
            "length": self.length,
            "nucleotide_distribution": self.nucleotide_distribution,
            "bi_nucleotide_distribution": self.bi_nucleotide_distribution
        }))

    @staticmethod
    def deserialize(data):
        res = yaml.load(data, yaml.Loader)
        stat = GenomeStatistic(
            res["chromosomes"],
            length=res.get("length"),
            nucleotide_distribution=res.get("nucleotide_distribution"),
            bi_nucleotide_distribution=res.get("bi_nucleotide_distribution")
        )
        return stat


class ReferenceGenome(
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin
):
    """Provides an interface for quering a reference genome."""

    config_validator = Validator

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        if resource.get_type() != "genome":
            raise ValueError(
                f"wrong type of resource passed: {resource.get_type()}")
        self._index: dict[str, Any] = {}
        self._chromosomes: list[str] = []
        self._sequence = None

        self.pars: dict = self._parse_pars(resource.get_config())

    @property
    def resource_id(self):
        return self.resource.resource_id

    @staticmethod
    def _parse_pars(config) -> dict:
        if "PARS" not in config:
            return {}

        assert config["PARS"]["X"] is not None
        regions_x = [
            Region.from_str(region) for region in config["PARS"]["X"]
        ]
        chrom_x = regions_x[0].chrom

        result = {
            chrom_x: regions_x
        }

        if config["PARS"]["Y"] is not None:
            regions_y = [
                Region.from_str(region) for region in config["PARS"]["Y"]
            ]
            chrom_y = regions_y[0].chrom
            result[chrom_y] = regions_y
        return result

    @property
    def chromosomes(self) -> list[str]:
        """Return a list of all chromosomes of the reference genome."""
        return self._chromosomes

    def _load_genome_index(self):
        config = self.resource.get_config()
        file_name = config["filename"]
        index_file_name = config.get(
            "index_file", f"{file_name}.fai")

        index_content = self.resource.get_file_content(index_file_name)
        self._parse_genome_index(index_content)

    def _parse_genome_index(self, index_content):
        for line in index_content.split("\n"):
            line = line.strip()
            if not line:
                break
            line = line.split()

            self._index[line[0]] = {
                "length": int(line[1]),
                "startBit": int(line[2]),
                "seqLineLength": int(line[3]),
                "lineLength": int(line[4]),
            }
        self._chromosomes = list(self._index.keys())

    @property
    def files(self):
        config = self.resource.get_config()
        file_name = config["filename"]
        index_file_name = config.get("index_file", f"{file_name}.fai")
        return {file_name, index_file_name}

    def close(self):
        """Close reference genome sequence file-like objects."""
        # FIXME: consider using weakref to work around this problem
        # self._sequence.close()
        # self._sequence = None

        # self._index = {}
        # self._chromosomes = []

    def open(self) -> ReferenceGenome:
        """Open reference genome resources."""
        if self.is_open():
            logger.info(
                "opening already opened reference genome %s",
                self.resource.resource_id)
            return self

        self._load_genome_index()

        config = self.resource.get_config()
        file_name = config["filename"]
        self._sequence = self.resource.open_raw_file(
            file_name, "rb", uncompress=False, seekable=True)

        return self

    def is_open(self):
        return self._sequence is not None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            logger.error(
                "exception while using reference genome: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        try:
            self.close()
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "exception during closing reference genome", exc_info=True)

    def get_chrom_length(self, chrom: str) -> int:
        """Return the length of a specified chromosome."""
        if not self._index:
            logger.warning("genome index not loaded; loading")
            self._load_genome_index()
        chrom_data = self._index.get(chrom)
        if chrom_data is None:
            raise ValueError(f"can't find chromosome {chrom}")
        return cast(int, chrom_data["length"])

    def get_all_chrom_lengths(self):
        """Return list of all chromosomes lengths."""
        if not self._index:
            logger.warning("genome index not loaded; loading")
            self._load_genome_index()
        return [
            (key, value["length"])
            for key, value in self._index.items()]

    def split_into_regions(self, region_size, chromosome=None):
        """
        Split the reference genome into regions and yield them.

        Can specify a specific chromosome to limit the regions to be
        in that chromosome only.
        """
        if chromosome is None:
            chromosome_lengths = self.get_all_chrom_lengths()
        else:
            chromosome_lengths = [
                (chromosome, self.get_chrom_length(chromosome))
            ]
        for chrom, chrom_len in chromosome_lengths:
            logger.debug(
                "Chromosome '%s' has length %s",
                chrom, chrom_len)
            i = 1
            while i < chrom_len - region_size:
                yield chrom, i, i + region_size - 1
                i += region_size
            yield chrom, i, None

    def fetch(self, chrom, start, stop, buffer_size=512):
        """
        Yield the nucleotides in a specific region.

        While line feed calculation can be inaccurate because not every fetch
        will start at the start of a line, line feeds add extra characters
        to read and the output is limited by the amount of nucleotides
        expected to be read.
        """
        if chrom not in self.chromosomes:
            logger.warning(
                "chromosome %s not found in %s",
                chrom, self.resource.resource_id)
            return None
        assert self._sequence is not None
        self._sequence.seek(
            self._index[chrom]["startBit"]
            + start
            - 1
            + (start - 1) // self._index[chrom]["seqLineLength"]
        )

        chrom_length = self.get_chrom_length(chrom)

        if stop is None:
            length = chrom_length - start + 1
        else:
            length = min(stop, chrom_length) - start + 1
        line_feeds = 1 + length // self._index[chrom]["seqLineLength"]

        total_length = length + line_feeds
        read_progress = 0

        while read_progress < length:
            read_length = min(buffer_size, total_length - read_progress)
            sequence = self._sequence.read(read_length).decode("ascii")
            sequence = sequence.replace("\n", "").upper()
            end = min(read_progress + read_length, length - read_progress)
            sequence = sequence[:end]
            for nuc in sequence:
                yield nuc
            read_progress += len(sequence)

    def get_sequence(self, chrom, start, stop):
        """Return sequence of nucleotides from specified chromosome region."""
        return "".join(self.fetch(chrom, start, stop))

    def pair_iter(self, chrom, start, stop):
        """
        Iterate and yield nucleotide pairs in the genome.

        The return value is a tuple of the previous and the current
        nucleotide.
        When the region start is after the chromosome's start, it will
        collect pairs from 1 position behind to account for cross-region pairs.
        When the region start is equal to the chromosome's start, it will
        first yield a pair of the first nucleotide as the current, and None
        as the previous to account for the first nucleotide in the chrom.
        """
        yield_single = False
        prev = None
        if start > 1:
            start -= 1
        else:
            yield_single = True

        nucs = self.fetch(chrom, start, stop)

        if not yield_single:
            try:
                prev = next(nucs)
            except StopIteration:
                yield None, None

        for current in nucs:
            yield prev, current
            prev = current

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        """Return true if specified position is pseudoautosomal."""
        def in_any_region(
                chrom: str, pos: int, regions: list[Region]) -> bool:
            return any(map(lambda reg: reg.isin(chrom, pos), regions))

        pars_regions = self.pars.get(chrom, None)
        if pars_regions:
            return in_any_region(
                chrom, pos, pars_regions  # type: ignore
            )
        return False

    def get_template(self):
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
                <h4>Length: {{ data["global_statistic"]["length"] }}</h4>

                <h4>Nucleotide distribution:</h4>
                {%
                    for nucleotide, prc in
                    data["global_statistic"]["nuc_distribution"].items()
                %}
                    <p>{{ nucleotide }}: {{ "%0.2f%%" % prc }}</p>
                {% endfor %}

                <h4>Bi-Nucleotide distribution:</h4>
                {%
                    for nucleotide_pair, prc in
                    data["global_statistic"]["bi_nuc_distribution"].items()
                %}
                    <p>{{ nucleotide_pair }}: {{ "%0.2f%%" % prc }}</p>
                {% endfor %}
            {% endif %}

            <h3>Chromosomes:</h3>
            <table>
            <tr><td>Chrom</td><td>Length</td></tr>
            {%- for chrom, length in data["chromosomes"] -%}
            <tr>
            <td>{{ chrom }}</td>
            <td>{{ length }}</td>
            </tr>
            {%- endfor -%}
            </table>

            {% endblock %}
        """))

    def _get_template_data(self):
        info = copy.deepcopy(self.config)
        info["global_statistic"] = {}
        statistics = self.get_statistics()
        global_statistic = statistics.global_statistic

        info["global_statistic"]["length"] = global_statistic.length
        info["global_statistic"]["nuc_distribution"] = \
            global_statistic.nucleotide_distribution
        info["global_statistic"]["bi_nuc_distribution"] = \
            global_statistic.bi_nucleotide_distribution

        info["chromosomes"] = self.get_all_chrom_lengths()

        return info

    @staticmethod
    def get_schema():
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "chrom_prefix": {"type": "string"},
            "PARS": {"type": "dict", "schema": {
                "X": {"type": "list", "schema": {"type": "string"}},
                "Y": {"type": "list", "schema": {"type": "string"}},
            }}
        }

    def get_info(self):
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self):
        return "placeholder"

    def calc_statistics_hash(self) -> bytes:
        manifest = self.resource.get_manifest()
        config = self.get_config()
        genome_filename = config["filename"]
        return json.dumps({
            "score_file": manifest[genome_filename].md5
        }, sort_keys=True, indent=2).encode()

    def add_statistics_build_tasks(self, task_graph, **kwargs) -> list[Task]:
        tasks = []

        region_size = kwargs.get("region_size", 1_000_000)

        chrom_save_tasks = []
        with self.open():
            for chrom in self.chromosomes:
                _, _, chrom_save_task = self._add_chrom_stats_tasks(
                    task_graph, chrom, region_size
                )
                chrom_save_tasks.append(chrom_save_task)

        tasks.extend(chrom_save_tasks)

        tasks.append(self._add_global_stat_task(task_graph, chrom_save_tasks))
        return tasks

    def _add_chrom_stats_tasks(self, task_graph, chrom, region_size):
        chrom_tasks = []
        regions = self.split_into_regions(region_size, chrom)
        for _, start, end in regions:
            chrom_tasks.append(task_graph.create_task(
                f"{self.resource.resource_id}_count_nucleotides_"
                f"{chrom}_{start}_{end}",
                ReferenceGenome._do_chrom_statistic,
                [self.resource, chrom, start, end],
                []
            ))

        merge_task = task_graph.create_task(
            f"{self.resource.resource_id}_merge_chrom_statistics_{chrom}",
            ReferenceGenome._merge_chrom_statistics,
            [*chrom_tasks],
            chrom_tasks
        )
        save_task = task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics_{chrom}",
            ReferenceGenome._save_chrom_statistic,
            [self.resource, chrom, merge_task],
            [merge_task]
        )

        return chrom_tasks, merge_task, save_task

    def _add_global_stat_task(self, task_graph, chrom_stats_save_tasks):
        return task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics",
            ReferenceGenome._do_global_statistic,
            [self.resource, *chrom_stats_save_tasks],
            chrom_stats_save_tasks
        )

    @staticmethod
    def _do_chrom_statistic(resource, chrom, start, end):
        impl = build_reference_genome_from_resource(resource)
        statistic = ChromosomeStatistic(chrom)
        with impl.open():
            for pair in impl.pair_iter(chrom, start, end):
                statistic.add_value(pair)

        statistic.finish()
        return statistic

    @staticmethod
    def _merge_chrom_statistics(*chrom_tasks):
        final_statistic = None
        for chrom_task_result in chrom_tasks:
            if final_statistic is None:
                final_statistic = chrom_task_result
            else:
                final_statistic.merge(chrom_task_result)
        return final_statistic

    @staticmethod
    def _save_chrom_statistic(resource, chrom, merged_statistic):
        proto = resource.proto
        if merged_statistic is None:
            logger.warning("Chrom statistic for %s is None", chrom)
            return {chrom: None}
        with proto.open_raw_file(
            resource,
            f"{ReferenceGenomeStatistics.get_statistics_folder()}"
            f"/{ReferenceGenomeStatistics.get_chrom_file(chrom)}",
            mode="wt"
        ) as outfile:
            outfile.write(merged_statistic.serialize())
        return merged_statistic

    @staticmethod
    def _do_global_statistic(resource, *chrom_save_tasks):
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
            mode="wt"
        ) as outfile:
            outfile.write(statistic.serialize())
        return statistic

    def get_statistics(self):
        return ReferenceGenomeStatistics.build_statistics(self.resource)


def build_reference_genome_from_file(filename) -> ReferenceGenome:
    """Open a reference genome from a file."""
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    res = build_local_resource(dirname, {
        "type": "genome",
        "filename": basename,
    })
    return build_reference_genome_from_resource(res)


def build_reference_genome_from_resource(
        resource: Optional[GenomicResource]) -> ReferenceGenome:
    """Open a reference genome from resource."""
    if resource is None:
        raise ValueError("None resource passed")

    if resource.get_type() != "genome":
        logger.error(
            "trying to open a resource %s of type "
            "%s as reference genome",
            resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    ref = ReferenceGenome(resource)
    return ref
