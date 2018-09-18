#!/usr/bin/env python

import os
import sys
import ConfigParser


class VariantDBConf(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        variant_db_conf = ConfigParser.SafeConfigParser({
            'wd': data_dir,
            'data': data_dir
        })
        variant_db_conf.read(data_dir + '/variantDB.conf')
        self.denovo_files = []
        self.transm_files = []
        for section in variant_db_conf.sections():
            if section.startswith('study.'):
                if variant_db_conf.has_option(section, 'study.type'):
                    study_types = variant_db_conf.get(section, 'study.type')
                    if 'CNV' in study_types:
                        # SKIP CNV studies
                        continue
                if variant_db_conf.has_option(section, 'denovoCalls.files'):
                    self.denovo_files.extend(
                        variant_db_conf.get(
                            section, 'denovoCalls.files').split('\n'))
                if variant_db_conf.has_option(section,
                                              'transmittedVariants.indexFile'):
                    self.transm_files.extend([
                        index_file + '.txt.bgz'
                        for index_file in variant_db_conf.get(
                            section,
                            'transmittedVariants.indexFile').split('\n')
                    ])
        self._validate()

    def _validate(self):
        outside_files = [
            filename for filename in self.all_variant_files
            if self.data_dir not in filename]
        if len(outside_files) != 0:
            sys.stderr.write(
                '[ERROR] Some configured variant files are '
                'outside of the data directory:\n{}\n'.format(
                    '\n'.join(outside_files)))
            sys.exit(1)

    @property
    def all_variant_files(self):
        return self.denovo_files + self.transm_files


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

    variant_db_conf = VariantDBConf(data_dir)
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

    denovo_args = '--config {}'.format(config)

    transm_args_format = denovo_args +\
        ' --options=direct:False -c chr -p position' \
        ' --region={chr}:{begin_pos}-{end_pos}'

    denovo_args += ' --options=direct:True'

    for filename in variant_db_conf.denovo_files:
        all_cmds.append(escape_target(to_destination(filename)))
        print(cmd_format.format(
            target=all_cmds[-1], sge_rreq=sge_rreq,
            input_file=filename, output_dir=output_dir,
            args=denovo_args, job_sufix='',
            log_prefix=log_dir + '/' + os.path.basename(filename)))

    chromosomes = map(lambda x: str(x), range(1, 23)) + ['X', 'Y']
    chr_labels = {'X': '23', 'Y': '24'}
    for filename in variant_db_conf.transm_files:
        output_file = to_destination(filename).replace('.bgz', '')
        file_cmds = []
        for chromosome in chromosomes:
            for i in range(0, 5):
                job_sufix = '-part-{chr:0>2}-{pos}'.format(
                    chr=chr_labels.get(chromosome, chromosome), pos=i)
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
              'SGE_RREQ="{sge_rreq}" bgzip "$<" && mv "$<.gz"'
              ' "$@" && tabix -b 2 -e 2 -S 1 "$@"\n'.format(
                  bgz_target=all_cmds[-1], merge_target=escaped_output_file,
                  sge_rreq=sge_rreq))

    print(" ".join(["all:"] + all_cmds))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
