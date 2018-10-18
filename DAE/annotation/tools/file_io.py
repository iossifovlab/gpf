from __future__ import print_function
from __future__ import unicode_literals
from builtins import str

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
            return TSVFormat(opts, 'r')

        @staticmethod
        def instance_w(opts):
            return TSVFormat(opts, 'w')

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

    def lines_read(self):
        line = self.reader.line_read()
        while line != ['']:
            yield line
            line = self.reader.line_read()

    def line_read(self):
        return self.reader.line_read()

    def line_write(self, input_):
        self.writer.line_write(input_)


class AbstractFormat(object):

    __metaclass__ = ABCMeta

    def __init__(self, opts, mode):
        self.opts = opts
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

    @abstractmethod
    def header_write(self, input_):
        pass

    @abstractmethod
    def line_read(self):
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

    def _setup(self):
        if self.mode == 'r':
            if self.opts.infile == '-':
                self.variant_file = sys.stdin
            else:
                assert_file_exists(self.opts.infile)
                if hasattr(self.opts, 'region'):
                    region = self.opts.region
                else:
                    region = None

                if region is None:
                    self.variant_file = open(self.opts.infile, 'r')
                else:
                    tabix_file = pysam.TabixFile(self.opts.infile)
                    try:
                        self.variant_file = tabix_file.fetch(region=region)
                    except ValueError:
                        self.variant_file = iter([])
            self._header_read()

        else:
            if self.opts.outfile != '-':
                self.outfile = open(self.opts.outfile, 'w')
            else:
                self.outfile = sys.stdout

    def _cleanup(self):
        if self.mode == 'r':
            sys.stderr.write('Processed ' + str(self.linecount) + ' lines.\n')
            if self.opts.infile != '-' and self.opts.region is None:
                self.variant_file.close()
        else:
            if self.opts.outfile != '-':
                self.outfile.close()

    def _header_read(self):
        if not self.opts.no_header:
            header_str = ""
            if self.opts.region is not None:
                with gzip.open(
                        self.opts.infile, 'rt', encoding='utf8') as infile:
                    header_str = infile.readline()[:-1]
            else:
                header_str = self.variant_file.readline()[:-1]
            if header_str[0] == '#':
                header_str = header_str[1:]
            self.header = header_str.split(self.opts.separator)

    def header_write(self, header):
        self.line_write(header)

    def line_read(self):
        if self.mode != 'r':
            print('Cannot read in write mode!', file=sys.stderr)
            sys.exit(1)

        line = next(self.variant_file)
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            print(self.linecount, 'lines read', file=sys.stderr)
        return line.rstrip('\n').split(self.opts.separator)

    def line_write(self, line):
        if self.mode != 'w':
            print('Cannot write in read mode!', file=sys.stderr)
            sys.exit(1)

        self.outfile.write('\t'.join(
            [to_str(column) for column in line]))
        self.outfile.write('\n')


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
