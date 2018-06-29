#!/usr/bin/env python

import os, sys
import time
import ConfigParser

class VariantDBConf(object):

    def __init__(self, data_dir):
        variant_db_conf = ConfigParser.SafeConfigParser({
            'wd': data_dir,
            'data': data_dir
        })
        variant_db_conf.read(data_dir + '/variantDB.conf')
        self.denovo_files = []
        self.transm_files = []
        for section in variant_db_conf.sections():
            if section.startswith('study.'):
                if variant_db_conf.has_option(section, 'denovoCalls.files'):
                    self.denovo_files.extend(
                        variant_db_conf.get(section, 'denovoCalls.files').split('\n'))
                if variant_db_conf.has_option(section,
                        'transmittedVariants.indexFile'):
                    self.transm_files.extend([
                        index_file + '.txt.bgz'
                        for index_file in variant_db_conf.get(section,
                            'transmittedVariants.indexFile').split('\n')
                    ])

    @property
    def all_variant_files(self):
        return self.denovo_files + self.transm_files

def escape_target(target):
    return target.replace(' ', '__')

def main(config, data_dir, output_dir):
    def to_destination(path):
        return path.replace(data_dir, output_dir)

    print('SHELL=/bin/bash -o pipefail')
    print('.DELETE_ON_ERROR:\n')
    print('all:\n')

    if output_dir[-1] == '/':
        output_dir = output_dir[0:-1]
    if data_dir[-1] == '/':
        data_dir = data_dir[0:-1]

    dirs = []
    all_cmds = []

    variant_db_conf = VariantDBConf(data_dir)
    all_input_files = variant_db_conf.all_variant_files
    copy_files = []
    for dirpath, dirnames, filenames in os.walk(data_dir):
        dirs.append(to_destination(dirpath))
        copy_files.extend([dirpath + '/' + file
            for file in filenames
            if dirpath + '/' + file not in all_input_files])

    log_dir = output_dir + '/log'
    dirs.append(log_dir)
    print('dirs:\n\tmkdir {}\n'.format(' '.join(dirs)))

    cmd_format = ('{target}: dirs\n\t(time'
        ' annotation_pipeline.py {args}'
        ' "{input_file}" "{output_file}{job_sufix}"'
        ' 2> "{log_prefix}-err{job_sufix}.txt") 2> "{log_prefix}-time{job_sufix}.txt"\n')

    denovo_args = '--config {}'.format(config)

    for file in variant_db_conf.denovo_files:
        output_file = to_destination(file)
        all_cmds.append(escape_target(output_file))
        print(cmd_format.format(target=all_cmds[-1],
            input_file=file,
            output_file=output_file,
            args=denovo_args, job_sufix='',
            log_prefix=log_dir + '/' + os.path.basename(file)))

    transm_args_format = denovo_args + \
        ' -c chr -p position --region={chr}:{begin_pos}-{end_pos}'

    chromosomes = map(lambda x: str(x), range(1, 23)) + ['X', 'Y']
    chr_labels = {'X': '23', 'Y': '24'}
    for file in variant_db_conf.transm_files:
        output_file=to_destination(file).replace('.bgz', '')
        file_cmds = []
        for chromosome in chromosomes:
            for i in range(0, 5):
                job_sufix = '-part-{chr:0>2}-{pos}'.format(chr=chr_labels.get(chromosome, chromosome), pos=i)
                file_cmds.append(escape_target(output_file + job_sufix))
                print(cmd_format.format(target=file_cmds[-1],
                    input_file=file,
                    output_file=output_file,
                    args=transm_args_format.format(
                        chr=chromosome,
                        begin_pos=i*50000000, end_pos=(i+1)*50000000-1),
                    log_prefix=log_dir + '/' + os.path.basename(file),
                    job_sufix=job_sufix))

        escaped_output_file = escape_target(output_file)
        print('{target}: {parts}\n\tmerge.sh "{merged}"\n'.format(
            target=escaped_output_file,
            merged=output_file,
            parts=' '.join(file_cmds)))

        all_cmds.append(escaped_output_file + '.bgz')
        print('{bgz_target}: {merge_target}\n\t'
            'bgzip "{output_file}" && '
            'mv "{output_file}.gz" "{output_file}.bgz"\n'.format(
                bgz_target=all_cmds[-1], merge_target=escaped_output_file,
                output_file=output_file))

    copy_cmd_format = '{target}: dirs\n\tcp "{file}" "{dest}"\n'
    for file in copy_files:
        dest = to_destination(file)
        all_cmds.append(escape_target(dest))
        print(copy_cmd_format.format(target=all_cmds[-1],
            file=file, dest=dest,
            log_prefix=log_dir + '/' + os.path.basename(file)))

    print(" ".join(["all:"] + all_cmds))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])