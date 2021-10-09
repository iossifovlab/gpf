import abc
import collections
import pysam
import os

from dae.genomic_resources.repository import GenomicResource


class GenomicPositionTable(abc.ABC):
    @ abc.abstractmethod
    def get_columns(self):
        pass

    @ abc.abstractmethod
    def get_chr_column(self):
        pass

    @ abc.abstractmethod
    def get_pos_column(self):
        pass

    @ abc.abstractmethod
    def get_chromosomes(self):
        pass

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
    def __init__(self, str_stream, chr_column="chr", pos_column="pos"):

        self.chr_column = chr_column
        self.pos_column = pos_column

        self.load(str_stream)

    def load(self, str_stream):
        hcs = None
        for line in str_stream:
            line = line.strip(" \t\n\r")
            if not line:
                continue
            hcs = line.split()
            break
        if not hcs:
            raise Exception("No header found")

        self.columns = tuple(hcs)

        self.chr_column_i = hcs.index(self.chr_column)
        self.pos_column_i = hcs.index(self.pos_column)

        records_by_chr = collections.defaultdict(list)
        for line in str_stream:
            line = line.strip(" \t\n\r")
            if not line:
                continue
            cs = tuple(line.split())
            if len(cs) != len(hcs):
                raise Exception("Inconsistent number of columns")
            ch = cs[self.chr_column_i]
            ps = int(cs[self.pos_column_i])
            records_by_chr[ch].append((ps, cs))
        self.records_by_chr = {c: sorted(pss)
                               for c, pss in records_by_chr.items()}

    def get_columns(self):
        return self.columns

    def get_chr_column(self):
        return self.chr_column

    def get_pos_column(self):
        return self.pos_column

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
    def __init__(self, tabix_file: pysam.TabixFile,
                 chr_column="chr", pos_column="pos"):
        self.tabix_file: pysam.TabixFile = tabix_file

        if chr_column not in self.get_columns():
            raise Exception(f"The chromosome cholumn {chr_column}"
                            " is not available")
        if pos_column not in self.get_columns():
            raise Exception(f"The position choumn {pos_column}"
                            " is not available")
        self.chr_column: str = chr_column
        self.pos_column: str = pos_column

    def get_columns(self):
        return tuple(self.tabix_file.header[-1].strip("#").split("\t"))

    def get_chr_column(self):
        return self.chr_column

    def get_pos_column(self):
        return self.pos_column

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


def get_genome_position_table(gr: GenomicResource, table_definition: dict):
    filename = table_definition['file']
    default_format = "tabix" if filename.endswith(".bgz") else "text"
    chClm = table_definition.get("chrColumn", "chr")
    psClm = table_definition.get("posColumn", "pos")
    frmt = table_definition.get("format", default_format)

    if frmt == "text":
        with gr.open_raw_file(filename, mode="rt", uncompress=True) as F:
            table = FlatGenomicPositionTable(F, chClm, psClm)
        return table
    elif frmt == "tabix":
        return TabixGenomicPositionTable(gr.open_tabix_file(filename))
    else:
        raise Exception("unknown table format")


def save_as_tabix_table(table: GenomicPositionTable,
                        full_file_path: str):
    tmp_file = full_file_path + ".tmp"
    with open(tmp_file, 'wt') as text_file:
        print("#" + "\t".join(table.get_columns()), file=text_file)
        for rec in table.get_all_records():
            print(*rec, sep="\t", file=text_file)
    pysam.tabix_compress(tmp_file, full_file_path, force=True)
    os.remove(tmp_file)
    clmns = table.get_columns()
    seq_ci = clmns.index(table.get_chr_column())
    pos_ci = clmns.index(table.get_pos_column())
    pysam.tabix_index(full_file_path, force=True,
                      seq_col=seq_ci, start_col=pos_ci, end_col=pos_ci)


if __name__ == "__main__":
    from dae.genomic_resources import build_genomic_resource_repository

    e_repo = build_genomic_resource_repository(
        {"id": "e", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": '''
                    text_table:
                        file: data.txt
                    tabix_table:
                        file: data.bgz''',
                "data.txt": '''
                    chr pos c1     c2
                    1   3   3.14   gosho
                    1   4   12.4   pesho
                    1   4   13.4   TRA
                    1   5   122.0  asdg
                    1   8   3.2    sdgasdgas
                    2   3   11.4   sasho'''
            }
        },

        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": "./d_repo"})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        get_genome_position_table(e_gr, e_gr.config['text_table']),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = get_genome_position_table(d_gr, d_gr.config['tabix_table'])
