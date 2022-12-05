"""Abstraction over genomic scores table."""
import abc
import collections
import os
import logging

from typing import Optional, Tuple, Any, Deque, Union, Dict, Generator
from collections import Counter
from dataclasses import dataclass

import pysam  # type: ignore
from box import Box  # type: ignore

from dae.genomic_resources.repository import GenomicResource

logger = logging.getLogger(__name__)
# pylint: disable=no-member
PysamFile = Union[pysam.TabixFile, pysam.VariantFile]


def parse_scoredef_config(config):
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


class Line:
    """Represents a line read from a tabix-indexed genomic position table."""

    def __init__(
        self,
        chrom: str,
        pos_begin: Union[int, str],
        pos_end: Union[int, str],
        attributes: Dict[str, Any],
        score_defs: Dict[str, ScoreDef],
        ref: Optional[str]=None,
        alt: Optional[str]=None,
        allele_index: Optional[int]=None,
        info: Optional[pysam.VariantRecordInfo]=None,
        info_meta: Optional[pysam.VariantHeaderMetadata]=None,
    ):
        self.chrom: str = chrom
        self.pos_begin: int = int(pos_begin)
        self.pos_end: int = int(pos_end)
        self.attributes: Dict[str, Any] = attributes
        self.score_defs: Dict[str, ScoreDef] = score_defs
        self.ref: Optional[str] = ref
        self.alt: Optional[str] = alt
        # Used for support of multiallelic variants in VCF files.
        # The allele index is None if the variant for this line
        # is missing its ALT, i.e. its value is '.'
        self.allele_index: Optional[int] = allele_index
        # VCF INFO fields column
        self.info: Optional[pysam.VariantRecordInfo] = info
        # VCF INFO fields metadata - holds metadata for info fields
        # such as description, type, whether the value is a tuple
        # of multiple score values, etc.
        self.info_meta: Optional[pysam.VariantHeaderMetadata] = info_meta
        if self.info is not None:
            assert self.info_meta is not None, \
                "Cannot use INFO without providing relevant metadata."

    def __eq__(self, other: object):
        if isinstance(other, Line):
            return self.chrom == other.chrom \
                and self.pos_begin == other.pos_begin \
                and self.pos_end == other.pos_end \
                and self.attributes == other.attributes
        if isinstance(other, tuple) and len(other) >= 3:
            return tuple(self) == other
        return False

    def __iter__(self):
        yield self.chrom
        yield self.pos_begin
        yield self.pos_end
        for attr in self.attributes.values():
            yield attr

    def __getitem__(self, key: int):
        if not isinstance(key, (int, slice)):
            raise TypeError(f"Key '{key}' must be of integer or slice type!")
        if isinstance(key, slice):
            return tuple(self)[key]
        if key == 0:
            return self.chrom
        if key == 1:
            return self.pos_begin
        if key == 2:
            return self.pos_end
        return tuple(self.attributes.values())[key - 3]

    def __repr__(self):
        return str(tuple(self))

    def get(self, key: str, default=None):
        if key == "chrom":
            return self.chrom
        if key == "pos_begin":
            return self.pos_begin
        if key == "pos_end":
            return self.pos_end
        try:
            return self.get_score(key)
        except KeyError:
            return self.attributes.get(key, default)

    def get_score(self, score_id):
        key = self.score_defs[score_id].col_key
        if self.info is not None:
            value, meta = self.info[key], self.info_meta[key]
            if isinstance(value, tuple):
                if meta.number == "A" and self.allele_index is not None:
                    value = value[self.allele_index]
                elif meta.number == "R":
                    value = value[
                        self.allele_index + 1
                        if self.allele_index is not None
                        else 0  # Get reference allele value if ALT is '.'
                    ]
        else:
            value = self.attributes[key]

        if score_id in self.score_defs:
            col_def = self.score_defs[score_id]
            if value in col_def.na_values:
                value = None
            elif col_def.value_parser is not None:
                value = col_def.value_parser(value)
        return value

    def get_available_scores(self):
        return tuple(self.score_defs.keys())


