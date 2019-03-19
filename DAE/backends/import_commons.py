from __future__ import print_function, absolute_import

# import os
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
        build_contigs, data_contigs, output_prefix,
        import_command,
        annotation_config,
        import_sources,
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
            suffix = "{:0>3}_{:0>3}_{}_".format(
                contig_index, part, contig
            )
            # target_prefix = os.path.join(output_prefix, suffix)

            parquet = Configure.from_prefix_parquet(
                output_prefix,
                bucket_index=bucket_index,
                suffix=suffix).parquet

            targets = [
                parquet.summary_variant
            ]

            all_targets.extend(targets)
            contig_targets[contig].extend(targets)

            command = "{targets}: " \
                "{import_sources}\n\t" \
                "{import_command} -o {output_prefix} " \
                "--bucket-index {bucket_index} " \
                "--region {region} " \
                "--sequential " \
                "--annotation {annotation_config} " \
                "{import_sources}" \
                .format(
                    import_command=import_command,
                    target_prefix=output_prefix,
                    targets=" ".join(targets),
                    bucket_index=bucket_index,
                    import_sources=import_sources,
                    region=str(region),
                    annotation_config=annotation_config,
                )
            makefile.append(command)

    print('SHELL=/bin/bash -o pipefail', file=outfile)
    print('.DELETE_ON_ERROR:\n', file=outfile)

    print("all: {}".format(" ".join(all_targets)), file=outfile)
    print("\n", file=outfile)

    for contig, targets in contig_targets.items():
        print("{}: {}".format(contig, " ".join(targets)), file=outfile)
    print("\n", file=outfile)

    print("\n\n".join(makefile), file=outfile)
