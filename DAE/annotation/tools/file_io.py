import sys
import os
import gzip
import pysam
from abc import ABCMeta, abstractmethod


def assert_file_exists(filepath):
    if filepath != '-' and os.path.exists(filepath) is False:
        sys.stderr.write("The given file '{}' does not exist!\n".format(filepath))
        sys.exit(-78)


class IOType:
    class TSV:
        @staticmethod
        def instance_r(opts):
            return TSVFormat(opts, 'r')

        @staticmethod
        def instance_w(opts):
            return TSVFormat(opts, 'w')


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
            sys.stderr.write("Unrecognized I/O mode '{}'!\n".format(mode))
            sys.exit(-78)
        self.mode = mode
        self.linecount = 0
        self.linecount_threshold = 1000
        self.percent_read = -1
        self.header = None

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _cleanup(self):
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
                self.filesize = os.path.getsize(self.opts.infile)

                if hasattr(self.opts, 'region'):
                    if(self.opts.region is not None):
                        tabix_file = pysam.TabixFile(self.opts.infile)
                        try:
                            self.variantFile = tabix_file.fetch(region=self.opts.region)
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
            sys.stderr.write('Processed ' + str(self.linecount) + ' lines.' + '\n')
            if self.opts.infile != '-':
                self.variantFile.close()
        else:
            if self.opts.outfile != '-':
                self.outfile.close()

    def _header_read(self):
        if not self.opts.no_header:
            header_str = self.variantFile.readline()[:-1]
            if hasattr(self.opts, 'region'):
                if(self.opts.region is not None):
                    with gzip.open(self.opts.infile) as file:
                        header_str = file.readline()[:-1]
            if header_str[0] == '#':
                header_str = header_str[1:]
            self.header = header_str.split('\t')

    def line_read(self):
        if self.mode != 'r':
            sys.stderr.write('Cannot read in write mode!\n')
            sys.exit(-78)

        line = self.variantFile.readline()
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            new_p = (self.variantFile.tell() * 100) / self.filesize
            if new_p > self.percent_read:
                self.percent_read = new_p
                sys.stderr.write(str(self.percent_read) + '%' + '\n')
        return line.rstrip().split('\t')

    def line_write(self, input_):
        if self.mode != 'w':
            sys.stderr.write('Cannot write in read mode!\n')
            sys.exit(-78)

        self.outfile.write('\t'.join(input_) + '\n')
