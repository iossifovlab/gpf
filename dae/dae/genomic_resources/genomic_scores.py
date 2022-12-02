"""Genomic scores resources."""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass
import copy

from typing import Generator, List, Tuple, cast, Type, Dict, Any, Optional, \
    Union

from jinja2 import Template
from markdown2 import markdown
from cerberus import Validator

from . import GenomicResource
from .resource_implementation import GenomicResourceImplementation, \
    get_base_resource_schema
from .genome_position_table import open_genome_position_table

from .aggregators import build_aggregator, AGGREGATOR_SCHEMA


logger = logging.getLogger(__name__)

ScoreValue = Union[str, int, float, bool, None]


class ScoreLine:
    """Provides and abstraction for a genomic score line."""

    def __init__(self, values: Tuple[str], scores: dict,
                 special_columns: dict):
        self.values = values
        self.score_columns = scores
        self.special_columns = special_columns

    def get_score_value(self, score_id):
        scr_def = self.score_columns[score_id]

        str_value = self.values[scr_def.col_index]
        if str_value in scr_def.na_values:
            return None
        return scr_def.value_parser(str_value)

    def get_special_column_value(self, col_id):
        clmn_def = self.special_columns[col_id]

        str_value = self.values[clmn_def.col_index]
        return clmn_def.value_parser(str_value)

    def get_chrom(self):
        return self.get_special_column_value("chrom")

    def get_pos_begin(self):
        return self.get_special_column_value("pos_begin")

    def get_pos_end(self):
        return self.get_special_column_value("pos_end")

    def __repr__(self):
        return f"ScoreLine({self.values})"


@dataclass
class ScoreDef:
    """Score configuration definition."""

    # pylint: disable=too-many-instance-attributes
    score_id: str
    desc: str
    col_index: Optional[int]
    type: str
    value_parser: Any
    na_values: Any
    pos_aggregator: Any
    nuc_aggregator: Any
    # description: str


