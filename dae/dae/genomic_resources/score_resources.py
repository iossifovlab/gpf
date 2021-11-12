
import abc
import logging
import re

from typing import List, Tuple
from box import Box

from . import GenomicResource
from .repository import GenomicResourceRealRepo
from .genome_position_table import open_genome_position_table

from .aggregators import get_aggregator_class


logger = logging.getLogger(__name__)


class ScoreLine:
    def __init__(self, values: Tuple[str], scores: dict,
                 special_columns: dict):
        self.values = values
        self.scores = scores
        self.special_columns = special_columns

    def get_score_value(self, score_id):
        scr_def = self.scores[score_id]

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


def create_aggregator_definition(aggregator_type):
    join_regex = r"^(join)\((.+)\)"
    join_match = re.match(join_regex, aggregator_type)
    if join_match is not None:
        separator = join_match.groups()[1]
        return {
            "name": "join",
            "args": [separator]
        }
    return {
        "name": aggregator_type,
    }


def create_aggregator(aggregator_def):
    aggregator_name = aggregator_def["name"]
    aggregator_class = get_aggregator_class(aggregator_name)
    if "args" in aggregator_def:
        return aggregator_class(*aggregator_def["args"])
    else:
        return aggregator_class()


class GenomicScoresResource(GenomicResource, abc.ABC):
    def __init__(self, resource_id: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(resource_id, version, repo, config)
        self.table = None
        self.scores = {}

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def get_default_annotation(self):
        if "default_annotation" in self.get_config():
            return Box(self.get_config()["default_annotation"])
        else:
            return Box({
                "attributes": [{"source": score, "dest": score}
                               for score in self.scores.keys()]
            })

    def open(self):
        self.table = open_genome_position_table(
            self, self.get_config()["table"])

        # load score configuraton
        for score_conf in self.get_config()['scores']:
            class ScoreDef:
                pass
            scr_def = ScoreDef()

            scr_def.id = score_conf["id"]

            if "index" in score_conf:
                scr_def.col_index = int(score_conf["index"])
            elif "name" in score_conf:
                scr_def.col_index = self.table.get_column_names().index(
                    score_conf["name"])
            else:
                raise Exception(
                    "The score configuration must have a column specified")

            scr_def.type = score_conf.get(
                "type", self.get_config().get("default.score.type", "float"))

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
                self.get_config().get(f"default_na_values.{scr_def.type}",
                                      default_na_values[scr_def.type]))
            default_type_pos_aggregators = {
                "float": "mean",
                "int": "mean",
                "str": "concatenate"
            }
            scr_def.pos_aggregator = score_conf.get(
                "position_aggregator",
                self.get_config().get(
                    scr_def.type + ".aggregator",
                    default_type_pos_aggregators[scr_def.type]))

            default_type_nuc_aggregators = {
                "float": "max",
                "int": "max",
                "str": "concatenate"
            }
            scr_def.nuc_aggregator = score_conf.get(
                "nucleotide_aggregator",
                self.get_config().get(
                    scr_def.type + ".aggregator",
                    default_type_nuc_aggregators[scr_def.type]))

            scr_def.description = score_conf.get("description", None)
            self.scores[scr_def.id] = scr_def

        special_clmns = {"chrom": str, "pos_begin": int, "pos_end": int}
        special_clmns.update(self.get_extra_special_columns())

        self.special_columns = {}
        for key, parser in special_clmns.items():
            class SpecialDef:
                pass
            spec_def = SpecialDef()
            spec_def.key = key
            spec_def.col_index = self.table.get_special_column_index(key)
            spec_def.value_parser = parser
            self.special_columns[key] = spec_def

        self._has_chrom_prefix = self.table.get_chromosomes(
        )[-1].startswith("chr")
        return True

    def get_score_config(self, score_id):
        return self.scores.get(score_id)

    def close(self):
        self.table.close()
        self.direct_infile.close()

    @staticmethod
    def get_extra_special_columns():
        return {}

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

    def _fetch_lines(self, chrom, pos_begin, pos_end):
        records = list(self.table.get_records_in_region(
            chrom, pos_begin, pos_end))

        return [
            ScoreLine(record, self.scores, self.special_columns)
            for record in records
        ]

        # return self._fetch_direct(chrom, pos_begin, pos_end)
        # self.last_pos = pos_end
        # if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
        #
        # return self._fetch_sequential(chrom, pos_begin, pos_end)

    def get_all_chromosomes(self):
        return self.table.get_chromosomes()

    def get_all_scores(self):
        return list(self.scores)


