# pylint: disable=too-many-lines
from __future__ import annotations

import os
import logging
import textwrap
import copy
import json

from typing import Iterator, Optional, cast, Type, Any, Union

from dataclasses import dataclass

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

from .aggregators import build_aggregator, AGGREGATOR_SCHEMA


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
        min_maxes = {}
        histograms = {}
        config = genomic_resource.get_config()
        if "histograms" not in config:
            return GenomicScoreStatistics(genomic_resource, {}, {})
        try:
            for hist_config in config["histograms"]:
                score_id = hist_config["score"]
                min_max_filepath = os.path.join(
                    GenomicScoreStatistics.get_statistics_folder(),
                    GenomicScoreStatistics.get_min_max_file(score_id)
                )
                with genomic_resource.open_raw_file(
                        min_max_filepath, mode="r") as infile:
                    min_max = MinMaxValue.deserialize(infile.read())
                    min_maxes[score_id] = min_max

                histogram_filepath = os.path.join(
                    GenomicScoreStatistics.get_statistics_folder(),
                    GenomicScoreStatistics.get_histogram_file(score_id)
                )
                with genomic_resource.open_raw_file(
                        histogram_filepath, mode="r") as infile:
                    histogram = Histogram.deserialize(infile.read())
                    histograms[score_id] = histogram
        except FileNotFoundError:
            logger.exception(
                "Couldn't load statistics of %s", genomic_resource.resource_id
            )
            return GenomicScoreStatistics(genomic_resource, {}, {})
        return GenomicScoreStatistics(genomic_resource, min_maxes, histograms)


