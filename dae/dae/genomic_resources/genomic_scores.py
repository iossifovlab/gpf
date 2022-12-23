"""Genomic scores resources."""

from __future__ import annotations

import logging
import textwrap
import copy

from typing import Iterator, List, cast, Type, Dict, Any, Union

from dataclasses import dataclass
from jinja2 import Template
from markdown2 import markdown
from cerberus import Validator

from . import GenomicResource
from .resource_implementation import GenomicResourceImplementation, \
    get_base_resource_schema
from .genomic_position_table import build_genomic_position_table, Line, \
    VCFGenomicPositionTable

from .aggregators import build_aggregator, AGGREGATOR_SCHEMA


logger = logging.getLogger(__name__)

ScoreValue = Union[str, int, float, bool, None]

VCF_TYPE_CONVERSION_MAP = {
    "Integer": "int",
    "Float": "float",
    "String": "str",
    "Flag": "bool",
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
        assert isinstance(line, Line)
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
                value = col_def.value_parser(value)
        return value

    def get_available_scores(self):
        return tuple(self.score_defs.keys())


class GenomicScore(GenomicResourceImplementation):
    """Genomic scores base class."""

    config_validator = Validator
    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def __init__(self, resource):
        super().__init__(resource)
        self.config["id"] = resource.resource_id
        self.table_loaded = False
        self.table = build_genomic_position_table(
            self.resource, self.config["table"]
        )
        self.score_definitions = self._generate_scoredefs()

    @staticmethod
    def _parse_scoredef_config(config):
        """Parse ScoreDef configuration."""
        scores = {}
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
        for score_conf in config["scores"]:
            col_type = score_conf.get(
                "type", config.get("default.score.type", "float"))

            col_key = score_conf.get("name") or str(score_conf["index"])

            col_def = ScoreDef(
                col_key,
                score_conf.get("desc", ""),
                col_type,
                type_parsers[col_type],
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
        if "scores" in self.config:
            return GenomicScore._parse_scoredef_config(self.config)
        if isinstance(self.table, VCFGenomicPositionTable):
            return GenomicScore._get_vcf_scoredefs(self.table.header)
        raise ValueError("No scores configured and not using a VCF")

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
                for score in self.score_definitions]
        }

    def get_score_config(self, score_id):
        return self.score_definitions.get(score_id)

    def close(self):
        # FIXME: consider using weekrefs
        # self.table.close()
        # self.table = None
        pass

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
        return self.table.get_column_names()

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
            raise ValueError(f"genomic score <{self.score_id()}> is not open")

        return self.table.get_chromosomes()

    def get_all_scores(self):
        return list(self.score_definitions)

    def fetch_region(
        self, chrom: str, pos_begin: int, pos_end: int, scores: List[str]
    ) -> Iterator[dict[str, ScoreValue]]:
        """Return score values in a region."""
        if not self.is_open():
            raise ValueError(f"genomic score <{self.score_id()}> is not open")

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        for line in self._fetch_lines(chrom, pos_begin, pos_end):
            line_pos_begin, line_pos_end = self._line_to_begin_end(line)

            val = {}
            for scr_id in scores:
                val[scr_id] = line.get_score(scr_id)

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
            {% for score in data["table"]["scores"] %}
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
        return {scr: line.get_score(scr) for scr in requested_scores}

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
