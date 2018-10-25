from __future__ import print_function

import sys
import os
import gzip
import pysam
import pyarrow as pa
import pyarrow.parquet as pq
from abc import ABCMeta, abstractmethod


def to_str(column_value):
    if isinstance(column_value, list):
        return '|'.join(map(to_str, column_value))
    elif column_value is None:
        return ''
    else:
        return str(column_value)


def assert_file_exists(filepath):
    if filepath != '-' and os.path.exists(filepath) is False:
        print(
            "The given file",
            filepath,
            "does not exist!",
            file=sys.stderr)
        sys.exit(1)


class Schema:

    # New types only need to be added here.
    type_map = {'str': (str, pa.string()),
                'float': (float, pa.float64()),
                'int': (int, pa.int32()),
                'list(str)': (str, pa.list_(pa.string())),
                'list(float)': (float, pa.list_(pa.float64())),
                'list(int)': (int, pa.list_(pa.float32()))}

    def __init__(self, schema_input=None):
        self.column_map = {}
        if schema_input is not None:
            self.load_from_config(schema_input)

    def load_from_config(self, schema_config):
        assert type(schema_config) is dict
        for type_, col_list in schema_config.items():
            assert type_ in self.type_map
            for col in col_list.split(','):
                self.column_map[col] = type_

    def merge(self, foreign):
        foreign_schema = foreign.column_map
        for key, value in foreign_schema.items():
            if key in self.column_map:
                assert self.column_map[key] == value
            else:
                self.column_map[key] = value

    def merge_columns(self, columns, new_name=None):
        col_type = None
        for column in columns:
            assert column in self.column_map
            if new_name is None:
                new_name = column
            if col_type is None:
                col_type = self.column_map[column]
            assert self.column_map[column] == col_type
            del(self.column_map[column])
        self.column_map[str(new_name)] = 'list({})'.format(col_type)

    def rename_column(self, column, new_name):
        assert column in self.column_map
        self.column_map[str(new_name)] = self.column_map[column]
        del(self.column_map[column])

    def type_query(self, query_type):
        assert query_type in self.type_map
        result = []
        for col, type_ in self.column_map.items():
            if type_ == query_type:
                result.append(col)
        return result

    def to_pyarrow(self):
        return pa.schema([pa.field(col, self.type_map[type_][1])
                          for col, type_
                          in self.column_map.items()])

    def coerce_value(self, type_):
        def coerce_(value):
            if type(value) is not list:
                if value in ['.', '']:
                    return None
                else:
                    return type_(value)
            if ';' in value:
                result = value.split(';')
            elif ',' in value:
                result = value.split(',')
            else:
                result = value
            return [None if value in ['.', ''] else type_(value)
                    for value in result]
        return coerce_

    def coerce_column(self, col_name, col_data):
        try:
            col_type = self.type_map[self.column_map[col_name]][0]
            return list(map(self.coerce_value(col_type), col_data))
        except ValueError:
            print('Column coercion failed:')
            print('Could not coerce column {} to specified type!'.format(col_name))
            sys.exit(-1)

    def __str__(self):
        ret_str = ""
        for key, value in self.column_map.items():
            ret_str += '{} -> {}: {}\n'.format(key, value, str(self.type_map[value]))
        return ret_str


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

    @abstractmethod
    def lines_read_iterator(self):
        pass

    @abstractmethod
    def line_write(self, input_):
        pass


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
            self.infile = open(self.filename, 'r')

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

    def _region_reset(self, region):
        region = self._handle_chrom_prefix(region)
        # print("_region_reset(", region, ")")

        self.lines_iterator = self.infile.fetch(
            region=region,
            parser=pysam.asTuple())

    def _setup(self):
        self.infile = pysam.TabixFile(self.filename)
        contig_name = self.infile.contigs[0]
        self._has_chrom_prefix = contig_name.startswith('chr')

        self._region_reset(self.region)
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
            self.outfile = open(self.filename, 'w')

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

    def __init__(self, opts, mode, buffer_size=1000):
        super(ParquetFormat, self).__init__(opts, mode)

        self.row_group_buffer = []
        self.column_buffer = {}
        if self.mode == 'w':
            self.buffer_size = buffer_size
            self.column_buffer = {}

    def _setup(self):
        if self.mode == 'r':
            if self.opts.infile != '-':
                assert_file_exists(self.opts.infile)
                self.pqfile = pq.ParquetFile(self.opts.infile)
                self.header = self.pqfile.schema.to_arrow_schema().names
                self.row_group_count = self.pqfile.num_row_groups
                self.row_group_curr = 0
                self.curr_line = 0
            else:
                self.variantFile = sys.stdin
            self._read_row_group()
        else:
            self.pq_writer = None
            if self.opts.outfile != '-':
                self.pqfile_out = self.opts.outfile
            else:
                self.pqfile_out = sys.stdout

    def _cleanup(self):
        if self.mode == 'r':
            print('Processed', self.linecount, 'lines.', file=sys.stderr)
        else:
            sys.stderr.write('Wrote {} lines.\n'.format(self.linecount))
            self._write_buffer()
            if self.opts.outfile != '-':
                self.pq_writer.close()

    def _read_row_group(self):
        if self.row_group_curr < self.row_group_count:
            for col in self.header:
                self.column_buffer[col] = []

            row_group_buffer = self.pqfile.read_row_group(self.row_group_curr)
            self.row_group_curr += 1
            for col in row_group_buffer.itercolumns():
                self.column_buffer[col.name] = col.data.to_pylist()

    def header_write(self, input_):
        self.header = input_
        if self.mode == 'w':
            for col in self.header:
                self.column_buffer[col.replace('#', '')] = []

    def line_read(self):
        if self.mode != 'r':
            print('Cannot read in write mode!', file=sys.stderr)
            sys.exit(1)

        line = []
        for col_name, col_data in self.column_buffer.items():
            line.append(col_data[self.curr_line])

        self.linecount += 1
        self.curr_line += 1
        if self.curr_line == len(col_data):
            self.curr_line = 0
            if self.row_group_curr >= self.row_group_count:
                return ['']  # EOF
            else:
                self._read_row_group()
        if self.linecount % self.linecount_threshold == 0:
            print(self.linecount, 'lines read.', file=sys.stderr)
        return list(map(to_str, line))

    def line_write(self, line):
        if self.mode != 'w':
            print('Cannot write in read mode!', file=sys.stderr)
            sys.exit(1)

        self.linecount += 1
        if self.linecount % self.buffer_size == 0:
            self._write_buffer()
        for col in range(0, len(line)):
            self.column_buffer[self.header[col].replace('#', '')].append(line[col])

    def _write_buffer(self):
        pa_col_buffer = []
        if self.pq_writer is None:
            self.pq_writer = pq.ParquetWriter(self.pqfile_out, self.schema.to_pyarrow())
        for col_name, col_data in self.column_buffer.items():
            pa_col_buffer.append(
                pa.column(col_name,
                          pa.array(self.schema.coerce_column(col_name, col_data))))

        buffer_table = pa.Table.from_arrays(pa_col_buffer, schema=self.schema.to_pyarrow())
        self.pq_writer.write_table(buffer_table)

        for col in self.column_buffer.keys():
            self.column_buffer[col] = []
