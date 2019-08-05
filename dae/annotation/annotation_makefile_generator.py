#!/usr/bin/env python

import os
import sys
import argparse
import pysam

from collections import OrderedDict
from configparser import ConfigParser
from box import Box

import dae.common.config
import dae.GenomeAccess
from dae.RegionOperations import Region


class VariantDBConfig(object):

    @classmethod
    def _parse_variants_db_config(cls, data_dir):
        config_parser = ConfigParser({
            'wd': data_dir,
            'data': data_dir
        })
        filename = os.path.join(data_dir, "variantDB.conf")

        config = OrderedDict()

        with open(filename, "r", encoding="utf8") as infile:
            config_parser.read_file(infile)
            for section in config_parser.sections():
                if section.startswith('study.'):
                    study = common.config._section_tree(
                        section, config_parser)
                    config[section] = study
        return config

    @classmethod
    def _collect_denovo_calls(cls, study):
        denovo_files = []

        denovo_calls = study.denovocalls
        if not denovo_calls:
            return []

        for key, data in denovo_calls.items():
            file_list = None
            if key == 'files':
                file_list = data
            else:
                if 'files' in data:
                    file_list = data['files']
            if not file_list:
                continue
            for filename in file_list.split("\n"):
                denovo_files.append(os.path.abspath(filename.strip()))
        return [(study, fname) for fname in list(set(denovo_files))]

    @classmethod
    def _collect_transmitted_calls(cls, study):

        transmitted_calls = study.transmittedvariants
        if not transmitted_calls:
            return []

        if 'indexfile' not in transmitted_calls:
            return []

        filename = "{}.txt.bgz".format(transmitted_calls.indexfile)
        # assert os.path.exists(filename)
        return [(study, os.path.abspath(filename))]

    @classmethod
    def _collect_studies(cls, config):
        denovo_files = []
        transmitted_files = []

        for study_name, study_config in config.items():
            if not study_name.startswith("study."):
                continue
            study = Box(study_config, default_box=True, default_box_attr=None)

            if 'CNV' in study.study.type:
                continue
            name = study_name.split('.')[1]
            study.name = name.replace(' ', '_')
            denovo_files.extend(cls._collect_denovo_calls(study))
            transmitted_files.extend(cls._collect_transmitted_calls(study))

        return denovo_files, transmitted_files

    def __init__(self, data_dir):
        self.data_dir = data_dir

        config = VariantDBConfig._parse_variants_db_config(data_dir)

        self.denovo_files, self.transmitted_files = \
            VariantDBConfig._collect_studies(config)

        self._validate()

    def _validate(self):
        outside_files = [
            filename for _, filename in self.all_variant_files
            if self.data_dir not in filename]
        if len(outside_files) != 0:
            print(
                '[ERROR] Some configured variant files are'
                'outside of the data directory:\n{}\n'.format(
                    '\n'.join(outside_files)), file=sys.stderr)
            sys.exit(1)

    @property
    def all_variant_files(self):
        return self.denovo_files + self.transmitted_files


def escape_target(target):
    return target.replace(' ', '__')


