'''
Created on Nov 25, 2016

@author: lubo
'''

from pheno_tool.pheno_common import PhenoFilterSet, PhenoFilterRange
from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role


def test_pheno_filter_set(phdb):
    df = phdb.get_persons_values_df(['pheno_common.race'])
    # assert 11283 == len(df)
    assert 10931 == len(df)

    f = PhenoFilterSet(phdb, 'pheno_common.race', set(['white']))
    res_df = f.apply(df)
    assert all(res_df['pheno_common.race'] == 'white')
    assert 8701 == len(res_df)

    f = PhenoFilterSet(phdb, 'pheno_common.race', set(['asian']))
    res_df = f.apply(df)
    assert all(res_df['pheno_common.race'] == 'asian')
    assert 455 == len(res_df)

    f = PhenoFilterSet(phdb, 'pheno_common.race', set(['white', 'asian']))
    res_df = f.apply(df)
    assert 9156 == len(res_df)


def test_pheno_filter_range(phdb):
    df = phdb.get_persons_values_df(['pheno_common.age_at_assessment'])

    f = PhenoFilterRange(
        phdb, 'pheno_common.age_at_assessment', (200, 220))
    res_df = f.apply(df)
    assert 178 == len(res_df)

    f = PhenoFilterRange(
        phdb, 'pheno_common.age_at_assessment', (200, None))
    res_df = f.apply(df)
    assert 5798 == len(res_df)

    f = PhenoFilterRange(
        phdb, 'pheno_common.age_at_assessment', (None, 200))
    res_df = f.apply(df)
    assert 4785 == len(res_df)

    f = PhenoFilterRange(
        phdb, 'pheno_common.age_at_assessment', (200, 200))
    res_df = f.apply(df)
    assert 10 == len(res_df)

    f = PhenoFilterRange(
        phdb, 'pheno_common.age_at_assessment', (None, None))
    res_df = f.apply(df)
    assert (5798 + 4785 - 10) == len(res_df)


def test_categorical_measure_filter(phdb, filter_builder):
    df = phdb.get_persons_values_df(['pheno_common.race'])

    f = filter_builder.make_filter(
        'pheno_common.race', set(['white', 'asian']))
    res_df = f.apply(df)
    assert 9156 == len(res_df)

    f = filter_builder.make_filter(
        'pheno_common.race', set(['white']))
    res_df = f.apply(df)
    assert 8701 == len(res_df)


def test_continuous_measure_filter(phdb, filter_builder):
    df = phdb.get_persons_values_df(['pheno_common.age_at_assessment'])

    f = filter_builder.make_filter(
        'pheno_common.age_at_assessment', (200, 200))

    res_df = f.apply(df)
    assert 10 == len(res_df)


def test_tool_with_filters(phdb, all_ssc_studies):
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
        pheno_filters={
            'pheno_common.race': ['white'],
            'pheno_common.age_at_assessment': (200, 250),
        }
    )
    persons = tool.list_of_subjects()
    assert 84 == len(persons)

    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
        pheno_filters={
            'pheno_common.race': ['white', 'more-than-one-race'],
            'pheno_common.age_at_assessment': (200, 250),
        }
    )
    persons = tool.list_of_subjects()
    assert 93 == len(persons)

    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
        pheno_filters={
            'pheno_common.race': ['more-than-one-race'],
            'pheno_common.age_at_assessment': (200, 250),
        }
    )
    persons = tool.list_of_subjects()
    assert 9 == len(persons)


def test_tool_with_filters_result_phenotype_and_genotype(
        phdb, all_ssc_studies, autism_candidates_genes):
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
        pheno_filters={
            'pheno_common.race': ['white'],
            'pheno_common.age_at_assessment': (200, 250),
        }
    )
    persons = tool.list_of_subjects()
    assert 84 == len(persons)

    res = tool.calc(
        VT(
            effect_types=['nonsynonymous', ],
            gene_syms=autism_candidates_genes,
            present_in_child=[
                'autism only', 'unaffected only', 'autism and unaffected'],
            present_in_parent=[
                'mother only', 'mother and father', 'neither'],
        )
    )

    assert len(res.phenotypes) == 84
