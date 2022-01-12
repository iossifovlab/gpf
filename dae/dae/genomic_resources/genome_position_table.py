import abc
import collections
import pysam
import os

from box import Box

from dae.genomic_resources.repository import GenomicResource


class GenomicPositionTable(abc.ABC):
    CHROM = "chrom"
    POS_BEGIN = "pos_begin"
    POS_END = "pos_end"

    def __init__(self, genomic_resource: GenomicResource, table_definition):
        self.genomic_resource = genomic_resource

        # v = Validator(TABLE_SCHEMA)
        # # v.allow_unknown = True
        # if not v.validate(table_definition):
        #     raise ValueError(v.errors)

        # self.definition = Box(v.normalized(table_definition))

        self.definition = Box(table_definition)
        self.chrom_map = None

        # handling the 'header' property
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

    def load(self):
        if self.header_mode == "file":
            self.header = self._get_tabix_header()

        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_tabix_header(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self):
        return self.tabix_file.contigs

    def get_all_records(self):
        for line in self.tabix_file.fetch(parser=pysam.asTuple()):
            if self.chrom_map:
                fchrom = line[self.chrom_column_i]
                if fchrom not in self.rev_chrom_map:
                    continue
                linel = list(line)
                linel[self.chrom_column_i] = self.rev_chrom_map[fchrom]
                yield tuple(linel)
            else:
                yield tuple(line)

    def get_records_in_region(self, ch: str, beg: int = None, end: int = None):
        if ch not in self.get_chromosomes():
            raise ValueError(f"The chromosome {ch} is not part of the table.")
        if beg:
            beg -= 1
        if self.chrom_map:
            fch = self.chrom_map[ch]
            for line in self.tabix_file.fetch(fch, beg, end,
                                              parser=pysam.asTuple()):
                linel = list(line)
                linel[self.chrom_column_i] = self.rev_chrom_map[fch]
                yield tuple(linel)
        else:
            for line in self.tabix_file.fetch(ch, beg, end,
                                              parser=pysam.asTuple()):
                yield tuple(line)

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