class PositionScoreResource(GenomicScoresResource):
    def __init__(self, resourceId: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(resourceId, version, repo, config)

    @staticmethod
    def get_resource_type():
        return "PositionScore"

    def fetch_scores(
            self, chrom: str, position: int, scores: List[str] = None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes.")

        line = self._fetch_lines(chrom, position, position)
        if not line:
            return None

        if len(line) != 1:
            raise ValueError(
                f"The resource {self.get_resource_it()} has "
                f"more than one ({len(line)}) lines for position "
                f"{chrom}:{position}")
        line = line[0]
        if not scores:
            scores = self.get_all_scores()
        return {scr: line.get_score_value(scr) for scr in scores}

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

        score_lines = self._fetch_lines(chrom, pos_begin, pos_end)

        scores = scores if scores else self.get_all_scores()
        aggregators = {}
        if non_default_pos_aggregators is None:
            non_default_pos_aggregators = {}

        for scr_id in scores:
            scr_def = self.scores[scr_id]
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, scr_def.pos_aggregator)
            aggregator_def = create_aggregator_definition(aggregator_type)
            aggregators[scr_id] = create_aggregator(aggregator_def)

        for line in score_lines:
            logger.debug(
                f"pos_end: {pos_end}; line.pos_end: {line.get_pos_end()}; "
                f"pos_begin: {pos_begin}; "
                f"line.pos_begin: {line.get_pos_begin()}"
            )

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


class NPScoreResource(GenomicScoresResource):

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    @staticmethod
    def get_resource_type():
        return "NPScore"

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

        lines = self._fetch_lines(chrom, position, position)
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
        if not scores:
            scores = self.get_all_scores()
        return {sc: line.get_score_value(sc) for sc in scores}

    def fetch_scores_agg(
            self, chrom: str, pos_begin: int, pos_end: int,
            scores: List[str] = None,
            non_default_pos_aggregators=None,
            non_default_nuc_aggregators=None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

        score_lines = self._fetch_lines(chrom, pos_begin, pos_end)
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
            scr_def = self.scores[scr_id]
            aggregator_type = non_default_pos_aggregators.get(
                scr_id, scr_def.pos_aggregator)
            aggregator_def = create_aggregator_definition(aggregator_type)
            pos_aggregators[scr_id] = create_aggregator(aggregator_def)

            aggregator_type = non_default_nuc_aggregators.get(
                scr_id, scr_def.nuc_aggregator)
            aggregator_def = create_aggregator_definition(aggregator_type)
            nuc_aggregators[scr_id] = create_aggregator(aggregator_def)

        # pos_aggregators = {
        #     score_id: aggregator_types[0]()
        #     for score_id, aggregator_types
        #     in scores_aggregators.items()
        # }

        # nuc_aggregators = {
        #     score_id: aggregator_types[1]()
        #     for score_id, aggregator_types
        #     in scores_aggregators.items()
        # }

        def aggregate_nucleotides():
            for col, nuc_agg in nuc_aggregators.items():
                pos_aggregators[col].add(nuc_agg.get_final())
                nuc_agg.clear()

        last_pos: int = score_lines[0].get_pos_begin()
        for line in score_lines:
            if line.get_pos_begin() != last_pos:
                aggregate_nucleotides()
            for col in line.scores:
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


class AlleleScoreResource(GenomicScoresResource):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end", "variant")

    @staticmethod
    def get_extra_special_columns():
        return {"reference": str, "alternative": str}

    @staticmethod
    def get_resource_type():
        return "AlleleScore"

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"NP Score resource {self.resource_id}")

        lines = self._fetch_lines(chrom, position, position)
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

        if not scores:
            scores = self.get_all_scores()

        return {sc: line.get_score_value(sc) for sc in scores}
