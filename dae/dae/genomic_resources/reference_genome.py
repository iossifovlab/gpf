"""Defines reference genome class."""
from __future__ import annotations

import os
import logging
import copy
import textwrap
import itertools
import json
import yaml
from typing import Optional, Any, cast


from jinja2 import Template
from markdown2 import markdown
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

    def __init__(self, chromosome, length=0, nucleotide_counts=None):
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
                nucleotide_counts.keys
            ) == set(
                ["A", "G", "C", "T", "N"]
            )
            self.nucleotide_counts = nucleotide_counts

        self.nucleotide_distribution = {}
        self.length = length
        self.test = ""

    def add_value(self, value):
        self.length += 1
        assert value in self.nucleotide_counts, value
        self.test += value
        self.nucleotide_counts[value] += 1

    def merge(self, other):
        local_keys = set(self.nucleotide_counts.keys)
        other_keys = set(other.nucleotide_counts.keys)
        matching_keys = local_keys.intersection(other_keys)
        missing_keys = other_keys.difference(local_keys)
        for k in matching_keys:
            self.nucleotide_counts[k] += other.nucleotide_counts[k]
        for k in missing_keys:
            self.nucleotide_counts[k] = other.nucleotide_counts[k]

        self.length += other.length

    def finish(self):
        for nucleotide, count in self.nucleotide_counts.items():
            self.nucleotide_distribution[nucleotide] = \
                count / self.length * 100

    def serialize(self):
        return cast(str, yaml.dump(
            {
                "chrom": self.statistic_id,
                "length": self.length,
                "nucleotide_counts": self.nucleotide_counts
            }
        ))

    @staticmethod
    def deserialize(data):
        res = yaml.load(data, yaml.Loader)
        stat = ChromosomeStatistic(
            res["chrom"], res.get("length"), res.get("nucleotide_counts")
        )
        stat.finish()
        return stat


