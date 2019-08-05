#!/usr/bin/env python

import argparse
import os
import datetime
import sys
from subprocess import check_output
from dae.annotation.annotation_makefile_generator import VariantDBConfig

compression = "zcat {}"
no_compression = "cat {}"
verify_sh = "{} | wc -l"
log_string = ("Integrity error:\n"
              "File {};\n"
              "Source: {} lines;\n"
              "Result: {} lines;\n"
              "Total : {} lines difference;\n\n")


def sanitize(path):
    if ';' in path:
        print('Semicolon detected in file path. Aborting...')
        sys.exit(-1)
    return('"{}"'.format(path))


def is_compressed(path):
    out = check_output('file {}'.format(path), shell=True)
    if 'gzip' in out:
        return True
    if 'ASCII' in out:
        return False
    else:
        print('Unsupported format for file {}. Aborting...'.format(path))
        sys.exit(-1)


def collect_lcs(directory):
    result = {}
    variantDB = VariantDBConfig(directory)
    print('#{}'.format(directory))
    for study, annotation_file in variantDB.denovo_files + \
            variantDB.transmitted_files:
        print('Collecting line count for {}...'.format(annotation_file))
        name = os.path.split(annotation_file)[1]
        annotation_file = sanitize(annotation_file)
        if(is_compressed(annotation_file)):
            lc = check_output(verify_sh.format(
                    compression.format(annotation_file)),
                    shell=True)
        else:
            lc = check_output(verify_sh.format(
                    no_compression.format(annotation_file)),
                    shell=True)
        result[name] = int(lc.strip())
    return result


def main():
    parser = argparse.ArgumentParser(
        description="tool to verify annotation result has no missing variants")

    parser.add_argument('data_dir', help="path to the instance data directory")
    parser.add_argument('output_dir', help="path to the output data directory")
    args = parser.parse_args()

    timestamp = datetime.date.today().strftime('%d-%m-%y')
    data_dir = os.path.abspath(args.data_dir)
    output_dir = os.path.abspath(args.output_dir)
    log_dir = os.path.join(output_dir,
                           'annotation-integrity-{}.txt'.format(timestamp))

    data_lcs = collect_lcs(data_dir)
    output_lcs = collect_lcs(output_dir)
    integrity_error = False

    with open(log_dir, 'w') as log:
        log.write(datetime.datetime.now()
                  .strftime('%d-%m-%y, %H:%M:%S') + '\n')
        for annotation_file, line_count in data_lcs.iteritems():
            assert annotation_file in output_lcs
            if line_count - output_lcs[annotation_file] != 0:
                integrity_error = True
                log.write(log_string.format(
                    annotation_file,
                    line_count,
                    output_lcs[annotation_file],
                    line_count - output_lcs[annotation_file]))
        if not integrity_error:
            log.write('No integrity errors found.\n')


if __name__ == '__main__':
    main()