class LineBuffer:
    """Represent a line buffer for Tabix genome position table."""

    def __init__(self):
        self.deque: Deque[Line] = collections.deque()

    def __len__(self):
        return len(self.deque)

    def clear(self):
        self.deque.clear()

    def append(self, line: Line):
        if len(self.deque) > 0 and self.peek_first().chrom != line.chrom:
            self.clear()
        self.deque.append(line)

    def peek_first(self) -> Line:
        return self.deque[0]

    def pop_first(self) -> Line:
        return self.deque.popleft()

    def peek_last(self) -> Optional[Line]:
        if len(self.deque) == 0:
            return None
        return self.deque[-1]

    def region(self) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """Return region stored in the buffer."""
        if len(self.deque) == 0:
            return None, None, None

        first_chrom, first_begin, first_end, *_ = self.peek_first()
        if len(self.deque) == 1:
            return first_chrom, first_begin, first_end

        last_chrom, _, last_end, *_ = self.peek_last()
        if first_chrom != last_chrom:
            self.clear()
            return None, None, None
        if first_end > last_end:
            self.clear()
            return None, None, None
        return first_chrom, first_begin, last_end

    def prune(self, chrom: str, pos: int) -> None:
        """Prune the buffer if needed."""
        if len(self.deque) == 0:
            return

        first_chrom, _first_beg, _, *_ = self.peek_first()
        if chrom != first_chrom:
            self.clear()
            return

        while len(self.deque) > 0:
            _, _first_beg, first_end, *_ = self.deque[0]

            if pos <= first_end:
                break
            self.deque.popleft()

    def contains(self, chrom: str, pos: int) -> bool:
        bchrom, bbeg, bend = self.region()

        if chrom == bchrom and bend >= pos >= bbeg:
            return True
        return False

    def find_index(self, chrom: str, pos: int) -> int:
        """Find index in line buffer that contains the passed position."""
        if len(self.deque) == 0 or not self.contains(chrom, pos):
            return -1

        if len(self.deque) == 1:
            return 0

        first_index = 0
        last_index = len(self.deque) - 1
        while True:
            mid_index = (last_index - first_index) // 2 + first_index
            if last_index <= first_index:
                break

            _, mid_beg, mid_end, *_ = self.deque[mid_index]
            if mid_end >= pos >= mid_beg:
                break

            if pos < mid_beg:
                last_index = mid_index - 1
            else:
                first_index = mid_index + 1

        while mid_index > 0:
            _, prev_beg, _prev_end, *_ = self.deque[mid_index - 1]
            if pos > prev_beg:
                break
            mid_index -= 1

        for index in range(mid_index, len(self.deque)):
            _, t_beg, t_end, *_ = self.deque[index]
            if t_end >= pos >= t_beg:
                mid_index = index
                break
            if t_beg >= pos:
                mid_index = index
                break

        return mid_index

    def fetch(self, chrom, pos_begin, pos_end) -> Generator[Line, None, None]:
        """Return a generator of rows matching the region."""
        beg_index = self.find_index(chrom, pos_begin)
        if beg_index == -1:
            return

        for index in range(beg_index, len(self.deque)):
            row = self.deque[index]
            _rchrom, rbeg, rend, *_rline = row
            if rend < pos_begin:
                continue
            if pos_end is not None and rbeg > pos_end:
                break
            yield row


