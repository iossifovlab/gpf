import os

from ..configure import Configure


def test_configure_prefix_dirname_parquet(temp_dirname):
    conf = Configure.from_prefix_parquet(temp_dirname)
    assert conf is not None
    print(conf)

    assert 'parquet' in conf
    parquet = conf.parquet

    assert 'summary_variant' in parquet
    assert not os.path.exists(parquet.summary_variant)
    assert temp_dirname in parquet.summary_variant
    assert temp_dirname == os.path.dirname(parquet.summary_variant)

    assert 'family_variant' in parquet
    assert not os.path.exists(parquet.family_variant)
    assert temp_dirname in parquet.family_variant
    assert temp_dirname == os.path.dirname(parquet.family_variant)

    assert 'effect_gene_variant' in parquet
    assert not os.path.exists(parquet.effect_gene_variant)
    assert temp_dirname in parquet.effect_gene_variant
    assert temp_dirname == os.path.dirname(parquet.effect_gene_variant)

    assert 'member_variant' in parquet
    assert not os.path.exists(parquet.member_variant)
    assert temp_dirname in parquet.member_variant
    assert temp_dirname == os.path.dirname(parquet.member_variant)


def test_configure_prefix_dirname_plus_fileprefix_parquet(temp_dirname):
    conf = Configure.from_prefix_parquet(
        os.path.join(temp_dirname, "test_"))

    assert conf is not None
    print(conf)

    assert 'parquet' in conf
    parquet = conf.parquet

    assert 'summary_variant' in parquet
    assert not os.path.exists(parquet.summary_variant)
    assert 'test_' in parquet.summary_variant
    assert temp_dirname in parquet.summary_variant

    assert 'family_variant' in parquet
    assert not os.path.exists(parquet.family_variant)
    assert 'test_' in parquet.family_variant
    assert temp_dirname in parquet.family_variant

    assert 'effect_gene_variant' in parquet
    assert not os.path.exists(parquet.effect_gene_variant)
    assert 'test_' in parquet.effect_gene_variant
    assert temp_dirname in parquet.effect_gene_variant

    assert 'member_variant' in parquet
    assert not os.path.exists(parquet.member_variant)
    assert 'test_' in parquet.member_variant
    assert temp_dirname in parquet.member_variant

