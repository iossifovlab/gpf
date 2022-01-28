import abc
import collections
import pysam  # type: ignore
import os
import logging
import struct
import gzip

from typing import Optional, Tuple, List

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


class TabixGenomicPositionTable(GenomicPositionTable):
    def __init__(self, genomic_resource: GenomicResource, table_definition,
                 tabix_file: pysam.TabixFile):
        self.tabix_file: pysam.TabixFile = tabix_file
        super().__init__(genomic_resource, table_definition)

        self._reset_current_pos()
        self.tabix_iterator = None
        self._call: Tuple[Optional[str], int, Optional[int]] = "", -1, -1
        self._call_result: List = []

        self.jump_threshold = 10_000
        self.sequential_count = 0
        self.direct_count = 0

    def load(self):
        if self.header_mode == "file":
            self.header = self._get_tabix_header()

        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_tabix_header(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self):
        return self.tabix_file.contigs

    def _update_current_pos(self, line):
        line_chrom, line_beg, line_end = line[self.chrom_column_i], \
            int(line[self.pos_begin_column_i]), \
            int(line[self.pos_end_column_i])
        
        curr_chrom, curr_beg, curr_end, buff = self.current_pos

        if line_chrom == curr_chrom and line_beg == curr_beg \
                and line_end == curr_end:
            buff.append(line)
            return True
        
        self.current_pos = line_chrom, line_beg, line_end, [line]
        return False

    def _reset_current_pos(self):
        self.current_pos = None, -1, -1, None

    def _map_file_chrom(self, chrom: str) -> str:
        """
        Transfroms chromosome (contig) name to the chromosomes (contigs)
        used in the score table
        """
        if self.chrom_map:
            return self.chrom_map[chrom]
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
        result[self.chrom_column_i] = self._map_result_chrom(
            result[self.chrom_column_i])
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

    def _should_use_sequential(self, fchrom, beg):
        assert fchrom is not None
        curr_chrom, curr_begin, _, _ = self.current_pos
        if curr_chrom != fchrom:
            return False
        if curr_begin > beg:
            return False
        if beg - curr_begin >= self.jump_threshold:
            return False
        return True

    def _sequential_rewind(self, fchrom, beg, end):

        curr_chrom, curr_begin, curr_end, curr_buff = self.current_pos
        assert curr_buff is not None
        assert curr_chrom == fchrom

        if end and curr_begin > end:
            return None

        if curr_begin >= beg or beg <= curr_end:
            return curr_buff

        while True:
            try:
                line = next(self.tabix_iterator)
                self._update_current_pos(line)
                curr_chrom, curr_begin, curr_end, _ = self.current_pos

                if curr_chrom != fchrom:
                    return None

                if end and curr_begin > end:
                    return None

                if curr_begin >= beg or beg <= curr_end:
                    return [line]

            except StopIteration:
                return None

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

        logger.info(
            f"score {self.genomic_resource.resource_id}; "
            f"current call {fchrom, beg, end}; prev call {self._call}; "
            f"curr position is {self.current_pos[:3]}; "
        )

        # if self._call == (fchrom, beg, end):
        #     logger.info(
        #         f"score {self.genomic_resource.resource_id}; "
        #         f"current call matches previous call {self._call}; "
        #         f"re-using previous result; "
        #         f"curr position is {self.current_pos[:3]}; "
        #     )

        #     for line in self._call_result:
        #         yield self._transform_result(line)
        #     return

        curr_chrom, curr_begin, _, _ = self.current_pos
        prev_chrom, _, prev_end = self._call

        if end is not None and prev_end is not None \
                and curr_chrom == prev_chrom \
                and beg > prev_end \
                and end < curr_begin:
            return None


        try:
            if self._should_use_sequential(fchrom, beg):
                self.sequential_count += 1
                logger.info(
                    f"score {self.genomic_resource.resource_id}; "
                    f"SEQUENTIAL ({self.sequential_count} times); "
                    f"current call is {fchrom, beg, end}; "
                    f"prev call was {self._call}; "
                    f"curr position is {self.current_pos[:3]}; "
                )
                buff = self._sequential_rewind(fchrom, beg, end)
                self._call = fchrom, beg, end
                # self._call_result = []
                if buff is None:
                    return
                # self._call_result = buff
                for line in buff:
                    yield self._transform_result(line)
            else:

                self.tabix_iterator = self.tabix_file.fetch(
                    fchrom, beg - 1, None, parser=pysam.asTuple())
                self._reset_current_pos()
                self.direct_count += 1
                logger.info(
                    f"score {self.genomic_resource.resource_id}; "
                    f"DIRECT ({self.direct_count} times); "
                    f"current call is {fchrom, beg, end}; "
                    f"prev call was {self._call}; "
                    f"curr position is {self.current_pos[:3]}; "
                )
                self._call = fchrom, beg, end
                # self._call_result = []

            while True:
                line = next(self.tabix_iterator)  # type: ignore
                self._update_current_pos(line)

                if end and self.current_pos[1] > end:
                    return
                # self._call_result.append(line)
                yield self._transform_result(line)
    
        except StopIteration:
            return

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