class GenomeStatistic(ChromosomeStatistic):
    """Class for the global reference genome statistic."""

    def __init__(
            self, chromosomes, length=0,
            nucleotide_counts=None, nucleotide_pair_counts=None
    ):
        super().__init__("global", length, nucleotide_counts)
        self.chromosomes = chromosomes
        nucleotides = ["A", "G", "C", "T"]
        pairs = map("".join, itertools.product(nucleotides, nucleotides))
        if nucleotide_pair_counts is None:
            self.nucleotide_pair_counts = {
                k: 0 for k in pairs
            }
        else:
            assert set(nucleotide_pair_counts.keys) == set(pairs)
            self.nucleotide_pair_counts = nucleotide_pair_counts
        self.bi_nucleotide_distribution = {}
        self.last_chrom = ""

    def _add_nucleotide_tuple(self, value1, value2):
        if value1 is None or value2 is None:
            return

        pair = f"{value1}{value2}"
        if pair not in self.nucleotide_pair_counts:
            return
        self.nucleotide_pair_counts[pair] += 1

    @property
    def chrom_count(self):
        return len(self.chromosomes)

    def add_value(self, value):
        chrom, left, right = value
        if self.last_chrom != chrom:
            super().add_value(left)
            self.last_chrom = chrom
        super().add_value(right)
        self._add_nucleotide_tuple(left, right)

    def finish(self):
        super().finish()

        total_pairs = sum(self.nucleotide_pair_counts.values())
        for pair, count in self.nucleotide_pair_counts.items():
            self.bi_nucleotide_distribution[pair] = count / total_pairs * 100

    def merge(self, other):
        super().merge(other)
        local_keys = set(self.nucleotide_pair_counts.keys)
        other_keys = set(other.nucleotide_pair_counts.keys)
        matching_keys = local_keys.intersection(other_keys)
        missing_keys = other_keys.difference(local_keys)
        for k in matching_keys:
            self.nucleotide_pair_counts[k] += other.chrom_statistics[k]
        for k in missing_keys:
            self.nucleotide_pair_counts[k] = other.chrom_statistics[k]

        self.length += other.length

    def serialize(self):
        return cast(str, yaml.dump({
            "chromosomes": self.chromosomes,
            "length": self.length,
            "nucleotide_counts": self.nucleotide_counts,
            "nucleotide_pair_counts": self.nucleotide_pair_counts
        }))

    @staticmethod
    def deserialize(data):
        res = yaml.load(data, yaml.Loader)
        stat = GenomeStatistic(
            res["chromosomes"],
            res.get("length"),
            res.get("nucleotide_counts"),
            res.get("nucleotide_pair_counts")
        )
        stat.finish()
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

    def _load_genome_index(self, index_content):
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

        config = self.resource.get_config()
        file_name = config["filename"]
        index_file_name = config.get(
            "index_file", f"{file_name}.fai")

        index_content = self.resource.get_file_content(index_file_name)
        self._load_genome_index(index_content)
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
        chrom_data = self._index.get(chrom)
        if chrom_data is None:
            raise ValueError(f"can't find chromosome {chrom}")
        return cast(int, chrom_data["length"])

    def get_all_chrom_lengths(self):
        """Return list of all chromosomes lengths."""
        return [
            (key, value["length"])
            for key, value in self._index.items()]

    def split_into_regions(self, region_size, chrom=None):
        if chrom is None:
            chromosome_lengths = self.get_all_chrom_lengths()
        else:
            chromosome_lengths = [(chrom, self.get_chrom_length(chrom))]
        for chrom, chrom_len in chromosome_lengths:
            logger.debug(
                "Chromosome '%s' has length %s",
                chrom, chrom_len)
            i = 1
            while i < chrom_len - region_size:
                yield chrom, i, i + region_size - 1
                i += region_size
            yield chrom, i, None

    def get_sequence(self, chrom, start, stop):
        """Return sequence of nucleotides from specified chromosome region."""
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

        if stop is None:
            length = self._index[chrom]["length"] - start + 1
        else:
            length = stop - start + 1
        line_feeds = 1 + length // self._index[chrom]["seqLineLength"]

        sequence = self._sequence.read(length + line_feeds).decode("ascii")
        sequence = sequence.replace("\n", "")[:length]
        return sequence.upper()

    def pair_iter(self, region_size=1_000_000):
        """
        Iterate and yield nucleotide pairs in the genome.

        The return value is a triple of the chromosome, the left and the right
        nucleotide.
        """
        self._sequence.seek(0)
        last_chrom = None
        last_nuc = None
        for chrom, start, end in self.split_into_regions(region_size):
            sequence = self.get_sequence(chrom, start, end)
            if chrom != last_chrom:
                last_chrom = chrom
            else:
                sequence = itertools.chain(
                    last_nuc, sequence
                )

            for left, right in zip(sequence, sequence[1:]):
                yield (chrom, left, right)
            last_nuc = sequence[-1]

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
            <hr>
            <h3>Genome file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>
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
            {% endblock %}
        """))

    def _get_template_data(self):
        info = copy.deepcopy(self.config)
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

        with self.open():
            for chrom in self.chromosomes:
                _, _, chrom_save_task = self._add_chrom_stats_tasks(
                    task_graph, chrom, region_size
                )
                tasks.append(chrom_save_task)

        # tasks.append(self._add_global_stat_task(task_graph))
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
        chroms = self.chromosomes
        merge_task = task_graph.create_task(
            f"{self.resource.resource_id}_merge_chrom_statistics_{chrom}",
            ReferenceGenome._merge_chrom_statistics,
            [chroms, *chrom_tasks],
            chrom_tasks
        )
        save_task = task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics_{chrom}",
            ReferenceGenome._save_chrom_statistics,
            [self.resource, merge_task],
            [merge_task]
        )

        return chrom_tasks, merge_task, save_task

    def _add_global_stat_task(self, task_graph):
        return task_graph.create_task(
            f"{self.resource.resource_id}_save_chrom_statistics",
            ReferenceGenome._do_global_statistic,
            [self.resource],
            []
        )

    @staticmethod
    def _do_chrom_statistic(resource, chrom, start, end):
        impl = build_reference_genome_from_resource(resource)
        statistic = ChromosomeStatistic(chrom)
        with impl.open():
            for nuc in impl.get_sequence(chrom, start, end):
                statistic.add_value(nuc)

        statistic.finish()
        return {
            chrom: statistic
        }

    @staticmethod
    def _merge_chrom_statistics(chroms, *chrom_tasks):
        res: dict[str, Optional[ChromosomeStatistic]] = {
            chrom: None for chrom in chroms}

        for chrom_task_result in chrom_tasks:
            for task_chrom, task_result in chrom_task_result.items():
                if res[task_chrom] is None:
                    res[task_chrom] = task_result
                else:
                    res[task_chrom].merge(task_result)
        return res

    @staticmethod
    def _save_chrom_statistics(resource, merged_statistics):
        proto = resource.proto
        for chrom, chrom_statistic in merged_statistics.items():
            if chrom_statistic is None:
                logger.warning("Chrom statistic for %s is None", chrom)
                continue
            with proto.open_raw_file(
                resource,
                f"{ReferenceGenomeStatistics.get_statistics_folder()}"
                f"/{ReferenceGenomeStatistics.get_chrom_file(chrom)}",
                mode="wt"
            ) as outfile:
                outfile.write(chrom_statistic.serialize())
        return merged_statistics

    @staticmethod
    def _do_global_statistic(resource):
        impl = build_reference_genome_from_resource(resource)
        with impl.open():
            statistic = GenomeStatistic(impl.chromosomes)
            for pair in impl.pair_iter():
                statistic.add_value(pair)

        proto = resource.proto
        with proto.open_raw_file(
            resource,
            f"{ReferenceGenomeStatistics.get_statistics_folder()}"
            f"/{ReferenceGenomeStatistics.get_global_statistic_file()}",
            mode="wt"
        ) as outfile:
            outfile.write(statistic.serialize())
        return statistic


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
