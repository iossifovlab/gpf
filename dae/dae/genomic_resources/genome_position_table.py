import abc
import collections
import pysam  # type: ignore
import os
import logging

from typing import Optional, Tuple, List, Any, Deque

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

        # handling the 'header' property
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
                        mapping["filename"], "rt", True) as F:
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

                if 'del_prefix' in mapping:
                    pref = mapping.del_prefix
                    new_chromosomes = [
                        ch[len(pref):] if ch.startswith(pref) else ch
                        for ch in new_chromosomes
                    ]

                if 'add_prefix' in mapping:
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
        except Exception:
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
        except ValueError:
            raise ValueError(f"The {index_prop} property in the table "
                             f"definition should be an integer.")

    def get_special_column_index(self, key):
        if self.header_mode == "none":
            return self._get_index_prop_for_special_column(key)
        try:
            return self._get_index_prop_for_special_column(key)
        except KeyError:
            column_name = self.get_special_column_name(key)
            try:
                return self.header.index(column_name)
            except ValueError:
                raise ValueError(f"The column {column_name} for the "
                                 f"special column {key} is not in the "
                                 f"header.")

    def get_special_column_name(self, key):
        if self.header_mode == "none":
            raise AttributeError("The table has no header.")
        if key in self.definition:
            if "name" in self.definition[key]:
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
        pass

    @abc.abstractmethod
    def close(self):
        pass

    def get_chromosomes(self):
        return self.chrom_order

    @abc.abstractmethod
    def get_file_chromosomes(self):
        '''
        This is to be overwritten by the subclass. It should return a list of
        the chromomes in the file in the order determinted by the file.
        '''
        pass


class FlatGenomicPositionTable(GenomicPositionTable):
    FORMAT_DEF = {
        # parameters are <column separator>, <strip_chars>, <space replacemnt>
        "mem": (None, " \t\n\r", True),
        "tsv": ("\t", "\n\r", False),
        "csv": (",", "\n\r", False)
    }

    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 str_stream, format):
        self.format = format
        self.str_stream = str_stream
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
                raise Exception("No header found")

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
                raise Exception("Inconsistent number of columns")
            else:
                col_number = len(cs)
            if space_replacement:
                cs = tuple(["" if v == 'EMPTY' else v for v in cs])
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

    def get_records_in_region(self, ch: str, beg: int = None, end: int = None):
        if self.chrom_map:
            fch = self.chrom_map[ch]
        else:
            fch = ch
        for ps_begin, ps_end, cs in self.records_by_chr[fch]:
            if beg and beg > ps_end:
                continue
            if end and end < ps_begin:
                continue
            if self.chrom_map:
                csl = list(cs)
                csl[self.chrom_column_i] = ch
                yield tuple(csl)
            else:
                yield cs

    def close(self):
        pass


