#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import pysam

from collections import OrderedDict
from configparser import ConfigParser
from box import Box

import common.config


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
                denovo_files.append(filename.strip())
        return denovo_files

    @classmethod
    def _collect_transmitted_calls(cls, study):

        transmitted_calls = study.transmittedvariants
        if not transmitted_calls:
            return []

        if 'indexfile' not in transmitted_calls:
            return []

        filename = "{}.txt.bgz".format(transmitted_calls.indexfile)
        # assert os.path.exists(filename)
        return [filename]

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
            filename for filename in self.all_variant_files
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


def main(config, data_dir, output_dir, sge_rreq):
    def to_destination(path):
        return path.replace(data_dir, output_dir)

    print('SHELL=/bin/bash -o pipefail')
    print('.DELETE_ON_ERROR:\n')
    print('all:\n')

    output_dir = os.path.abspath(output_dir)
    data_dir = os.path.abspath(data_dir)

    all_cmds = []

    variant_db_conf = VariantDBConfig(data_dir)
    all_input_files = variant_db_conf.all_variant_files

    dirs = [to_destination(data_dir)]
    copy_files = []
    for dirpath, _dirnames, filenames in os.walk(data_dir + "/cccc"):
        dirs.append(to_destination(dirpath))
        copy_files.extend([
            dirpath + '/' + filename
            for filename in filenames
            if dirpath + '/' + filename not in all_input_files])

    log_dir = output_dir + '/log'
    dirs.append(log_dir)
    print('{output_dir}:\n\tmkdir -p {subdir_list}\n'.format(
        output_dir=output_dir, subdir_list=' '.join(dirs)))

    cmd_format = (
        '{target}: {output_dir}\n\t(SGE_RREQ="{sge_rreq}" time'
        ' annotation_pipeline.py {args}'
        ' "{input_file}" "$@"'
        ' 2> "{log_prefix}-err{job_sufix}.txt")'
        ' 2> "{log_prefix}-time{job_sufix}.txt"\n')

    common_args = '--config {}'.format(config)

    transm_args_format = common_args +\
        ' -c chr -p position' \
        ' --region={chr}:{begin_pos}-{end_pos}'

    denovo_args = common_args + ' --direct'

    for filename in variant_db_conf.denovo_files:
        all_cmds.append(escape_target(to_destination(filename)))
        print(cmd_format.format(
            target=all_cmds[-1], sge_rreq=sge_rreq,
            input_file=filename, output_dir=output_dir,
            args=denovo_args, job_sufix='',
            log_prefix=log_dir + '/' + os.path.basename(filename)))

    for filename in variant_db_conf.transmitted_files:
        output_file = to_destination(filename).replace('.bgz', '')
        tf = pysam.TabixFile(filename)
        contigs = tf.contigs
        tf.close()

        file_cmds = []
        for index, chromosome in enumerate(contigs):
            for i in range(0, 5):
                job_sufix = '-part-{chr_index:0>3}-{pos}-{chromosome}'.format(
                    chr_index=index, pos=i, chromosome=chromosome)
                file_cmds.append(escape_target(output_file + job_sufix))
                print(cmd_format.format(
                    target=file_cmds[-1],
                    sge_rreq=sge_rreq,
                    input_file=filename,
                    output_dir=output_dir,
                    args=transm_args_format.format(
                        chr=chromosome,
                        begin_pos=i * 50000000,
                        end_pos=(i + 1) * 50000000 - 1),
                    log_prefix=log_dir + '/' + os.path.basename(filename),
                    job_sufix=job_sufix))

        escaped_output_file = escape_target(output_file)
        print('{target}: {parts}\n\tSGE_RREQ="{sge_rreq}"'
              ' merge.sh "$@"\n'.format(
                  target=escaped_output_file, sge_rreq=sge_rreq,
                  parts=' '.join(file_cmds)))

        all_cmds.append(escaped_output_file + '.bgz')
        print('{bgz_target}: {merge_target}\n\t'
              'SGE_RREQ="{sge_rreq}" bgzip -c "$<" > "$@" && '
              'tabix -S 1 -s 1 -b 2 -e 2 "$@"\n'.format(
                  bgz_target=all_cmds[-1], merge_target=escaped_output_file,
                  sge_rreq=sge_rreq))

    print(" ".join(["all:"] + all_cmds))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
