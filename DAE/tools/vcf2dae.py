#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str

import os
import subprocess
import argparse
import tempfile


def run_command(cmd):
    print("executing", cmd)
    try:
        subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as ex:
        status = ex.returncode
        output = ex.output

        print(status, output)
        raise Exception("FAILURE AT: " + cmd)


def main():
    parser = argparse.ArgumentParser(
        description="converts list of VCF files to DAE transmitted varaints")

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        'vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )

    parser.add_argument(
        "-x", "--project", dest="project",
        metavar="project", help="project name [defualt:VIP")
    parser.add_argument(
        "-l", "--lab", dest="lab",
        default="cshl",
        metavar="lab", help="lab name")

    parser.add_argument(
        "-o", "--output-prefix", dest="output_prefix", 
        default="transmission",
        help="prefix of output transmission file")

    parser.add_argument(
        "-w", "--work-dir", dest="work_dir", default=".",
        help="work directory where to store result and temporary files")

    parser.add_argument(
        "-m", "--minPercentOfGenotypeSamples",
        dest="minPercentOfGenotypeSamples", type=float, default=25.,
        help="threshold percentage of gentyped samples to printout "
        "[default: 25]")

    parser.add_argument(
        "-t", "--tooManyThresholdFamilies",
        dest="tooManyThresholdFamilies", type=int, default=10,
        help="threshold for TOOMANY to printout [defaylt: 10]")

    parser.add_argument(
        "-s", "--missingInfoAsNone",
        action="store_true",
        dest="missingInfoAsNone",
        default=False,
        help="missing sample Genotype will be filled with 'None' for many VCF "
        "files input")

    parser.add_argument(
        "--chr", action="store_true",
        dest="prepend_chr", default=False,
        help="adds prefix to 'chr' to contig names")

    parser.add_argument(
        "--nochr", action="store_true",
        dest="remove_chr", default=False,
        help="removes prefix to 'chr' from contig names")

    args = parser.parse_args()
    print(args)

    tempdir = tempfile.mkdtemp(dir=args.work_dir)
    dae_prefix = os.path.join(args.work_dir, args.output_prefix)

    dae_name = "{}.txt".format(args.output_prefix)
    dae_too_name = "{}-TOOMANY.txt".format(args.output_prefix)

    dae_fullname = os.path.join(args.work_dir, dae_name)
    dae_too_fullname = os.path.join(args.work_dir, dae_too_name)

    temp_dae_name = os.path.join(tempdir, dae_name)
    temp_dae_too_name = os.path.join(tempdir, dae_too_name)
    temp_dae_prefix = os.path.join(tempdir, args.output_prefix)

    # main procedure
    # cmd = ' '.join( ['vcf2DAEc.py', '-p', ox.pedFile, '-d', ox.dataFile,
    # '-x', ox.project, '-l', ox.lab, \
    cmd = ' '.join(
        [
            'vcf2dae_command_fast.py',
            args.pedigree,
            '"' + args.vcf + '"',

            '-x', args.project,
            '-l', args.lab,
            '-o', temp_dae_prefix,
            '-m', str(args.minPercentOfGenotypeSamples),
            '-t', str(args.tooManyThresholdFamilies),
        ])

    if args.missingInfoAsNone:
        cmd += ' --missingInfoAsNone'
    if args.prepend_chr:
        cmd += ' --chr'
    if args.remove_chr:
        cmd += ' --nochr'
    run_command(cmd)

    # HW
    cmd = ' '.join([
        'hw.py',
        '-c', temp_dae_name,
        dae_fullname
    ])
    run_command(cmd)

    # family file
    cmd = ' '.join([
        'mv',
        temp_dae_prefix + '-families.txt',
        dae_prefix + '-families.txt'
    ])
    run_command(cmd)

    # toomany file
    cmd = ' '.join([
        'mv',
        temp_dae_too_name,
        dae_too_fullname
    ])
    run_command(cmd)


if __name__ == "__main__":
    main()
