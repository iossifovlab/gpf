import os
import sys

from collections import OrderedDict
from dae.RegionOperations import Region

from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescription

from dae.utils.dict_utils import recursive_dict_update


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


def construct_import_annotation_pipeline(
        dae_config, genomes_db, argv=None, defaults=None):
    if defaults is None:
        defaults = {}
    if argv is not None and 'annotation_config' in argv and \
            argv.annotation_config is not None:
        config_filename = argv.annotation_config
    else:
        config_filename = dae_config.annotation.conf_file

    assert os.path.exists(config_filename), config_filename
    options = {}
    if argv is not None:
        options = {
            k: v for k, v in argv._get_kwargs()
        }
    options.update({
        "vcf": True,
        'c': 'chrom',
        'p': 'position',
        'r': 'reference',
        'a': 'alternative',
    })
    options = Box(options, default_box=True, default_box_attr=None)

    annotation_defaults = {'values': dae_config.annotation_defaults}

    annotation_defaults = recursive_dict_update(annotation_defaults, defaults)

    pipeline = PipelineAnnotator.build(
        options, config_filename, dae_config.dae_data_dir, genomes_db,
        defaults=annotation_defaults)
    return pipeline


def generate_region_argument_string(chrom, start, end):
    if start is None and end is None:
        return f'{chrom}'
    else:
        assert start and end, f'{start}-{end} is an invalid region!'
        return f'{chrom}:{start}-{end}'


def generate_region_argument(fa, description):
    segment = fa.position // description.region_length
    start = (segment * description.region_length) + 1
    end = (segment + 1) * description.region_length

    return (fa.chromosome, start, end)


def generate_makefile(genome, contigs, tool, argv):
    if argv.partition_description is None:
        output = 'all: \n'
        output += f'\t{tool}' \
            f'--o {argv.output} '
        print(output)
        return

    description = ParquetPartitionDescription.from_config(
        argv.partition_description)

    assert set(description.chromosomes).issubset(contigs), \
        (description.chromosomes, contigs)

    targets = dict()
    other_regions = dict()
    contig_lengths = dict(genome.get_all_chr_lengths())

    for contig in description.chromosomes:
        assert contig in contig_lengths, (contig, contig_lengths)
        region_bins = contig_lengths[contig] // description.region_length \
            + bool(contig_lengths[contig] % description.region_length)
        for rb_idx in range(0, region_bins):

            if description.region_length < contig_lengths[contig]:
                start = rb_idx * description.region_length + 1
                end = (rb_idx + 1) * description.region_length
            else:
                start, end = None, None

            if contig in description.chromosomes:
                region_bin = f'{contig}_{rb_idx}'
                targets[region_bin] = (contig, start, end)
            else:
                region_bin = f'other_{rb_idx}'
                other_regions.setdefault(region_bin, set()).add(
                    (contig, start, end)
                )

    output = ''
    all_target = 'all:'
    main_targets = ''
    other_targets = ''
    for target_name in targets.keys():
        all_target += f' {target_name}'

    for target_name, target_args in targets.items():
        command = f'{tool} ' \
            f'--skip-pedigree --o {argv.output}' \
            f' --pd {argv.partition_description}' \
            f' --region {generate_region_argument_string(*target_args)}' \
            f' --ped-file-format {argv.ped_file_format}'
        main_targets += f'{target_name}:\n'
        main_targets += f'\t{command}\n\n'

    if len(other_regions) > 0:
        for region_bin, command_args in other_regions.items():
            all_target += f' {region_bin}'
            other_targets += f'{region_bin}:\n'
            regions = ' '.join(
                map(
                    lambda x: generate_region_argument_string(*x),
                    command_args
                )
            )
            command = f'{tool} ' \
                f'--skip-pedigree --o {argv.output} ' \
                f'--pd {argv.partition_description} ' \
                f'--region {regions}'
            other_targets += f'\t{command}\n\n'

    output += f'{all_target}\n'
    output += '.PHONY: all\n\n'
    output += main_targets
    output += other_targets
    print(output)
