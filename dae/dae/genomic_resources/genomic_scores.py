from __future__ import annotations

import abc
import logging
from numbers import Number

from typing import Generator, List, Tuple, cast, Type, Dict, Any


from . import GenomicResource
from .repository import GenomicResourceRealRepo
from .genome_position_table import open_genome_position_table

from .aggregators import build_aggregator


logger = logging.getLogger(__name__)


class ScoreLine:
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

    def get_special_column_value(self, id):
        clmn_def = self.special_columns[id]

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

class GenomicScore(abc.ABC):
    def __init__(self, config, table, score_columns, special_columns):
        self.config = config
        self.table = table
        self.score_columns = score_columns
        self.special_columns = special_columns

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def get_config(self):
        return self.config

    def score_id(self):
        return self.get_config().get("id")

    def get_default_annotation(self) -> Dict[str, Any]:
        if "default_annotation" in self.get_config():
            return cast(
                Dict[str, Any], self.get_config()["default_annotation"])
        else:
            return {
                "attributes": [{"source": score, "destination": score}
                               for score in self.score_columns.keys()]
            }

    def get_score_config(self, score_id):
        return self.score_columns.get(score_id)

    def close(self):
        self.table.close()

    def _line_to_begin_end(self, line):
        begin = line.get_pos_begin()
        end = line.get_pos_end()
        if end < begin:
            raise Exception(f"The resource line {line.values} has a regions "
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
        return self.table.get_chromosomes()

    def get_all_scores(self):
        return list(self.score_columns)

    def fetch_region(self, chrom: str, pos_begin: int, pos_end: int,
                     scores: List[str]) \
            -> Generator[dict[str, Number], None, None]:
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

            for i in range(left, right+1):
                yield val


class PositionScore(GenomicScore):

    @staticmethod
    def get_resource_type():
        return "position_score"

    def fetch_scores(
            self, chrom: str, position: int, scores: List[str] = None):

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

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: List[str] = None, non_default_pos_aggregators=None):
        '''
        # Case 1:
        #    res.fetch_scores_agg("1", 10, 20) -->
        #       all score with default aggregators
        # Case 2:
        #    res.fetch_scores_agg("1", 10, 20,
        #                         non_default_aggregators={"bla":"max"}) -->
        #       all score with default aggregators but 'bla' should use 'max'
        '''
        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))

        requested_scores = scores if scores else self.get_all_scores()
        aggregators = {}
        if non_default_pos_aggregators is None:
            non_default_pos_aggregators = {}

        for scr_id in requested_scores:
            scr_def = self.score_columns[scr_id]
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, scr_def.pos_aggregator)
            aggregators[scr_id] = build_aggregator(aggregator_type)

        for line in score_lines:
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
                for i in range(left, right+1):
                    aggregators[scr_id].add(val)

        return {
            score_id: aggregator
            for score_id, aggregator
            in aggregators.items()
        }


class NPScore(GenomicScore):

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    @staticmethod
    def get_resource_type():
        return "np_score"

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id()}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        line = None
        for li in lines:
            if li.get_special_column_value("reference") == reference \
                    and li.get_special_column_value("alternative") \
                    == alternative:
                line = li
                break

        if not line:
            return None
        requested_scores = scores if scores else self.get_all_scores()
        return {sc: line.get_score_value(sc) for sc in requested_scores}

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: List[str] = None,
            non_default_pos_aggregators=None,
            non_default_nuc_aggregators=None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id()}")

        score_lines = list(self._fetch_lines(chrom, pos_begin, pos_end))
        if not score_lines:
            return None

        scores = scores if scores else self.get_all_scores()

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
                for i in range(left, right+1):
                    nuc_aggregators[col].add(val)
            last_pos = line.get_pos_begin()
        aggregate_nucleotides()

        return {
            score_id: aggregator
            for score_id, aggregator
            in pos_aggregators.items()
        }


class AlleleScore(GenomicScore):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end", "variant")

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    @staticmethod
    def get_resource_type():
        return "allele_score"

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.score_id()}")

        lines = list(self._fetch_lines(chrom, position, position))
        if not lines:
            return None

        line = None
        for li in lines:
            if li.get_special_column_value("reference") == reference and \
                    li.get_special_column_value("alternative") == alternative:
                line = li
                break

        if line is None:
            return None

        requested_scores = scores if scores else self.get_all_scores()
        return {sc: line.get_score_value(sc) for sc in requested_scores}


