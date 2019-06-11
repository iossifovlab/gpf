from __future__ import print_function, absolute_import

import os
import sys

from collections import OrderedDict
from RegionOperations import Region

from .configure import Configure


def build_contig_regions(genome, TRANSMITTED_STEP=10000000):
    contigs = OrderedDict(genome.get_all_chr_lengths())
    contig_regions = OrderedDict()
    if TRANSMITTED_STEP is None:
        for contig, _ in contigs.items():
            contig_regions[contig] = [Region(contig, None, None)]
        return contig_regions

    contig_parts = OrderedDict([
        (contig, max(int(size / TRANSMITTED_STEP), 1))
        for contig, size in contigs.items()
    ])
    for contig, size in contigs.items():
        regions = []
        total_parts = contig_parts[contig]
        step = int(size / total_parts + 1)
        for index in range(total_parts):
            begin_pos = index * step
            end_pos = (index + 1) * step - 1
            if index + 1 == total_parts:
                end_pos = size
            region = Region(contig, begin_pos, end_pos)
            regions.append(region)
        contig_regions[contig] = regions
    return contig_regions


def contigs_makefile_generate(
        build_contigs, data_contigs, output_directory,
        import_command,
        annotation_config,
        import_sources,
        log_directory=None,
        outfile=sys.stdout):

    makefile = []
    all_targets = []
    contig_targets = OrderedDict()

    for contig_index, contig in enumerate(data_contigs):
        if contig not in build_contigs:
            continue
        assert contig in build_contigs, contig
        # assert len(build_contigs) < 5000, len(build_contigs)
        contig_targets[contig] = []

        for part, region in enumerate(build_contigs[contig]):
            bucket_index = (contig_index + 1) * 100 + part
            suffix = "{:0>3}_{:0>3}_{}".format(
                contig_index, part, contig
            )
            # target_prefix = os.path.join(output_prefix, suffix)

            parquet = Configure.from_prefix_impala(
                output_directory,
                bucket_index=bucket_index,
                suffix=suffix).impala

            targets = [
                parquet.files.variant
            ]

            all_targets.extend(targets)
            contig_targets[contig].extend(targets)

            command = "{import_command} -o {output_directory} " \
                "--bucket-index {bucket_index} " \
                "--region {region} " \
                "--annotation {annotation_config} " \
                "{import_sources}" \
                .format(
                    import_command=import_command,
                    output_directory=output_directory,
                    targets=" ".join(targets),
                    bucket_index=bucket_index,
                    import_sources=import_sources,
                    region=str(region),
                    annotation_config=annotation_config,
                )
            if log_directory is not None:
                if not os.path.exists(log_directory):
                    os.makedirs(log_directory)
                assert os.path.exists(log_directory), log_directory
                assert os.path.isdir(log_directory), log_directory
                log_filename = os.path.join(
                    log_directory,
                    "log_{:0>6}.log".format(bucket_index))
                time_filename = os.path.join(
                    log_directory,
                    "time_{:0>6}.log".format(bucket_index))

                command = "time ({command} &> {log_filename}) " \
                    "2> {time_filename}".format(
                        command=command,
                        log_filename=log_filename,
                        time_filename=time_filename
                    )

            make_rule = "{targets}: " \
                "{import_sources}\n\t" \
                "{command}" \
                .format(
                    command=command,
                    targets=" ".join(targets),
                    import_sources=import_sources,
                )
            makefile.append(make_rule)

    print('SHELL=/bin/bash -o pipefail', file=outfile)
    print('.DELETE_ON_ERROR:\n', file=outfile)

    print("all: {}".format(" ".join(all_targets)), file=outfile)
    print("\n", file=outfile)

    for contig, targets in contig_targets.items():
        print("{}: {}".format(contig, " ".join(targets)), file=outfile)
    print("\n", file=outfile)

    print("\n\n".join(makefile), file=outfile)
