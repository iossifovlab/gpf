import pytest

from dae.enrichment_tool.genotype_helper import GenotypeHelper


@pytest.mark.parametrize('people_group,effect_types,count', [
    ('autism', 'missense', 2),
    ('autism', 'synonymous', 2),
    ('autism', ['missense', 'synonymous'], 4),
    ('unaffected', 'missense', 0),
    ('unaffected', 'synonymous', 1),
    ('unaffected', ['missense', 'synonymous'], 1),
])
def test_get_variants(f1_trio, people_group, effect_types, count):
    pg = f1_trio.get_families_group('phenotype')
    gh = GenotypeHelper(f1_trio, pg, people_group)

    assert len(gh.get_variants(effect_types)) == count


@pytest.mark.parametrize('people_group,male,female,unspecified,count', [
    ('autism', 1, 1, 0, 2),
    ('unaffected', 0, 1, 0, 1),
])
def test_get_children_stats(
        f1_trio, people_group, male, female, unspecified, count):
    pg = f1_trio.get_families_group('phenotype')
    gh = GenotypeHelper(f1_trio, pg, people_group)

    children_stats = gh.get_children_stats()

    assert len(children_stats) == count
    assert children_stats['M'] == male
    assert children_stats['F'] == female
    assert children_stats['U'] == unspecified

    children_stats = gh.get_children_stats()
    assert len(children_stats) == count
