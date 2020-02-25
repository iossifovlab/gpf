#!/usr/bin/env python
# encoding: utf-8
"""
extract_family_variants.py -- extracts transmitted variants for given families.

Created on Jan 19, 2018

@author:     lubo

@contact:    lubomir.chorbadjiev@gmail.com
"""
import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import gzip

__all__ = []
__version__ = 0.1
__date__ = "2018-01-19"
__updated__ = "2018-01-19"

DEBUG = 0
TESTRUN = 0
PROFILE = 0


class FilterFamilies(object):
    def __init__(self, args):
        self.outdir = args.outdir
        self.name = args.name
        self.families = set([f.strip() for f in args.families.split(",")])
        self.summary_filename = args.transmittedfile
        self.tm_filename = args.toomanyfile

    def handle(self):
        print(
            "Working with summary filename: {}".format(self.summary_filename)
        )
        out_filename = os.path.join(self.outdir, "{}.txt".format(self.name))
        out_tm_filename = os.path.join(
            self.outdir, "{}-TOOMANY.txt".format(self.name)
        )
        print(
            "Storing result into: {} and {}".format(
                out_filename, out_tm_filename
            )
        )

        with gzip.open(self.summary_filename, "r") as fh, gzip.open(
            self.tm_filename, "r"
        ) as tmfh, open(out_filename, "w") as out, open(
            out_tm_filename, "w"
        ) as out_tm:

            header_line = fh.readline()
            out.write(header_line)
            out.write("\n")

            column_names = header_line.rstrip().split("\t")

            tm_header_line = tmfh.readline()
            tm_column_names = tm_header_line.rstrip().split("\t")

            out_tm.write(header_line)
            out_tm.write("\n")

            print(column_names)
            print(tm_column_names)

            vrow = 1
            for line in fh:
                try:
                    if line[0] == "#":
                        print("skipping comment: {}".format(line.strip()))
                        continue
                    line = line.strip("\r\n")
                    data = line.split("\t")
                    vals = dict(list(zip(column_names, data)))
                    family_data = vals["familyData"]
                    if family_data == "TOOMANY":
                        tm_line = tmfh.readline()
                        tm_line = tm_line.strip("\r\n")
                        tm_data = tm_line.split("\t")
                        family_data = tm_data[3]
                        check = any([f in family_data for f in self.families])
                        if check:
                            out.write(line)
                            out.write("\n")
                            out_tm.write(tm_line)
                            out_tm.write("\n")

                    else:
                        check = any([f in family_data for f in self.families])
                        if check:
                            out.write(line)
                            out.write("\n")

                    if vrow % 10000 == 0:
                        sys.stderr.write(".")
                    vrow += 1
                except Exception as ex:
                    import traceback

                    print(
                        "exception thrown during processing line: |{}|".format(
                            line
                        )
                    )
                    traceback.print_exc()
                    raise ex

            sys.stderr.write("\n")


def main(argv=None):  # IGNORE:C0111
    """Command line options."""

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = "%%(prog)s %s (%s)" % (
        program_version,
        program_build_date,
    )
    program_shortdesc = __import__("__main__").__doc__.split("\n")[1]
    program_desc = """%s
%s
USAGE
""" % (
        program_shortdesc,
        str(__date__),
    )

    try:
        # Setup argument parser
        parser = ArgumentParser(
            description=program_desc,
            formatter_class=RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "-o",
            "--outdir",
            default=".",
            dest="outdir",
            help="output directory where to store SQL files."
            "[default: %(default)s]",
        )
        parser.add_argument(
            "-N",
            "--name",
            dest="name",
            help="result filenames base " "[default: %(default)s]",
        )

        parser.add_argument(
            "-V",
            "--version",
            action="version",
            version=program_version_message,
        )

        parser.add_argument(
            "-F",
            "--families",
            dest="families",
            help="comman separated list of families",
        )

        parser.add_argument(
            "-T",
            "--transmittedfile",
            dest="transmittedfile",
            help="transmitted variants base file name",
        )

        parser.add_argument(
            "-M",
            "--toomanyfile",
            dest="toomanyfile",
            help="transmitted variants family variants file name",
        )

        args = parser.parse_args()

        handler = FilterFamilies(args)
        handler.handle()

        return 0
    except KeyboardInterrupt:
        # handle keyboard interrupt
        return 0
    except Exception as e:
        import traceback

        traceback.print_exc()

        if DEBUG or TESTRUN:
            raise (e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
