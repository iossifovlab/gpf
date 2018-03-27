'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function

import shutil
from variants.configure import Configure
from variants.tests.conftest import relative_to_this_test_folder
import os
from variants.builder import variants_builder as VB
from variants.vcf_utils import mat2str


def test_variants_build_multi(temp_dirname):

    conf = Configure.from_prefix(
        relative_to_this_test_folder("fixtures/trios_multi"))

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, "trios_multi")

    fvars = VB(prefix)
    assert fvars is not None
    conf = Configure.from_prefix(prefix)

    assert os.path.exists(conf.annotation)


def test_variants_builder():
    prefix = relative_to_this_test_folder('fixtures/effects_trio')

    genome_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "chrAll.fa")
    print(genome_file)

    gene_models_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "refGene-201309.gz")
    print(gene_models_file)

    fvars = VB(prefix=prefix, genome_file=genome_file,
               gene_models_file=gene_models_file)

    vs = fvars.query_variants()

    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), sep='\t')
        for aa in v.falt_alleles:
            print(v.effect[aa].worst, v.effect[aa].gene)
            print(v['all.nAltAlls'][aa], v['all.altFreq'][aa])
