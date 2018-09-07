import sys
import time
import datetime
import pysam
import gzip
from file_io import IOManager, IOType
from abc import ABCMeta, abstractmethod


class AnnotatorBase():
    """
    `AnnotatorBase` is base class of all `Annotators` and `Preannotators`.
    """

    __metaclass__ = ABCMeta

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header

    def annotate_file(self, file_io_manager):
        """
            Method for annotating file from `Annotator`.
        """
        if not self.opts.no_header:
            file_io_manager.line_write(file_io_manager.header)

        for line in file_io_manager.lines_read():
            if '#' in line[0]:
                file_io_manager.line_write(line)
                continue
            annotated = self.line_annotations(line, self.new_columns)
            file_io_manager.line_write(annotated)

    @property
    @abstractmethod
    def new_columns(self):
        """
            New columns to be added to the original variants.
        """

    @abstractmethod
    def line_annotations(self, line, new_columns):
        """
            Method returning annotations for the given line
            in the order from new_columns parameter.
        """


def give_column_number(s, header):
    try:
        return len(header) - header[::-1].index(s)
    except:
        sys.stderr.write("Used parameter: " + s + " does NOT exist in the input file header\n")
        sys.exit(-678)


def assign_values(param, header=None):
    if param is None:
        return(param)
    try:
        param = int(param)
    except:
        if header is None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, header)
    return(param)


def main(argument_parser, annotator_factory,
         start=time.time()):

    argument_parser.add_argument('--region',
        help='region to annotate (chr:begin-end) (input should be tabix indexed)',
        action='store')

    argument_parser.add_argument(
            'infile', nargs='?', action='store',
            default='-', help='path to input file; defaults to stdin')
    argument_parser.add_argument(
            'outfile', nargs='?', action='store',
            default='-', help='path to output file; defaults to stdout')

    opts = argument_parser.parse_args()

    # Hardcoded to work with tsv files until parquet support is added
    with IOManager(opts, IOType.TSV, IOType.TSV) as io_manager:
        annotator = annotator_factory(opts=opts, header=io_manager.header)
        annotator.annotate_file(io_manager)

    sys.stderr.write("# PROCESSING DETAILS:\n")
    sys.stderr.write("# " + time.asctime() + "\n")
    sys.stderr.write("# " + " ".join(sys.argv[1:]) + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start, 0))) + "\n")
