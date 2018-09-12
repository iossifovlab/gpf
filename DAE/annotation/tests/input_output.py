import os

DATA_DIR = './data/dir'

OUTPUT_DIR = './output/dir'

CONFIG = 'config.conf'

DIRS = [OUTPUT_DIR, OUTPUT_DIR + '/cccc', OUTPUT_DIR + '/cccc/DENOVO_STUDY',
        OUTPUT_DIR + '/cccc/OTHER_STUDY',
        OUTPUT_DIR + '/cccc/TRANSMITTED_STUDY', OUTPUT_DIR + '/log']

DENOVO_FILES = ['/cccc/DENOVO_STUDY/data_annotated.tsv']
TRANSMITTED_FILES =\
    ['/cccc/TRANSMITTED_STUDY/TRANSMITTED_STUDY.format-annot.txt.bgz']

JOB_SUFIX = '-part-{chr:0>2}-{pos}'

DENOVO_INPUT_FILES = map(lambda df: DATA_DIR + df, DENOVO_FILES)
DENOVO_OUTPUT_FILES = map(lambda df: OUTPUT_DIR + df, DENOVO_FILES)

TRANSMITTED_INPUT_FILES = map(lambda tf: DATA_DIR + tf, TRANSMITTED_FILES)
TRANSMITTED_OUTPUT_FILES = map(lambda tf: OUTPUT_DIR + tf, TRANSMITTED_FILES)

SGE_RREQ = 'sge_rreq'

DENOVO_ARGS = '--config {}'.format(CONFIG)
TRANSMITTED_ARGS = DENOVO_ARGS + ' --options=direct:False -c chr -p position '\
                                 '--region={chr}:{begin_pos}-{end_pos}'
DENOVO_ARGS += ' --options=direct:True'

CHROMOSOMES = map(lambda x: str(x), range(1, 23)) + ['X', 'Y']
CHROMOSOMES_LABELS = {'X': '23', 'Y': '24'}

CMD_FORMAT = ('{target}: {output_dir}\n\t(SGE_RREQ="{sge_rreq}" time'
              ' annotation_pipeline.py {args}'
              ' "{input_file}" "$@"'
              ' 2> "{log_prefix}-err{job_sufix}.txt") 2> '
              '"{log_prefix}-time{job_sufix}.txt"\n')

DENOVO = ''.join([
    CMD_FORMAT
    .format(target=output_file, sge_rreq=SGE_RREQ, input_file=input_file,
            output_dir=OUTPUT_DIR, args=DENOVO_ARGS, job_sufix='',
            log_prefix=DIRS[-1] + '/' + os.path.basename(input_file))
    for input_file, output_file in zip(DENOVO_INPUT_FILES, DENOVO_OUTPUT_FILES)
])

TEMP_FILES = map(
    lambda tf: ' '.join([' '.join(
        [(tf + JOB_SUFIX).format(chr=CHROMOSOMES_LABELS.get(chrom, chrom),
                                 pos=i).replace('.bgz', '')
         for i in range(0, 5)]) for chrom in CHROMOSOMES]),
    TRANSMITTED_OUTPUT_FILES)

TRANSMITTED = ''.join([''.join([''.join([
    CMD_FORMAT
    .format(target=(output_file + JOB_SUFIX).format(
        chr=CHROMOSOMES_LABELS.get(chrom, chrom), pos=i).replace('.bgz', ''),
        sge_rreq=SGE_RREQ, input_file=input_file, output_dir=OUTPUT_DIR,
        args=TRANSMITTED_ARGS.format(chr=chrom, begin_pos=i * 50000000,
                                     end_pos=(i + 1) * 50000000 - 1),
        log_prefix=DIRS[-1] + '/' + os.path.basename(input_file),
        job_sufix=JOB_SUFIX.format(
            chr=CHROMOSOMES_LABELS.get(chrom, chrom), pos=i)) + '\n'
    for i in range(0, 5)]) for chrom in CHROMOSOMES]) +
    '{target}: {parts}\n\tSGE_RREQ="{sge_rreq}" merge.sh "$@"\n\n'.format(
        target=output_file.replace('.bgz', ''), sge_rreq=SGE_RREQ,
        parts=temp_files) +
    '{bgz_target}: {merge_target}\n\tSGE_RREQ="{sge_rreq}" bgzip "$<" && '
    'mv "$<.gz" "$@" && tabix -b 2 -e 2 -S 1 "$@"\n'.format(
        bgz_target=output_file,
        merge_target=output_file.replace('.bgz', ''), sge_rreq=SGE_RREQ)
    for input_file, output_file, temp_files in zip(TRANSMITTED_INPUT_FILES,
                                                   TRANSMITTED_OUTPUT_FILES,
                                                   TEMP_FILES)])

MAKEFILE_OUTPUT = """SHELL=/bin/bash -o pipefail
.DELETE_ON_ERROR:\n
all:\n
{output_dir}:\n\tmkdir {subdir_list}\n
{denovo}
{transmitted}
all: {denovo_output} {transmitted_output}
""".format(output_dir=OUTPUT_DIR, subdir_list=' '.join(DIRS), denovo=DENOVO,
           transmitted=TRANSMITTED,
           denovo_output=' '.join(DENOVO_OUTPUT_FILES),
           transmitted_output=' '.join(TRANSMITTED_OUTPUT_FILES))
