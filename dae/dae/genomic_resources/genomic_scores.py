# pylint: disable=too-many-lines
from __future__ import annotations

import os
import logging
import textwrap
import copy
import json

from typing import Iterator, Optional, cast, Type, Any, Union

from dataclasses import dataclass
from functools import lru_cache

from jinja2 import Template

from dae.task_graph.graph import TaskGraph
from . import GenomicResource
from .reference_genome import build_reference_genome_from_resource
from .resource_implementation import GenomicResourceImplementation, \
    ResourceStatistics, \
    get_base_resource_schema, \
    InfoImplementationMixin, \
    ResourceConfigValidationMixin
from .genomic_position_table import build_genomic_position_table, Line, \
    TabixGenomicPositionTable, VCFGenomicPositionTable, VCFLine
from .histogram import Histogram, HistogramStatisticMixin
from .statistics.min_max import MinMaxValue, MinMaxValueStatisticMixin

from .aggregators import build_aggregator, AGGREGATOR_SCHEMA, Aggregator


logger = logging.getLogger(__name__)

ScoreValue = Union[str, int, float, bool, None]

VCF_TYPE_CONVERSION_MAP = {
    "Integer": "int",
    "Float": "float",
    "String": "str",
    "Flag": "bool",
}

SCORE_TYPE_PARSERS = {
    "str": str,
    "float": float,
    "int": int
}


@dataclass
class ScoreDef:
    """Score configuration definition."""

    # pylint: disable=too-many-instance-attributes
    col_key: str
    desc: str
    type: str
    value_parser: Any
    na_values: Any
    pos_aggregator: Any
    nuc_aggregator: Any
    allele_aggregator: Any


class ScoreLine:
    """Abstraction for a genomic score line. Wraps the line adapter."""

    def __init__(self, line: Line, score_defs: dict):
        assert isinstance(line, (Line, VCFLine))
        self.line: Line = line
        self.score_defs = score_defs

    @property
    def chrom(self):
        return self.line.chrom

    @property
    def pos_begin(self):
        return self.line.pos_begin

    @property
    def pos_end(self):
        return self.line.pos_end

    @property
    def ref(self):
        return self.line.ref

    @property
    def alt(self):
        return self.line.alt

    def get_score(self, score_id):
        """Get and parse configured score from line."""
        key = self.score_defs[score_id].col_key
        value = self.line.get(key)
        if score_id in self.score_defs:
            col_def = self.score_defs[score_id]
            if value in col_def.na_values:
                value = None
            elif col_def.value_parser is not None:
                try:  # Temporary workaround for GRR generation
                    value = col_def.value_parser(value)
                except Exception as err:  # pylint: disable=broad-except
                    logger.error(err)
                    value = None
        return value

    def get_available_scores(self):
        return tuple(self.score_defs.keys())


class GenomicScoreStatistics(
    ResourceStatistics,
    HistogramStatisticMixin,
    MinMaxValueStatisticMixin
):
    """
    Class for genomic score statistics.

    Contains histograms and min max values mapped by score ID.
    """

    def __init__(self, resource_id, min_maxes, histograms):
        super().__init__(resource_id)
        self.score_min_maxes = min_maxes
        self.score_histograms = histograms

    @staticmethod
    def build_statistics(genomic_resource):
        genomic_score = build_score_from_resource(genomic_resource)
        min_maxes = {}
        histograms = {}
        for score_id in genomic_score.get_config_histograms():
            min_max_filepath = os.path.join(
                GenomicScoreStatistics.get_statistics_folder(),
                GenomicScoreStatistics.get_min_max_file(score_id)
            )
            try:
                with genomic_resource.open_raw_file(
                        min_max_filepath, mode="r") as infile:
                    min_max = MinMaxValue.deserialize(infile.read())
                    min_maxes[score_id] = min_max
            except FileNotFoundError:
                logger.warning(
                    "unable to load min/max statistics file: %s",
                    min_max_filepath)
        for hist_config in genomic_score.get_config_histograms().values():
            score_id = hist_config["score"]

            histogram_filepath = os.path.join(
                GenomicScoreStatistics.get_statistics_folder(),
                GenomicScoreStatistics.get_histogram_file(score_id)
            )
            try:
                with genomic_resource.open_raw_file(
                        histogram_filepath, mode="r") as infile:
                    histogram = Histogram.deserialize(infile.read())
                    histograms[score_id] = histogram
            except FileNotFoundError:
                logger.warning(
                    "unable to load histogram file: %s",
                    histogram_filepath)

        return GenomicScoreStatistics(genomic_resource, min_maxes, histograms)


