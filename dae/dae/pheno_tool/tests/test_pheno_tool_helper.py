import pytest
from box import Box
from dae.pheno_tool.tool import PhenoToolHelper
from dae.variants.attributes import Role
from collections import Counter


def mock_allele(effect, in_members):
    return {
        'effects': {
            'types': {effect}
        },
        'variant_in_members': in_members
    }


def mocked_query_variants(**kwargs):
    variants = [{
            'matched_alleles': [
                mock_allele('splice-site', ['fam2.prb', 'fam3.prb']),
                mock_allele('frame-shift', ['fam2.prb']),
                mock_allele('nonsense', ['fam2.prb']),
                mock_allele('no-frame-shift-newStop', ['fam2.prb']),
                mock_allele('missense', ['fam1.prb']),
                mock_allele('synonymous', ['fam1.prb', 'fam3.prb']),
            ]
        },
    ]

    for v in variants:
        yield Box(v)


def mocked_pheno_filter_transform(pheno_filters):
    return None


mocked_study = Box({
    'families': {
        'fam1': {
            'family_id': 'fam1',
            'members_in_order': [
                {'person_id': 'fam1.dad', 'role': Role.dad},
                {'person_id': 'fam1.mom', 'role': Role.mom},
                {'person_id': 'fam1.prb', 'role': Role.prb},
                {'person_id': 'fam1.sib', 'role': Role.sib}
            ]
        },
        'fam2': {
            'family_id': 'fam2',
            'members_in_order': [
                {'person_id': 'fam2.dad', 'role': Role.dad},
                {'person_id': 'fam2.mom', 'role': Role.mom},
                {'person_id': 'fam2.prb', 'role': Role.prb},
                {'person_id': 'fam2.sib', 'role': Role.sib}
            ]
        },
        'fam3': {
            'family_id': 'fam3',
            'members_in_order': [
                {'person_id': 'fam3.dad', 'role': Role.dad},
                {'person_id': 'fam3.mom', 'role': Role.mom},
                {'person_id': 'fam3.prb', 'role': Role.prb},
                {'person_id': 'fam3.sib', 'role': Role.sib}
            ]
        }
    },
    'query_variants': mocked_query_variants,
    '_transform_pheno_filters_to_people_ids': mocked_pheno_filter_transform
})


def test_genotype_data_persons():
    helper = PhenoToolHelper(mocked_study)
    assert helper.genotype_data_persons() == \
        {'fam1.prb', 'fam2.prb', 'fam3.prb'}


def test_genotype_data_persons_family_filters():
    helper = PhenoToolHelper(mocked_study)
    assert helper.genotype_data_persons(family_ids=['fam2']) == {'fam2.prb'}


def test_genotype_data_persons_roles():
    helper = PhenoToolHelper(mocked_study)
    assert helper.genotype_data_persons(roles=[Role.prb, Role.sib]) == \
        {'fam1.prb', 'fam2.prb', 'fam3.prb',
         'fam1.sib', 'fam2.sib', 'fam3.sib'}


def test_genotype_data_persons_invalid_roles():
    helper = PhenoToolHelper(mocked_study)
    with pytest.raises(AssertionError):
        helper.genotype_data_persons(roles=Role.prb)


def test_genotype_data_persons_invalid_family_ids():
    helper = PhenoToolHelper(mocked_study)
    with pytest.raises(AssertionError):
        helper.genotype_data_persons(family_ids='fam1')


def test_pheno_filter_persons(mocker):
    helper = PhenoToolHelper(mocked_study)
    mocker.spy(mocked_study, '_transform_pheno_filters_to_people_ids')
    helper.pheno_filter_persons([1])
    mocked_study._transform_pheno_filters_to_people_ids.\
        assert_called_once_with([1])


def test_pheno_filter_persons_none_or_empty():
    helper = PhenoToolHelper(mocked_study)
    assert helper.pheno_filter_persons(None) is None
    assert helper.pheno_filter_persons(list()) is None


def test_pheno_filter_persons_invalid_input_type():
    helper = PhenoToolHelper(mocked_study)
    with pytest.raises(AssertionError):
        helper.pheno_filter_persons(dict)
    with pytest.raises(AssertionError):
        helper.pheno_filter_persons(tuple)


def test_genotype_data_variants():
    helper = PhenoToolHelper(mocked_study)
    variants = helper.genotype_data_variants(
        {
            'effectTypes': ['Splice-site', 'Frame-shift',
                            'Nonsense', 'No-frame-shift-newStop',
                            'Missense', 'Synonymous']
        }
    )

    assert variants.get('missense') == Counter({'fam1.prb': 1})
    assert variants.get('synonymous') == Counter({'fam1.prb': 1,
                                                  'fam3.prb': 1})
    assert variants.get('splice-site') == Counter({'fam2.prb': 1,
                                                   'fam3.prb': 1})
    assert variants.get('frame-shift') == Counter({'fam2.prb': 1})
    assert variants.get('nonsense') == Counter({'fam2.prb': 1})
    assert variants.get('no-frame-shift-newStop') == Counter({'fam2.prb': 1})


def test_genotype_data_variants_invalid_data():
    helper = PhenoToolHelper(mocked_study)
    with pytest.raises(AssertionError):
        helper.genotype_data_variants({
                'effect_types': ['Splice-site', 'Frame-shift']
            }
        )


def test_genotype_data_variants_specific_effects():
    helper = PhenoToolHelper(mocked_study)
    variants = helper.genotype_data_variants(
        {
            'effectTypes': ['Missense', 'Synonymous']
        }
    )

    assert variants.get('missense') == Counter({'fam1.prb': 1})
    assert variants.get('synonymous') == Counter({'fam1.prb': 1,
                                                  'fam3.prb': 1})


def test_genotype_data_variants_lgds():
    helper = PhenoToolHelper(mocked_study)
    variants = helper.genotype_data_variants({'effectTypes': ['LGDs']})

    assert variants.get('lgds') == Counter({'fam2.prb': 1, 'fam3.prb': 1})


def test_genotype_data_variants_nonsynonymous():
    helper = PhenoToolHelper(mocked_study)
    variants = \
        helper.genotype_data_variants({'effectTypes': ['Nonsynonymous']})

    assert variants.get('nonsynonymous') == Counter({'fam1.prb': 1,
                                                     'fam2.prb': 1,
                                                     'fam3.prb': 1})


def test_genotype_data_variants_lgds_mixed():
    helper = PhenoToolHelper(mocked_study)
    variants = helper.genotype_data_variants(
        {
            'effectTypes': ['LGDs', 'Frame-shift', 'Splice-site']
        }
    )

    assert variants.get('lgds') == Counter({'fam2.prb': 1, 'fam3.prb': 1})
    assert variants.get('frame-shift') == Counter({'fam2.prb': 1})
    assert variants.get('splice-site') == Counter({'fam2.prb': 1,
                                                   'fam3.prb': 1})


def test_genotype_data_variants_family_filters(mocker):
    helper = PhenoToolHelper(mocked_study)
    mocker.spy(mocked_study, 'query_variants')
    helper.genotype_data_variants({'effectTypes': ['LGDs'],
                                   'familyIds': {0: 'fam1', 1: 'fam2'}})

    mocked_study.query_variants.assert_called_once_with(
        effectTypes=['LGDs'],
        familyIds={0: 'fam1', 1: 'fam2'})
