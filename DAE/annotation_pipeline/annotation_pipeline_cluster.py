#!/usr/bin/env python
from builtins import str
from builtins import range
from subprocess import call

QUEUES='all.q@wigclust1.cshl.edu,all.q@wigclust10.cshl.edu,all.q@wigclust11.cshl.edu,all.q@wigclust12.cshl.edu,all.q@wigclust13.cshl.edu,all.q@wigclust14.cshl.edu,all.q@wigclust15.cshl.edu,all.q@wigclust16.cshl.edu,all.q@wigclust17.cshl.edu,all.q@wigclust18.cshl.edu,all.q@wigclust19.cshl.edu,all.q@wigclust2.cshl.edu,all.q@wigclust20.cshl.edu,all.q@wigclust21.cshl.edu,all.q@wigclust22.cshl.edu,all.q@wigclust23.cshl.edu,all.q@wigclust24.cshl.edu,all.q@wigclust3.cshl.edu,all.q@wigclust4.cshl.edu,all.q@wigclust5.cshl.edu,all.q@wigclust6.cshl.edu,all.q@wigclust8.cshl.edu,all.q@wigclust9.cshl.edu'

chromosomes = [str(x) for x in range(1, 23)] + ['X', 'Y']

chr_labels = {'X': '23', 'Y': '24'}


base_dir='/mnt/wigclust22/data/unsafe/gotsev'
output_dir='{}/output'.format(base_dir)
input_file='{}/test-annotation-data/transmissionIndex-HW-DNRM.txt.gz'.format(base_dir)
config_file='{}/sample_annotation_pipeline.conf'.format(base_dir)
for chromosome in chromosomes:
    for position in range(0, 25, 5):
        execute_str = ('qsub -l virtual_free=10G -q {queues} -N "ANNOT-{chr}-{pos}" '
            '-o "{output_dir}/{chr_label:0>2}_{pos:0>2}_o.txt" -e "{output_dir}/{chr_label:0>2}_{pos:0>2}_e.txt" '
            '-v PATH -v DAE_DB_DIR -v DAE_SOURCE_DIR -v dbNSFP_PATH -v PYTHONPATH -b yes '
            'annotation_pipeline.py {input_file} --config {config_file} '
            '--region={chr}:{begin_pos}-{end_pos}').format(
                queues=QUEUES, output_dir=output_dir, input_file=input_file,
                config_file=config_file, chr=chromosome, chr_label=chr_labels.get(chromosome, chromosome),
                pos=position, begin_pos=position * 10000000, end_pos=(position + 5) * 10000000 - 1)
        call(execute_str, shell=True)
