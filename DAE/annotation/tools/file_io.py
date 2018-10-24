from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from builtins import open

import sys
import os
import gzip
import pysam
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from abc import ABCMeta, abstractmethod


def assert_file_exists(filepath):
    if filepath != '-' and os.path.exists(filepath) is False:
        print(
            "The given file",
            filepath,
            "does not exist!",
            file=sys.stderr)
        sys.exit(1)


class IOType:
    class TSV:
        @staticmethod
        def instance_r(opts):
            filename = opts.infile
            if TSVFormat.is_tabix(filename):
                return TabixReader(opts)
            if TSVFormat.is_gzip(filename):
                return TSVGzipReader(opts)
            return TSVReader(opts)

        @staticmethod
        def instance_w(opts):
            return TSVWriter(opts)

    class Parquet:
        @staticmethod
        def instance_r(opts):
            return ParquetFormat(opts, 'r')

        @staticmethod
        def instance_w(opts):
            return ParquetFormat(opts, 'w')


class IOManager(object):

    def __init__(self, opts, io_type_r, io_type_w):
        self.opts = opts
        self.reader = io_type_r.instance_r(self.opts)
        self.writer = io_type_w.instance_w(self.opts)

    def __enter__(self):
        self.reader._setup()
        self.writer._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reader._cleanup()
        self.writer._cleanup()

    def _setup(self):
        self.reader._setup()
        self.writer._setup()

    def _cleanup(self):
        self.reader._cleanup()
        self.writer._cleanup()

    @property
    def header(self):
        return self.reader.header

    def header_write(self, input_):
        self.writer.header_write(input_)

    def lines_read_iterator(self):
        return self.reader.lines_read_iterator()

    def line_write(self, input_):
        self.writer.line_write(input_)


class AbstractFormat(object):

    __metaclass__ = ABCMeta

    def __init__(self, opts, mode):
        self.opts = opts
        self.options = opts

        if mode != 'r' and mode != 'w':
            print("Unrecognized I/O mode '{}'!".format(mode), file=sys.stderr)
            sys.exit(1)
        self.mode = mode
        self.linecount = 0
        self.linecount_threshold = 1000
        self.header = None

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _cleanup(self):
        pass

    # @abstractmethod
    # def line_read(self):
    #     pass

    @abstractmethod
    def lines_read_iterator(self):
        pass

    @abstractmethod
    def line_write(self, input_):
        pass


def to_str(column_value):
    if isinstance(column_value, list):
        return '|'.join(map(to_str, column_value))
    elif column_value is None:
        return ''
    else:
        return str(column_value)


class TSVFormat(AbstractFormat):

    def __init__(self, opts, mode):
        super(TSVFormat, self).__init__(opts, mode)

    @staticmethod
    def is_tabix(filename):
        if not TSVFormat.is_gzip(filename):
            return False
        if not os.path.exists("{}.tbi".format(filename)):
            return False
        return True

    @staticmethod
    def is_gzip(filename):
        try:
            if filename == '-':
                return False
            if not os.path.exists(filename):
                return False

            with gzip.open(filename, "rt") as infile:
                infile.readline()
            return True
        except Exception:
            return False

    def _progress_step(self):
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            print(self.linecount, 'lines read', file=sys.stderr)

    def _progress_done(self):
        print('Processed', self.linecount, 'lines.', file=sys.stderr)


class TSVReader(TSVFormat):

    def __init__(self, options, filename=None):
        super(TSVReader, self).__init__(options, 'r')
        if filename is None:
            assert options.infile is not None
            filename = options.infile
        self.filename = filename

        if self.options.region is not None:
            print(
                "region {} passed to TSVReader({})"
                " NOT SUPPORTED and ignored".format(
                    self.options.region, self.filename),
                file=sys.stderr)
        self.separator = '\t'
        if self.options.separator:
            self.separator = self.options.separator

    def _setup(self):
        if self.filename == '-':
            self.infile = sys.stdin
        else:
            assert os.path.exists(self.filename)
            assert not self.is_gzip(self.filename)
            self.infile = open(self.filename, 'r', encoding='utf8')

        self.header = self._header_read()

    def _cleanup(self):
        self._progress_done()

        if self.filename != '-':
            self.infile.close()

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def _header_read(self):
        if self.options.no_header:
            return None
        else:
            line = self.infile.readline()
            header_str = line.strip()
            if header_str.startswith("#"):
                header_str = header_str[1:]
            return header_str.split(self.separator)

    def line_write(self, line):
        raise NotImplementedError()

    def line_read(self):
        line = self.infile.readline()
        line = line.rstrip('\n')

        if not line:
            return None
        self._progress_step()
        return line.rstrip('\n').split(self.separator)

    def lines_read_iterator(self):
        line = self.line_read()
        while line:
            yield line
            line = self.line_read()


class TSVGzipReader(TSVReader):

    def __init__(self, options, filename=None):
        super(TSVGzipReader, self).__init__(options, filename)

    def _setup(self):

        assert os.path.exists(self.filename)
        assert self.is_gzip(self.filename)
        self.infile = gzip.open(self.filename, 'rt')

        self.header = self._header_read()


