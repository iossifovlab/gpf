import sys, os
import time, datetime
import pysam, gzip
from abc import ABCMeta, abstractmethod

class AnnotatorBase():
    """
    `AnnotatorBase` is base class of all `Annotators` and `Preannotators`.
    """

    __metaclass__ = ABCMeta

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header

    def annotate_file(self, input, output):
        """
            Method for annotating file from `Annotator`.
        """
        if self.opts.no_header == False:
            output.write("\t".join(self.header) + "\n")

        sys.stderr.write("...processing....................\n")
        k = 0

        for l in input:
            if l[0] == "#":
                output.write(l)
                continue
            k += 1
            if k%1000 == 0:
                sys.stderr.write(str(k) + " lines processed\n")

            line = l[:-1].split("\t")
            line_annotations = self.line_annotations(line, self.new_columns)
            output.write("\t".join(line + line_annotations) + "\n")

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
    if param == None:
        return(param)
    try:
        param = int(param)
    except:
        if header == None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, header)
    return(param)



def main(argument_parser, annotator_factory):
    start=time.time()

    argument_parser.add_argument('infile', nargs='?', action='store',
        default='-', help='path to input file; defaults to stdin')
    argument_parser.add_argument('outfile', nargs='?', action='store',
        default='-', help='path to output file; defaults to stdout')

    opts = argument_parser.parse_args()

    if opts.infile != '-' and os.path.exists(opts.infile) == False:
        sys.stderr.write("The given input file does not exist!\n")
        sys.exit(-78)

    if opts.infile=='-':
        variantFile = sys.stdin
    elif hasattr(opts,'region'): #case for MultiAnnotator
        if(opts.region is not None):
            tabix_file = pysam.TabixFile(opts.infile)
            try:
                variantFile = tabix_file.fetch(region=opts.region)
            except ValueError:
                variantFile = iter([])
        else:
            variantFile = open(opts.infile)
    else:
        variantFile = open(opts.infile)

    if opts.no_header == False:
        header_str = variantFile.readline()[:-1]
        if hasattr(opts,'region'): #case for MultiAnnotator
            if(opts.region is not None):
                with gzip.open(opts.infile) as file:
                    header_str=file.readline()[:-1]
        if header_str[0] == '#':
            header_str = header_str[1:]
        header = header_str.split('\t')
    else:
        header = None

    if opts.outfile != '-':
        out = open(opts.outfile, 'w')
    else:
        out = sys.stdout

    annotator = annotator_factory(opts=opts, header=header)
    annotator.annotate_file(variantFile, out)

    sys.stderr.write("# PROCESSING DETAILS:\n")
    sys.stderr.write("# " + time.asctime() + "\n")
    sys.stderr.write("# " + " ".join(sys.argv[1:]) + "\n")

    if opts.infile != '-':
        variantFile.close()

    if opts.outfile != '-':
        out.close()
        sys.stderr.write("Output file saved as: " + opts.outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")
