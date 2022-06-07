import abc
import collections
import os
import logging

from typing import Optional, Tuple, Any, Deque

import pysam  # type: ignore
from box import Box  # type: ignore

from dae.genomic_resources.repository import GenomicResource

logger = logging.getLogger(__name__)


class GenomicPositionTable(abc.ABC):
    CHROM = "chrom"
    POS_BEGIN = "pos_begin"
    POS_END = "pos_end"

    def __init__(self, genomic_resource: GenomicResource, table_definition):
        self.genomic_resource = genomic_resource

        self.definition = Box(table_definition)
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
            for hi, hc in enumerate(self.header):
                if not isinstance(hc, str):
                    raise ValueError(f"The {hi}-th header {hc} in the table "
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

    def _build_chrom_mapping(self):
        self.chrom_map = None
        self.chrom_order = self.get_file_chromosomes()

        if "chrom_mapping" in self.definition:
            mapping = self.definition.chrom_mapping
            if "filename" in mapping:
                self.chrom_map = {}
                self.chrom_order = []
                with self.genomic_resource.open_raw_file(
                        mapping["filename"], "rt") as F:
                    hcs = F.readline().strip("\n\r").split("\t")
                    if hcs != ["chrom", "file_chrom"]:
                        raise ValueError(
                            f"The chromosome mapping file "
                            f"{mapping['file']} in resource "
                            f"{self.genomic_resource.get_id()} is "
                            f"is expected to have the two columns "
                            f"'chrom' and 'file_chrom'")
                    for line in F:
                        ch, fch = line.strip("\n\r").split("\t")
                        assert ch not in self.chrom_map
                        self.chrom_map[ch] = fch
                        self.chrom_order.append(ch)
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

    @abc.abstractmethod
    def load(self):
        pass

    @abc.abstractmethod
    def get_all_records(self):
        pass

    @abc.abstractmethod
    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):
        """
        Returns an iterable over the records in the range [pos_begin, pos_end].
        The interval is closed on both sides and 1-based.
        """

    @abc.abstractmethod
    def close(self):
        """Close the resource."""

    def get_chromosomes(self):
        return self.chrom_order

    @abc.abstractmethod
    def get_file_chromosomes(self):
        """
        This is to be overwritten by the subclass. It should return a list of
        the chromomes in the file in the order determinted by the file.
        """

    def get_chromosome_length(self, chrom, step=1_000_000):
        """
        Returns the length of a chromosome (or contig). The returned value is
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
    FORMAT_DEF = {
        # parameters are <column separator>, <strip_chars>, <space replacemnt>
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

        records_by_chr = collections.defaultdict(list)
        for line in self.str_stream:
            line = line.strip(strip_chars)
            if not line:
                continue
            cs = tuple(line.split(clmn_sep))
            if col_number and len(cs) != col_number:
                raise ValueError("Inconsistent number of columns")
            else:
                col_number = len(cs)
            if space_replacement:
                cs = tuple(["" if v == "EMPTY" else v for v in cs])
            ch = cs[self.chrom_column_i]
            ps_begin = int(cs[self.pos_begin_column_i])
            ps_end = int(cs[self.pos_end_column_i])
            records_by_chr[ch].append((ps_begin, ps_end, cs))
        self.records_by_chr = {
            c: sorted(pss) for c, pss in records_by_chr.items()}

        self._build_chrom_mapping()

    def get_file_chromosomes(self):
        return sorted(self.records_by_chr.keys())

    def get_all_records(self):
        for ch in self.get_chromosomes():
            if self.chrom_map:
                if ch not in self.chrom_map:
                    continue
                fch = self.chrom_map[ch]
                pss = self.records_by_chr[fch]
                for _, _, cs in pss:
                    csl = list(cs)
                    csl[self.chrom_column_i] = ch
                    yield tuple(csl)
            else:
                pss = self.records_by_chr[ch]
                for _, _, cs in pss:
                    yield cs

    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):

        if self.chrom_map:
            fch = self.chrom_map[chrom]
        else:
            fch = chrom
        for ps_begin, ps_end, cs in self.records_by_chr[fch]:
            if pos_begin and pos_begin > ps_end:
                continue
            if pos_end and pos_end < ps_begin:
                continue
            if self.chrom_map:
                csl = list(cs)
                csl[self.chrom_column_i] = chrom
                yield tuple(csl)
            else:
                yield cs

    def close(self):
        """Nothing to close."""


class LineBuffer:

    def __init__(self):
        self.deque: Deque = collections.deque()

    def __len__(self):
        return len(self.deque)

    def clear(self):
        self.deque.clear()
    
    def append(self, chrom: str, pos_begin: int, pos_end: int, line: Any):
        if len(self.deque) > 0 and self.peek_first()[0] != chrom:
            self.clear()
        self.deque.append((chrom, pos_begin, pos_end, line))

    def peek_first(self):
        return self.deque[0]

    def pop_first(self):
        return self.deque.popleft()

    def peek_last(self):
        if len(self.deque) == 0:
            return None, None, None, None
        return self.deque[-1]

    def region(self):
        if len(self.deque) == 0:
            return None, None, None

        first_chrom, first_begin, first_end, _ = self.peek_first()
        if len(self.deque) == 1:
            return first_chrom, first_begin, first_end

        last_chrom, _, last_end, _ = self.peek_last()
        if first_chrom != last_chrom:
            self.clear()
            return None, None, None
        if first_end > last_end:
            self.clear()
            return None, None, None
        return first_chrom, first_begin, last_end

    def prune(self, chrom: str, pos: int) -> None:
        if len(self.deque) == 0:
            return

        first_chrom, _first_beg, _, _ = self.peek_first()
        if chrom != first_chrom:
            self.clear()
            return

        while len(self.deque) > 0:
            _, _first_beg, first_end, _ = self.deque[0]

            if pos <= first_end:
                break
            self.deque.popleft()

    def contains(self, chrom: str, pos: int) -> bool:
        bchrom, bbeg, bend = self.region()

        if chrom == bchrom and pos >= bbeg and pos <= bend:
            return True
        return False

    def find_index(self, chrom: str, pos: int) -> int:
        if len(self.deque) == 0:
            return -1
        if not self.contains(chrom, pos):
            return -1
        
        if len(self.deque) == 1:
            return 0
        
        first_index = 0
        last_index = len(self.deque) - 1
        depth = 0
        while True:
            depth += 1
            mid_index = (last_index - first_index) // 2 + first_index
            if last_index <= first_index:
                break

            _, mid_beg, mid_end, _ = self.deque[mid_index]
            if pos >= mid_beg and pos <= mid_end:
                break

            if depth >= 100:
                logger.error(
                    "chrom=%s; pos=%s; region=%s; "
                    "first_index=%s; last_index=%s; "
                    "mid_index=%s; "
                    "mid_beg=%s; mid_end=%s; ",
                    chrom, pos, self.region(), first_index, last_index,
                    mid_index, mid_beg, mid_end
                )
                logger.error("deque: %s", self.deque)

            if pos < mid_beg:
                last_index = mid_index - 1
            else:
                first_index = mid_index + 1

        while mid_index > 0:
            _, prev_beg, _prev_end, _ = self.deque[mid_index - 1]
            if pos > prev_beg:
                break
            mid_index -= 1

        for index in range(mid_index, len(self.deque)):
            _, t_beg, t_end, _ = self.deque[index]
            if pos >= t_beg and pos <= t_end:
                mid_index = index
                break
            if t_beg >= pos:
                mid_index = index
                break

        return mid_index

    def fetch(self, chrom, pos_begin, pos_end):
        beg_index = self.find_index(chrom, pos_begin)
        if beg_index == -1:
            return

        for index in range(beg_index, len(self.deque)):
            row = self.deque[index]
            _rchrom, rbeg, rend, _rline = row
            if rend < pos_begin:
                continue
            if pos_end is not None and rbeg > pos_end:
                break
            yield row


class TabixGenomicPositionTable(GenomicPositionTable):
    BUFFER_MAXSIZE = 20_000

    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 tabix_file: pysam.TabixFile):  # pylint: disable=no-member
        super().__init__(genomic_resource, table_definition)

        self.jump_threshold: int = 2_500
        if "jump_threshold" in self.definition:
            jt = self.definition["jump_threshold"]
            if jt == "none":
                self.jump_threshold = 0
            else:
                self.jump_threshold = int(jt)

        self.jump_threshold = min(self.jump_threshold, self.BUFFER_MAXSIZE//2)

        self.tabix_file: pysam.TabixFile = tabix_file  # pylint: disable=no-member
        self.tabix_iterator = None

        self._last_call: Tuple[str, int, Optional[int]] = "", -1, -1
        self.buffer = LineBuffer()

    def load(self):
        if self.header_mode == "file":
            self.header = self._get_tabix_header()

        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_tabix_header(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self):
        return self.tabix_file.contigs

    def _map_file_chrom(self, chrom: str) -> str:
        """
        Transfroms chromosome (contig) name to the chromosomes (contigs)
        used in the score table
        """
        if self.chrom_map:
            return self.chrom_map.get(chrom)
        return chrom

    def _map_result_chrom(self, chrom: str) -> str:
        """
        Transfroms chromosome (contig) from score table to the 
        chromosomes (contigs) used in the genome corrdinates.
        """
        if self.chrom_map:
            return self.rev_chrom_map[chrom]
        else:
            return chrom

    def _transform_result(self, line):
        result = list(line)
        rchrom = self._map_result_chrom(result[self.chrom_column_i])
        if rchrom is None:
            return None
        result[self.chrom_column_i] = rchrom
        return tuple(result)

    def get_all_records(self):
        for line in self.tabix_file.fetch(parser=pysam.asTuple()):  # pylint: disable=no-member
            if self.chrom_map:
                fchrom = line[self.chrom_column_i]
                if fchrom not in self.rev_chrom_map:
                    continue
                result = list(line)
                result[self.chrom_column_i] = self.rev_chrom_map[fchrom]
                yield tuple(result)
            else:
                yield tuple(line)

    def _should_use_sequential(self, chrom, pos):
        if self.jump_threshold == 0:
            return False

        assert chrom is not None
        if len(self.buffer) == 0:
            return False

        last_chrom, _last_begin, last_end, _ = self.buffer.peek_last()
        if chrom != last_chrom:
            return False
        if pos < last_end:
            return False

        if pos - last_end >= self.jump_threshold:
            return False
        return True

    def _gen_from_tabix(self, chrom, pos, buffering=True):
        try:
            while True:
                line = next(self.tabix_iterator)  # type: ignore
                line_chrom = line[self.chrom_column_i]
                line_beg = int(line[self.pos_begin_column_i])
                line_end = int(line[self.pos_end_column_i])

                if buffering:
                    self.buffer.append(line_chrom, line_beg, line_end, line)

                if line_chrom != chrom:
                    return
                if pos is not None and line_beg > pos:
                    return
                result = self._transform_result(line)
                if result:
                    yield line_chrom, line_beg, line_end, result
        except StopIteration:
            pass

    def _sequential_rewind(self, chrom, pos):
        assert len(self.buffer) > 0
        assert self.jump_threshold > 0

        last_chrom, last_begin, last_end, _ = self.buffer.peek_last()
        assert chrom == last_chrom
        assert pos >= last_begin

        for row in self._gen_from_tabix(chrom, pos, buffering=True):
            last_chrom, last_begin, last_end, _ = row
        if pos >= last_end:
            return True
        else:
            return False

    def _gen_from_buffer_and_tabix(self, chrom, beg, end):
        for row in self.buffer.fetch(chrom, beg, end):
            line_chrom, line_beg, line_end, line = row
            result = self._transform_result(line)
            if result:
                yield line_chrom, line_beg, line_end, result
        _, _last_beg, last_end, _ = self.buffer.peek_last()
        if end < last_end:
            return

        yield from self._gen_from_tabix(chrom, end, buffering=True)

    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):

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
        
        prev_call_chrom, _prev_call_beg, prev_call_end = self._last_call

        if not buffering or len(self.buffer) == 0 or prev_call_chrom != fchrom:
            # no buffering
            self._last_call = "", -1, None
        else:
            self._last_call = fchrom, pos_begin, pos_end

            first_chrom, first_beg, _first_end, _ = self.buffer.peek_first()
            if first_chrom == fchrom and prev_call_end is not None \
                    and pos_begin > prev_call_end and pos_end < first_beg:

                assert first_chrom == prev_call_chrom
                return

            elif self.buffer.contains(fchrom, pos_begin):
                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    _, _, _, line = row
                    yield line

                self.buffer.prune(fchrom, pos_begin)
                return

            elif self._should_use_sequential(fchrom, pos_begin):
                self._sequential_rewind(fchrom, pos_begin)

                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    _, _, _, line = row
                    yield line

                self.buffer.prune(fchrom, pos_begin)
                return

        self.tabix_iterator = self.tabix_file.fetch(
            fchrom, pos_begin - 1, None, parser=pysam.asTuple())  # pylint: disable=no-member
        self.buffer.clear()

        for row in self._gen_from_tabix(fchrom, pos_end, buffering=buffering):
            _, _, _, line = row
            yield line

        self.buffer.prune(fchrom, pos_begin)

    def close(self):
        self.tabix_file.close()


def open_genome_position_table(gr: GenomicResource, table_definition: dict):
    filename = table_definition["filename"]

    if filename.endswith(".bgz"):
        default_format = "tabix"
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
        with gr.open_raw_file(filename, mode="rt", uncompress=True) as F:
            table = FlatGenomicPositionTable(
                gr, table_definition, F, table_format)
            table.load()
        return table
    elif table_format == "tabix":
        table = TabixGenomicPositionTable(
            gr, table_definition, gr.open_tabix_file(filename))
        table.load()
        return table
    else:
        raise ValueError("unknown table format")


def save_as_tabix_table(table: GenomicPositionTable,
                        full_file_path: str):
    tmp_file = full_file_path + ".tmp"
    with open(tmp_file, "wt", encoding="utf8") as text_file:
        if table.header_mode != "none":
            print("#" + "\t".join(table.get_column_names()), file=text_file)
        for rec in table.get_all_records():
            print(*rec, sep="\t", file=text_file)
    pysam.tabix_compress(tmp_file, full_file_path, force=True)  # pylint: disable=no-member
    os.remove(tmp_file)

    pysam.tabix_index(full_file_path, force=True,  # pylint: disable=no-member
                      seq_col=table.chrom_column_i,
                      start_col=table.pos_begin_column_i,
                      end_col=table.pos_end_column_i)