class GenomicScore(
    GenomicResourceImplementation,
    ResourceConfigValidationMixin,
    InfoImplementationMixin
):
    # pylint: disable=too-many-public-methods
    """Genomic scores base class."""

    def __init__(self, resource):
        super().__init__(resource)
        self.config = self.validate_and_normalize_schema(
            self.config, resource
        )
        self.config["id"] = resource.resource_id
        self.table_loaded = False
        self.table = build_genomic_position_table(
            self.resource, self.config["table"]
        )
        self.score_definitions = self._generate_scoredefs()

    def get_score_histogram_image_file(self, score_id: str):
        statistics = self.get_statistics()
        if score_id not in statistics.score_histograms:
            return None
        return os.path.join(
            GenomicScoreStatistics.get_statistics_folder(),
            GenomicScoreStatistics.get_histogram_image_file(score_id))

    @lru_cache(maxsize=64)
    def get_statistics(self):
        return GenomicScoreStatistics.build_statistics(self.resource)

    @property
    def files(self):
        files = set()
        files.add(self.table.definition.filename)
        if isinstance(self.table, TabixGenomicPositionTable):
            files.add(f"{self.table.definition.filename}.tbi")
        return files

    @staticmethod
    def _parse_scoredef_config(config):
        """Parse ScoreDef configuration."""
        scores = {}
        default_na_values = {
            "str": {},
            "float": {"", "nan", ".", "NA"},
            "int": {"", "nan", ".", "NA"}
        }
        default_type_pos_aggregators = {
            "float": "mean",
            "int": "mean",
            "str": "concatenate"
        }
        default_type_nuc_aggregators = {
            "float": "max",
            "int": "max",
            "str": "concatenate"
        }
        default_type_allele_aggregators = {
            "float": "max",
            "int": "max",
            "str": "concatenate"
        }
        for score_conf in config["scores"]:
            col_type = score_conf.get(
                "type", config.get("default.score.type", "float"))

            col_key = score_conf.get("name") or score_conf["index"]

            col_def = ScoreDef(
                col_key,
                score_conf.get("desc", ""),
                col_type,
                SCORE_TYPE_PARSERS[col_type],
                score_conf.get(
                    "na_values",
                    config.get(
                        f"default_na_values.{col_type}",
                        default_na_values[col_type])),
                score_conf.get(
                    "position_aggregator",
                    config.get(
                        f"{col_type}.aggregator",
                        default_type_pos_aggregators[col_type])),
                score_conf.get(
                    "nucleotide_aggregator",
                    config.get(
                        f"{col_type}.aggregator",
                        default_type_nuc_aggregators[col_type])),
                score_conf.get(
                    "allele_aggregator",
                    config.get(
                        f"{col_type}.aggregator",
                        default_type_allele_aggregators[col_type])),
            )
            scores[score_conf["id"]] = col_def
        return scores

    @staticmethod
    def _get_vcf_scoredefs(vcf_header_info):
        def converter(val):
            try:
                return ",".join(map(str, val))
            except TypeError:
                return val
        return {
            key: ScoreDef(
                key,
                value.description or "",
                VCF_TYPE_CONVERSION_MAP[value.type],  # type: ignore
                converter if value.number not in (1, "A", "R") else None,
                tuple(), None, None, None
            ) for key, value in vcf_header_info.items()
        }

    def _validate_scoredefs(self):
        assert "scores" in self.config
        if self.table.header_mode == "none":
            assert all("name" not in score
                       for score in self.config["scores"]), \
                ("Cannot configure score columns by"
                 " name when header_mode is 'none'!")
        else:
            assert self.table.header is not None
            for score in self.config["scores"]:
                if "name" in score:
                    assert score["name"] in self.table.header
                elif "index" in score:
                    assert 0 <= score["index"] < len(self.table.header)
                else:
                    raise AssertionError("Either an index or name must"
                                         " be configured for scores!")

    def _generate_scoredefs(self):
        if isinstance(self.table, VCFGenomicPositionTable):
            vcf_scoredefs = GenomicScore._get_vcf_scoredefs(self.table.header)
            scoredefs = {}
            if "scores" in self.config:
                # allow overriding of vcf-generated scoredefs
                for over in self.config["scores"]:
                    score = vcf_scoredefs[over["id"]]
                    score.desc = over.get("desc", score.desc)
                    score.type = over.get("type", score.type)
                    score.value_parser = SCORE_TYPE_PARSERS[score.type]
                    score.na_values = over.get("na_values", score.na_values)
                    scoredefs[over["id"]] = score
                return scoredefs
            return vcf_scoredefs
        if "scores" in self.config:
            return GenomicScore._parse_scoredef_config(self.config)
        raise ValueError("No scores configured and not using a VCF")

    def get_config(self):
        return self.config

    @property
    def score_id(self):
        return self.get_config().get("id")

    def get_default_annotation(self) -> dict[str, Any]:
        if "default_annotation" in self.get_config():
            return cast(
                dict[str, Any], self.get_config()["default_annotation"])
        return {
            "attributes": [
                {"source": score, "destination": score}
                for score in self.score_definitions]
        }

    def _get_default_annotation_attribute(self, score: str) -> Optional[str]:
        """Return default annotation attribute for a score.

        Returns None if the score is not included in the default annotation.
        Returns the destination attribute if present or the score if not.
        """
        default_annotation = self.get_default_annotation()
        atts = []
        for att_conf in default_annotation.get("attributes", []):
            if att_conf["source"] != score:
                continue
            dst = score
            if "destination" in att_conf:
                dst = att_conf["destination"]
            atts.append(dst)
        if atts:
            return ",".join(atts)
        return None

    def get_score_config(self, score_id):
        return self.score_definitions.get(score_id)

    def close(self):
        self.table.close()
        self.table_loaded = False

    def is_open(self):
        return self.table_loaded

    def open(self) -> GenomicScore:
        """Open genomic score resource and returns it."""
        if self.is_open():
            logger.info(
                "opening already opened genomic score: %s",
                self.resource.resource_id)
            return self
        self.table.open()
        self.table_loaded = True
        if "scores" in self.config:
            self._validate_scoredefs()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            logger.error(
                "exception while working with genomic score: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        self.close()

    @staticmethod
    def _line_to_begin_end(line):
        if line.pos_end < line.pos_begin:
            raise IOError(
                f"The resource line {line} has a regions "
                f" with end {line.pos_end} smaller that the "
                f"begining {line.pos_end}.")
        return line.pos_begin, line.pos_end

    def _get_header(self):
        assert self.table is not None
        return self.table.header

    def get_config_histograms(self):
        """Collect all configurations of histograms for the genomic score."""
        result = {}
        for score_id, score in self.score_definitions.items():
            if score.type in {"int", "float"}:
                result[score_id] = Histogram.default_config(score_id)
        hist_config_overwrite = self.get_config().get("histograms", {})
        for hist_config in hist_config_overwrite:
            result[hist_config["score"]] = copy.deepcopy(hist_config)
        return result

    def get_resource_id(self):
        return self.config["id"]

    def _fetch_lines(
        self, chrom: str,
        pos_begin: Optional[int], pos_end: Optional[int]
    ) -> Iterator[ScoreLine]:
        for line in self.table.get_records_in_region(
            chrom, pos_begin, pos_end
        ):
            yield ScoreLine(line, self.score_definitions)

    def get_all_chromosomes(self):
        if not self.is_open():
            raise ValueError(f"genomic score <{self.score_id}> is not open")

        return self.table.get_chromosomes()

    def get_all_scores(self):
        return list(self.score_definitions)

    def fetch_region(
        self, chrom: str,
        pos_begin: Optional[int], pos_end: Optional[int], scores: list[str]
    ) -> Iterator[dict[str, ScoreValue]]:
        """Return score values in a region."""
        if not self.is_open():
            raise ValueError(f"genomic score <{self.score_id}> is not open")

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        for line in self._fetch_lines(chrom, pos_begin, pos_end):
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)

            val = {}
            for scr_id in scores:
                try:
                    val[scr_id] = line.get_score(scr_id)
                except (KeyError, IndexError):
                    logger.exception(
                        "Failed to fetch score %s in region %s:%s-%s",
                        scr_id,
                        chrom,
                        line_pos_begin,
                        line_pos_end
                    )
                    val[scr_id] = None

            if pos_begin is not None:
                left = max(pos_begin, line_pos_begin)
            else:
                left = line_pos_begin
            if pos_end is not None:
                right = min(pos_end, line_pos_end)
            else:
                right = line_pos_end

            for _ in range(left, right + 1):
                yield val

    def get_template(self):
        return Template(textwrap.dedent("""
        {% extends base %}
        {% block content %}

        {% set scores = data.genomic_scores %}

        <h1>Scores</h1>

        <table border="1">
        <tr>
        <th>id</th>
        <th>type</th>
        <th>default annotation</th>
        <th>description</th>
        <th>histogram</th>
        <th>range</th>
        </tr>

        {%- for score_id, score in scores.score_definitions.items() -%}

        <tr class="score-definition">

        <td>{{ score_id }}</td>

        <td>{{ score.type }}</td>

        {% set attr = scores._get_default_annotation_attribute(score_id) %}
        <td>{{ attr if attr else "" }}</td>

        <td>{{ score.desc }}</td>

        <td>
        {% set hist_image_file =
            scores.get_score_histogram_image_file(score_id) %}
        {%- if hist_image_file %}
        <img src="{{ hist_image_file }}"
            alt="{{ "HISTOGRAM FOR " + score_id }}"
            title={{ score_id }}
            width="200">
        {%- else -%}
        NO HISTOGRAM
        {%- endif -%}
        </td>

        <td>
        {% set statistics = scores.get_statistics() %}
        {% set min_max = statistics.score_min_maxes.get(score_id) %}
        {%- if min_max is not none and
                min_max.min is not none and min_max.max is not none -%}
        ({{"%0.3f" % min_max.min}}, {{"%0.3f" % min_max.max}})
        {%- else -%}
        NO RANGE
        {%- endif -%}
        </td>

        </tr>
        {%- endfor %}

        </table>

        {% endblock %}
        """))

    def _get_template_data(self):
        return {"genomic_scores": self}

    def get_info(self):
        return InfoImplementationMixin.get_info(self)

    @ staticmethod
    def get_schema():
        scores_schema = {
            "type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "type": {"type": "string"},
                    "desc": {"type": "string"},
                    "na_values": {"type": ["string", "list"]}
                }
            }
        }
        return {
            **get_base_resource_schema(),
            "table": {"type": "dict", "schema": {
                "filename": {"type": "string"},
                "index_filename": {"type": "string"},
                "desc": {"type": "string"},
                "format": {"type": "string"},
                "header_mode": {"type": "string"},
                "header": {"type": ["string", "list"]},
                "chrom": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"}
                }},
                "pos_begin": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"}
                }},
                "pos_end": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"}
                }},
                "chrom_mapping": {"type": "dict", "schema": {
                    "filename": {
                        "type": "string",
                        "excludes": ["add_prefix", "del_prefix"]
                    },
                    "add_prefix": {"type": "string"},
                    "del_prefix": {"type": "string", "excludes": "add_prefix"}
                }}
            }},
            "scores": scores_schema,
            "histograms": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "score": {"type": "string"},
                    "bins": {"type": "integer"},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                    "x_min_log": {"type": "number"},
                    "x_scale": {"type": "string"},
                    "y_scale": {"type": "string"},
                }
            }},
            "default_annotation": {"type": "dict", "allow_unknown": True}
        }

    def add_statistics_build_tasks(self, task_graph: TaskGraph, **kwargs):
        with self.open():
            region_size = kwargs.get("region_size", 1_000_000)
            grr = kwargs.get("grr")
            _, _, save_task = self._add_min_max_tasks(
                task_graph, region_size, grr
            )

            _, _, save_task = self._add_histogram_tasks(
                task_graph, save_task, region_size, grr
            )

            return [save_task]

    _REF_GENOME_CACHE: dict[str, Any] = {}

    @ staticmethod
    def _get_reference_genome_cached(grr, genome_id):
        if genome_id is None or grr is None:
            return None
        if genome_id in GenomicScore._REF_GENOME_CACHE:
            return GenomicScore._REF_GENOME_CACHE[genome_id]
        try:
            ref_genome = build_reference_genome_from_resource(
                grr.get_resource(genome_id)
            )
            logger.info(
                "Using reference genome label <%s> ",
                genome_id,
            )
        except FileNotFoundError:
            logger.warning(
                "Couldn't find reference genome %s",
                genome_id,
            )
            return None
        ref_genome.open()
        GenomicScore._REF_GENOME_CACHE[genome_id] = ref_genome
        return ref_genome

    def _get_chrom_regions(self, region_size, grr=None):
        ref_genome_id = self.resource.get_labels().get("reference_genome")
        ref_genome = self._get_reference_genome_cached(grr, ref_genome_id)
        if ref_genome is not None:
            regions = self._split_into_regions(region_size, ref_genome)
        else:
            regions = self._split_into_regions(region_size)
        return regions

    def _add_min_max_tasks(self, graph, region_size, grr=None):
        """
        Add and return calculation, merging and saving tasks for min max.

        The tasks are returned in a triple containing a list of calculation
        tasks, the merge task and the save task.
        """
        min_max_tasks = []
        regions = self._get_chrom_regions(region_size, grr)
        for chrom, start, end in regions:
            min_max_tasks.append(graph.create_task(
                f"{self.score_id}_calculate_min_max_{chrom}_{start}_{end}",
                GenomicScore._do_min_max,
                [self.resource, chrom, start, end],
                []
            ))
        score_ids = list(self.get_config_histograms().keys())
        merge_task = graph.create_task(
            f"{self.score_id}_merge_min_max",
            GenomicScore._merge_min_max,
            [score_ids, *min_max_tasks],
            min_max_tasks
        )
        save_task = graph.create_task(
            f"{self.score_id}_save_min_max",
            GenomicScore._save_min_max,
            [self.resource, merge_task],
            [merge_task]
        )
        return min_max_tasks, merge_task, save_task

    @ staticmethod
    def _do_min_max(resource, chrom, start, end):
        impl = build_score_from_resource(resource)
        score_ids = list(impl.get_config_histograms())
        res = {
            scr_id: MinMaxValue(scr_id, None, None)
            for scr_id in score_ids
        }
        with impl.open():
            for record in impl.fetch_region(chrom, start, end, score_ids):
                for scr_id in score_ids:
                    res[scr_id].add_record(record)
        return res

    @ staticmethod
    def _merge_min_max(score_ids, *calculate_tasks):

        res: dict[str, Optional[MinMaxValue]] = {
            score_id: None for score_id in score_ids}
        for score_id in score_ids:
            for min_max_region in calculate_tasks:
                if res[score_id] is None:
                    res[score_id] = min_max_region[score_id]
                else:
                    assert res[score_id] is not None
                    res[score_id].merge(  # type: ignore
                        min_max_region[score_id])
        return res

    @ staticmethod
    def _save_min_max(resource, merged_min_max):
        proto = resource.proto
        for score_id, score_min_max in merged_min_max.items():
            if score_min_max is None:
                logger.warning("Min max for %s is None", score_id)
                continue
            with proto.open_raw_file(
                resource,
                f"{GenomicScoreStatistics.get_statistics_folder()}"
                f"/{GenomicScoreStatistics.get_min_max_file(score_id)}",
                mode="wt"
            ) as outfile:
                outfile.write(score_min_max.serialize())
        return merged_min_max

    def _add_histogram_tasks(
        self, graph, save_minmax_task, region_size, grr=None
    ):
        """
        Add histogram tasks for specific score id.

        The histogram tasks are dependant on the provided minmax task.
        """
        histogram_tasks = []
        regions = self._get_chrom_regions(region_size, grr)
        for chrom, start, end in regions:
            histogram_tasks.append(graph.create_task(
                f"{self.score_id}_calculate_histogram_{chrom}_{start}_{end}",
                GenomicScore._do_histogram,
                [self.resource, chrom, start, end, save_minmax_task],
                [save_minmax_task]
            ))
        merge_task = graph.create_task(
            f"{self.score_id}_merge_histograms",
            GenomicScore._merge_histograms,
            [self.resource, *histogram_tasks],
            histogram_tasks
        )
        save_task = graph.create_task(
            f"{self.score_id}_save_histograms",
            GenomicScore._save_histograms,
            [self.resource, merge_task],
            [merge_task]
        )
        return histogram_tasks, merge_task, save_task

    @ staticmethod
    def _do_histogram(resource, chrom, start, end, save_minmax_task):
        impl = build_score_from_resource(resource)
        hist_configs = list(impl.get_config_histograms().values())
        if not hist_configs:
            return {}
        res = {}
        for hist_config in hist_configs:
            score_id = hist_config["score"]
            if hist_config.get("min") is None:
                hist_config["min"] = save_minmax_task[score_id].min
            if hist_config.get("max") is None:
                hist_config["max"] = save_minmax_task[score_id].max
            try:
                res[score_id] = Histogram(hist_config)
            except ValueError:
                logger.warning("skipping histogram for %s", score_id)
        score_ids = list(res.keys())
        with impl.open():
            for record in impl.fetch_region(chrom, start, end, score_ids):
                for scr_id in score_ids:
                    res[scr_id].add_record(record)
        return res

    @ staticmethod
    def _merge_histograms(resource, *calculated_histograms):
        impl = build_score_from_resource(resource)
        hist_configs = list(impl.get_config_histograms().values())
        if not hist_configs:
            return {}
        res: dict = {}
        for hist_config in hist_configs:
            res[hist_config["score"]] = None
        score_ids = list(res.keys())

        skipped_score_histograms = set()
        for score_id in score_ids:
            for histogram_region in calculated_histograms:
                if score_id not in histogram_region:
                    skipped_score_histograms.add(score_id)
                    continue
                if res[score_id] is None:
                    res[score_id] = histogram_region[score_id]
                else:
                    res[score_id].merge(histogram_region[score_id])
        if skipped_score_histograms:
            logger.warning(
                "skipped merging histograms: %s", skipped_score_histograms)
        return res

    @ staticmethod
    def _save_histograms(resource, merged_histograms):
        proto = resource.proto
        for score_id, score_histogram in merged_histograms.items():
            if score_histogram is None:
                logger.warning("Histogram for %s is None", score_id)
                continue
            with proto.open_raw_file(
                resource,
                f"{GenomicScoreStatistics.get_statistics_folder()}"
                f"/{GenomicScoreStatistics.get_histogram_file(score_id)}",
                mode="wt"
            ) as outfile:
                outfile.write(score_histogram.serialize())

            with proto.open_raw_file(
                resource,
                f"{GenomicScoreStatistics.get_statistics_folder()}/"
                f"{GenomicScoreStatistics.get_histogram_image_file(score_id)}",
                mode="wb"
            ) as outfile:
                score_histogram.plot(outfile)
        return merged_histograms

    def _split_into_regions(self, region_size, reference_genome=None):
        chromosomes = self.get_all_chromosomes()
        for chrom in chromosomes:
            if reference_genome is not None \
                    and chrom in reference_genome.chromosomes:
                chrom_len = reference_genome.get_chrom_length(chrom)
            else:
                if reference_genome is not None:
                    logger.info(
                        "chromosome %s of %s not found in reference genome %s",
                        chrom, self.resource.resource_id,
                        reference_genome.resource_id
                    )
                else:
                    logger.info(
                        "chromosome %s of %s using table, no reference genome",
                        chrom, self.resource.resource_id
                    )
                chrom_len = self.table.get_chromosome_length(chrom)
            logger.debug(
                "Chromosome '%s' has length %s",
                chrom, chrom_len)
            i = 1
            while i < chrom_len - region_size:
                yield chrom, i, i + region_size - 1
                i += region_size
            yield chrom, i, None

    def calc_info_hash(self):
        """Compute and return the info hash."""
        return "infohash"

    def calc_statistics_hash(self) -> bytes:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        manifest = self.resource.get_manifest()
        config = self.get_config()
        score_filename = config["table"]["filename"]
        return json.dumps({
            "config": {
                "scores": config.get("scores", {}),
                "histograms": list(self.get_config_histograms().values()),
                "table": config["table"]
            },
            "score_file": manifest[score_filename].md5
        }, sort_keys=True, indent=2).encode()


