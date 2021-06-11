import sys
import os
import logging
import gzip
import pysam

from dae.annotation.tools.schema import Schema
from dae.annotation.tools.utils import handle_header, handle_chrom_prefix

logger = logging.getLogger(__name__)


def is_gzip(filename):
    try:
        if filename == "-":
            return False
        if not os.path.exists(filename):
            return False

        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:
        return False


def is_tabix(filename):
    if not is_gzip(filename):
        return False
    if not os.path.exists("{}.tbi".format(filename)):
        return False
    return True


def regions_intersect(b1, e1, b2, e2):
    if b1 >= b2 and b1 <= e2:
        return True
    if e1 >= b2 and e1 <= e2:
        return True
    if b2 >= b1 and b2 <= e1:
        return True
    if e2 >= b1 and e2 <= e1:
        return True
    return False


class FileReader:
    def __init__(self):
        self.linecount = 0
        self.linecount_threshold = 1000

    def _setup(self):
        raise NotImplementedError()

    def _cleanup(self):
        raise NotImplementedError()

    def lines_read_iterator(self):
        raise NotImplementedError()

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def _progress_step(self):
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            logger.log(f"{self.linecount} lines read")


class TSVReader(FileReader):
    def __init__(
        self, filename, col_order=None,
        separator=None
    ):
        super.__init__()

        self.filename = filename
        self.separator = "\t" if separator is None else separator

        assert os.path.exists(self.filename)

    def _header_read(self):
        if self.schema:
            return self.schema.col_names

        if self.col_order:
            return self.col_order

        line = self.infile.readline()
        header_str = line.strip()
        if header_str.startswith("#"):
            header_str = header_str[1:]
        return handle_header(header_str.split(self.separator))

    def _setup(self):
        if is_gzip(self.filename):
            self.infile = gzip.open(self.filename, "rt")
        else:
            self.infile = open(self.filename, "r")

        self.schema = Schema.from_dict({"str": self._header_read()})

    def _cleanup(self):
        self.infile.close()

    def line_read(self):
        line = self.infile.readline().rstrip("\n")

        if not line:
            return None
        self._progress_step()
        return line.split(self.separator)

    def lines_read_iterator(self):
        line = self.line_read()
        while line:
            yield line
            line = self.line_read()


class TabixReader(FileReader):

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def __init__(
        self, filename, tabix_filename,
        id_names=None, id_indexes=None,
        col_order=None, separator=None,
        region=None
    ):

        assert id_names is not None or id_indexes is not None
        super.__init__()

        self.filename = filename
        self.tabix_filename = tabix_filename
        self.col_order = col_order
        self.separator = "\t" if separator is None else separator
        self.region = region
        self.buffer = []
        self.id_names = id_names
        self.id_indexes = id_indexes
        self.last_pos = 0

        assert os.path.exists(self.filename)
        assert os.path.exists(self.tabix_filename)
        assert is_gzip(self.filename)
        assert is_tabix(self.tabix_filename)

    @property
    def _buffer_chrom(self):
        if len(self.buffer) == 0:
            return None

        return self.buffer[0][self._chrom_idx]

    @property
    def _buffer_pos_begin(self):
        if len(self.buffer) == 0:
            return -1

        return self.buffer[0][self._pos_begin_idx]

    @property
    def _buffer_pos_end(self):
        if len(self.buffer) == 0:
            return -1

        return self.buffer[0][self._pos_end_idx]

    def _header_read(self):
        if self.schema:
            return self.schema.col_names

        if self.col_order is not None:
            return self.col_order

        line = list(self.infile.header)
        if not line:
            with TSVReader(self.options, self.filename) as tempreader:
                return tempreader.schema.col_names
        else:
            header_str = line[-1]
            if header_str.startswith("#"):
                header_str = header_str[1:]
            return handle_header(header_str.split(self.separator))

    def _region_reset(self, region):
        region = handle_chrom_prefix(self._has_chrom_prefix, region)
        try:
            self._lines_iterator = self.infile.fetch(
                region=region, parser=pysam.asTuple()
            )
        except ValueError as ex:
            print(
                f"could not find region {region} in {self.filename}:",
                ex, file=sys.stderr)
            self._lines_iterator = None

    def _setup(self):
        self.infile = pysam.TabixFile(self.filename, index=self.tabix_filename)
        self.direct_infile = pysam.TabixFile(
            self.filename,
            index=self.tabix_filename
        )
        contig_name = self.infile.contigs[-1]
        self._has_chrom_prefix = contig_name.startswith("chr")

        self._region_reset(self.region)
        self.schema = Schema.from_dict({"str": self._header_read()})
        if self.id_names is not None:
            col_names = self.schema.col_names
            self._chrom_idx = col_names.index(self.id_names["chrom"])
            self._pos_begin_idx = col_names.index(self.id_names["pos_begin"])
            self._pos_end_idx = col_names.index(self.id_names["pos_end"])
        else:
            self._chrom_idx = self.id_indexes["chrom"]
            self._pos_begin_idx = self.id_indexes["pos_begin"]
            self._pos_end_idx = self.id_indexes["pos_end"]

    def _cleanup(self):
        self.infile.close()

    def lines_read_iterator(self):
        if self._lines_iterator is None:
            return None

        for line in self._lines_iterator:
            self._progress_step()
            yield line

    def _purge_buffer(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while len(self.buffer) > 0:
            line = self.buffer[0]
            if (
                line[self._chrom_idx] == chrom and
                line[self._pos_end_idx] >= pos_begin
            ):
                break
            self.buffer.pop(0)

    def _fill_buffer(self, chrom, pos_begin, pos_end):
        if self._buffer_chrom == chrom and self._buffer_pos_end > pos_end:
            return
        if self._lines_iterator is None:
            return

        line = None
        for line in self._lines_iterator:
            if line[self._pos_end_idx] >= pos_begin:
                break

        if not line:
            return

        self.append(line)

        for line in self.access.lines_iterator:
            chrom = line[self._chrom_idx]
            assert chrom == self._buffer_chrom, (chrom, self._buffer_chrom)
            self.append(line)
            if line[self._pos_end_idx] > pos_end:
                break

    def _select_lines(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.buffer:
            if line[self._chrom_idx] != chrom:
                continue
            if regions_intersect(
                pos_begin, pos_end,
                line[self._pos_begin_idx], line[self._pos_end_idx]
            ):
                result.append(line)
        return result

    def fetch(self, chrom, pos_begin, pos_end):
        if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
            self.last_pos = pos_end
            return self._fetch_direct(chrom, pos_begin, pos_end)
        else:
            self.last_pos = pos_end
            return self._fetch_sequential(chrom, pos_begin, pos_end)

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if (
            chrom != self._buffer_chrom
            or pos_begin < self._buffer_pos_begin
            or (pos_begin - self._buffer_pos_end) > self.LONG_JUMP_THRESHOLD
        ):
            self._reset(chrom, pos_begin)

        if self.lines_iterator is None:
            return []

        self._purge_buffer(chrom, pos_begin, pos_end)
        self._fill_buffer(chrom, pos_begin, pos_end)
        return self._select_lines(chrom, pos_begin, pos_end)

    def _fetch_direct(self, chrom, pos_begin, pos_end):
        try:
            result = []
            for line in self.direct_infile.fetch(
                str(chrom), pos_begin - 1, pos_end, parser=pysam.asTuple()
            ):
                result.append(line)
            return result
        except ValueError as ex:
            print(
                f"could not find region {chrom}:{pos_begin}-{pos_end} "
                f"in {self.filename}: ",
                ex,
                file=sys.stderr,
            )
            return []
