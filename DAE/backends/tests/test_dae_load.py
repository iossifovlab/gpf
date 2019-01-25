'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import, unicode_literals

import os

import numpy as np
from utils.vcf_utils import str2mat, best2gt, GENOTYPE_TYPE, mat2str

from ..configure import Configure

from ..thrift.parquet_io import VariantsParquetWriter
from ..thrift.raw_dae import RawDAE, BaseDAE


def test_dae_full_variants_iterator(raw_dae, temp_dirname):
    dae = raw_dae("fixtures/transmission")
    dae.load_families()

    assert dae is not None

    for sv, fvs in dae.full_variants_iterator():
        print(sv, fvs)

    conf = Configure.from_prefix_parquet(temp_dirname).parquet
    variants_writer = VariantsParquetWriter(dae.full_variants_iterator())
    variants_writer.save_variants_to_parquet(
        summary_filename=conf.summary_variant,
        family_filename=conf.family_variant,
        effect_gene_filename=conf.effect_gene_variant,
        member_filename=conf.member_variant,
        batch_size=2
    )

    assert os.path.exists(conf.summary_variant)
    assert os.path.exists(conf.family_variant)


def test_explode_family_genotype():
    fgt = RawDAE.explode_family_genotypes(
        'f3:2121/0101:11 27 34 13/0 26 0 15/0 0 0 0')
    print(fgt)


def test_str2mat():
    res = str2mat("2121/0101")
    assert res.dtype == GENOTYPE_TYPE
    assert np.all(res == np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8))


def test_best2gt():
    best = np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[0, 1, 0, 1], [0, 0, 0, 0]], dtype=np.int8))

    best = np.array([[0, 1, 0, 1], [2, 1, 2, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[1, 1, 1, 1], [1, 0, 1, 0]], dtype=np.int8))


def test_load_denovo(raw_denovo):
    denovo = raw_denovo("fixtures/denovo")
    denovo.load_families()

    assert denovo is not None
    assert denovo.families is not None

    df = denovo.load_denovo_variants()
    assert df is not None
    print(df.head())

    vs = denovo.full_variants_iterator()
    for sv, fvs in vs:
        for v in fvs:
            print(v, mat2str(v.best_st))


def test_load_denovo_families(raw_denovo):
    denovo = raw_denovo("fixtures/denovo")

    denovo.load_families()
    assert denovo.families is not None


def test_gene_effects_split():
    gene_effects = \
        "MIB2:missense|MIB2:intron|MIB2:non-coding|MIB2:5'UTR-intron"
    genes, effects = BaseDAE.split_gene_effects(gene_effects)
    print(genes, effects)
    assert genes == [u'MIB2', u'MIB2', u'MIB2', u'MIB2']
    assert effects == [u'missense', u'intron', u'non-coding', u"5'UTR-intron"]