class LineBuffer:

    def __init__(self):
        self.deque: Deque = collections.deque()
        self.maxlen = 0
        self.find_count = 0
        self.maxdepth = 0
        self.fetch_count = 0
        self.append_count = 0
        self.prune_count = 0

    def __len__(self):
        return len(self.deque)

    def clear(self):
        self.deque.clear()
    
    def append(self, chrom: str, pos_begin: int, pos_end: int, line: Any):
        self.append_count += 1

        if len(self.deque) > 0 and self.peek_first()[0] != chrom:
            self.clear()
        self.deque.append((chrom, pos_begin, pos_end, line))
        if len(self.deque) > self.maxlen:
            self.maxlen = len(self.deque)

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

    PRUNE_CUTOFF = 50

    def prune(self, chrom: str, beg: int) -> None:
        self.prune_count += 1

        if len(self.deque) == 0:
            return

        first_chrom, first_beg, _, _ = self.peek_first()
        if chrom != first_chrom:
            self.clear()
            return

        pos = beg - self.PRUNE_CUTOFF
        while len(self.deque) > 0:
            _, first_beg, first_end, _ = self.deque[0]

            if pos <= first_end:
                break
            self.deque.popleft()

    def contains(self, chrom: str, pos: int) -> bool:
        bchrom, bbeg, bend = self.region()

        if chrom == bchrom and pos >= bbeg and pos <= bend:
            return True
        return False

    def find_index(self, chrom: str, pos: int) -> int:
        self.find_count += 1

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
                    f"chrom={chrom}; pos={pos}; region={self.region()}; "
                    f"first_index={first_index}; last_index={last_index}; "
                    f"mid_index={mid_index}; "
                    f"mid_beg={mid_beg}; mid_end={mid_end}; "
                )
                logger.error(f"{self.deque}")

            if pos < mid_beg:
                last_index = mid_index - 1
            else:
                first_index = mid_index + 1

        while mid_index > 0:
            _, prev_beg, prev_end, _ = self.deque[mid_index - 1]
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

        if depth > self.maxdepth:
            self.maxdepth = depth

        return mid_index

    def fetch(self, chrom, pos_begin, pos_end):
        self.fetch_count += 1

        beg_index = self.find_index(chrom, pos_begin)
        if beg_index == -1:
            return

        for index in range(beg_index, len(self.deque)):
            row = self.deque[index]
            rchrom, rbeg, rend, rline = row
            if rend < pos_begin:
                continue
            if pos_end is not None and rbeg > pos_end:
                break
            yield row

    def dump_stats(self, resource_id):
        logger.info(
            f"score {resource_id}; "
            f"buffer stats: len={len(self.deque)} "
            f"(maxlen={self.maxlen}); "
            f"append={self.append_count}; "
            f"prune={self.prune_count}; "
            f"find={self.find_count} (depth={self.maxdepth}); "
            f"fetch={self.fetch_count}; "
            f"region={self.region()}"
        )

        # logger.debug(f"score {resource_id}: {self.deque}")