class GenomicPositionTable(abc.ABC):
    """Abstraction over genomic scores table."""

    CHROM = "chrom"
    POS_BEGIN = "pos_begin"
    POS_END = "pos_end"

    def __init__(self, genomic_resource: GenomicResource, table_definition):
        self.genomic_resource = genomic_resource

        self.definition = Box(table_definition)
        self.score_definitions = self._generate_scoredefs()
        self.chrom_map = None
        self.chrom_order = None
        self.rev_chrom_map = None

        self.chrom_column_i = None
        self.pos_begin_column_i = None
        self.pos_end_column_i = None

        # handling the header property
        self.header: Optional[tuple] = None

        self.header_mode = self.definition.get("header_mode", "file")
        if self.header_mode == "list":
            self.header = tuple(self.definition.header)
            for hindex, hcolumn in enumerate(self.header):
                if not isinstance(hcolumn, str):
                    raise ValueError(
                        f"The {hindex}-th header {hcolumn} in the table "
                        f"definition is not a string.")
        else:
            if self.header_mode in {"file", "none"}:
                self.header = None
            else:
                raise ValueError(
                    f"The 'header' property in a table definition "
                    f"must be 'file' [by default], 'none', or a "
                    f"list of strings. The current value "
                    f"{self.header_mode} does not meet these "
                    f"requirements.")

    def _generate_scoredefs(self):
        return parse_scoredef_config(self.definition) \
            if "scores" in self.definition else {}

    def _build_chrom_mapping(self):
        self.chrom_map = None
        self.chrom_order = self.get_file_chromosomes()

        if "chrom_mapping" in self.definition:
            mapping = self.definition.chrom_mapping
            if "filename" in mapping:
                self.chrom_map = {}
                self.chrom_order = []
                with self.genomic_resource.open_raw_file(
                        mapping["filename"], "rt") as infile:
                    hcs = infile.readline().strip("\n\r").split("\t")
                    if hcs != ["chrom", "file_chrom"]:
                        raise ValueError(
                            f"The chromosome mapping file "
                            f"{mapping['filename']} in resource "
                            f"{self.genomic_resource.get_id()} is "
                            f"expected to have the two columns "
                            f"'chrom' and 'file_chrom'")
                    for line in infile:
                        chrom, fchrom = line.strip("\n\r").split("\t")
                        assert chrom not in self.chrom_map
                        self.chrom_map[chrom] = fchrom
                        self.chrom_order.append(chrom)
                    assert len(set(self.chrom_map.values())) == \
                        len(self.chrom_map)
            else:
                chromosomes = self.chrom_order
                new_chromosomes = chromosomes

                if "del_prefix" in mapping:
                    pref = mapping.del_prefix
                    new_chromosomes = [
                        ch[len(pref):] if ch.startswith(pref) else ch
                        for ch in new_chromosomes
                    ]

                if "add_prefix" in mapping:
                    pref = mapping.add_prefix
                    new_chromosomes = [
                        f"{pref}{chrom}" for chrom in new_chromosomes]
                self.chrom_map = dict(zip(new_chromosomes, chromosomes))
                self.chrom_order = new_chromosomes
            self.rev_chrom_map = {
                fch: ch for ch, fch in self.chrom_map.items()}

    def _set_special_column_indexes(self):
        self.chrom_column_i = self.get_special_column_index(self.CHROM)
        self.pos_begin_column_i = self.get_special_column_index(self.POS_BEGIN)
        self.pos_end_column_i = self.pos_begin_column_i
        try:
            self.pos_end_column_i = self.get_special_column_index(self.POS_END)
        except (ValueError, KeyError):
            definition = self.definition.to_dict()
            definition[self.POS_END] = {"index": self.pos_end_column_i}
            self.definition = Box(definition)

    def get_column_names(self):
        return self.header

    def _get_index_prop_for_special_column(self, key):
        index_prop = key + ".index"

        if key not in self.definition:
            raise KeyError(f"The table definition has no index "
                           f"({index_prop} property) for the special "
                           f"column {key}.")
        if "index" not in self.definition[key]:
            raise KeyError(f"The table definition has no index "
                           f"({index_prop} property) for the special "
                           f"column {key}.")

        try:
            return int(self.definition[key].index)
        except ValueError as ex:
            raise ValueError(f"The {index_prop} property in the table "
                             f"definition should be an integer.") from ex

    def get_special_column_index(self, key):
        """Get special columns index."""
        if self.header_mode == "none":
            return self._get_index_prop_for_special_column(key)
        try:
            return self._get_index_prop_for_special_column(key)
        except KeyError:
            column_name = self.get_special_column_name(key)
            try:
                return self.header.index(column_name)
            except ValueError as ex:
                raise ValueError(f"The column {column_name} for the "
                                 f"special column {key} is not in the "
                                 f"header.") from ex

    def get_special_column_name(self, key):
        if self.header_mode == "none":
            raise AttributeError("The table has no header.")
        if key in self.definition and "name" in self.definition[key]:
            return self.definition[key].name
        return key

    def _get_other_columns(self) -> Tuple[Optional[tuple], Optional[tuple]]:
        if self.header is not None:
            return zip(*(
                (i, x) for i, x in enumerate(self.header)
                if i not in (self.chrom_column_i,
                            self.pos_begin_column_i,
                            self.pos_end_column_i)
            ))
        return None, None

    @abc.abstractmethod
    def load(self):
        pass

    @abc.abstractmethod
    def get_all_records(self):
        pass

    @abc.abstractmethod
    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):
        """Return an iterable over the records in the specified range.

        The interval is closed on both sides and 1-based.
        """

    @abc.abstractmethod
    def close(self):
        """Close the resource."""

    def get_chromosomes(self):
        return self.chrom_order

    @abc.abstractmethod
    def get_file_chromosomes(self):
        """Return chromosomes in a genomic table file.

        This is to be overwritten by the subclass. It should return a list of
        the chromomes in the file in the order determinted by the file.
        """

    def get_chromosome_length(self, chrom, step=1_000_000):
        """Return the length of a chromosome (or contig).

        The returned value is
        the index of the last record for the chromosome + 1.
        """
        def any_records(riter):
            try:
                next(riter)
            except StopIteration:
                return False
            else:
                return True

        # First we find any region that includes the last record i.e.
        # the length of the chromosome
        left, right = None, None
        pos = step
        while left is None or right is None:
            if any_records(self.get_records_in_region(chrom, pos, None)):
                left = pos
                pos = pos * 2
            else:
                right = pos
                pos = pos // 2

        # Second we use binary search to narrow the region until we find the
        # index of the last element (in left) and the length (in right)
        while (right - left) > 1:
            pos = (left + right) // 2
            if any_records(self.get_records_in_region(chrom, pos, None)):
                left = pos
            else:
                right = pos
        return right


