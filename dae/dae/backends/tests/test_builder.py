import os
import shutil

from ..configure import Configure

from ..vcf.builder import variants_builder


def test_variants_build_multi(temp_dirname, fixture_dirname, genomes_db):

    conf = Configure.from_prefix_vcf(
        fixture_dirname('backends/trios_multi'))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, 'trios_multi')

    fvars = variants_builder(prefix, genomes_db)
    assert fvars is not None
    conf = Configure.from_prefix_vcf(prefix)
    conf = conf.vcf

    assert os.path.exists(conf.annotation)


def test_variants_builder(temp_dirname, fixture_dirname, genomes_db):
    conf = Configure.from_prefix_vcf(
        fixture_dirname('backends/effects_trio'))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, 'effects_trio')

    fvars = variants_builder(prefix, genomes_db)

    vs = fvars.query_variants()
    assert vs is not None


def test_variants_build_twice(temp_dirname, fixture_dirname, genomes_db):

    conf = Configure.from_prefix_vcf(
        fixture_dirname('backends/trios_multi'))
    conf = conf.vcf

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, 'trios_multi')

    fvars = variants_builder(prefix, genomes_db)
    assert fvars is not None
    conf = Configure.from_prefix_vcf(prefix)
    conf = conf.vcf

    assert os.path.exists(conf.annotation)
