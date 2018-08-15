import copy
from pheno.common import Role
import pytest

BASE_QUERY = {
    'gender': [
        'female',
        'male'
    ],
    'safe': True,
    'effectTypes': [
        'Nonsense',
        'Frame-shift',
        'Splice-site',
        'Missense',
    ],
    'variantTypes': [
        'sub', 'ins', 'del', 'CNV'
    ]
}

TRANSMITTED_QUERY = copy.deepcopy(BASE_QUERY)
TRANSMITTED_QUERY.update({
    'presentInParent': {
        'presentInParent': [
            'mother only',
            'father only',
            'mother and father'
        ],
        'rarity': {
            'ultraRare': True,
            'minFreq': None,
            'maxFreq': None
        }
    },
    'presentInChild': [
        'affected only',
        'unaffected only',
        'affected and unaffected',
        'neither'
    ],
    'limit': 2000
})


def assert_members_with_role_have_variant(variant, role):
    members_with_index = enumerate(variant.memberInOrder)
    members_with_role = filter(lambda p: p[1].role == role, members_with_index)

    assert any(variant.bestSt[1][i] > 0
               for i, _ in members_with_role)


def assert_members_with_role_and_variant_count(variant, role, count):
    variant_in_members = 0
    for i, m in enumerate(variant.memberInOrder):
        if m.role == role and variant.bestSt[1][i] > 0:
            variant_in_members += 1

    assert variant_in_members == count


def test_denovo_simple_role_filter(ssc):
    query = copy.deepcopy(BASE_QUERY)
    query['roles'] = ['prb', 'sib']

    vs = ssc.get_denovo_variants(**query)
    vs = list(vs)
    assert len(vs) == 4036


def test_denovo_only_parents_role_filter(ssc):
    query = copy.deepcopy(BASE_QUERY)
    query['roles'] = ['mom', 'dad']

    vs = ssc.get_denovo_variants(**query)
    vs = list(vs)
    assert len(vs) == 0


def test_denovo_only_sibling_role_filter(ssc):
    query = copy.deepcopy(BASE_QUERY)
    query['roles'] = ['sib']

    # FIXME: CNV have weird best state...
    query['variantTypes'].remove('CNV')
    print(query['variantTypes'])

    vs = ssc.get_denovo_variants(**query)
    vs = list(vs)
    assert len(vs) == 1646

    for variant in vs:
        assert_members_with_role_have_variant(variant, Role.sib)


@pytest.mark.skip(reason="needed to implement for transmitted mysql queries")
def test_transmitted_only_mother_role_filter(ssc):
    query = copy.deepcopy(TRANSMITTED_QUERY)
    query['roles'] = ['mom']

    vs = ssc.get_transmitted_variants(**query)
    vs = list(vs)
    assert len(vs) == 2000

    for variant in vs:
        assert_members_with_role_have_variant(variant, Role.mom)


