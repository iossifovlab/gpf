import sys
import time
import datetime

def give_column_number(s, header):
    try:
        c = header.index(s)
        return(c+1)
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

    (opts, args) = argument_parser.parse_args()

    if opts.help:
        print_help()
        sys.exit(0)


    infile = '-'
    outfile = None

    if len(args) > 0:
        infile = args[0]

    if infile != '-' and os.path.exists(infile) == False:
        sys.stderr.write("The given input file does not exist!\n")
        sys.exit(-78)

    if len(args) > 1:
        outfile = args[1]
    if outfile=='-':
        outfile = None

    if infile=='-':
        variantFile = sys.stdin
    else:
        variantFile = open(infile)

    if opts.no_header == False:
        header_str = variantFile.readline()
        header = header_str.split()
    else:
        header = None

    if outfile != None:
        out = open(outfile, 'w')
    else:
        out = sys.stdout

    annotator = annotator_factory(opts=opts, header=header)
    annotator.annotate_file(variantFile, out)

    out.write("# PROCESSING DETAILS:\n")
    out.write("# " + time.asctime() + "\n")
    out.write("# " + " ".join(sys.argv[1:]) + "\n")

    if infile != '-':
        variantFile.close()

    if outfile != None:
        out.close()
        sys.stderr.write("Output file saved as: " + outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")
