# pylint: disable=too-many-lines
from __future__ import annotations

import copy
import logging
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import lru_cache
from types import TracebackType
from typing import (
    Any,
    cast,
)
from urllib.parse import quote

from dae.genomic_resources.genomic_position_table import (
    Line,
    VCFGenomicPositionTable,
    VCFLine,
    build_genomic_position_table,
)
from dae.genomic_resources.genomic_position_table.line import LineBase
from dae.genomic_resources.histogram import (
    Histogram,
    HistogramConfig,
    NumberHistogram,
    build_histogram_config,
    load_histogram,
)
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)

from .aggregators import AGGREGATOR_SCHEMA, Aggregator, build_aggregator

logger = logging.getLogger(__name__)

ScoreValue = str | int | float | bool | None

VCF_TYPE_CONVERSION_MAP = {
    "Integer": "int",
    "Float": "float",
    "String": "str",
    "Flag": "bool",
}

SCORE_TYPE_PARSERS = {
    "str": str,
    "float": float,
    "int": int,
}


@dataclass
class ScoreDef:
    """Score configuration definition."""

    # pylint: disable=too-many-instance-attributes
    score_id: str
    desc: str  # string that will be interpretted as md
    value_type: str  # "str", "int", "float"
    pos_aggregator: str | None     # a valid aggregator type
    nuc_aggregator: str | None     # a valid aggregator type
    allele_aggregator: str | None  # a valid aggregator type

    small_values_desc: str | None
    large_values_desc: str | None

    hist_conf: HistogramConfig | None


@dataclass
class _ScoreDef:
    """Private score configuration definition. Includes internals."""

    # pylint: disable=too-many-instance-attributes
    score_id: str
    desc: str  # string that will be interpretted as md
    value_type: str  # "str", "int", "float"
    pos_aggregator: str | None     # a valid aggregator type
    nuc_aggregator: str | None     # a valid aggregator type
    allele_aggregator: str | None  # a valid aggregator type

    small_values_desc: str | None
    large_values_desc: str | None

    hist_conf: HistogramConfig | None

    col_name: str | None                       # internal
    col_index: int | None                      # internal

    value_parser: Any                             # internal
    na_values: Any                                # internal
    score_index: int | str | None = None       # internal

    def to_public(self) -> ScoreDef:
        return ScoreDef(
            self.score_id,
            self.desc,
            self.value_type,
            self.pos_aggregator,
            self.nuc_aggregator,
            self.allele_aggregator,
            self.small_values_desc,
            self.large_values_desc,
            self.hist_conf,
        )

    def __post_init__(self) -> None:
        if self.value_type is None:
            return
        default_na_values = {
            "str": {},
            "float": {"", "nan", ".", "NA"},
            "int": {"", "nan", ".", "NA"},
            "bool": {},
        }
        default_pos_aggregators = {
            "float": "mean",
            "int": "mean",
            "str": "concatenate",
            "bool": None,
        }
        default_nuc_aggregators = {
            "float": "max",
            "int": "max",
            "str": "concatenate",
            "bool": None,
        }
        default_allele_aggregators = {
            "float": "max",
            "int": "max",
            "str": "concatenate",
            "bool": None,
        }
        if self.pos_aggregator is None:
            self.pos_aggregator = default_pos_aggregators[self.value_type]
        if self.nuc_aggregator is None:
            self.nuc_aggregator = default_nuc_aggregators[self.value_type]
        if self.allele_aggregator is None:
            self.allele_aggregator = \
                default_allele_aggregators[self.value_type]
        if self.na_values is None:
            self.na_values = default_na_values[self.value_type]


class ScoreLine:
    """Abstraction for a genomic score line. Wraps the line adapter."""

    def __init__(self, line: LineBase, score_defs: dict[str, _ScoreDef]):
        assert isinstance(line, (Line, VCFLine))
        self.line = line
        self.score_defs = score_defs

    @property
    def chrom(self) -> str:
        return self.line.chrom

    @property
    def pos_begin(self) -> int:
        return self.line.pos_begin

    @property
    def pos_end(self) -> int:
        return self.line.pos_end

    @property
    def ref(self) -> str | None:
        return self.line.ref

    @property
    def alt(self) -> str | None:
        return self.line.alt

    def get_score(self, score_id: str) -> Any | None:
        """Get and parse configured score from line."""
        key = self.score_defs[score_id].score_index
        assert key is not None

        value: str | None = self.line.get(key)
        if score_id in self.score_defs:
            col_def = self.score_defs[score_id]
            if value in col_def.na_values:
                value = None
            elif col_def.value_parser is not None:
                # pylint: disable=broad-except
                try:  # Temporary workaround for GRR generation
                    value = col_def.value_parser(value)
                except Exception:
                    logger.exception(
                        "unable to parse value %s for score %s",
                        value, score_id)
                    value = None
        return value

    def get_available_scores(self) -> tuple[Any, ...]:
        return tuple(self.score_defs.keys())