class TabixReader(TSVFormat):

    def __init__(self, options, filename=None):
        super(TabixReader, self).__init__(options, 'r')
        if filename is None:
            assert options.infile is not None
            filename = options.infile
        self.filename = filename

        assert os.path.exists(self.filename)
        assert self.is_gzip(self.filename)
        assert os.path.exists("{}.tbi".format(self.filename))
        self.separator = '\t'
        self.region = self.options.region
        self._has_chrom_prefix = None

    def _handle_chrom_prefix(self, data):
        if data is None:
            return data
        if self._has_chrom_prefix and not data.startswith('chr'):
            return "chr{}".format(data)
        if not self._has_chrom_prefix and data.startswith('chr'):
            return data[3:]
        return data

    def _setup(self):
        self.infile = pysam.TabixFile(self.filename)
        contig_name = self.infile.contigs[0]
        self._has_chrom_prefix = contig_name.startswith('chr')

        region = self._handle_chrom_prefix(self.region)

        self.lines_iterator = self.infile.fetch(
            region=region,
            parser=pysam.asTuple())

        self.header = self._header_read()

    def _header_read(self):
        if self.options.no_header:
            return None
        else:
            line = self.infile.header
            line = list(line)
            if not line:
                return None
            header_str = line[0]
            if header_str.startswith("#"):
                header_str = header_str[1:]
            return header_str.split(self.separator)

    def _cleanup(self):
        self._progress_done()
        self.infile.close()

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def line_write(self, line):
        raise NotImplementedError()

    # def line_read(self):
    #     line = next(self.lines_iterator)
    #     self._progress_step()
    #     return line

    def lines_read_iterator(self):
        for line in self.lines_iterator:
            self._progress_step()
            # print(self.linecount, line)

            yield line


class TSVWriter(TSVFormat):

    def __init__(self, options, filename=None):
        super(TSVWriter, self).__init__(options, 'w')
        if filename is None:
            assert options.outfile is not None
            filename = options.outfile
        self.filename = filename

        self.separator = '\t'
        if self.options.separator:
            self.separator = self.options.separator

    def _setup(self):
        if self.filename == '-':
            self.outfile = sys.stdout
        else:
            self.outfile = open(self.filename, 'w', encoding='utf8')

    def _cleanup(self):
        if self.filename != '-':
            self.outfile.close()

    def line_write(self, line):
        self.outfile.write('\t'.join(
            [to_str(column) for column in line]))
        self.outfile.write('\n')

    def line_read(self):
        raise NotImplementedError()

    def lines_read_iterator(self):
        raise NotImplementedError()


class ParquetFormat(AbstractFormat):

    def __init__(self, opts, mode):
        super(ParquetFormat, self).__init__(opts, mode)

        self.row_group_buffer = []
        if self.mode == 'w':
            self.pq_writer = None
            self.buffer_limit = 50

    def _setup(self):
        if self.mode == 'r':
            if self.opts.infile != '-':
                assert_file_exists(self.opts.infile)
                self.pqfile = pq.ParquetFile(self.opts.infile)
                self.row_group_count = self.pqfile.num_row_groups
                self.row_group_curr = 0
            else:
                self.variantFile = sys.stdin
            self._read_row_group()
        else:
            if self.opts.outfile != '-':
                self.pqfile_out = self.opts.outfile
            else:
                self.pqfile_out = sys.stdout

    def _cleanup(self):
        if self.mode == 'r':
            print('Processed', self.linecount, 'lines.', file=sys.stderr)
        else:
            self._write_buffer()
            if self.opts.outfile != '-':
                self.pq_writer.close()

    def _read_row_group(self):
        if self.row_group_curr < self.row_group_count:
            if self.header is None:
                pd_buffer = self.pqfile.read_row_group(
                    self.row_group_curr).to_pandas()
                self.header = [str(i) for i in list(pd_buffer)]
                self.header[0] = self.header[0].strip('#')
                self.row_group_buffer = pd_buffer.values
            else:
                self.row_group_buffer = self.pqfile.read_row_group(
                    self.row_group_curr).to_pandas().values
            self.row_group_buffer = self.row_group_buffer.tolist()
            self.row_group_curr += 1

    def header_write(self, input_):
        self.header = input_

    def line_read(self):
        if self.mode != 'r':
            print('Cannot read in write mode!', file=sys.stderr)
            sys.exit(1)

        if not self.row_group_buffer:
            if self.row_group_curr >= self.row_group_count:
                return ['']  # EOF
            else:
                self._read_row_group()

        line = self.row_group_buffer[0]
        self.row_group_buffer = self.row_group_buffer[1:]
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            print(self.linecount, 'lines read.', file=sys.stderr)
        return line

    def line_write(self, input_):
        if self.mode != 'w':
            print('Cannot write in read mode!', file=sys.stderr)
            sys.exit(1)

        self.row_group_buffer.append(input_)
        if len(self.row_group_buffer) >= self.buffer_limit:
            self._write_buffer()

    def _write_buffer(self):
        buffer_df = pd.DataFrame(self.row_group_buffer, columns=self.header)
        buffer_table = pa.Table.from_pandas(buffer_df, preserve_index=False)
        if self.pq_writer is None:
            self.pq_writer = pq.ParquetWriter(
                self.pqfile_out, buffer_table.schema)
        self.pq_writer.write_table(buffer_table)
        self.row_group_buffer = []