@dataclass
class PositionScoreQuery:
    score: str
    position_aggregator: Optional[str] = None


@dataclass
class NPScoreQuery:
    score: str
    position_aggregator: Optional[str] = None
    nucleotide_aggregator: Optional[str] = None


@dataclass
class AlleleScoreQuery:
    score: str
    position_aggregator: Optional[str] = None
    allele_aggregator: Optional[str] = None


@dataclass
class PositionScoreAggr:
    score: str
    position_aggregator: Aggregator


@dataclass
class NPScoreAggr:
    score: str
    position_aggregator: Aggregator
    nucleotide_aggregator: Aggregator


@dataclass
class AlleleScoreAggr:
    score: str
    position_aggregator: Aggregator
    allele_aggregator: Aggregator


ScoreQuery = Union[PositionScoreQuery, NPScoreQuery, AlleleScoreQuery]


class PositionScore(GenomicScore):
    """Defines position genomic score."""

    @ staticmethod
    def get_schema():
        schema = copy.deepcopy(GenomicScore.get_schema())
        scores_schema = schema["scores"]["schema"]["schema"]
        scores_schema["position_aggregator"] = AGGREGATOR_SCHEMA
        return schema

    def open(self) -> PositionScore:
        return cast(PositionScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int,
            scores: Optional[list[str]] = None) -> Optional[list[Any]]:
        """Fetch score values at specific genomic position."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        if len(lines) != 1:
            raise ValueError(
                f"The resource {self.score_id} has "
                f"more than one ({len(lines)}) lines for position "
                f"{chrom}:{position}")
        line = lines[0]

        requested_scores = scores if scores else self.get_all_scores()
        return [line.get_score(scr) for scr in requested_scores]

    def _build_scores_agg(self, scores: list[PositionScoreQuery]):
        score_aggs = []
        for score in scores:
            if score.position_aggregator is not None:
                aggregator_type = score.position_aggregator
            else:
                aggregator_type = \
                    self.score_definitions[score.score].pos_aggregator

            score_aggs.append(
                PositionScoreAggr(
                    score.score,
                    build_aggregator(aggregator_type)))
        return score_aggs

    def fetch_scores_agg(  # pylint: disable=too-many-arguments,too-many-locals
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: Optional[list[PositionScoreQuery]] = None
    ) -> list[Aggregator]:
        """Fetch score values in a region and aggregates them.

        Case 1:
           res.fetch_scores_agg("1", 10, 20) -->
              all score with default aggregators
        Case 2:
           res.fetch_scores_agg("1", 10, 20,
                                non_default_aggregators={"bla":"max"}) -->
              all score with default aggregators but 'bla' should use 'max'
        """
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")
        if scores is None:
            scores = [
                PositionScoreQuery(score_id)
                for score_id in self.get_all_scores()]

        score_aggs = self._build_scores_agg(scores)

        for line in self._fetch_lines(chrom, pos_begin, pos_end):
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)
            for sagg in score_aggs:
                val = line.get_score(sagg.score)

                left = (
                    pos_begin
                    if pos_begin >= line_pos_begin
                    else line_pos_begin
                )
                right = (
                    pos_end
                    if pos_end <= line_pos_end
                    else line_pos_end
                )
                for _ in range(left, right + 1):
                    sagg.position_aggregator.add(val)

        return [squery.position_aggregator for squery in score_aggs]


class NPScore(GenomicScore):
    """Defines nucleotide-position genomic score."""

    @ staticmethod
    def get_schema():
        schema = copy.deepcopy(GenomicScore.get_schema())
        schema["table"]["schema"]["reference"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"}
            }
        }
        schema["table"]["schema"]["alternative"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"}
            }
        }

        scores_schema = schema["scores"]["schema"]["schema"]
        scores_schema["position_aggregator"] = AGGREGATOR_SCHEMA
        scores_schema["nucleotide_aggregator"] = AGGREGATOR_SCHEMA
        return schema

    def open(self) -> NPScore:
        return cast(NPScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: Optional[list[str]] = None) -> Optional[list[Any]]:
        """Fetch score values at specified genomic position and nucleotide."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        selected_line = None
        for line in lines:
            if line.ref == reference and line.alt == alternative:
                selected_line = line
                break

        if not selected_line:
            return None
        requested_scores = scores if scores else self.get_all_scores()
        return [selected_line.get_score(sc) for sc in requested_scores]

    def _build_scores_agg(
            self, score_queries: list[NPScoreQuery]) -> list[NPScoreAggr]:
        score_aggs = []
        for squery in score_queries:
            scr_def = self.score_definitions[squery.score]
            if squery.position_aggregator is not None:
                aggregator_type = squery.position_aggregator
            else:
                aggregator_type = scr_def.pos_aggregator
            position_aggregator = build_aggregator(aggregator_type)

            if squery.nucleotide_aggregator is not None:
                aggregator_type = squery.nucleotide_aggregator
            else:
                aggregator_type = scr_def.nuc_aggregator
            nucleotide_aggregator = build_aggregator(aggregator_type)
            score_aggs.append(
                NPScoreAggr(
                    squery.score, position_aggregator, nucleotide_aggregator))
        return score_aggs

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: Optional[list[NPScoreQuery]] = None
    ) -> list[Aggregator]:
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        # FIXME:
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id}")

        if scores is None:
            scores = [
                NPScoreQuery(score_id)
                for score_id in self.get_all_scores()]

        score_aggs = self._build_scores_agg(scores)

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return [sagg.position_aggregator for sagg in score_aggs]

        def aggregate_nucleotides():
            for sagg in score_aggs:
                sagg.position_aggregator.add(
                    sagg.nucleotide_aggregator.get_final())
                sagg.nucleotide_aggregator.clear()

        last_pos: int = score_lines[0].pos_begin
        for line in score_lines:
            if line.pos_begin != last_pos:
                aggregate_nucleotides()

            for sagg in score_aggs:
                val = line.get_score(sagg.score)
                left = (
                    pos_begin
                    if pos_begin >= line.pos_begin
                    else line.pos_begin
                )
                right = (
                    pos_end
                    if pos_end <= line.pos_end
                    else line.pos_end
                )
                for _ in range(left, right + 1):
                    sagg.nucleotide_aggregator.add(val)
            last_pos = line.pos_begin
        aggregate_nucleotides()

        return [sagg.position_aggregator for sagg in score_aggs]


