#!/usr/bin/env python

import commands
import optparse


def main():
    # copy of options for vcf2DAEc.py
    usage = "usage: %prog [options] "\
        "<families pedigree file> <list of vcf files>"
    parser = optparse.OptionParser(usage=usage)

    parser.add_option(
        "-x", "--project", dest="project", default="VIP",
        metavar="project", help="project name [defualt:VIP")
    parser.add_option(
        "-l", "--lab", dest="lab", default="SF",
        metavar="lab", help="lab name [defualt:SF")

    parser.add_option(
        "-o", "--outputPrefix", dest="outputPrefix", default="transmission",
        metavar="outputPrefix", help="prefix of output transmission file")

    parser.add_option(
        "-m", "--minPercentOfGenotypeSamples",
        dest="minPercentOfGenotypeSamples", type=float, default=25.,
        metavar="minPercentOfGenotypeSamples",
        help="threshold percentage of gentyped samples to printout "
        "[default: 25]")

    parser.add_option(
        "-t", "--tooManyThresholdFamilies",
        dest="tooManyThresholdFamilies", type=int, default=10,
        metavar="tooManyThresholdFamilies",
        help="threshold for TOOMANY to printout [defaylt: 10]")

    parser.add_option(
        "-s", "--missingInfoAsNone",
        action="store_true",
        dest="missingInfoAsNone",
        default=False,
        metavar="missingInfoAsNone",
        help="missing sample Genotype will be filled with 'None' for many VCF "
        "files input")

    ox, args = parser.parse_args()

    def tExt(xxx): return '.zZqZz{:d}'.format(xxx) if isinstance(
        xxx, int) else '.zZqZz{:s}'.format(xxx)
    # tmp files' extension

    # main procedure
    # cmd = ' '.join( ['vcf2DAEc.py', '-p', ox.pedFile, '-d', ox.dataFile,
    # '-x', ox.project, '-l', ox.lab, \
    cmd = ' '.join(
        ['vcf2DAEc_fast.py', '-p', args[0], '-d "' + args[1] + '" -x',
         ox.project, '-l', ox.lab,
         '-o', ox.outputPrefix +
         tExt(0), '-m', str(ox.minPercentOfGenotypeSamples),
         '-t', str(ox.tooManyThresholdFamilies)])
    if ox.missingInfoAsNone:
        cmd += ' '.join([' --missingInfoAsNone', ' > ' +
                         ox.outputPrefix + '-complex.txt'])
    else:
        cmd += ' > ' + ox.outputPrefix + '-complex.txt'

    print "executing", cmd
    status, out = commands.getstatusoutput(cmd)
    print status, out
    if status:
        raise Exception("FAILURE AT: " + cmd)
    # family file
    cmd = ' '.join(['\\mv', ox.outputPrefix + tExt(0) +
                    '-families.txt', ox.outputPrefix + '-families.txt'])
    print "executing", cmd

    status, out = commands.getstatusoutput(cmd)
    print status, out
    if status:
        raise Exception("FAILURE AT: " + cmd)
    # HW
    cmd = ' '.join(['hw.py -c', ox.outputPrefix + tExt(0) +
                    '.txt', ox.outputPrefix + tExt(1) + '.txt'])
    print "executing", cmd

    status, out = commands.getstatusoutput(cmd)
    print status, out
    if status:
        raise Exception("FAILURE AT: " + cmd)


if __name__ == "__main__":
    main()
