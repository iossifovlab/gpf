'''
Created on Nov 16, 2016

@author: lubo
'''
from pheno_tool.genotype_helper import VariantsType as VT


def test_get_variants_denovo(
        autism_candidates_genes, genotype_helper):

    vs = genotype_helper.get_variants(
        VT(
            effect_types=['LGDs'],
            gene_syms=autism_candidates_genes,
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['neither'],
        ))
    variants = [v for v in vs]
    assert 137 == len(variants)


def test_get_variants_father_ultra_rare(
        autism_candidates_genes, genotype_helper):

    vs = genotype_helper.get_variants(
        VT(
            effect_types=['LGDs'],
            gene_syms=autism_candidates_genes,
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=[
                'father only',
                'mother and father',
                'neither'
            ],
        )
    )
    variants = [v for v in vs]
    assert 176 == len(variants)


def test_get_variants_father_rarity(
        autism_candidates_genes, genotype_helper):

    vt = VT(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        present_in_child=[
            'autism only',
            'autism and unaffected',
            'neither'],
        present_in_parent=[
            'father only',
            'mother and father',
            'neither'
        ],
        rarity='rare',
        rarity_max=1.0,
    )
    query = vt._dae_query_request()

    assert query['maxAltFreqPrcnt'] == 1.0
    assert query['minAltFreqPrcnt'] is None

    vs = genotype_helper.get_variants(vt)
    variants = [v for v in vs]

    for v in variants:
        if v.popType != 'denovo':
            assert 'dad' in v.fromParentS or v.fromParentS == ''
            assert v.altFreqPrcnt <= 1.0

    assert 250 == len(variants)


def test_get_variants_father_interval(
        autism_candidates_genes, genotype_helper):

    vt = VT(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        rarity='interval',
        rarity_max=50.0,
        rarity_min=1.0,
        present_in_child=[
            'autism only', 'autism and unaffected', 'neither'],
        present_in_parent=[
            'father only',
            'mother and father',
            'neither'
        ],
    )
    query = vt._dae_query_request()

    assert query['maxAltFreqPrcnt'] == 50.0
    assert query['minAltFreqPrcnt'] == 1.0

    vs = genotype_helper.get_variants(vt)
    variants = [v for v in vs]
    for v in variants:
        if v.popType != 'denovo':
            assert 'dad' in v.fromParentS or v.fromParentS == ''
            assert v.altFreqPrcnt >= 1.0 and v.altFreqPrcnt <= 50.0

    assert 593 == len(variants)


def test_get_single_gene_all(
        genotype_helper):
    vs = genotype_helper.get_variants(
        VT(
            effect_types=['LGDs'],
            gene_syms=['POGZ'],
            rarity='all',
            present_in_child=[
                'autism only', 'autism and unaffected', 'neither'],
            present_in_parent=[
                'father only',
                'mother and father',
                'neither'
            ],
        )
    )
    variants = [v for v in vs]
    assert 6 == len(variants)


def test_get_single_gene_persons_variants_all(
        genotype_helper):

    res = genotype_helper.get_persons_variants(
        VT(
            effect_types=['LGDs'],
            gene_syms=['POGZ'],
            rarity='all',
            present_in_child=[
                'autism only', 'autism and unaffected', 'neither'],
            present_in_parent=['father only', 'mother only',
                               'mother and father', 'neither'],
        )
    )
    assert 6 == len(res)


def test_get_persons_variants_denovo(
        autism_candidates_genes, genotype_helper):

    res = genotype_helper.get_persons_variants(
        VT(
            effect_types=['LGDs'],
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['neither'],
            gene_syms=autism_candidates_genes,
        )
    )
    assert 137 == len(res)


def test_get_person_variants_father_all(
        autism_candidates_genes, genotype_helper):

    vs = genotype_helper.get_variants(
        VT(
            effect_types=['Frame-shift', 'Nonsense', 'Splice-site'],
            gene_syms=autism_candidates_genes,
            rarity='rare',
            rarity_max=10.0,
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['father only', 'mother and father', 'neither'],
        )
    )
    variants = [v for v in vs]
    assert 503 == len(variants)

    res = genotype_helper.get_persons_variants(
        VT(
            effect_types=['Frame-shift', 'Nonsense', 'Splice-site'],
            gene_syms=autism_candidates_genes,
            rarity='rare',
            rarity_max=10.0,
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['father only', 'mother and father', 'neither'],
        )
    )
    assert 934 == len(res)
    assert 3 == max(res.values())
    ps3 = [p for (p, c) in res.items() if c == 3]
    assert 6 == len(ps3)

    assert '13528.p1' in ps3
    assert '13528.fa' in ps3

    assert '13216.p1' in ps3
    assert '13216.fa' in ps3


def test_get_lgds_variants_for_family(
        autism_candidates_genes, genotype_helper):

    vs = genotype_helper.get_variants(
        VT(
            effect_types=['LGDs'],
            present_in_child=[
                'autism only', 'unaffected only', 'autism and unaffected',
                'neither'],
            present_in_parent=[
                'father only', 'mother only', 'mother and father',
                'neither'],
            rarity='all',
            family_ids=['11000'],
        )
    )
    variants = [v for v in vs]
    assert 100 == len(variants)


def test_get_persons_variants_df_denovo(
        autism_candidates_genes, genotype_helper):

    res = genotype_helper.get_persons_variants_df(
        VT(
            effect_types=['LGDs'],
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['neither'],
            gene_syms=autism_candidates_genes,
        )
    )
    assert 137 == len(res)
    assert 'variants' in res.columns
    assert 1 == res.loc['12645.p1', 'variants']
    assert 1 == res.iloc[0, 0]