class FlatGenomicPositionTable(GenomicPositionTable):
    """In-memory genomic position table."""

    FORMAT_DEF = {
        # parameters are <column separator>, <strip_chars>, <space replacement>
        "mem": (None, " \t\n\r", True),
        "tsv": ("\t", "\n\r", False),
        "csv": (",", "\n\r", False)
    }

    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 str_stream, fileformat):
        self.format = fileformat
        self.str_stream = str_stream
        self.records_by_chr: dict[str, Any] = {}
        super().__init__(genomic_resource, table_definition)

    def load(self):
        clmn_sep, strip_chars, space_replacement = \
            FlatGenomicPositionTable.FORMAT_DEF[self.format]
        if self.header_mode == "file":
            hcs = None
            for line in self.str_stream:
                line = line.strip(strip_chars)
                if not line:
                    continue
                hcs = line.split(clmn_sep)
                break
            if not hcs:
                raise ValueError("No header found")

            self.header = tuple(hcs)
        col_number = len(self.header) if self.header else None

        self._set_special_column_indexes()

        other_indices, other_columns = self._get_other_columns()

        records_by_chr = collections.defaultdict(list)
        for line in self.str_stream:
            line = line.strip(strip_chars)
            if not line:
                continue
            columns = tuple(line.split(clmn_sep))
            if col_number and len(columns) != col_number:
                raise ValueError("Inconsistent number of columns")

            col_number = len(columns)
            if space_replacement:
                columns = tuple("" if v == "EMPTY" else v for v in columns)
            chrom = columns[self.chrom_column_i]
            ps_begin = int(columns[self.pos_begin_column_i])
            ps_end = int(columns[self.pos_end_column_i])

            ref_key, alt_key = None, None
            if "ref" in self.definition:
                ref_key = self.get_special_column_index("ref") \
                    if self.header_mode == "none" \
                    else self.get_special_column_name("ref")
            if "alt" in self.definition:
                alt_key = self.get_special_column_index("alt") \
                    if self.header_mode == "none" \
                    else self.get_special_column_name("alt")

            if other_indices and other_columns:
                attributes = dict(zip(other_columns, (columns[i] for i in other_indices)))
            else:
                attributes = {str(idx): value for idx, value in enumerate(columns)
                              if idx not in (self.chrom_column_i,
                                             self.pos_begin_column_i,
                                             self.pos_end_column_i)}
            ref, alt = attributes.get(ref_key), attributes.get(alt_key)
            records_by_chr[chrom].append(
                Line(chrom, ps_begin, ps_end, attributes, self.score_definitions,
                     ref=ref, alt=alt)
            )
        self.records_by_chr = {
            c: sorted(pss, key=lambda l: (l[:3], l.ref, l.alt)) for c, pss in records_by_chr.items()
        }
        self._build_chrom_mapping()

    def get_file_chromosomes(self):
        return sorted(self.records_by_chr.keys())

    def get_all_records(self):
        for chrom in self.get_chromosomes():
            if self.chrom_map:
                if chrom not in self.chrom_map:
                    continue
                fchrom = self.chrom_map[chrom]
                for line in self.records_by_chr[fchrom]:
                    yield Line(
                        chrom, line.pos_begin, line.pos_end,
                        line.attributes, self.score_definitions
                    )
            else:
                for line in self.records_by_chr[chrom]:
                    yield line

    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):

        if self.chrom_map:
            fch = self.chrom_map[chrom]
        else:
            fch = chrom
        for line in self.records_by_chr[fch]:
            if pos_begin and pos_begin > line.pos_end:
                continue
            if pos_end and pos_end < line.pos_begin:
                continue
            if self.chrom_map:
                yield Line(
                    chrom, line.pos_begin, line.pos_end,
                    line.attributes, self.score_definitions
                )
            else:
                yield line

    def close(self):
        """Nothing to close."""


