from __future__ import print_function

import sys
import os
import gzip
# import copy

import pysam
import pyarrow as pa
import pyarrow.parquet as pq
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from box import Box


def to_str(column_value):
    if isinstance(column_value, list):
        return '|'.join(map(to_str, column_value))
    elif column_value is None:
        return ''
    else:
        return str(column_value)


class Schema(object):

    # New types only need to be added here.
    type_map = {'str': (str, pa.string()),
                'float': (float, pa.float64()),
                'int': (int, pa.int32()),
                'list(str)': (str, pa.list_(pa.string())),
                'list(float)': (float, pa.list_(pa.float64())),
                'list(int)': (int, pa.list_(pa.float32()))}

    def __init__(self):
        self.columns = OrderedDict()

    @classmethod
    def produce_type(cls, type_name):
        assert type_name in cls.type_map
        return Box({'type_name': type_name,
                    'type_py': cls.type_map[type_name][0],
                    'type_pa': cls.type_map[type_name][1]},
                   default_box=True,
                   default_box_attr=None)

    @classmethod
    def from_parquet(cls, pq_schema):
        return cls.from_arrow(pq_schema.to_arrow_schema())

    @classmethod
    def from_arrow(cls, pa_schema):
        new_schema = Schema()
        for col in pa_schema:
            for type_name, types in new_schema.type_map.items():
                if col.type == types[1]:
                    new_schema.columns[col.name] = cls.produce_type(type_name)
                    break
        return new_schema

    @classmethod
    def from_dict(cls, schema_dict):
        new_schema = Schema()
        assert type(schema_dict) is dict
        for col_type, col_list in schema_dict.items():
            assert col_type in new_schema.type_map
            col_list.replace(' ', '')
            col_list.replace('\t', '')
            col_list.replace('\n', '')
            for col in col_list.split(','):
                new_schema.columns[col] = cls.produce_type(col_type)
        return new_schema

    @staticmethod
    def merge_schemas(left, right):
        merged_schema = Schema()
        missing_columns = OrderedDict()
        for key, value in right.columns.items():
            if key in left.columns:
                # assert left.columns[key] == value
                left.columns[key] = value
            else:
                missing_columns[key] = value
        merged_schema.columns.update(left.columns)
        merged_schema.columns.update(missing_columns)
        return merged_schema

    def to_arrow(self):
        return pa.schema([pa.field(col, col_type.type_pa, nullable=True)
                          for col, col_type
                          in self.columns.items()])

    def __str__(self):
        ret_str = ""
        for col, col_type in self.columns.items():
            ret_str += '{} -> [{} / {}]\n'.format(col, col_type.type_py,
                                                  col_type.type_pa)
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
            return ParquetReader(opts)

        @staticmethod
        def instance_w(opts):
            return ParquetWriter(opts)


class IOManager(object):

    def __init__(self, opts, io_type_r, io_type_w):
        self.options = opts
        self.reader = io_type_r.instance_r(self.options)
        self.writer = io_type_w.instance_w(self.options)

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

    def __init__(self, opts):
        options = Box(opts.to_dict(), default_box=True, default_box_attr=None)
        self.options = options

        self.linecount = 0
        self.linecount_threshold = 1000
        self.header = None
        self.schema = None

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

    def __init__(self, opts):
        super(TSVFormat, self).__init__(opts)

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
        super(TSVReader, self).__init__(options)
        if filename is None:
            assert options.infile is not None
            filename = options.infile
        self.filename = filename
        self.schema = None

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
        self.schema = Schema.from_dict({'str': ','.join(self.header)})

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
        if self.header:
            return self.header

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
        self.schema = Schema.from_dict({'str': ','.join(self.header)})


class TabixReader(TSVFormat):

    def __init__(self, options, filename=None):
        super(TabixReader, self).__init__(options)
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

        try:
            self.lines_iterator = self.infile.fetch(
                region=region,
                parser=pysam.asTuple())
        except ValueError as ex:
            print("could not find region: ", region,
                  ex, file=sys.stderr)
            self.lines_iterator = None

    def _setup(self):
        self.infile = pysam.TabixFile(self.filename)
        contig_name = self.infile.contigs[-1]
        self._has_chrom_prefix = contig_name.startswith('chr')

        self._region_reset(self.region)
        self.header = self._header_read()
        self.schema = Schema.from_dict({'str': ','.join(self.header)})

    def _header_read(self):
        if self.header:
            return self.header

        if self.options.no_header:
            return None

        line = self.infile.header
        line = list(line)
        if not line:
            with TSVGzipReader(self.options, self.filename) as tempreader:
                return tempreader.header
        else:
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
        if self.lines_iterator is None:
            return

        for line in self.lines_iterator:
            self._progress_step()
            # print(self.linecount, line)

            yield line


class TSVWriter(TSVFormat):
    NA_VALUE = ''

    def __init__(self, options, filename=None):
        super(TSVWriter, self).__init__(options)
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
            [
                to_str(val) if val is not None else self.NA_VALUE
                for val in line
            ]))
        self.outfile.write('\n')

    def header_write(self, line):
        self.line_write(line)

    def line_read(self):
        raise NotImplementedError()

    def lines_read_iterator(self):
        raise NotImplementedError()


