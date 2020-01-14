import os

from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator
from dae.backends.impala.parquet_io import ParquetPartitionDescription
from dae.utils.dict_utils import recursive_dict_update


def construct_import_annotation_pipeline(
        dae_config, genomes_db,
        annotation_configfile=None, defaults=None):

    if defaults is None:
        defaults = {}
    if annotation_configfile is not None:
        config_filename = annotation_configfile
    else:
        config_filename = dae_config.annotation.conf_file

    assert os.path.exists(config_filename), config_filename
    options = {
        "vcf": True,
        'c': 'chrom',
        'p': 'position',
        'r': 'reference',
        'a': 'alternative',
    }
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

    common_command = f'{tool} ' \
        f'--skip-pedigree --o {argv.output}' \
        f' --pd {argv.partition_description}' \
        f' --ped-file-format {argv.ped_file_format}'
    if 'annotation_config' in argv:
        common_command += f' --annotation-config {argv.annotation_config}'

    for target_name in targets.keys():
        all_target += f' {target_name}'

    bucket_index = 100

    for target_name, target_args in targets.items():
        main_targets += f'{target_name}:\n'
        main_targets += f'\t{common_command} '
        main_targets += \
            f'-b {bucket_index} '
        main_targets += \
            f' --region {generate_region_argument_string(*target_args)}\n\n'
        bucket_index += 1

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
            other_targets += f'\t{common_command}'
            other_targets += f' --region {regions}\n\n'

    output += f'{all_target}\n'
    output += '.PHONY: all\n\n'
    output += main_targets
    output += other_targets
    print(output)