class GenomicScore(
    GenomicResourceImplementation,
    ResourceConfigValidationMixin,
    InfoImplementationMixin
):
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
                tuple(), None, None
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

    def get_resource_id(self):
        return self.config["id"]

    def _fetch_lines(
        self, chrom: str, pos_begin: int, pos_end: int
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
        self, chrom: str, pos_begin: int, pos_end: int, scores: list[str]
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
            <hr>
            <h3>Score file:</h3>
            <a href="{{ data["table"]["filename"] }}">
            {{ data["table"]["filename"] }}
            </a>
            <p>
            File format: {{ data["table"]["format"] }}
            </p>

            {%- if data["table"]["chrom"] -%}
            {%- if data["table"]["chrom"]["index"] is not none -%}
            <p>
            chrom column index in file:
            {{ data["table"]["chrom"]["index"] }}
            </p>
            {%- endif %}
            {%- if data["table"]["chrom"]["name"] -%}
            <p>
            chrom column name in header:
            {{ data["table"]["chrom"]["name"] }}
            </p>
            {%- endif -%}
            {%- endif %}

            {%- if data["table"]["pos_begin"] -%}
            {%- if data["table"]["pos_begin"]["index"] is not none -%}
            <p>
            pos_begin column index in file:
            {{ data["table"]["pos_begin"]["index"] }}
            </p>
            {%- endif %}
            {%- if data["table"]["pos_begin"]["name"] -%}
            <p>
            pos_begin column name in header:
            {{ data["table"]["pos_begin"]["name"] }}
            </p>
            {%- endif -%}
            {%- endif %}

            {%- if data["table"]["pos_end"] -%}
            {%- if data["table"]["pos_end"]["index"] is not none -%}
            <p>
            pos_end column index in file:
            {{ data["table"]["pos_end"]["index"] }}
            </p>
            {%- endif %}
            {%- if data["table"]["pos_end"]["name"] -%}
            <p>
            pos_end column name in header:
            {{ data["table"]["pos_end"]["name"] }}
            </p>
            {%- endif -%}
            {%- endif %}

            {%- if data["table"]["reference"] -%}
            {%- if data["table"]["reference"]["index"] is not none -%}
            <p>
            reference column index in file:
            {{ data["table"]["reference"]["index"] }}
            </p>
            {%- endif -%}
            {%- if data["table"]["reference"]["name"] -%}
            <p>
            reference column name in header:
            {{ data["table"]["reference"]["name"] }}
            </p>
            {%- endif -%}
            {%- endif %}

            {%- if data["table"]["alternative"] -%}
            {%- if data["table"]["alternative"]["index"] is not none -%}
            <p>
            alternative column index in file:
            {{ data["table"]["alternative"]["index"] }}
            </p>
            {%- endif -%}
            {%- if data["table"]["alternative"]["name"] -%}
            <p>
            alternative column name in header:
            {{ data["table"]["alternative"]["name"] }}
            </p>
            {%- endif -%}
            {%- endif %}

            <h3>Score definitions:</h3>
            {%- for score in data["scores"] -%}
            <div class="score-definition">
            <p>Score ID: {{ score["id"] }}</p>
            {%- if "index" in score -%}
            <p>Column index in file: {{ score["index"] }}</p>
            {%- elif "name" in score -%}
            <p>Column name in file header: {{ score["name"] }}
            {%- endif -%}
            {%- if "destination" in score -%}
            <p>Annotation destination: {{ score["destination"] }}
            {%- endif -%}
            <p>Score data type: {{ score["type"] }}
            <p> Description: {{ score["desc"] }}
            </div>
            {%- endfor %}

            <h3>Min max values:</h3>
            {%- for min_max in data["min_max"] %}
            <div class="minmax">
            <h4>{{ min_max["score_id"] }}</h4>
            <p>Min: {{ min_max["min"] }}</p>
            <p>Max: {{ min_max["max"] }}</p>
            </div>
            {%- endfor %}

            <h3>Histograms:</h3>
            {% for hist in data["histograms"] %}
            <div class="histogram">
            <h4>{{ hist["score"] }}</h4>
            <img src="{{ data["statistics_dir"] }}/{{ hist["img_file"] }}"
            alt={{ hist["score"] }}
            title={{ hist["score"] }}>
            </div>
            {% endfor %}

            {% endblock %}
        """))

    def _get_template_data(self):
        info = copy.deepcopy(self.config)

        statistics = self.get_statistics()

        info["statistics_dir"] = statistics.get_statistics_folder()

        if "histograms" in info:
            for hist_config in info["histograms"]:
                hist_config["img_file"] = statistics.get_histogram_image_file(
                    hist_config["score"]
                )

        if "scores" in info:
            for score_config in info["scores"]:
                score_id = score_config["id"]
                default_annotation = self.get_default_annotation()
                for annotation_definition in default_annotation["attributes"]:
                    if annotation_definition["source"] == score_id:
                        score_config["destination"] = \
                            annotation_definition["destination"]

        info["min_max"] = []
        for score_id, min_max in statistics.score_min_maxes.items():
            info["min_max"].append({
                "score_id": score_id,
                "min": min_max.min,
                "max": min_max.max
            })

        return info

    def get_info(self):
        return InfoImplementationMixin.get_info(self)

    @staticmethod
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

    @staticmethod
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
        ref_genome_id = self.get_label("reference_genome")
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
        score_ids = self.get_all_scores()
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

    @staticmethod
    def _do_min_max(resource, chrom, start, end):
        impl = build_score_from_resource(resource)
        score_ids = impl.get_all_scores()
        res = {
            scr_id: MinMaxValue(scr_id, None, None)
            for scr_id in score_ids
        }
        with impl.open():
            for record in impl.fetch_region(chrom, start, end, score_ids):
                for scr_id in score_ids:
                    res[scr_id].add_record(record)
        return res

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _do_histogram(resource, chrom, start, end, save_minmax_task):
        impl = build_score_from_resource(resource)
        if "histograms" not in impl.get_config():
            return {}
        hist_configs = impl.get_config()["histograms"]
        res = {}
        for hist_config in hist_configs:
            score_id = hist_config["score"]
            if hist_config.get("min") is None:
                hist_config["min"] = save_minmax_task[score_id].min
            if hist_config.get("max") is None:
                hist_config["max"] = save_minmax_task[score_id].max
            res[score_id] = Histogram(hist_config)
        score_ids = list(res.keys())
        with impl.open():
            for record in impl.fetch_region(chrom, start, end, score_ids):
                for scr_id in score_ids:
                    res[scr_id].add_record(record)
        return res

    @staticmethod
    def _merge_histograms(resource, *calculated_histograms):
        if "histograms" not in resource.config:
            return {}
        hist_configs = resource.config["histograms"]
        res: dict = {}
        for hist_config in hist_configs:
            res[hist_config["score"]] = None
        score_ids = list(res.keys())

        for score_id in score_ids:
            for histogram_region in calculated_histograms:
                if res[score_id] is None:
                    res[score_id] = histogram_region[score_id]
                else:
                    res[score_id].merge(histogram_region[score_id])
        return res

    @staticmethod
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
                "histograms": config.get("histograms", {}),
                "table": config["table"]
            },
            "score_file": manifest[score_filename].md5
        }, sort_keys=True, indent=2).encode()


class PositionScore(GenomicScore):
    """Defines position genomic score."""

    @staticmethod
    def get_schema():
        schema = copy.deepcopy(GenomicScore.get_schema())
        scores_schema = schema["scores"]["schema"]["schema"]
        scores_schema["position_aggregator"] = AGGREGATOR_SCHEMA
        return schema

    def open(self) -> PositionScore:
        return cast(PositionScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int,
            scores: Optional[list[str]] = None):
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
        return {scr: line.get_score(scr) for scr in requested_scores}

    def fetch_scores_agg(  # pylint: disable=too-many-arguments,too-many-locals
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: Optional[list[str]] = None,
            non_default_pos_aggregators=None):
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

        requested_scores = scores if scores else self.get_all_scores()
        aggregators = {}
        if non_default_pos_aggregators is None:
            non_default_pos_aggregators = {}

        for scr_id in requested_scores:
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, self.score_definitions[scr_id].pos_aggregator)
            aggregators[scr_id] = build_aggregator(aggregator_type)

        for line in self._fetch_lines(chrom, pos_begin, pos_end):
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)

            for scr_id, aggregator in aggregators.items():
                val = line.get_score(scr_id)

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
                    aggregator.add(val)

        return aggregators


class NPScore(GenomicScore):
    """Defines nucleotide-position genomic score."""

    @staticmethod
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
            scores: Optional[list[str]] = None):
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
        return {
            sc: selected_line.get_score(sc) for sc in requested_scores
        }

    def _construct_aggregators(
            self, scores,
            non_default_pos_aggregators, non_default_nuc_aggregators):

        if non_default_pos_aggregators is None:
            non_default_pos_aggregators = {}
        if non_default_nuc_aggregators is None:
            non_default_nuc_aggregators = {}
        pos_aggregators = {}
        nuc_aggregators = {}

        for scr_id in scores:
            scr_def = self.score_definitions[scr_id]
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, scr_def.pos_aggregator)
            pos_aggregators[scr_id] = build_aggregator(aggregator_type)

            aggregator_type = non_default_nuc_aggregators.get(
                scr_id, scr_def.nuc_aggregator)
            nuc_aggregators[scr_id] = build_aggregator(aggregator_type)
        return pos_aggregators, nuc_aggregators

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: Optional[list[str]] = None,
            non_default_pos_aggregators=None,
            non_default_nuc_aggregators=None):
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        # FIXME:
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id}")

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return None

        scores = scores if scores else self.get_all_scores()
        pos_aggregators, nuc_aggregators = self._construct_aggregators(
            scores, non_default_pos_aggregators, non_default_nuc_aggregators
        )

        def aggregate_nucleotides():
            for col, nuc_agg in nuc_aggregators.items():
                pos_aggregators[col].add(nuc_agg.get_final())
                nuc_agg.clear()

        last_pos: int = score_lines[0].pos_begin
        for line in score_lines:
            if line.pos_begin != last_pos:
                aggregate_nucleotides()
            for col in line.get_available_scores():
                val = line.get_score(col)

                if col not in nuc_aggregators:
                    continue
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
                    nuc_aggregators[col].add(val)
            last_pos = line.pos_begin
        aggregate_nucleotides()

        return pos_aggregators


class AlleleScore(GenomicScore):
    """Defines allele genomic scores."""

    @staticmethod
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
            scores: Optional[list[str]] = None):
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
        return {
            sc: selected_line.get_score(sc)
            for sc in requested_scores}


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
