import os
import sys

from collections import OrderedDict
from dae.RegionOperations import Region

from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator

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
        rows=100000,
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

    def recursive_dict_update(input_dict, updater_dict):
        # FIXME !
        # This method cannot handle nested dictionaries
        # that hold a reference to the dictionary that
        # contains them. If such a dictionary is given
        # to this function, it will reach the maximum
        # recursion depth.

        result_dict = dict(input_dict)
        for key, val in updater_dict.items():
            if key in result_dict and type(val) is dict:
                result_dict[key] = recursive_dict_update(
                    result_dict[key], updater_dict[key])
            else:
                result_dict[key] = updater_dict[key]
        return result_dict

    annotation_defaults = recursive_dict_update(annotation_defaults, defaults)

    pipeline = PipelineAnnotator.build(
        options, config_filename, dae_config.dae_data_dir, genomes_db,
        defaults=annotation_defaults)
    return pipeline