class ParquetReader(AbstractFormat):

    def __init__(self, opts, buffer_size=1000):
        super(ParquetReader, self).__init__(opts)
        self.buffer_size = buffer_size
        self.row_group_buffer = []
        self.column_buffer = {}
        self.row_group_curr = 0
        self.buffer_line = 0
        self.schema = Schema()

    def _setup(self):
        assert self.options.infile != '-'
        assert os.path.exists(self.options.infile)
        self.pqfile = pq.ParquetFile(self.options.infile)
        self.schema = Schema.from_parquet(self.pqfile.schema)
        self.header = list(self.schema.columns.keys())
        self.row_group_count = self.pqfile.num_row_groups
        self._read_row_group()

    def _cleanup(self):
        print('Read', self.linecount, 'lines.', file=sys.stderr)

    def _read_row_group(self):
        if self.row_group_curr < self.row_group_count:
            row_group_buffer = self.pqfile.read_row_group(self.row_group_curr)
            self.row_count = row_group_buffer.shape[0]
            self.row_group_curr += 1
            for col in row_group_buffer.itercolumns():
                self.column_buffer[col.name] = col.data.to_pylist()

    def _line_read(self):
        if self.buffer_line == self.row_count:
            if self.row_group_curr >= self.row_group_count:
                return None  # EOF
            else:
                self.buffer_line = 0
                self._read_row_group()

        line = {}
        for col_name, col_data in self.column_buffer.items():
            line[col_name] = col_data[self.buffer_line]

        self.linecount += 1
        self.buffer_line += 1

        if self.linecount % self.linecount_threshold == 0:
            print(self.linecount, 'lines read.', file=sys.stderr)

        return list(line.values())

    def lines_read_iterator(self):
        line = self._line_read()
        while line:
            yield line
            line = self._line_read()

    def line_write(self, line):
        raise NotImplementedError()


class ParquetWriter(AbstractFormat):

    def __init__(self, opts, buffer_size=1000):
        super(ParquetWriter, self).__init__(opts)
        self.row_group_buffer = []
        self.buffer_size = buffer_size
        self.column_buffer = {}
        self.pq_writer = None
        self.buffer_line = 0

    def _setup(self):
        assert self.options.outfile != '-'

    def _cleanup(self):
        print('Wrote', self.linecount, 'lines.', file=sys.stderr)
        self._write_buffer()
        self.pq_writer.close()

    @classmethod
    def get_col_type(cls, col_data):
        for val in col_data:
            if type(val) is list:
                return cls.get_col_type(val)
            elif type(val):
                return type(val)

    @staticmethod
    def coerce_func(new_type):
        def coercer(data):
            if type(data) is list:
                return [None if val in ['.', ''] else new_type(val)
                        for val in data]
            else:
                if data in ['.', '']:
                    return None
                else:
                    return new_type(data)
        return coercer

    @classmethod
    def coerce_column(cls, col_name, col_data, expected_col_type):
        assert col_data
        # actual_col_type = cls.get_col_type(col_data)

        # if actual_col_type is expected_col_type:
        #     return col_data
        # else:
        #     coerce_func = cls.coerce_func(expected_col_type)
        coerce_func = cls.coerce_func(expected_col_type)

        try:
            return list(map(coerce_func, col_data))
        except ValueError:
            print('Column coercion failed:')
            print('Could not coerce column', col_name, 'to specified type!',
                  file=sys.stderr)
            sys.exit(-1)

    def header_write(self, header):
        self.header = header
        for col in self.header:
            self.column_buffer[col.replace('#', '')] = []

    # def _init_header(self):
    #     self.header = list(self.schema.columns.keys())
    #     for col in self.header:
    #         self.column_buffer[col.replace('#', '')] = []

    def _write_buffer(self):
        buffer_table = []
        if not self.pq_writer:
            self.pq_writer = pq.ParquetWriter(self.options.outfile,
                                              self.schema.to_arrow())

        for col_name, col_data in self.column_buffer.items():
            col_type = self.schema.columns[col_name].type_py
            col = pa.column(col_name,
                            pa.array(self.coerce_column(col_name,
                                                        col_data,
                                                        col_type)))
            buffer_table.append(col)

        self.pq_writer.write_table(pa.Table.from_arrays(
                                     buffer_table,
                                     schema=self.schema.to_arrow()))

        for col in self.column_buffer.keys():
            self.column_buffer[col] = []
        self.buffer_line = 0

    def line_write(self, line):
        # if self.header is None:
        #     self._init_header()

        if self.buffer_line == self.buffer_size:
            self._write_buffer()
        for col in range(0, len(line)):
            self.column_buffer[self.header[col]].append(line[col])
        self.linecount += 1
        self.buffer_line += 1

    def lines_read_iterator(self):
        raise NotImplementedError()