class TabixHelper:

    TABIX_MAGIC = b'TBI\x01'
    TABIX_BLOCK_BYTES_MASK = 0x0000000000000FFFF

    def __init__(self, index_filename):
        self.index_filename = index_filename
        self.index = None
    
    def open(self):
        assert self.index is None
        self.index = gzip.open(self.index_filename, "rb")
    
    def close(self):
        assert self.index is not None
        self.index.close()
        self.index = None

    def read_values(self, fmt):
        size = struct.calcsize(fmt)
        packet = self.index.read(size)

        res = struct.unpack(fmt, packet)
        return res

    def load_index(self):

        (magic, ) = self.read_values("<4s")
        if magic != self.TABIX_MAGIC:
            logger.error(
                f"wrong tabix index magic {magic} in {self.index_filename}")
            raise ValueError("wrong tabix index magic")
        self.data = {}

        self._load_header()
        self._load_contig_names()
        self._load_contig_indices()
    
    def _load_contig_indices(self):
        self.data["contigs"] = {}
        for contig_index in range(self.data["n_contigs"]):
            contig = {}
            contig["contig_index"] = contig_index
            contig["contig_name"] = self.data["contig_names"][contig_index]
            self.data["contigs"][contig_index] = contig

            (n_bins, ) = self.read_values("<i")
            logger.debug(f"contig {contig_index} ({contig['contig_name']})")
            logger.debug(f"n_bins={n_bins}")

            contig["n_bins"] = n_bins
            contig["bins"] = []
            contig["bins_begin"] = None
            contig["bins_end"] = None

            for bin_n in range(n_bins):
                (bin_v, n_chunk) = self.read_values("<Ii")

                logger.debug(
                    f"bin_n   {bin_n + 1}/{n_bins}")
                logger.debug(
                    f"bin     Distinct bin number  uint32_t {bin_v:15,d}")
                logger.debug(
                    f"n_chunk # chunks             int32_t  {n_chunk:15,d}")
                contig["bins"].append({
                    "bin_n": bin_n,
                    "bin": bin_v,
                    "n_chunk": n_chunk,
                })

                chunks = self.read_values('<' + ('Q'*(n_chunk*2)))
                logger.debug(f"chunks: {chunks}")
                real_file_offsets = [c >> 16 for c in chunks]
                block_bytes_offsets = [
                    c & self.TABIX_BLOCK_BYTES_MASK for c in chunks]
                logger.debug(f"file offsets: {real_file_offsets}")
                logger.debug(f"block offsets: {block_bytes_offsets}")

                break

    def _load_contig_names(self):
        l_nm = self.data["l_nm"]
        names = self.index.read(l_nm)
        result = [n.decode("utf8") for n in names.split(b"\x00") if n]
        logger.debug(f"contig names loaded: {result}")

        self.data["contig_names"] = result

    def _load_header(self):        
        (
            n_contigs,# # sequences                              int32_t
            f_format, # Format (0: generic; 1: SAM; 2: VCF)      int32_t
            col_seq,  # Column for the sequence name             int32_t
            col_beg,  # Column for the start of a region         int32_t
            col_end,  # Column for the end of a region           int32_t
            meta,     # Leading character for comment lines      int32_t
            skip,     # # lines to skip at the beginning         int32_t
            l_nm      # Length of concatenated sequence names    int32_t
        ) = self.read_values('<8i')

        logger.debug(
            f"n_contigs    # sequences                           int32_t "
            f"{n_contigs:15,d}")
        logger.debug(
            f"format   Format (0: generic; 1: SAM; 2: VCF)   int32_t "
            f"{f_format:15,d}")
        logger.debug(
            f"col_seq  Column for the sequence name          int32_t "
            f"{col_seq:15,d}")
        logger.debug(
            f"col_beg  Column for the start of a region      int32_t "
            f"{col_beg:15,d}")
        logger.debug(
            f"col_end  Column for the end of a region        int32_t "
            f"{col_end:15,d}")
        logger.debug(
            f"meta     Leading character for comment lines   int32_t "
            f"{meta:15,d}")
        logger.debug(
            f"skip     # lines to skip at the beginning      int32_t "
            f"{skip:15,d}")
        logger.debug(
            f"l_nm     Length of concatenated sequence names int32_t "
            f"{l_nm:15,d}")

        self.data["n_contigs"] = n_contigs
        self.data["format"] = f_format
        self.data["col_seq"] = col_seq
        self.data["col_beg"] = col_beg
        self.data["col_end"] = col_end
        self.data["meta"] = chr(meta)
        self.data["skip"] = skip
        self.data["l_nm"] = l_nm
