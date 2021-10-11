import abc
import collections
import pysam
import os

from dae.genomic_resources.repository import GenomicResource


class GenomicPositionTable(abc.ABC):
    def __init__(self, table_definition, chrom_key="chr", pos_key="pos"):
        self.definition = table_definition
        self.chrom_key = chrom_key
        self.pos_key = pos_key

        # handling the 'header' property
        self.header_mode = table_definition.get("header", "file")
        if isinstance(self.header_mode, list):
            self.header = tuple(self.header_mode)
            self.header_mode = "array"
            for hi, hc in enumerate(self.header):
                if not isinstance(hc, str):
                    raise Exception(f"The {hi}-th header {hc} in the table "
                                    f"definition is not a string.")
        else:
            if self.header_mode in {"file", "none"}:
                self.header = None
            else:
                raise Exception(f"The 'header' property in a table definition "
                                f"must be 'file' [by default], 'none', or a "
                                f"list of strings. The current value "
                                f"{self.header_mode} does not meet these "
                                f"requirements.")

    def get_column_names(self):
        return self.header

    def _get_index_prop_for_special_column(self, key):
        index_prop = key + ".index"
        try:
            return int(self.definition[index_prop])
        except KeyError:
            raise KeyError(f"The table definition has no index "
                           f"({index_prop} property) for the special "
                           f"column {key}.")
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
            raise Exception("The table has no header.")
        return self.definition.get(key + ".name", key)

    @ abc.abstractmethod
    def get_all_records(self):
        pass

    @ abc.abstractmethod
    def get_records_in_region(self, ch: str, beg: int = None, end: int = None):
        pass

    @ abc.abstractmethod
    def close(self):
        pass


class FlatGenomicPositionTable(GenomicPositionTable):
    FORMAT_DEF = {
        # parameters are <column separator>, <strip_chars>, <space replacemnt>
        "mem": (None, " \t\n\r", True),
        "tsv": ("\t", "\n\r", False),
        "csv": (",", "\n\r", False)
    }

    def __init__(self, table_definition, str_stream, format,
                 chrom_key="chr", pos_key="pos"):
        super().__init__(table_definition, chrom_key, pos_key)
        self.format = format
        self.load(str_stream)

    def load(self, str_stream):
        clmn_sep, strip_chars, space_replacement = \
            FlatGenomicPositionTable.FORMAT_DEF[self.format]
        if self.header_mode == "file":
            hcs = None
            for line in str_stream:
                line = line.strip(strip_chars)
                if not line:
                    continue
                hcs = line.split(clmn_sep)
                break
            if not hcs:
                raise Exception("No header found")

            self.header = tuple(hcs)
        col_number = len(self.header) if self.header else None
        self.chr_column_i = self.get_special_column_index(self.chrom_key)
        self.pos_column_i = self.get_special_column_index(self.pos_key)

        records_by_chr = collections.defaultdict(list)
        for line in str_stream:
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
            ch = cs[self.chr_column_i]
            ps = int(cs[self.pos_column_i])
            records_by_chr[ch].append((ps, cs))
        self.records_by_chr = {c: sorted(pss)
                               for c, pss in records_by_chr.items()}

    def get_chromosomes(self):
        return sorted(self.records_by_chr.keys())

    def get_all_records(self):
        for ch in self.get_chromosomes():
            pss = self.records_by_chr[ch]
            for _, cs in pss:
                yield cs

    def get_records_in_region(self, ch: str, beg: int = None, end: int = None):
        for ps, cs in self.records_by_chr[ch]:
            if beg and beg > ps:
                continue
            if end and end < ps:
                continue
            yield cs

    def close(self):
        pass


class TabixGenomicPositionTable(GenomicPositionTable):
    def __init__(self, table_definition, tabix_file: pysam.TabixFile,
                 chrom_key="chr", pos_key="pos"):
        super().__init__(table_definition, chrom_key, pos_key)
        self.tabix_file: pysam.TabixFile = tabix_file

        if self.header_mode == "file":
            self.header = self._get_tabix_header()

        self.chr_column_i = self.get_special_column_index(self.chrom_key)
        self.pos_column_i = self.get_special_column_index(self.chrom_key)

    def _get_tabix_header(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_chromosomes(self):
        return self.tabix_file.contigs

    def get_all_records(self):
        for line in self.tabix_file.fetch(parser=pysam.asTuple()):
            yield tuple(line)

    def get_records_in_region(self, ch: str, beg: int = None, end: int = None):
        if beg:
            beg -= 1
        for line in self.tabix_file.fetch(ch, beg, end,
                                          parser=pysam.asTuple()):
            yield tuple(line)

    def close(self):
        self.tabix_file.close()


def get_genome_position_table(gr: GenomicResource, table_definition: dict,
                              chrom_key="chr", pos_key="pos"):
    filename = table_definition['file']

    if filename.endswith(".bgz"):
        default_format = "tabix"
    elif filename.endswith(".txt") or filename.endswith(".txt.gz") or \
            filename.endswith(".tsv") or filename.endswith(".tsv.gz"):
        default_format = "tsv"
    elif filename.endswith(".csv") or filename.endswith(".csv.gz"):
        default_format = "csv"
    else:
        default_format = "mem"
    frmt = table_definition.get("format", default_format)

    if frmt in ["mem", "csv", "tsv"]:
        with gr.open_raw_file(filename, mode="rt", uncompress=True) as F:
            table = FlatGenomicPositionTable(table_definition, F, frmt,
                                             chrom_key, pos_key)
        return table
    elif frmt == "tabix":
        return TabixGenomicPositionTable(table_definition,
                                         gr.open_tabix_file(filename),
                                         chrom_key, pos_key)
    else:
        raise Exception("unknown table format")


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
                      seq_col=table.chr_column_i,
                      start_col=table.pos_column_i,
                      end_col=table.pos_column_i)


if __name__ == "__main__":
    from dae.genomic_resources import build_genomic_resource_repository

    e_repo = build_genomic_resource_repository(
        {"id": "e", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": '''
                    text_table:
                        header: none
                        file: data.mem
                        chr.index: 0
                        pos.index: 1
                    tabix_table:
                        header: none
                        chr.index: 0
                        pos.index: 1
                        file: data.bgz''',
                "data.mem": '''
                    1   3   3.14   gosho
                    1   4   12.4   pesho
                    1   4   13.4   TRA
                    1   5   122.0  asdg
                    1   8   3.2    sdgasdgas
                    2   3   11.4   sasho'''
            }
        },

        })
    e_gr = e_repo.get_resource("one")
    e_table = get_genome_position_table(e_gr, e_gr.config['text_table'])

    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": "./d_repo"})
    d_repo.store_all_resources(e_repo)

    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        get_genome_position_table(e_gr, e_gr.config['text_table']),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    d_table = get_genome_position_table(d_gr, d_gr.config['tabix_table'])
