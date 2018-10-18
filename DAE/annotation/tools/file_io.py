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
        sys.stderr.write(
            "The given file '{}' does not exist!\n".format(filepath))
        sys.exit(-1)


class Schema:
    # TODO Schema and various header lists overlap.
    # The order of the column names can be stored
    # in the Schema class instead, to reduce redundancy.

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
        for entry in schema_config:
            if entry[0] in self.type_map:
                for col in entry[1].split(','):
                    self.column_map[col] = entry[0]
            else:
                print(('Unrecognized column type {} when'
                       'loading schema from config file.').format(entry[0]))
                sys.exit(-1)

    def merge(self, foreign):
        foreign_schema = foreign.column_map
        for key, value in foreign_schema.items():
            if key in self.column_map:
                if self.column_map[key] != value:
                    print('Error encountered during merging of schemas!')
                    print('Column {} has conflicting types:'.format(key))
                    print('> {}'.format(self.column_map[key]))
                    print('< {}'.format(value))
                    sys.exit(-1)
            else:
                self.column_map[key] = value

    def merge_columns(self, columns, new_name=None):
        col_type = None
        for column in columns:
            if column not in self.column_map:
                print('No such column {} exists that can be merged.'.format(column))
                sys.exit(-1)

            if new_name is None:
                new_name = column
            elif type(new_name) is not str:
                print('Non-string new name passed for merged columns!')
                sys.exit(-1)

            if col_type is None:
                col_type = self.column_map[column]

            elif self.column_map[column] != col_type:
                print('Error - attempted merging columns with different types!')
                print(columns)
                sys.exit(-1)
            del(self.column_map[column])
        self.column_map[new_name] = 'list({})'.format(col_type)

    def type_query(self, query_type):
        if query_type not in self.type_map:
            print('No such type "{}" is defined.'.format(type))
            sys.exit(-1)
        else:
            result = []
            for col, type in self.column_map.items():
                if type == query_type:
                    result.append(col)
            return result

    def to_pyarrow(self):
        return pa.schema([pa.field(col, self.type_map[type_][1])
                          for col, type_
                          in self.column_map.items()])

    def coerce_value(self, type_):
        def coerce(value):
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
        return coerce

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

    @property
    def header(self):
        return self.reader.header

    def header_write(self, input_):
        self.writer.header_write(input_)

    def set_schema(self, schema):
        self.schema = schema
        self.reader.schema = self.schema
        self.writer.schema = self.schema

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
        self.schema = None
        if mode != 'r' and mode != 'w':
            print("Unrecognized I/O mode '{}'!".format(mode), file=sys.stderr)
            sys.exit(-1)
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


class TSVFormat(AbstractFormat):

    def __init__(self, opts, mode):
        super(TSVFormat, self).__init__(opts, mode)

    def _setup(self):
        if self.mode == 'r':
            if self.opts.infile != '-':
                assert_file_exists(self.opts.infile)

                if hasattr(self.opts, 'region'):
                    region = self.opts.region
                    if(region is not None):
                        tabix_file = pysam.TabixFile(self.opts.infile)
                        try:
                            self.variantFile = tabix_file.fetch(region=region)
                        except ValueError:
                            self.variantFile = iter([])
                    else:
                        self.variantFile = open(self.opts.infile, 'r')
                else:
                    self.variantFile = open(self.opts.infile, 'r')
            else:
                self.variantFile = sys.stdin
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
                self.variantFile.close()
        else:
            if self.opts.outfile != '-':
                self.outfile.close()

    def _header_read(self):
        if not self.opts.no_header:
            header_str = ""
            if self.opts.region is not None:
                with gzip.open(self.opts.infile, 'rt', encoding='utf8') as file:
                        header_str = file.readline()[:-1]
            else:
                header_str = self.variantFile.readline()[:-1]
            if header_str[0] == '#':
                header_str = header_str[1:]
            self.header = header_str.split('\t')

    def header_write(self, header):
        self.line_write(header)

    def line_read(self):
        if self.mode != 'r':
            sys.stderr.write('Cannot read in write mode!\n')
            sys.exit(-78)

        line = next(self.variantFile)
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            sys.stderr.write(str(self.linecount) + ' lines read\n')
        return line.rstrip('\n').split('\t')

    def line_write(self, line):
        if self.mode != 'w':
            sys.stderr.write('Cannot write in read mode!\n')
            sys.exit(-78)

        self.outfile.write('\t'.join([to_str(column)
                                      for column in line]) + '\n')


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
            sys.stderr.write('Read {} lines.\n'.format(self.linecount))
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
            sys.stderr.write('Cannot read in write mode!\n')
            sys.exit(-78)

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
            sys.stderr.write(str(self.linecount) + ' lines read.\n')
        return list(map(to_str, line))

    def line_write(self, line):
        if self.mode != 'w':
            sys.stderr.write('Cannot write in read mode!\n')
            sys.exit(-78)

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
