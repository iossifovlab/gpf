import collections
from typing import Optional, Tuple, Any, Deque, Union, Dict, Generator
# pylint: disable=no-member
import pysam  # type: ignore

from .table import ScoreDef

class Line:
    """Represents a line read from a genomic position table.

    Provides uniform access to a number of important columns - chromosome,
    start position, end position, reference allele and alternative allele,
    as well as access to values of configured score columns. Score columns
    are parsed depending on their configuration and the type of genome position
    table they are read from.
    """

    def __init__(
        self,
        chrom: str,
        pos_begin: Union[int, str],
        pos_end: Union[int, str],
        attributes: Dict[str, Any],
        score_defs: Dict[str, ScoreDef],
        ref: Optional[str] = None,
        alt: Optional[str] = None,
    ):
        self.chrom: str = chrom
        self.pos_begin: int = int(pos_begin)
        self.pos_end: int = int(pos_end)
        self.attributes: Dict[str, Any] = attributes
        self.score_defs: Dict[str, ScoreDef] = score_defs
        self.ref: Optional[str] = ref
        self.alt: Optional[str] = alt

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

    def _fetch_score_value(self, key):
        return self.attributes[key]

    def get(self, key: str, default=None):
        """Universal getter function."""
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
        """Get and parse configured score from line."""
        key = self.score_defs[score_id].col_key
        value = self._fetch_score_value(key)
        if score_id in self.score_defs:
            col_def = self.score_defs[score_id]
            if value in col_def.na_values:
                value = None
            elif col_def.value_parser is not None:
                value = col_def.value_parser(value)
        return value

    def get_available_scores(self):
        return tuple(self.score_defs.keys())


class VCFLine(Line):
    """Line adapter for lines derived from a VCF file.

    Implements functionality for handling multi-allelic variants
    and INFO fields.
    """

    def __init__(
        self,
        chrom: str,
        pos_begin: Union[int, str],
        pos_end: Union[int, str],
        score_defs: Dict[str, ScoreDef],
        ref: str,
        alt: Optional[str],
        allele_index: Optional[int],
        info: pysam.VariantRecordInfo,
        info_meta: pysam.VariantHeaderMetadata,
    ):
        super().__init__(
            chrom, pos_begin, pos_end, {}, score_defs, ref, alt
        )
        # Used for support of multiallelic variants in VCF files.
        # The allele index is None if the variant for this line
        # is missing its ALT, i.e. its value is '.'
        self.allele_index: Optional[int] = allele_index
        # VCF INFO fields column
        self.info: pysam.VariantRecordInfo = info
        # VCF INFO fields metadata - holds metadata for info fields
        # such as description, type, whether the value is a tuple
        # of multiple score values, etc.
        self.info_meta: pysam.VariantHeaderMetadata = info_meta

    def _fetch_score_value(self, key):
        value, meta = self.info.get(key), self.info_meta.get(key)
        if isinstance(value, tuple):
            if meta.number == "A" and self.allele_index is not None:
                value = value[self.allele_index]
            elif meta.number == "R":
                value = value[
                    self.allele_index + 1
                    if self.allele_index is not None
                    else 0  # Get reference allele value if ALT is '.'
                ]
        return value


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

    def peek_last(self) -> Line:
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
        if bchrom is None or bbeg is None or bend is None:
            return False
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
