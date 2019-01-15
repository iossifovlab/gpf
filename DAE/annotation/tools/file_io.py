from __future__ import print_function

from annotation.tools.file_io_tsv import TSVFormat, \
        TSVReader, TSVWriter, TabixReaderVariants, TSVGzipReader
try:
    parquet_enabled = True
    from annotation.tools.file_io_parquet import ParquetReader, \
        ParquetWriter
except ImportError:
    parquet_enabled = False


class IOType:
    class TSV:
        @staticmethod
        def instance_r(opts):
            filename = opts.infile
            if TSVFormat.is_tabix(filename):
                return TabixReaderVariants(opts)
            if TSVFormat.is_gzip(filename):
                return TSVGzipReader(opts)
            return TSVReader(opts)

        @staticmethod
        def instance_w(opts):
            return TSVWriter(opts)

    class Parquet:
        @staticmethod
        def instance_r(opts):
            assert parquet_enabled
            return ParquetReader(opts)

        @staticmethod
        def instance_w(opts):
            assert parquet_enabled
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
        return self.reader.schema.col_names

    def header_write(self, input_):
        self.writer.header_write(input_)

    def lines_read_iterator(self):
        return self.reader.lines_read_iterator()

    def line_write(self, input_):
        self.writer.line_write(input_)