@dataclass
class PositionScoreQuery:
    score: str
    position_aggregator: str | None = None


@dataclass
class NPScoreQuery:
    score: str
    position_aggregator: str | None = None
    nucleotide_aggregator: str | None = None


@dataclass
class AlleleScoreQuery:
    score: str
    position_aggregator: str | None = None
    allele_aggregator: str | None = None


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


ScoreQuery = PositionScoreQuery | NPScoreQuery | AlleleScoreQuery


class GenomicScore(ResourceConfigValidationMixin):
    """Genomic scores base class.

    PositionScore, NPScore and AlleleScore inherit from this class.
    Statistics builder implementation uses only GenomicScore interface
    to build all defined statistics.
    """

    def __init__(self, resource: GenomicResource):
        self.resource = resource
        self.resource_id = resource.resource_id
        assert self.resource.config is not None
        self.config: dict = self.resource.config
        self.config = self.validate_and_normalize_schema(
            self.config, resource,
        )
        self.config["id"] = resource.resource_id
        self.table_loaded = False
        self.table = build_genomic_position_table(
            self.resource, self.config["table"],
        )
        self.score_definitions = self._build_scoredefs()

    @staticmethod
    def get_schema() -> dict[str, Any]:
        scores_schema = {
            "type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "column_index": {
                        "type": "integer",
                        "excludes": ["index", "name", "column_name"],
                    },
                    "column_name": {
                        "type": "string",
                        "excludes": ["name", "index", "column_index"],
                    },
                    "type": {"type": "string"},
                    "desc": {"type": "string"},
                    "na_values": {"type": ["string", "list"]},
                    "large_values_desc": {"type": "string"},
                    "small_values_desc": {"type": "string"},
                    "number_hist": {"type": "dict", "schema": {
                        "number_of_bins": {
                            "type": "number",
                        },
                        "view_range": {"type": "dict", "schema": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        }},
                        "x_log_scale": {
                            "type": "boolean",
                        },
                        "y_log_scale": {
                            "type": "boolean",
                        },
                        "x_min_log": {
                            "type": "number",
                        },
                    }},
                    "categorical_hist": {"type": "dict", "schema": {
                        "y_log_scale": {
                            "type": "boolean",
                        },
                        "value_order": {
                            "type": "list", "schema": {"type": "string"},
                        },
                    }},
                    "null_hist": {"type": "dict", "schema": {
                        "reason": {
                            "type": "string",
                        },
                    }},
                    "histogram": {"type": "dict", "schema": {
                        "type": {"type": "string"},
                        "number_of_bins": {
                            "type": "number",
                            "dependencies": {"type": "number"},
                        },
                        "view_range": {"type": "dict", "schema": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        }, "dependencies": {"type": "number"}},
                        "x_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": "number"},
                        },
                        "y_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": ["number", "categorical"]},
                        },
                        "x_min_log": {
                            "type": "number",
                            "dependencies": {"type": ["number", "categorical"]},
                        },
                        "value_order": {
                            "type": "list", "schema": {"type": "string"},
                            "dependencies": {"type": "categorical"},
                        },
                        "reason": {
                            "type": "string",
                            "dependencies": {"type": "null"},
                        },
                    }},
                },
            },
        }
        return {
            **get_base_resource_schema(),
            "table": {"type": "dict", "schema": {
                "filename": {"type": "string"},
                "index_filename": {"type": "string"},
                "zero_based": {"type": "boolean", "default": False},
                "desc": {"type": "string"},
                "format": {"type": "string"},
                "header_mode": {"type": "string"},
                "header": {"type": ["string", "list"]},
                "chrom": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "column_index": {
                        "type": "integer",
                        "excludes": ["index", "name", "column_name"],
                    },
                    "column_name": {
                        "type": "string",
                        "excludes": ["name", "index", "column_index"],
                    },
                }},
                "pos_begin": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "column_index": {
                        "type": "integer",
                        "excludes": ["index", "name", "column_name"],
                    },
                    "column_name": {
                        "type": "string",
                        "excludes": ["name", "index", "column_index"],
                    },
                }},
                "pos_end": {"type": "dict", "schema": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "excludes": "index"},
                    "column_index": {
                        "type": "integer",
                        "excludes": ["index", "name", "column_name"],
                    },
                    "column_name": {
                        "type": "string",
                        "excludes": ["name", "index", "column_index"],
                    },
                }},
                "chrom_mapping": {"type": "dict", "schema": {
                    "filename": {
                        "type": "string",
                        "excludes": ["add_prefix", "del_prefix"],
                    },
                    "add_prefix": {"type": "string"},
                    "del_prefix": {"type": "string", "excludes": "add_prefix"},
                }},
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
                },
            }},
            "default_annotation": {
                "type": ["dict", "list"], "allow_unknown": True,
            },
        }

    @staticmethod
    def _parse_scoredef_config(
        config: dict[str, Any],
    ) -> dict[str, _ScoreDef]:
        """Parse ScoreDef configuration."""
        scores = {}

        for score_conf in config["scores"]:
            value_parser = SCORE_TYPE_PARSERS[score_conf.get("type", "float")]

            col_name = score_conf.get("column_name") \
                or score_conf.get("name")
            col_index_str = score_conf.get("column_index") \
                or score_conf.get("index")
            col_index = int(col_index_str) if col_index_str else None

            hist_conf = build_histogram_config(score_conf)

            score_def = _ScoreDef(
                score_id=score_conf["id"],
                desc=score_conf.get("desc", ""),
                value_type=score_conf.get("type"),
                pos_aggregator=score_conf.get("position_aggregator"),
                nuc_aggregator=score_conf.get("nucleotide_aggregator"),
                allele_aggregator=score_conf.get("allele_aggregator"),
                small_values_desc=score_conf.get("small_values_desc"),
                large_values_desc=score_conf.get("large_values_desc"),
                col_name=col_name,
                col_index=col_index,
                hist_conf=hist_conf,
                value_parser=value_parser,
                na_values=score_conf.get("na_values"),
            )

            scores[score_conf["id"]] = score_def
        return scores

    def _parse_vcf_scoredefs(
        self,
        vcf_header_info: dict[str, Any] | None,
        config_scoredefs: dict[str, _ScoreDef] | None,
    ) -> dict[str, _ScoreDef]:
        def converter(val: Any) -> Any:
            try:
                return ",".join(map(str, val))
            except TypeError:
                return val

        vcf_scoredefs = {}

        assert vcf_header_info is not None

        for key, value in vcf_header_info.items():
            value_parser: Callable[[str], Any] | None = converter
            if value.number in (1, "A", "R"):
                value_parser = None

            vcf_scoredefs[key] = _ScoreDef(
                score_id=key,
                col_name=key,
                col_index=None,
                desc=value.description or "",
                value_type=VCF_TYPE_CONVERSION_MAP[value.type],
                value_parser=value_parser,
                na_values=(),
                pos_aggregator=None,
                nuc_aggregator=None,
                allele_aggregator=None,
                small_values_desc=None,
                large_values_desc=None,
                hist_conf=None,
            )
        if config_scoredefs is None:
            return vcf_scoredefs

        # allow overriding of vcf-generated scoredefs
        scoredefs = {}
        for score, config_scoredef in config_scoredefs.items():
            vcf_scoredef = vcf_scoredefs[score]

            if config_scoredef.desc:
                vcf_scoredef.desc = config_scoredef.desc
            if config_scoredef.value_type:
                vcf_scoredef.value_type = config_scoredef.value_type
            vcf_scoredef.value_parser = config_scoredef.value_parser
            vcf_scoredef.na_values = config_scoredef.na_values
            vcf_scoredef.hist_conf = config_scoredef.hist_conf
            scoredefs[score] = vcf_scoredef
        return scoredefs

    def _validate_scoredefs(self) -> None:
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
                    score["column_name"] = score["name"]
                    logger.debug(
                        "%s: Using 'name' to configure score columns is"
                        " outdated, use 'column_name' instead.",
                        self.resource.get_full_id(),
                    )
                elif "index" in score:
                    score["column_index"] = score["index"]
                    logger.debug(
                        "%s: Using 'index' to configure score columns is"
                        " outdated, use 'column_index' instead.",
                        self.resource.get_full_id(),
                    )

                if "column_name" in score:
                    assert score["column_name"] in self.table.header
                elif "column_index" in score:
                    assert 0 <= score["column_index"] < len(self.table.header)
                else:
                    raise AssertionError("Either an index or name must"
                                         " be configured for scores!")

    def _build_scoredefs(self) -> dict[str, _ScoreDef]:
        config_scoredefs = None
        if "scores" in self.config:
            config_scoredefs = self._parse_scoredef_config(self.config)

        if isinstance(self.table, VCFGenomicPositionTable):
            return self._parse_vcf_scoredefs(
                cast(dict[str, Any], self.table.header), config_scoredefs)

        if config_scoredefs is None:
            raise ValueError("No scores configured and not using a VCF")

        return config_scoredefs

    def get_config(self) -> dict[str, Any]:
        return self.config

    def get_default_annotation_attributes(self) -> list[Any]:
        """Collect default annotation attributes."""
        default_annotation = self.get_config().get("default_annotation")
        if not default_annotation:
            return [
                {"source": attr, "name": attr}
                for attr in self.score_definitions
            ]

        if not isinstance(default_annotation, list):
            raise TypeError(
                "The default_annotation in the "
                f"{self.resource_id} resource is not a list.")
        return default_annotation

    def get_default_annotation_attribute(self, score_id: str) -> str | None:
        """Return default annotation attribute for a score.

        Returns None if the score is not included in the default annotation.
        Returns the name of the attribute if present or the score if not.
        """
        attributes = self.get_default_annotation_attributes()
        result = []
        for attr in attributes:
            if attr["source"] != score_id:
                continue
            dst = score_id
            if "name" in attr:
                dst = attr["name"]
            result.append(dst)
        if result:
            return ",".join(result)
        return None

    def get_score_definition(self, score_id: str) -> _ScoreDef | None:
        return self.score_definitions.get(score_id)

    def close(self) -> None:
        self.table.close()
        self.table_loaded = False

    def is_open(self) -> bool:
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

        if isinstance(self.table, VCFGenomicPositionTable):
            for score_def in self.score_definitions.values():
                assert score_def.col_name is not None
                score_def.score_index = score_def.col_name
        else:
            for score_def in self.score_definitions.values():
                if score_def.col_index is None:
                    assert self.table.header is not None
                    assert score_def.col_name is not None
                    score_def.score_index = self.table.header.index(
                        score_def.col_name)
                else:
                    assert score_def.col_name is None
                    score_def.score_index = score_def.col_index
        return self

    def __enter__(self) -> GenomicScore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            logger.error(
                "exception while working with genomic score: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        self.close()

    @staticmethod
    def _line_to_begin_end(line: ScoreLine) -> tuple[int, int]:
        if line.pos_end < line.pos_begin:
            raise OSError(
                f"The resource line {line} has a regions "
                f" with end {line.pos_end} smaller that the "
                f"begining {line.pos_end}.")
        return line.pos_begin, line.pos_end

    def _get_header(self) -> tuple[Any, ...] | None:
        assert self.table is not None
        return self.table.header

    def _fetch_lines(
        self, chrom: str,
        pos_begin: int | None, pos_end: int | None,
    ) -> Iterator[ScoreLine]:
        for line in self.table.get_records_in_region(
            chrom, pos_begin, pos_end,
        ):
            yield ScoreLine(line, self.score_definitions)

    def get_all_chromosomes(self) -> list[str]:
        if not self.is_open():
            raise ValueError(f"genomic score <{self.resource_id}> is not open")

        return self.table.get_chromosomes()

    def get_all_scores(self) -> list[str]:
        return list(self.score_definitions)

    def fetch_region(
        self, chrom: str,
        pos_begin: int | None, pos_end: int | None, scores: Iterable[str],
    ) -> Iterator[dict[str, ScoreValue]]:
        """Return score values in a region."""
        if not self.is_open():
            raise ValueError(f"genomic score <{self.resource_id}> is not open")

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

    @lru_cache(maxsize=64)
    def get_number_range(
        self, score_id: str,
    ) -> tuple[float, float] | None:
        """Return the value range for a number score."""
        if score_id not in self.get_all_scores():
            raise ValueError(
                f"unknown score {score_id}; "
                f"available scores are {self.get_all_scores()}")
        hist = self.get_score_histogram(score_id)
        if isinstance(hist, NumberHistogram):
            return (hist.min_value, hist.max_value)
        return None

    def get_histogram_filename(self, score_id: str) -> str:
        return f"statistics/histogram_{score_id}.yaml"

    @lru_cache(maxsize=64)
    def get_score_histogram(self, score_id: str) -> Histogram:
        """Return defined histogram for a score."""
        if score_id not in self.score_definitions:
            raise ValueError(
                f"unexpected score ID {score_id}; available scores are: "
                f"{self.score_definitions.keys()}")

        hist_filename = self.get_histogram_filename(score_id)
        return load_histogram(self.resource, hist_filename)

    def get_histogram_image_filename(self, score_id: str) -> str:
        return f"statistics/histogram_{score_id}.png"

    def get_histogram_image_url(self, score_id: str) -> str | None:
        return (
            f"{self.resource.get_url()}/"
            f"{quote(self.get_histogram_image_filename(score_id))}"
        )


class PositionScore(GenomicScore):
    """Defines position genomic score."""

    @staticmethod
    def get_schema() -> dict[str, Any]:
        schema = copy.deepcopy(GenomicScore.get_schema())
        scores_schema = schema["scores"]["schema"]["schema"]
        scores_schema["position_aggregator"] = AGGREGATOR_SCHEMA
        return schema

    def open(self) -> PositionScore:
        return cast(PositionScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int,
            scores: list[str] | None = None) -> list[Any] | None:
        """Fetch score values at specific genomic position."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        if len(lines) != 1:
            raise ValueError(
                f"The resource {self.resource_id} has "
                f"more than one ({len(lines)}) lines for position "
                f"{chrom}:{position}")
        line = lines[0]

        requested_scores = scores or self.get_all_scores()
        return [line.get_score(scr) for scr in requested_scores]

    def _build_scores_agg(
        self, scores: list[PositionScoreQuery],
    ) -> list[PositionScoreAggr]:
        score_aggs = []
        aggregator_type: str | None
        for score in scores:
            if score.position_aggregator is not None:
                aggregator_type = score.position_aggregator
            else:
                aggregator_type = \
                    self.score_definitions[score.score].pos_aggregator
            assert aggregator_type is not None
            score_aggs.append(
                PositionScoreAggr(
                    score.score,
                    build_aggregator(aggregator_type)),
            )
        return score_aggs

    def fetch_scores_agg(  # pylint: disable=too-many-arguments,too-many-locals
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: list[PositionScoreQuery] | None = None,
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
                    max(pos_begin, line_pos_begin)
                )
                right = (
                    min(pos_end, line_pos_end)
                )
                for _ in range(left, right + 1):
                    sagg.position_aggregator.add(val)

        return [squery.position_aggregator for squery in score_aggs]


class NPScore(GenomicScore):
    """Defines nucleotide-position genomic score."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "np_score":
            raise ValueError("The resrouce provided to NPScore should be of"
                             f"'np_score' type, not a '{resource.get_type()}'")
        super().__init__(resource)

    @staticmethod
    def get_schema() -> dict[str, Any]:
        schema = copy.deepcopy(GenomicScore.get_schema())
        schema["table"]["schema"]["reference"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"},
            },
        }
        schema["table"]["schema"]["alternative"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"},
            },
        }

        scores_schema = schema["scores"]["schema"]["schema"]
        scores_schema["position_aggregator"] = AGGREGATOR_SCHEMA
        scores_schema["nucleotide_aggregator"] = AGGREGATOR_SCHEMA
        return schema

    def open(self) -> NPScore:
        return cast(NPScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: list[str] | None = None) -> list[Any] | None:
        """Fetch score values at specified genomic position and nucleotide."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

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
        requested_scores = scores or self.get_all_scores()
        return [selected_line.get_score(sc) for sc in requested_scores]

    def _build_scores_agg(
            self, score_queries: list[NPScoreQuery]) -> list[NPScoreAggr]:
        score_aggs = []
        for squery in score_queries:
            scr_def = self.score_definitions[squery.score]
            if squery.position_aggregator is not None:
                aggregator_type = squery.position_aggregator
            else:
                assert scr_def.pos_aggregator is not None
                aggregator_type = scr_def.pos_aggregator
            position_aggregator = build_aggregator(aggregator_type)

            if squery.nucleotide_aggregator is not None:
                aggregator_type = squery.nucleotide_aggregator
            else:
                assert scr_def.nuc_aggregator is not None
                aggregator_type = scr_def.nuc_aggregator
            nucleotide_aggregator = build_aggregator(aggregator_type)
            score_aggs.append(
                NPScoreAggr(
                    squery.score, position_aggregator, nucleotide_aggregator))
        return score_aggs

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: list[NPScoreQuery] | None = None,
    ) -> list[Aggregator]:
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

        if scores is None:
            scores = [
                NPScoreQuery(score_id)
                for score_id in self.get_all_scores()]

        score_aggs = self._build_scores_agg(scores)

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return [sagg.position_aggregator for sagg in score_aggs]

        def aggregate_nucleotides() -> None:
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
                    max(pos_begin, line.pos_begin)
                )
                right = (
                    min(pos_end, line.pos_end)
                )
                for _ in range(left, right + 1):
                    sagg.nucleotide_aggregator.add(val)
            last_pos = line.pos_begin
        aggregate_nucleotides()

        return [sagg.position_aggregator for sagg in score_aggs]


class AlleleScore(GenomicScore):
    """Defines allele genomic scores."""

    @staticmethod
    def get_schema() -> dict[str, Any]:
        schema = copy.deepcopy(GenomicScore.get_schema())
        schema["table"]["schema"]["reference"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"},
            },
        }
        schema["table"]["schema"]["alternative"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"},
            },
        }
        schema["table"]["schema"]["variant"] = {
            "type": "dict", "schema": {
                "index": {"type": "integer"},
                "name": {"type": "string", "excludes": "index"},
            },
        }
        return schema

    def open(self) -> AlleleScore:
        return cast(AlleleScore, super().open())

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: list[str] | None = None) -> list[Any] | None:
        """Fetch scores values for specific allele."""
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"Allele Score resource {self.resource_id}")

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

        requested_scores = scores or self.get_all_scores()
        return [
            selected_line.get_score(sc)
            for sc in requested_scores]

    def _build_scores_agg(
        self, score_queries: list[AlleleScoreQuery],
    ) -> list[AlleleScoreAggr]:
        score_aggs = []
        for squery in score_queries:
            scr_def = self.score_definitions[squery.score]
            if squery.position_aggregator is not None:
                aggregator_type = squery.position_aggregator
            else:
                assert scr_def.pos_aggregator is not None
                aggregator_type = scr_def.pos_aggregator
            position_aggregator = build_aggregator(aggregator_type)

            if squery.allele_aggregator is not None:
                aggregator_type = squery.allele_aggregator
            else:
                assert scr_def.allele_aggregator is not None
                aggregator_type = scr_def.allele_aggregator
            allele_aggregator = build_aggregator(aggregator_type)
            score_aggs.append(
                AlleleScoreAggr(
                    squery.score, position_aggregator, allele_aggregator))
        return score_aggs

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: list[AlleleScoreQuery] | None = None,
    ) -> list[Aggregator]:
        """Fetch score values in a region and aggregates them."""
        # pylint: disable=too-many-locals
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

        if scores is None:
            scores = [
                AlleleScoreQuery(score_id)
                for score_id in self.get_all_scores()]

        score_aggs = self._build_scores_agg(scores)

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return [sagg.position_aggregator for sagg in score_aggs]

        def aggregate_alleles() -> None:
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
                    max(pos_begin, line.pos_begin)
                )
                right = (
                    min(pos_end, line.pos_end)
                )
                for _ in range(left, right + 1):
                    sagg.allele_aggregator.add(val)
            last_pos = line.pos_begin
        aggregate_alleles()

        return [sagg.position_aggregator for sagg in score_aggs]


def build_score_from_resource(
    resource: GenomicResource,
) -> GenomicScore:
    """Build a genomic score resource and return the coresponding score."""
    type_to_ctor = {
        "position_score": PositionScore,
        "np_score": NPScore,
        "allele_score": AlleleScore,
    }
    ctor = type_to_ctor.get(resource.get_type())
    if ctor is None:
        raise ValueError(f"Resource {resource.get_id()} is not of score type")
    return ctor(resource)
