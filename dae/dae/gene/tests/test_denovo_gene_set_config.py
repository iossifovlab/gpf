import pytest
from box import Box
from copy import deepcopy

from dae.gene.tests.conftest import fixtures_dir

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory
from dae.utils.people_group_utils import select_people_groups


def test_id(f4_trio_denovo_gene_set_config):
    assert f4_trio_denovo_gene_set_config.id == 'f4_trio'


def test_cache_file(f4_trio_denovo_gene_set_config):
    assert DenovoGeneSetCollectionFactory.denovo_gene_set_cache_file(
        f4_trio_denovo_gene_set_config, 'phenotype') == \
            fixtures_dir() + '/studies/f4_trio/denovo-cache-phenotype.json'


def test_people_groups(f4_trio_denovo_gene_set_config):
    selected_people_groups = \
        f4_trio_denovo_gene_set_config.denovo_gene_sets.selected_people_groups

    people_groups = select_people_groups(
        f4_trio_denovo_gene_set_config.people_group,
        selected_people_groups)

    assert isinstance(people_groups, dict)
    assert len(people_groups) == 1
    assert 'phenotype' in people_groups
    assert people_groups['phenotype']['name'] == 'Phenotype'
    assert people_groups['phenotype']['source'] == 'phenotype'
    domain_ids = list(
        map(lambda x: x[0], people_groups['phenotype']['domain']))
    assert set(domain_ids) == {
        'autism', 'congenital_heart_disease', 'epilepsy',
        'intellectual_disability', 'schizophrenia', 'unaffected'
    }


def test_gene_sets_names(f4_trio_denovo_gene_set_config):
    assert f4_trio_denovo_gene_set_config.denovo_gene_sets.gene_sets_names == [
        'LGDs', 'LGDs.Male', 'LGDs.Female', 'LGDs.Recurrent', 'LGDs.Single',
        'LGDs.Triple', 'Missense', 'Missense.Single', 'Missense.Male',
        'Missense.Female', 'Missense.Recurrent', 'Missense.Triple',
        'Synonymous'
    ]


def test_recurrency_criterias(f4_trio_denovo_gene_set_config):
    recurrency_criteria = \
        f4_trio_denovo_gene_set_config.denovo_gene_sets.recurrency_criteria

    assert len(recurrency_criteria.segments) == 3

    assert recurrency_criteria.segments.Single.start == 1
    assert recurrency_criteria.segments.Single.end == 2

    assert recurrency_criteria.segments.Triple.start == 3
    assert recurrency_criteria.segments.Triple.end == -1

    assert recurrency_criteria.segments.Recurrent.start == 2
    assert recurrency_criteria.segments.Recurrent.end == -1


def test_standard_criterias(f4_trio_denovo_gene_set_config):
    denovo_gs_config = f4_trio_denovo_gene_set_config.denovo_gene_sets
    standard_criterias = denovo_gs_config.standard_criterias
    assert \
        denovo_gs_config.selected_standard_criterias_values == \
        ['effect_types', 'sexes']

    assert len(standard_criterias) == 2

    effect_types = standard_criterias[0].segments

    assert standard_criterias[0].section_id() == 'effect_types'
    assert effect_types[0] is not None
    assert effect_types[0] == 'LGDs'

    assert effect_types[1] is not None
    assert effect_types[1] == 'missense'

    assert effect_types[2] is not None
    assert effect_types[2] == 'synonymous'

    sexes = standard_criterias[1].segments

    assert standard_criterias[1].section_id() == 'sexes'
    assert sexes[0] is not None
    assert sexes[0] == 'F'

    assert sexes[1] is not None
    assert sexes[1] == 'M'

    assert sexes[2] is not None
    assert sexes[2] == 'U'


@pytest.mark.skip()
def test_empty():
    config = Box({
        'study_config': {
            'denovoGeneSets': {
                'enabled': False
            },
            'config_file': '/conf/denovo_gene_sets.conf'
        }
    })

    assert DenovoGeneSetConfigParser.parse(config) is None

    config.study_config.enrichment = None
    assert DenovoGeneSetConfigParser.parse(config) is None

    config.study_config = None
    assert DenovoGeneSetConfigParser.parse(config) is None

    assert DenovoGeneSetConfigParser.parse(None) is None


@pytest.mark.skip()
def test_missing_people_group(variants_db_fixture):
    f4_study_config = deepcopy(variants_db_fixture.get_config('f4_trio'))
    f4_study_config.people_group_config.people_group = {}
    f1_trio_config = DenovoGeneSetConfigParser.parse(f4_study_config)

    assert f1_trio_config.denovo_gene_sets is None


@pytest.mark.skip()
def test_missing_people_groups(variants_db_fixture):
    f1_trio_config = DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config('f1_study'))

    assert f1_trio_config is None