class GenomicScore(GenomicResourceImplementation):
    """Genomic scores base class."""

    config_validator = Validator

    def __init__(self, resource):
        super().__init__(resource)
        self.config["id"] = resource.resource_id
        self.score_columns = self._configure_score_columns(self.config)
        self.special_columns = _configure_special_columns(
            extra_special_columns=self.get_extra_special_columns())

        self.table = None

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    @staticmethod
    def _configure_score_columns(config):
        """Parse score configuration."""
        scores = {}
        for score_conf in config["scores"]:
            scr_type = score_conf.get(
                "type", config.get("default.score.type", "float"))

            type_parsers = {
                "str": str,
                "float": float,
                "int": int
            }
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

            scr_def = ScoreDef(
                score_conf["id"],
                score_conf.get("desc", ""),
                None,  # col_index,
                scr_type,
                type_parsers[scr_type],
                score_conf.get(
                    "na_values",
                    config.get(
                        f"default_na_values.{scr_type}",
                        default_na_values[scr_type])),
                score_conf.get(
                    "position_aggregator",
                    config.get(
                        f"{scr_type}.aggregator",
                        default_type_pos_aggregators[scr_type])),
                score_conf.get(
                    "nucleotide_aggregator",
                    config.get(
                        f"{scr_type}.aggregator",
                        default_type_nuc_aggregators[scr_type])),
                # score_conf.get("description", None)
            )
            scores[scr_def.score_id] = scr_def

        return scores

    def get_config(self):
        return self.config

    def score_id(self):
        return self.get_config().get("id")

    def get_default_annotation(self) -> Dict[str, Any]:
        if "default_annotation" in self.get_config():
            return cast(
                Dict[str, Any], self.get_config()["default_annotation"])
        return {
            "attributes": [
                {"source": score, "destination": score}
                for score in self.score_columns]
        }

    @staticmethod
    def get_extra_special_columns():
        return None

    def get_score_config(self, score_id):
        return self.score_columns.get(score_id)

    def close(self):
        # FIXME: consider using weekrefs
        # self.table.close()
        # self.table = None
        pass

    def is_open(self):
        return self.table is not None

    def open(self) -> GenomicScore:
        """Open genomic score resource and returns it."""
        if self.is_open():
            logger.info(
                "opening already opened genomic score: %s",
                self.resource.resource_id)
            return self

        self.table = open_genome_position_table(
            self.resource,
            self.config["table"])
        self._configure_score_columns_indices()
        self._configure_special_columns_indices()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            logger.error(
                "exception while working with genomic score: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        self.close()

    def _configure_score_columns_indices(self):
        for score_conf in self.config["scores"]:
            if "index" in score_conf:
                col_index = int(score_conf["index"])
            elif "name" in score_conf:
                col_index = self.table.get_column_names().index(
                    score_conf["name"])
            else:
                raise ValueError(
                    "The score configuration must have a column specified")

            score_def = self.score_columns[score_conf["id"]]
            score_def.col_index = col_index

    def _configure_special_columns_indices(self):
        for key, spec_def in self.special_columns.items():
            col_index = self.table.get_special_column_index(key)
            spec_def.col_index = col_index

    @staticmethod
    def _line_to_begin_end(line):
        begin = line.get_pos_begin()
        end = line.get_pos_end()
        if end < begin:
            raise IOError(
                f"The resource line {line.values} has a regions "
                f" with end {end} smaller that the "
                f"begining {end}.")
        return begin, end

    def _get_header(self):
        return self.table.get_column_names()

    def get_resource_id(self):
        return self.config["id"]

    def _fetch_lines(
            self, chrom: str,
            pos_begin: int, pos_end: int) -> Generator[ScoreLine, None, None]:
        records = self.table.get_records_in_region(
            chrom, pos_begin, pos_end)

        for record in records:
            yield ScoreLine(record, self.score_columns, self.special_columns)

    def get_all_chromosomes(self):
        if not self.is_open():
            raise ValueError(f"genomic score <{self.score_id()}> is not open")

        return self.table.get_chromosomes()

    def get_all_scores(self):
        return list(self.score_columns)

    def fetch_region(self, chrom: str, pos_begin: int, pos_end: int,
                     scores: List[str]) \
            -> Generator[dict[str, ScoreValue], None, None]:
        """Return score values in a region."""
        if not self.is_open():
            raise ValueError(f"genomic score <{self.score_id()}> is not open")

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        line_iter = self._fetch_lines(chrom, pos_begin, pos_end)
        for line in line_iter:
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)

            val = {}
            for scr_id in scores:
                val[scr_id] = line.get_score_value(scr_id)

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

    @staticmethod
    def get_template():
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

            {% if data["table"]["chrom"] %}
            {% if data["table"]["chrom"]["index"] is not none %}
            <p>
            chrom column index in file:
            {{ data["table"]["chrom"]["index"] }}
            </p>
            {% endif %}
            {% if data["table"]["chrom"]["name"] %}
            <p>
            chrom column name in header:
            {{ data["table"]["chrom"]["name"] }}
            </p>
            {% endif %}
            {% endif %}

            {% if data["table"]["pos_begin"] %}
            {% if data["table"]["pos_begin"]["index"] is not none %}
            <p>
            pos_begin column index in file:
            {{ data["table"]["pos_begin"]["index"] }}
            </p>
            {% endif %}
            {% if data["table"]["pos_begin"]["name"] %}
            <p>
            pos_begin column name in header:
            {{ data["table"]["pos_begin"]["name"] }}
            </p>
            {% endif %}
            {% endif %}

            {% if data["table"]["pos_end"] %}
            {% if data["table"]["pos_end"]["index"] is not none %}
            <p>
            pos_end column index in file:
            {{ data["table"]["pos_end"]["index"] }}
            </p>
            {% endif %}
            {% if data["table"]["pos_end"]["name"] %}
            <p>
            pos_end column name in header:
            {{ data["table"]["pos_end"]["name"] }}
            </p>
            {% endif %}
            {% endif %}

            {% if data["table"]["reference"] %}
            {% if data["table"]["reference"]["index"] is not none %}
            <p>
            reference column index in file:
            {{ data["table"]["reference"]["index"] }}
            </p>
            {% endif %}
            {% if data["table"]["reference"]["name"] %}
            <p>
            reference column name in header:
            {{ data["table"]["reference"]["name"] }}
            </p>
            {% endif %}
            {% endif %}

            {% if data["table"]["alternative"] %}
            {% if data["table"]["alternative"]["index"] is not none %}
            <p>
            alternative column index in file:
            {{ data["table"]["alternative"]["index"] }}
            </p>
            {% endif %}
            {% if data["table"]["alternative"]["name"] %}
            <p>
            alternative column name in header:
            {{ data["table"]["alternative"]["name"] }}
            </p>
            {% endif %}
            {% endif %}

            <h3>Score definitions:</h3>
            {% for score in data["scores"] %}
            <div class="score-definition">
            <p>Score ID: {{ score["id"] }}</p>
            {% if "index" in score %}
            <p>Column index in file: {{ score["index"] }}</p>
            {% elif "name" in score %}
            <p>Column name in file header: {{ score["name"] }}
            {% endif %}
            <p>Score data type: {{ score["type"] }}
            <p> Description: {{ score["desc"] }}
            </div>
            {% endfor %}
            <h3>Histograms:</h3>
            {% for hist in data["histograms"] %}
            <div class="histogram">
            <h4>{{ hist["score"] }}</h4>
            <img src="histograms/{{ hist["score"] }}.png"
            alt={{ hist["score"] }}
            title={{ hist["score"] }}>
            </div>
            {% endfor %}
            {% endblock %}
        """))

    def get_info(self):
        info = copy.deepcopy(self.config)
        if "meta" in info:
            info["meta"] = markdown(info["meta"])
        return info

    @staticmethod
    def get_schema():
        return {
            **get_base_resource_schema(),
            "table": {"type": "dict", "schema": {
                "filename": {"type": "string"},
                "format": {"type": "string"},
                "header_mode": {"type": "string"},
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
            "scores": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "type": {"type": "string"},
                    "desc": {"type": "string"},
                    "na_values": {"type": "string"}
                }
            }},
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
            self, chrom: str, position: int, scores: List[str] = None):
        """Fetch score values at specific genomic position."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        if len(lines) != 1:
            raise ValueError(
                f"The resource {self.score_id()} has "
                f"more than one ({len(lines)}) lines for position "
                f"{chrom}:{position}")
        line = lines[0]

        requested_scores = scores if scores else self.get_all_scores()
        return {scr: line.get_score_value(scr) for scr in requested_scores}

    def fetch_scores_agg(  # pylint: disable=too-many-arguments,too-many-locals
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: List[str] = None, non_default_pos_aggregators=None):
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
                scr_id, self.score_columns[scr_id].pos_aggregator)
            aggregators[scr_id] = build_aggregator(aggregator_type)

        for line in self._fetch_lines(chrom, pos_begin, pos_end):
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)

            for scr_id, aggregator in aggregators.items():
                val = line.get_score_value(scr_id)

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

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):
        """Fetch score values at specified genomic position and nucleotide."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id()}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        selected_line = None
        for line in lines:
            if line.get_special_column_value("reference") == reference \
                    and line.get_special_column_value("alternative") \
                    == alternative:
                selected_line = line
                break

        if not selected_line:
            return None
        requested_scores = scores if scores else self.get_all_scores()
        return {
            sc: selected_line.get_score_value(sc)
            for sc in requested_scores
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
            scr_def = self.score_columns[scr_id]
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, scr_def.pos_aggregator)
            pos_aggregators[scr_id] = build_aggregator(aggregator_type)

            aggregator_type = non_default_nuc_aggregators.get(
                scr_id, scr_def.nuc_aggregator)
            nuc_aggregators[scr_id] = build_aggregator(aggregator_type)
        return pos_aggregators, nuc_aggregators

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: List[str] = None,
            non_default_pos_aggregators=None,
            non_default_nuc_aggregators=None):
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        # FIXME:
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id()}")

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

        last_pos: int = score_lines[0].get_pos_begin()
        for line in score_lines:
            if line.get_pos_begin() != last_pos:
                aggregate_nucleotides()
            for col in line.score_columns:
                val = line.get_score_value(col)

                if col not in nuc_aggregators:
                    continue
                left = (
                    pos_begin
                    if pos_begin >= line.get_pos_begin()
                    else line.get_pos_begin()
                )
                right = (
                    pos_end
                    if pos_end <= line.get_pos_end()
                    else line.get_pos_end()
                )
                for _ in range(left, right + 1):
                    nuc_aggregators[col].add(val)
            last_pos = line.get_pos_begin()
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
        return schema

    def open(self) -> AlleleScore:
        return cast(AlleleScore, super().open())

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end", "variant")

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):
        """Fetch scores values for specific allele."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"Allele Score resource {self.score_id()}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        selected_line = None
        for line in lines:
            if line.get_special_column_value("reference") == reference and \
                    line.get_special_column_value("alternative") \
                    == alternative:
                selected_line = line
                break

        if selected_line is None:
            return None

        requested_scores = scores if scores else self.get_all_scores()
        return {
            sc: selected_line.get_score_value(sc)
            for sc in requested_scores}


def _configure_special_columns(
        # table,
        extra_special_columns=None):
    special_clmns = {"chrom": str, "pos_begin": int, "pos_end": int}
    if extra_special_columns is not None:
        special_clmns.update(extra_special_columns)

    special_columns = {}
    for key, parser in special_clmns.items():

        @dataclass
        class SpecialDef:
            """Score special columns definition."""

            key: str
            col_index: int
            value_parser: Any

        spec_def = SpecialDef(
            key,
            None,  # table.get_special_column_index(key),
            parser)
        special_columns[key] = spec_def

    return special_columns


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