class TabixGenomicPositionTable(GenomicPositionTable):
    """Represents Tabix file genome position table."""

    BUFFER_MAXSIZE = 20_000

    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 variants_file: PysamFile):
        super().__init__(genomic_resource, table_definition)
        self.jump_threshold: int = 2_500
        if "jump_threshold" in self.definition:
            threshold = self.definition["jump_threshold"]
            if threshold == "none":
                self.jump_threshold = 0
            else:
                self.jump_threshold = int(threshold)

        self.jump_threshold = min(
            self.jump_threshold, self.BUFFER_MAXSIZE // 2)

        self._last_call: Tuple[str, int, Optional[int]] = "", -1, -1
        self.buffer = LineBuffer()
        self.stats: Counter = Counter()
        # pylint: disable=no-member
        self.variants_file: PysamFile = variants_file
        self.line_iterator = None

    def load(self):
        if self.header_mode == "file":
            self.header = self._get_header()

        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_header(self):
        return tuple(self.variants_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self):
        return self.variants_file.contigs

    def _map_file_chrom(self, chrom: str) -> str:
        """Transfrom chromosome name to the chromosomes from score file."""
        if self.chrom_map:
            return self.chrom_map.get(chrom)
        return chrom

    def _map_result_chrom(self, chrom: str) -> str:
        """Transfroms chromosome from score file to the genome chromosomes."""
        if self.chrom_map:
            return self.rev_chrom_map[chrom]
        return chrom

    def _transform_result(self, line: Line) -> Line:
        rchrom = self._map_result_chrom(line.chrom)
        if rchrom is None:
            return None
        return Line(
            rchrom, line.pos_begin, line.pos_end,
            line.attributes, line.score_defs,
            allele_index=line.allele_index
        )

    def get_all_records(self):
        # pylint: disable=no-member
        for line in self.get_line_iterator():
            if self.chrom_map:
                if line.chrom in self.rev_chrom_map:
                    yield self._transform_result(line)
                else:
                    continue
            else:
                yield line

    def _should_use_sequential_seek_forward(self, chrom, pos) -> bool:
        """Determine if sequentially seeking forward is appropriate.

        Determine whether to use sequential access or jump-ahead
        optimization for a given chromosome and position. Sequential access is
        used if the position is on the same chromosome and the distance between
        it and the last line in the buffer is less than the jump threshold.
        """
        if self.jump_threshold == 0:
            return False

        assert chrom is not None
        if len(self.buffer) == 0:
            return False

        last_chrom, _last_begin, last_end, *_ = self.buffer.peek_last()
        if chrom != last_chrom:
            return False
        if pos < last_end:
            return False

        if pos - last_end >= self.jump_threshold:
            return False
        return True

    def _sequential_seek_forward(self, chrom, pos):
        """Advance the buffer forward to the given position."""
        assert len(self.buffer) > 0
        assert self.jump_threshold > 0

        last_chrom, last_begin, last_end, *_ = self.buffer.peek_last()
        assert chrom == last_chrom
        assert pos >= last_begin

        self.stats["sequential seek forward"] += 1

        for row in self._gen_from_tabix(chrom, pos, buffering=True):
            last_chrom, last_begin, last_end, *_ = row
        return bool(pos >= last_end)

    def _gen_from_tabix(self, chrom, pos, buffering=True):
        try:
            while True:
                line = next(self.line_iterator)

                if buffering:
                    self.buffer.append(line)

                if line.chrom != chrom:
                    return
                if pos is not None and line.pos_begin > pos:
                    return
                result = self._transform_result(line)
                self.stats["yield from tabix"] += 1
                if result:
                    yield result
        except StopIteration:
            pass

    def _gen_from_buffer_and_tabix(self, chrom, beg, end):
        for line in self.buffer.fetch(chrom, beg, end):
            self.stats["yield from buffer"] += 1
            result = self._transform_result(line)
            if result:
                yield result
        _, _last_beg, last_end, *_ = self.buffer.peek_last()
        if end < last_end:
            return

        yield from self._gen_from_tabix(chrom, end, buffering=True)

    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):
        self.stats["calls"] += 1

        if chrom not in self.get_chromosomes():
            logger.error(
                "chromosome %s not found in the tabix file "
                "from %s; %s",
                chrom, self.genomic_resource.resource_id, self.definition)
            raise ValueError(
                f"The chromosome {chrom} is not part of the table.")

        fchrom = self._map_file_chrom(chrom)
        buffering = True
        if pos_begin is None:
            pos_begin = 1
        if pos_end is None or pos_end - pos_begin > self.BUFFER_MAXSIZE:
            buffering = False
            self.stats["without buffering"] += 1
        else:
            self.stats["with buffering"] += 1

        prev_call_chrom, _prev_call_beg, prev_call_end = self._last_call
        self._last_call = fchrom, pos_begin, pos_end

        if buffering and len(self.buffer) > 0 and prev_call_chrom == fchrom:

            first_chrom, first_beg, _first_end, *_ = self.buffer.peek_first()
            if first_chrom == fchrom and prev_call_end is not None \
                    and pos_begin > prev_call_end and pos_end < first_beg:

                assert first_chrom == prev_call_chrom
                self.stats["not found"] += 1
                return

            if self.buffer.contains(fchrom, pos_begin):
                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    self.stats["yield from buffer and tabix"] += 1
                    yield row

                self.buffer.prune(fchrom, pos_begin)
                return

            if self._should_use_sequential_seek_forward(fchrom, pos_begin):
                self._sequential_seek_forward(fchrom, pos_begin)

                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    yield row

                self.buffer.prune(fchrom, pos_begin)
                return

        # without using buffer
        self.line_iterator = self.get_line_iterator(fchrom, pos_begin - 1)

        for row in self._gen_from_tabix(fchrom, pos_end, buffering=buffering):
            yield row

        self.buffer.prune(fchrom, pos_begin)

    def get_line_iterator(self, *args):
        self.stats["tabix fetch"] += 1
        self.buffer.clear()

        other_indices, other_columns = self._get_other_columns()

        ref_key, alt_key = None, None
        if "ref" in self.definition:
            ref_key = self.get_special_column_index("ref") \
                if self.header_mode == "none" \
                else self.get_special_column_name("ref")
        if "alt" in self.definition:
            alt_key = self.get_special_column_index("alt") \
                if self.header_mode == "none" \
                else self.get_special_column_name("alt")

        for raw in self.variants_file.fetch(*args, parser=pysam.asTuple()):
            if other_indices and other_columns:
                attributes = dict(zip(other_columns, (raw[i] for i in other_indices)))
            else:
                attributes = {str(idx): value for idx, value in enumerate(raw)
                              if idx not in (self.chrom_column_i,
                                             self.pos_begin_column_i,
                                             self.pos_end_column_i)}
            ref, alt = attributes.get(ref_key), attributes.get(alt_key)
            yield Line(
                raw[self.chrom_column_i],
                raw[self.pos_begin_column_i],
                raw[self.pos_end_column_i],
                attributes, self.score_definitions,
                ref=ref, alt=alt,
            )

    def close(self):
        self.variants_file.close()
        print(
            f"genome position table: ({self.genomic_resource.resource_id})>",
            self.stats)


