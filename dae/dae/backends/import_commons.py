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


def contigs_makefile_generate(
        build_contigs, data_contigs, output_directory,
        import_command,
        annotation_config,
        import_sources,
        log_directory=None,
        rows=100000,
        outfile=sys.stdout,
        env=""):

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

            parquet_files = ParquetManager.build_parquet_filenames(
                output_directory,
                bucket_index=bucket_index,
                suffix=suffix
            )

            targets = [
                parquet_files.variant
            ]

            all_targets.extend(targets)
            contig_targets[contig].extend(targets)

            command = "{import_command} -o {output_directory} " \
                "--bucket-index {bucket_index} " \
                "--region {region} " \
                "--rows {rows} " \
                "--annotation {annotation_config} " \
                "{import_sources}" \
                .format(
                    import_command=import_command,
                    output_directory=output_directory,
                    targets=" ".join(targets),
                    bucket_index=bucket_index,
                    import_sources=import_sources,
                    region=str(region),
                    rows=rows,
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

                command = "time -o {time_filename} {command} &> " \
                    "{log_filename} ".format(
                        command=command,
                        log_filename=log_filename,
                        time_filename=time_filename
                    )

            make_rule = "{targets}: " \
                "{import_sources}\n\t" \
                "{env}{command}" \
                .format(
                    command=command,
                    targets=" ".join(targets),
                    import_sources=import_sources,
                    env=env
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