def _configure_score_columns(table, config, ):
    # load score configuraton
    scores = {}
    for score_conf in config['scores']:

        class ScoreDef:
            pass
        scr_def = ScoreDef()

        scr_def.id = score_conf["id"]
        scr_def.desc = score_conf.get("desc", "")

        if "index" in score_conf:
            scr_def.col_index = int(score_conf["index"])
        elif "name" in score_conf:
            scr_def.col_index = table.get_column_names().index(
                score_conf["name"])
        else:
            raise ValueError(
                "The score configuration must have a column specified")

        scr_def.type = score_conf.get(
            "type", config.get("default.score.type", "float"))

        type_parsers = {
            "str": str,
            "float": float,
            "int": int
        }

        scr_def.value_parser = type_parsers[scr_def.type]

        default_na_values = {
            "str": [],
            "float": ["", 'nan', '.'],
            "int": ["", 'nan', '.']
        }

        scr_def.na_values = score_conf.get(
            "na_values",
            config.get(
                f"default_na_values.{scr_def.type}",
                default_na_values[scr_def.type]))
        default_type_pos_aggregators = {
            "float": "mean",
            "int": "mean",
            "str": "concatenate"
        }
        scr_def.pos_aggregator = score_conf.get(
            "position_aggregator",
            config.get(
                scr_def.type + ".aggregator",
                default_type_pos_aggregators[scr_def.type]))

        default_type_nuc_aggregators = {
            "float": "max",
            "int": "max",
            "str": "concatenate"
        }
        scr_def.nuc_aggregator = score_conf.get(
            "nucleotide_aggregator",
            config.get(
                scr_def.type + ".aggregator",
                default_type_nuc_aggregators[scr_def.type]))

        scr_def.description = score_conf.get("description", None)
        scores[scr_def.id] = scr_def

    return scores


def _configure_special_columns(table, extra_special_columns=None):
    special_clmns = {"chrom": str, "pos_begin": int, "pos_end": int}
    if extra_special_columns is not None:
        special_clmns.update(extra_special_columns)

    special_columns = {}
    for key, parser in special_clmns.items():
        class SpecialDef:
            pass
        spec_def = SpecialDef()
        spec_def.key = key
        spec_def.col_index = table.get_special_column_index(key)
        spec_def.value_parser = parser
        special_columns[key] = spec_def

    return special_columns


def _open_genomic_score_from_resource(
        clazz: Type[GenomicScore],
        resource: GenomicResource,
        extra_special_columns=None) -> GenomicScore:

    config = resource.get_config()
    config["id"] = resource.resource_id

    table = open_genome_position_table(
        resource, resource.get_config()["table"])
    score_columns = _configure_score_columns(table, config)
    special_columns = _configure_special_columns(table, extra_special_columns)

    return clazz(config, table, score_columns, special_columns)


def open_position_score_from_resource(
        resource: GenomicResource) -> PositionScore:

    result = _open_genomic_score_from_resource(
        PositionScore,
        resource,
        extra_special_columns=None)

    return cast(PositionScore, result)


def open_np_score_from_resource(
        resource: GenomicResource) -> NPScore:

    result = _open_genomic_score_from_resource(
        NPScore,
        resource,
        extra_special_columns={"reference": str, "alternative": str})

    return cast(NPScore, result)


def open_allele_score_from_resource(
        resource: GenomicResource) -> AlleleScore:

    result = _open_genomic_score_from_resource(
        AlleleScore,
        resource,
        extra_special_columns={"reference": str, "alternative": str})

    return cast(AlleleScore, result)


def open_score_from_resource(resource: GenomicResource) -> GenomicScore:
    type_to_ctor = {
        PositionScore.get_resource_type(): open_position_score_from_resource,
        NPScore.get_resource_type(): open_np_score_from_resource,
        AlleleScore.get_resource_type(): open_allele_score_from_resource,
    }
    ctor = type_to_ctor.get(resource.get_type())
    if ctor is None:
        raise ValueError(f"Resource {resource.get_id()} is not of score type")

    return ctor(resource)