class VCFGenomicPositionTable(TabixGenomicPositionTable):
    """Represents a VCF file genome position table."""

    CHROM = "CHROM"
    POS_BEGIN = "POS"
    POS_END = "POS"

    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 variants_file: PysamFile):
        super().__init__(genomic_resource, table_definition, variants_file)
        if "scores" not in self.definition:
            # We can safely put 'None' for most fields, because
            # pysam casts the values to their correct types beforehand
            # We only need to join tuple values, as annotators cannot
            # handle tuples
            tuple_conv = lambda x: ",".join(map(str, x))
            self.score_definitions = {
                key: ScoreDef(
                    key,
                    value.description,
                    None,
                    tuple_conv if value.number not in (1, "A", "R") else None,
                    tuple(),
                    None,
                    None
                ) for key, value in self.variants_file.header.info.items()
            }

    def _get_header(self):
        return ("CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO")

    def get_file_chromosomes(self):
        return self.variants_file.header.contigs

    def get_line_iterator(self, *args):
        self.stats["tabix fetch"] += 1
        self.buffer.clear()
        for raw_line in self.variants_file.fetch(*args):
            for allele_index, alt in enumerate(raw_line.alts or [None]):
                yield Line(
                    raw_line.contig, raw_line.pos, raw_line.pos, {},
                    self.score_definitions,
                    allele_index=allele_index if alt is not None else None,
                    ref=raw_line.ref,
                    alt=alt,
                    info=raw_line.info,
                    info_meta=raw_line.header.info,
                )