class AlleleScore(GenomicScore):
    """Defines allele genomic scores."""

    @ staticmethod
    def get_schema():
        schema = copy.deepcopy(GenomicScore.get_schema())
        schema["table"]["schema"]["reference"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"}
            }
        }
        schema["table"]["schema"]["alternative"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"}
            }
        }
        schema["table"]["schema"]["variant"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"}
            }
        }
        return schema

    def open(self) -> AlleleScore:
        return cast(AlleleScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: Optional[list[str]] = None) -> Optional[list[Any]]:
        """Fetch scores values for specific allele."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"Allele Score resource {self.score_id}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        selected_line = None
        for line in lines:
            if line.ref == reference and line.alt == alternative:
                selected_line = line
                break

        if selected_line is None:
            return None

        requested_scores = scores if scores else self.get_all_scores()
        return [
            selected_line.get_score(sc)
            for sc in requested_scores]

    def _build_scores_agg(
        self, score_queries: list[AlleleScoreQuery]
    ) -> list[AlleleScoreAggr]:
        score_aggs = []
        for squery in score_queries:
            scr_def = self.score_definitions[squery.score]
            if squery.position_aggregator is not None:
                aggregator_type = squery.position_aggregator
            else:
                aggregator_type = scr_def.pos_aggregator
            position_aggregator = build_aggregator(aggregator_type)

            if squery.allele_aggregator is not None:
                aggregator_type = squery.allele_aggregator
            else:
                aggregator_type = scr_def.allele_aggregator
            allele_aggregator = build_aggregator(aggregator_type)
            score_aggs.append(
                AlleleScoreAggr(
                    squery.score, position_aggregator, allele_aggregator))
        return score_aggs

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: Optional[list[AlleleScoreQuery]] = None
    ) -> list[Aggregator]:
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        # FIXME:
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id}")

        if scores is None:
            scores = [
                AlleleScoreQuery(score_id)
                for score_id in self.get_all_scores()]

        score_aggs = self._build_scores_agg(scores)

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return [sagg.position_aggregator for sagg in score_aggs]

        def aggregate_alleles():
            for sagg in score_aggs:
                sagg.position_aggregator.add(
                    sagg.allele_aggregator.get_final())
                sagg.allele_aggregator.clear()

        last_pos: int = score_lines[0].pos_begin
        for line in score_lines:
            if line.pos_begin != last_pos:
                aggregate_alleles()

            for sagg in score_aggs:
                val = line.get_score(sagg.score)
                left = (
                    pos_begin
                    if pos_begin >= line.pos_begin
                    else line.pos_begin
                )
                right = (
                    pos_end
                    if pos_end <= line.pos_end
                    else line.pos_end
                )
                for _ in range(left, right + 1):
                    sagg.allele_aggregator.add(val)
            last_pos = line.pos_begin
        aggregate_alleles()

        return [sagg.position_aggregator for sagg in score_aggs]


def _build_genomic_score_from_resource(
        clazz: Type[GenomicScore],
        resource: GenomicResource) -> GenomicScore:
    return clazz(resource)


def build_position_score_from_resource(
        resource: GenomicResource) -> PositionScore:
    """Build a position score genomic resource and returns a position score."""
    result = _build_genomic_score_from_resource(
        PositionScore,
        resource)
    return cast(PositionScore, result)


def build_np_score_from_resource(
        resource: GenomicResource) -> NPScore:
    """Build a NP-score genomic resource and returns a NP-score."""
    result = _build_genomic_score_from_resource(
        NPScore,
        resource)
    return cast(NPScore, result)


def build_allele_score_from_resource(
        resource: GenomicResource) -> AlleleScore:
    """Build a allele score genomic resource and returns an allele score."""
    result = _build_genomic_score_from_resource(
        AlleleScore,
        resource)
    return cast(AlleleScore, result)


def build_score_from_resource(resource: GenomicResource) -> GenomicScore:
    """Build a genomic score resource and return the coresponding score."""
    type_to_ctor = {
        "position_score": build_position_score_from_resource,
        "np_score": build_np_score_from_resource,
        "allele_score": build_allele_score_from_resource,
    }
    ctor = type_to_ctor.get(resource.get_type())
    if ctor is None:
        raise ValueError(f"Resource {resource.get_id()} is not of score type")
    return ctor(resource)
