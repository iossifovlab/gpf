'''
Created on Mar 19, 2018

@author: lubo
'''
import shutil
import os

from ..configure import Configure

from ..vcf.builder import variants_builder as VB

import sys


def test_variants_build_multi(temp_dirname, fixture_dirname):

    conf = Configure.from_prefix_vcf(
        fixture_dirname("backends/trios_multi"))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, "trios_multi")

    fvars = VB(prefix)
    assert fvars is not None
    conf = Configure.from_prefix_vcf(prefix)
    conf = conf.vcf

    assert os.path.exists(conf.annotation)


def test_variants_builder(temp_dirname, fixture_dirname):
    conf = Configure.from_prefix_vcf(
        fixture_dirname("backends/effects_trio"))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, "effects_trio")

    genome_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "chrAll.fa")
    print(genome_file, file=sys.stderr)

    gene_models_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "refGene-201309.gz")
    print(gene_models_file, file=sys.stderr)

    fvars = VB(prefix=prefix, genome_file=genome_file,
               gene_models_file=gene_models_file)

    vs = fvars.query_variants()
    assert vs is not None


def test_variants_build_twice(temp_dirname, fixture_dirname):

    conf = Configure.from_prefix_vcf(
        fixture_dirname("backends/trios_multi"))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, "trios_multi")

    fvars = VB(prefix)
    assert fvars is not None
    conf = Configure.from_prefix_vcf(prefix)
    conf = conf.vcf

    assert os.path.exists(conf.annotation)

    fvars = VB(prefix,
               genome_file="ala_bala.txt", gene_models_file="ala_bala.txt")

    assert fvars is not None