class TabixGenomicPositionTable(GenomicPositionTable):
    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 tabix_file: pysam.TabixFile):
        self.tabix_file: pysam.TabixFile = tabix_file
        super().__init__(genomic_resource, table_definition)

        self.tabix_iterator = None

        self.jump_threshold: int = 2_500
        self._last_call: Tuple[str, int, int] = "", -1, -1

        self.empty_count = 0
        self.buffer_count = 0
        self.sequential_count = 0
        self.direct_count = 0
        self.buffer = LineBuffer()

    def dump_stats(self):
        logger.info(
            f"score {self.genomic_resource.resource_id}; "
            f"empty/buffer/sequential/direct ("
            f"{self.empty_count}/{self.buffer_count}/"
            f"{self.sequential_count}/{self.direct_count}); "
        )

    def load(self):
        if self.header_mode == "file":
            self.header = self._get_tabix_header()

        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_tabix_header(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self):
        return self.tabix_file.contigs

    def _update_buffer(self, line):
        line_chrom = line[self.chrom_column_i]
        line_beg = int(line[self.pos_begin_column_i])
        line_end = int(line[self.pos_end_column_i])
        
        self.buffer.append(line_chrom, line_beg, line_end, line)
        return line_chrom, line_beg, line_end, line

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
        for line in self.tabix_file.fetch(parser=pysam.asTuple()):
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
        assert chrom is not None
        if len(self.buffer) == 0:
            return False

        last_chrom, last_begin, last_end, _ = self.buffer.peek_last()
        if chrom != last_chrom:
            return False
        if pos < last_end:
            return False

        if pos - last_end >= self.jump_threshold:
            return False
        return True

    def _gen_from_tabix(self, chrom, end):
        try:
            while True:
                line = next(self.tabix_iterator)  # type: ignore
                line_chrom, line_beg, line_end, _ = self._update_buffer(line)

                if line_chrom != chrom:
                    return
                if end is not None and line_beg > end:
                    return
                result = self._transform_result(line)
                if result:
                    yield line_chrom, line_beg, line_end, result
        except StopIteration:
            pass

    def _sequential_rewind(self, chrom, pos):
        assert len(self.buffer) > 0

        last_chrom, last_begin, last_end, _ = self.buffer.peek_last()
        assert chrom == last_chrom
        assert pos >= last_begin

        for row in self._gen_from_tabix(chrom, pos):
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
        _, last_beg, last_end, _ = self.buffer.peek_last()
        if end < last_end:
            return

        yield from self._gen_from_tabix(chrom, end)

    def get_records_in_region(
            self, chrom: str, beg: int = None, end: int = None):

        if chrom not in self.get_chromosomes():
            logger.error(
                f"chromosome {chrom} not found in the tabix file "
                f"from {self.genomic_resource.resource_id}; "
                f"{self.definition}")
            raise ValueError(
                f"The chromosome {chrom} is not part of the table.")

        fchrom = self._map_file_chrom(chrom)
        if beg is None:
            beg = 1

        self.buffer.dump_stats(self.genomic_resource.resource_id)
        self.dump_stats()

        prev_chrom, prev_beg, prev_end = self._last_call
        self._last_call = fchrom, beg, end

        if end is not None and len(self.buffer) > 0:
            first_chrom, first_beg, first_end, _ = self.buffer.peek_first()
            if first_chrom == fchrom and prev_end is not None \
                    and beg > prev_end and end < first_beg:

                assert first_chrom == prev_chrom
                self.empty_count += 1
                # logger.info(
                #     f"score {self.genomic_resource.resource_id}; "
                #     f"EMPTY ({self.empty_count} times); "
                #     f"current call is {fchrom, beg, end}; "
                #     f"prev call is {prev_chrom, prev_beg, prev_end}; "
                #     f"buffer region is {self.buffer.region()}; "
                # )
                return

            elif self.buffer.contains(fchrom, beg):
                self.buffer_count += 1
                # logger.info(
                #     f"score {self.genomic_resource.resource_id}; "
                #     f"BUFFER ({self.buffer_count} times); "
                #     f"current call is {fchrom, beg, end}; "
                #     f"buffer region is {self.buffer.region()}; "
                # )

                for row in self._gen_from_buffer_and_tabix(fchrom, beg, end):
                    _, _, _, line = row
                    yield line

                self.buffer.dump_stats(self.genomic_resource.resource_id)
                self.buffer.prune(fchrom, beg)
                return

            elif self._should_use_sequential(fchrom, beg):
                self.sequential_count += 1
                # logger.info(
                #     f"score {self.genomic_resource.resource_id}; "
                #     f"SEQUENTIAL ({self.sequential_count} times); "
                #     f"current call is {fchrom, beg, end}; "
                #     f"buffer region is {self.buffer.region()}; "
                # )
                self._sequential_rewind(fchrom, beg)

                for row in self._gen_from_buffer_and_tabix(fchrom, beg, end):
                    _, _, _, line = row
                    yield line

                self.buffer.dump_stats(self.genomic_resource.resource_id)
                self.buffer.prune(fchrom, beg)
                return

        self.tabix_iterator = self.tabix_file.fetch(
            fchrom, beg - 1, None, parser=pysam.asTuple())
        self.buffer.clear()

        self.direct_count += 1
        # logger.info(
        #     f"score {self.genomic_resource.resource_id}; "
        #     f"DIRECT ({self.direct_count} times); "
        #     f"current call is {fchrom, beg, end}; "
        #     f"buffer region is {self.buffer.region()}; "
        # )

        for row in self._gen_from_tabix(fchrom, end):
            _, _, _, line = row
            yield line

        # self.buffer.dump_stats(self.genomic_resource.resource_id)
        self.buffer.prune(fchrom, beg)

    def close(self):
        self.tabix_file.close()


def open_genome_position_table(gr: GenomicResource, table_definition: dict):
    filename = table_definition['filename']

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
    with open(tmp_file, 'wt') as text_file:
        if table.header_mode != "none":
            print("#" + "\t".join(table.get_column_names()), file=text_file)
        for rec in table.get_all_records():
            print(*rec, sep="\t", file=text_file)
    pysam.tabix_compress(tmp_file, full_file_path, force=True)
    os.remove(tmp_file)

    pysam.tabix_index(full_file_path, force=True,
                      seq_col=table.chrom_column_i,
                      start_col=table.pos_begin_column_i,
                      end_col=table.pos_end_column_i)