def open_genome_position_table(
        resource: GenomicResource, table_definition: dict):
    """Open a genome position table from genomic resource."""
    filename = table_definition["filename"]

    if filename.endswith(".bgz"):
        default_format = "tabix"
    elif filename.endswith(".vcf.gz"):
        default_format = "vcf_info"
    elif filename.endswith(".txt") or filename.endswith(".txt.gz") or \
            filename.endswith(".tsv") or filename.endswith(".tsv.gz"):
        default_format = "tsv"
    elif filename.endswith(".csv") or filename.endswith(".csv.gz"):
        default_format = "csv"
    else:
        default_format = "mem"

    table_format = table_definition.get("format", default_format)

    table: GenomicPositionTable

    if table_format in ["mem", "csv", "tsv"]:
        with resource.open_raw_file(
                filename, mode="rt", uncompress=True) as infile:
            table = FlatGenomicPositionTable(
                resource, table_definition, infile, table_format)
            table.load()
        return table
    if table_format == "tabix":
        table = TabixGenomicPositionTable(
            resource, table_definition, resource.open_tabix_file(filename))
        table.load()
        return table
    if table_format == "vcf_info":
        table = VCFGenomicPositionTable(
            resource, table_definition, resource.open_vcf_file(filename))
        table.load()
        return table

    raise ValueError("unknown table format")


def save_as_tabix_table(
        table: GenomicPositionTable,
        full_file_path: str):
    """Save a genome position table as Tabix table."""
    tmp_file = full_file_path + ".tmp"
    with open(tmp_file, "wt", encoding="utf8") as text_file:
        if table.header_mode != "none":
            print("#" + "\t".join(table.get_column_names()), file=text_file)
        for rec in table.get_all_records():
            print(*rec, sep="\t", file=text_file)
    # pylint: disable=no-member
    pysam.tabix_compress(tmp_file, full_file_path, force=True)
    os.remove(tmp_file)

    pysam.tabix_index(full_file_path, force=True,
                      seq_col=table.chrom_column_i,
                      start_col=table.pos_begin_column_i,
                      end_col=table.pos_end_column_i)