class MakefileBuilder(VariantDBConfig):
    TRANSMITTED_STEP = 50000000

    def __init__(
            self, annotation_config, data_dir, output_dir,
            sge_rreq, genome_file):
        super(MakefileBuilder, self).__init__(os.path.abspath(data_dir))
        self.annotation_config = annotation_config
        self.output_dir = os.path.abspath(output_dir)
        self.log_dir = os.path.join(output_dir, 'log')

        self.sge_rreq = sge_rreq

        self.genome_file = genome_file
        assert os.path.exists(self.genome_file)

        genome = GenomeAccess.openRef(self.genome_file)
        self.genome = genome
        assert self.genome is not None

        self.makefile = []
        self.all_targets = []

        self.build_contig_regions()

    def build_contig_regions(self):
        self.contigs = OrderedDict(self.genome.get_all_chr_lengths())
        self.contig_parts = OrderedDict([
            (contig, int(size / self.TRANSMITTED_STEP + 1))
            for contig, size in self.contigs.items()
        ])
        self.contig_regions = OrderedDict()
        for contig, size in self.contigs.items():
            regions = []
            total_parts = self.contig_parts[contig]
            step = int(size / total_parts + 1)
            for index in range(total_parts):
                begin_pos = index * step
                end_pos = (index + 1) * step - 1
                if index + 1 == total_parts:
                    end_pos = size
                region = Region(contig, begin_pos, end_pos)
                regions.append(region)
            self.contig_regions[contig] = regions

    def to_destination(self, path):
        return path.replace(self.data_dir, self.output_dir)

    def escape_target(self, target):
        return target.replace(' ', '__')

    def build_directory_structure(self, variant_files=None):
        directories = [self.to_destination(self.data_dir)]
        directories.append(os.path.join(self.output_dir, 'log'))

        if variant_files is None:
            variant_files = set([
                os.path.abspath(name) for _, name in self.all_variant_files])
        for dirpath, _dirnames, filenames in os.walk(self.data_dir):
            check = any([
                os.path.join(dirpath, name) in variant_files
                for name in filenames
            ])
            if check:
                target_dir = self.to_destination(dirpath)
                directories.append(target_dir)
                command = '{target_dir}:\n\tmkdir -p {target_dir}\n'.format(
                        target_dir=target_dir)
                self.makefile.append(command)

        command = '{output_dir}: {subdir_list}\n'.format(
                output_dir=self.output_dir, subdir_list=' '.join(directories)
        )
        self.makefile.append(command)

    COMMAND = (
        '{target}: {output_dir} {input_file}\n\t(SGE_RREQ="{sge_rreq}" time'
        ' annotation_pipeline.py --notabix {args}'
        ' "{input_file}" "$@"'
        ' 2> "{log_prefix}-err{job_sufix}.txt")'
        ' 2> "{log_prefix}-time{job_sufix}.txt"\n')

    def build_denovo_files(self):
        args = '--mode=replace --config {} --direct --Graw {}'.format(
            self.annotation_config,
            self.genome_file)

        for study, filename in self.denovo_files:
            target = self.escape_target(self.to_destination(filename))
            logfile_prefix = "{}-{}".format(
                study.name, os.path.basename(filename))
            command = self.COMMAND.format(
                target=target,
                sge_rreq=self.sge_rreq,
                input_file=filename,
                output_dir=self.output_dir,
                args=args,
                job_sufix='',
                log_prefix=os.path.join(
                    self.log_dir, logfile_prefix)
            )
            self.makefile.append(command)
            self.all_targets.append(target)

    def transmitted_file_contigs(self, source_filename):
        tf = pysam.TabixFile(source_filename)
        contigs = tf.contigs
        tf.close()
        if 'chr' in contigs:
            contigs = [c for c in contigs if c != 'chr']
        return contigs

    def build_transmitted_file_parts(
            self, study, source_filename, output_basename):
        parts = []
        contigs = self.transmitted_file_contigs(source_filename)

        for contig_index, contig in enumerate(contigs):
            assert contig in self.contigs, contig
            for region_index, region in enumerate(self.contig_regions[contig]):
                part_sufix = \
                    '-part-{contig_index:0>3}-{region_index}-{contig}'.format(
                        contig_index=contig_index,
                        region_index=region_index,
                        contig=contig)
                target = self.escape_target(output_basename + part_sufix)
                args = '--mode=replace --config {config} --sequential ' \
                    '-c chr -p position' \
                    ' --Graw {genome_file}' \
                    ' --region={chr}:{begin_pos}-{end_pos}'.format(
                        config=self.annotation_config,
                        genome_file=self.genome_file,
                        chr=contig,
                        begin_pos=region.start,
                        end_pos=region.end,
                    )
                logfile_prefix = "{}-{}".format(
                    study.name, os.path.basename(source_filename))

                command = self.COMMAND.format(
                    target=target,
                    sge_rreq=self.sge_rreq,
                    input_file=source_filename,
                    output_dir=self.output_dir,
                    args=args,
                    log_prefix=os.path.join(
                        self.log_dir, logfile_prefix),
                    job_sufix=part_sufix)
                self.makefile.append(command)
                parts.append(target)
        return parts

    def build_transmitted_file(self, study, source_filename):
        output_basename = self.to_destination(
            source_filename).replace('.bgz', '')

        parts = self.build_transmitted_file_parts(
            study, source_filename, output_basename)

        escaped_output_file = escape_target(output_basename)
        command = '{target}: {parts}\n\tSGE_RREQ="{sge_rreq}"' \
            ' merge.sh $? > "$@"\n'.format(
                target=escaped_output_file,
                sge_rreq=self.sge_rreq,
                parts=' '.join(parts))
        self.makefile.append(command)

        target = escaped_output_file + '.bgz'
        command = '{bgz_target}: {merge_target}\n\t' \
            'SGE_RREQ="{sge_rreq}" bgzip -c "$<" > "$@" && ' \
            'tabix -S 1 -s 1 -b 2 -e 2 "$@"\n'.format(
                bgz_target=target,
                merge_target=escaped_output_file,
                sge_rreq=self.sge_rreq)
        self.all_targets.append(target)
        self.makefile.append(command)

    def build_transmitted_files(self):
        for study, filename in self.transmitted_files:
            self.build_transmitted_file(study, filename)

    def build(self, outfile=sys.stdout):

        self.build_directory_structure()
        self.build_denovo_files()
        self.build_transmitted_files()

        print('SHELL=/bin/bash -o pipefail', file=outfile)
        print('.DELETE_ON_ERROR:\n', file=outfile)
        print(" ".join(["all:"] + self.all_targets), file=outfile)
        print('\n', file=outfile)

        for ln in self.makefile:
            print(ln, file=outfile)
            print('\n', file=outfile)

    @staticmethod
    def main(argv):
        parser = argparse.ArgumentParser(
            description="generates a makefile to reannotate GPF instance data",
            conflict_handler='resolve')

        parser.add_argument(
            'data_dir',
            nargs=1,
            action='store',
            help="path to the instance data directory"
        )
        parser.add_argument(
            'output_dir',
            nargs=1,
            action='store',
            help="path to the ouput data directory"
        )

        parser.add_argument(
            '--annotation-config',
            required=True, action='store',
            help='config file location')

        parser.add_argument(
            '--sge-options',
            action='store',
            default='',
            help="options to pass to SGE"
        )

        parser.add_argument(
            '--Graw',
            dest='genome_file',
            required=True,
            action='store',
            help='reference genome file location',
        )

        parser.add_argument(
            '-m', '--makefile',
            dest='makefile',
            action='store',
            default=None,
            help='output file name where to sore the generated makefile'
        )

        options = parser.parse_args(argv)
        assert options.annotation_config is not None
        assert os.path.exists(options.annotation_config), \
            options.annotation_config

        assert options.genome_file is not None
        assert os.path.exists(options.genome_file)

        assert len(options.data_dir) == 1
        assert len(options.output_dir) == 1
        data_dir = options.data_dir[0]
        output_dir = options.output_dir[0]

        builder = MakefileBuilder(
            os.path.abspath(options.annotation_config),
            os.path.abspath(data_dir),
            os.path.abspath(output_dir),
            options.sge_options,
            options.genome_file)

        if options.makefile is None:
            builder.build(sys.stdout)
        else:
            with open(options.makefile, "w") as outfile:
                builder.build(outfile)


if __name__ == '__main__':
    MakefileBuilder.main(sys.argv[1:])
