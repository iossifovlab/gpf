from __future__ import print_function

import sys
import os

import pyarrow as pa
import pyarrow.parquet as pq
from box import Box
from annotation.tools.schema import Schema
from annotation.tools.file_io_tsv import AbstractFormat
from collections import OrderedDict


class ParquetSchema(Schema):

    # New types only need to be added here.
    type_map = OrderedDict([
                ('str', (str, pa.string())),
                ('float', (float, pa.float64())),
                ('int', (int, pa.uint32())),
                ('int8', (int, pa.int8())),
                ('int16', (int, pa.int16())),
                ('int32', (int, pa.int32())),
                ('int64', (int, pa.int64())),
                ('list(str)', (str, pa.list_(pa.string()))),
                ('list(float)', (float, pa.list_(pa.float64()))),
                ('list(int)', (int, pa.list_(pa.uint32())))])

    def __init__(self):
        super(ParquetSchema, self).__init__()

    @classmethod
    def produce_type(cls, type_name):
        assert type_name in cls.type_map
        return Box({'type_name': type_name,
                    'type_py': cls.type_map[type_name][0],
                    'type_pa': cls.type_map[type_name][1]},
                   default_box=True,
                   default_box_attr=None)

    def create_column(self, col_name, col_type):
        if col_name not in self.columns:
            self.columns[col_name] = ParquetSchema.produce_type(col_type)

    @classmethod
    def convert(cls, schema):
        if isinstance(schema, ParquetSchema):
            return schema
        assert isinstance(schema, Schema)
        pq_schema = ParquetSchema()
        for col_name, col_type in schema.columns.items():
            pq_schema.columns[col_name] = \
                ParquetSchema.produce_type(col_type.type_name)
        return pq_schema

    @classmethod
    def from_dict(cls, schema_dict):
        return cls.convert(Schema.from_dict(schema_dict))

    @classmethod
    def merge_schemas(cls, left, right):
        return cls.convert(Schema.merge_schemas(left, right))

    @classmethod
    def from_parquet(cls, pq_schema):
        return cls.from_arrow(pq_schema.to_arrow_schema())

    @classmethod
    def from_arrow(cls, pa_schema):
        new_schema = ParquetSchema()
        for col in pa_schema:
            for type_name, types in new_schema.type_map.items():
                if col.type == types[1]:
                    new_schema.columns[col.name] = cls.produce_type(type_name)
                    break
        if len(new_schema.columns) != len(pa_schema):
            print(("An error occured during conversion of the"
                   " Parquet file's schema. This is most likely caused"
                   " by a missing type counterpart in"
                   " type_map (ParquetSchema class)."),
                  file=sys.stderr)
            sys.exit(-1)
        return new_schema

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


class ParquetReader(AbstractFormat):

    def __init__(self, opts, buffer_size=1000):
        super(ParquetReader, self).__init__(opts)
        self.buffer_size = buffer_size
        self.row_group_buffer = []
        self.column_buffer = {}
        self.row_group_curr = 0
        self.buffer_line = 0
        self.schema = ParquetSchema()

    def _setup(self):
        assert self.options.infile != '-'
        assert os.path.exists(self.options.infile)
        self.pqfile = pq.ParquetFile(self.options.infile)
        self.schema = ParquetSchema.from_parquet(self.pqfile.schema)
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
        self.schema = ParquetSchema()

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
                return [None if val in [None, '.', ''] else new_type(val)
                        for val in data]
            else:
                if data in [None, '.', '']:
                    return None
                else:
                    return new_type(data)
        return coercer

    @classmethod
    def coerce_column(cls, col_name, col_data, expected_col_type):
        assert col_data
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

    def _write_buffer(self):
        buffer_table = []
        if not isinstance(self.schema, ParquetSchema):
            self.schema = ParquetSchema.convert(self.schema)
        if not self.pq_writer:
            self.pq_writer = pq.ParquetWriter(self.options.outfile,
                                              self.schema.to_arrow())

        for col_name, col_data in self.column_buffer.items():
            col_type = self.schema.columns[col_name].type_py
            pa_type = self.schema.columns[col_name].type_pa
            col = pa.column(col_name,
                            pa.array(self.coerce_column(col_name,
                                                        col_data,
                                                        col_type),
                                     type=pa_type))
            buffer_table.append(col)

        self.pq_writer.write_table(pa.Table.from_arrays(
                                   buffer_table,
                                   schema=self.schema.to_arrow()))

        for col in self.column_buffer.keys():
            self.column_buffer[col] = []
        self.buffer_line = 0

    def line_write(self, line):
        if self.buffer_line == self.buffer_size:
            self._write_buffer()
        for col in range(0, len(line)):
            self.column_buffer[self.header[col]].append(line[col])
        self.linecount += 1
        self.buffer_line += 1

    def lines_read_iterator(self):
        raise NotImplementedError()
