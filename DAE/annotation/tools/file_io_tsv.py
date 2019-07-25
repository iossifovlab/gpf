from __future__ import print_function, absolute_import

import sys
import os
import gzip

import pysam
from abc import ABCMeta, abstractmethod
from box import Box
from annotation.tools.schema import Schema
from annotation.tools.utils import handle_header


def to_str(column_value):
    if isinstance(column_value, list):
        return '|'.join(map(to_str, column_value))
    elif column_value is None:
        return ''
    else:
        return str(column_value)


def handle_chrom_prefix(expect_prefix, data):
    if data is None:
        return data
    if expect_prefix and not data.startswith('chr'):
        return "chr{}".format(data)
    if not expect_prefix and data.startswith('chr'):
        return data[3:]
    return data


class RegionHelper(object):

    def __init__(self, region_string, pos_index):
        self.pos_start, self.pos_end = \
            RegionHelper.parse_region_string(region_string)
        self.pos_index = pos_index

    @staticmethod
    def parse_region_string(region):
        region = region.split(':')
        assert len(region) == 2

        pos_start = None
        pos_end = None
        if '-' in region[1]:
            pos_start = region[1].split('-')[0]
            pos_end = region[1].split('-')[1]
        else:
            pos_start = region[1]

        try:
            pos_start = int(pos_start)
            if pos_end:
                pos_end = int(pos_end)
            return (pos_start,
                    pos_end)
        except ValueError:
            sys.exit(-1)

    def contains(self, line):
        try:
            pos = int(line[self.pos_index])
        except ValueError:
            sys.exit(-1)

        if self.pos_end:
            if pos >= self.pos_start and pos <= self.pos_end:
                return True
            return False
        else:
            if pos >= self.pos_start:
                return True
            return False


class NoRegionHelper(object):
    def contains(self, pos):
        return True


class AbstractFormat(object):

    __metaclass__ = ABCMeta

    def __init__(self, opts):
        options = Box(opts.to_dict(), default_box=True, default_box_attr=None)
        self.options = options

        self.linecount = 0
        self.linecount_threshold = 1000
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
        pass
        # print('Processed', self.linecount, 'lines.', file=sys.stderr)


class TSVReader(TSVFormat):

    def __init__(self, options, filename=None):
        super(TSVReader, self).__init__(options)
        if filename is None:
            assert options.infile is not None
            filename = options.infile
        self.filename = filename
        self.schema = None
        self.seek_pos = 0

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
            assert os.path.exists(self.filename), self.filename
            assert not self.is_gzip(self.filename)
            self.infile = open(self.filename, 'r')

        if self.options.vcf:
            self._skip_metalines()

        self.schema = Schema.from_dict({'str': ','.join(self._header_read())})

    def _skip_metalines(self):
        self.seek_pos = self.infile.tell()
        while self.infile.readline().startswith('##'):
            self.seek_pos = self.infile.tell()
        self.infile.seek(self.seek_pos)

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
        if self.schema:
            return self.schema.col_names

        if self.options.no_header:
            line = self.infile.readline()
            self.infile.seek(self.seek_pos)
            return [str(index) for index, col
                    in enumerate(line.strip()
                                 .split(self.separator))]
        else:
            line = self.infile.readline()
            header_str = line.strip()
            if header_str.startswith("#"):
                header_str = header_str[1:]
            return handle_header(header_str.split(self.separator))

    def line_write(self, line):
        raise NotImplementedError()

    def line_read(self):
        line = self.infile.readline().rstrip('\n')

        if not line:
            return None
        self._progress_step()
        return line.split(self.separator)

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

        if self.options.vcf:
            self._skip_metalines()

        self.schema = Schema.from_dict({'str': ','.join(self._header_read())})


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

    def _region_reset(self, region):
        region = handle_chrom_prefix(self._has_chrom_prefix, region)
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
        self.schema = Schema.from_dict({'str': ','.join(self._header_read())})

    def _header_read(self):
        if self.schema:
            return self.schema.col_names

        line = list(self.infile.header)
        if not line:
            with TSVGzipReader(self.options, self.filename) as tempreader:
                return tempreader.schema.col_names
        else:
            header_str = line[-1]
            if header_str.startswith("#"):
                header_str = header_str[1:]
            return handle_header(header_str.split(self.separator))

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

    def lines_read_iterator(self):
        if self.lines_iterator is None:
            return

        for line in self.lines_iterator:
            self._progress_step()
            yield line


class TabixReaderVariants(TabixReader):

    def __init__(self, options, filename=None):
        super(TabixReaderVariants, self).__init__(options, filename)

    def _setup(self):
        super(TabixReaderVariants, self)._setup()

        if self.options.vcf and self.options.region:
            pos_index = self.schema.col_names.index(self.options.p)
            self.region_helper = RegionHelper(self.options.region, pos_index)
        else:
            self.region_helper = NoRegionHelper()

    def lines_read_iterator(self):
        if self.lines_iterator is None:
            return

        for line in self.lines_iterator:
            self._progress_step()

            if self.region_helper.contains(line):
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

    def lines_read_iterator(self):
        raise NotImplementedError()
