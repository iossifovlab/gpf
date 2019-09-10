from box import Box

from dae.gene.tests.conftest import fixtures_dir

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser

from dae.studies.helpers import expand_effect_types
from dae.variants.attributes import Sex


def test_id(f4_trio_denovo_gene_set_config):
    assert f4_trio_denovo_gene_set_config.id == 'f4_trio'


def test_cache_file(f4_trio_denovo_gene_set_config):
    assert DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
        f4_trio_denovo_gene_set_config, 'phenotype') == \
            fixtures_dir() + '/studies/f4_trio/denovo-cache-phenotype.json'


def test_people_groups(f4_trio_denovo_gene_set_config):
    assert f4_trio_denovo_gene_set_config.people_groups == ['phenotype']


def test_gene_sets_names(f4_trio_denovo_gene_set_config):
    assert f4_trio_denovo_gene_set_config.gene_sets_names == [
        'LGDs', 'LGDs.Male', 'LGDs.Female', 'LGDs.Recurrent', 'LGDs.Single',
        'LGDs.Triple', 'LGDs.WE.Recurrent', 'LGDs.WE.Triple', 'Missense',
        'Missense.Single', 'Missense.Male', 'Missense.Female',
        'Missense.Recurrent', 'Missense.Triple', 'Missense.WE.Recurrent',
        'Missense.WE.Triple', 'Synonymous', 'Synonymous.WE',
        'Synonymous.WE.Recurrent', 'Synonymous.WE.Triple'
    ]


def test_recurrency_criterias(f4_trio_denovo_gene_set_config):
    recurrency_criterias = f4_trio_denovo_gene_set_config.recurrency_criterias

    assert len(recurrency_criterias) == 3

    assert recurrency_criterias['Single']['from'] == 1
    assert recurrency_criterias['Single']['to'] == 2

    assert recurrency_criterias['Triple']['from'] == 3
    assert recurrency_criterias['Triple']['to'] == -1

    assert recurrency_criterias['Recurrent']['from'] == 2
    assert recurrency_criterias['Recurrent']['to'] == -1


def test_standard_criterias(f4_trio_denovo_gene_set_config):
    standard_criterias = f4_trio_denovo_gene_set_config.standard_criterias
    assert \
        f4_trio_denovo_gene_set_config.selected_standard_criterias_values == \
        ['effect_types', 'sexes']

    assert len(standard_criterias) == 2

    effect_types = standard_criterias[0]

    assert effect_types[0]['property'] == 'effect_types'
    assert effect_types[0]['name'] == 'LGDs'
    assert effect_types[0]['value'] == expand_effect_types('LGDs')

    assert effect_types[1]['property'] == 'effect_types'
    assert effect_types[1]['name'] == 'Missense'
    assert effect_types[1]['value'] == expand_effect_types('missense')

    assert effect_types[2]['property'] == 'effect_types'
    assert effect_types[2]['name'] == 'Synonymous'
    assert effect_types[2]['value'] == expand_effect_types('synonymous')

    sexes = standard_criterias[1]

    assert sexes[0]['property'] == 'sexes'
    assert sexes[0]['name'] == 'Female'
    assert sexes[0]['value'] == [Sex.female]

    assert sexes[1]['property'] == 'sexes'
    assert sexes[1]['name'] == 'Male'
    assert sexes[1]['value'] == [Sex.male]

    assert sexes[2]['property'] == 'sexes'
    assert sexes[2]['name'] == 'Unspecified'
    assert sexes[2]['value'] == [Sex.unspecified]


def test_denovo_gene_sets(f4_trio_denovo_gene_set_config):
    denovo_gene_sets = f4_trio_denovo_gene_set_config.denovo_gene_sets

    assert len(denovo_gene_sets) == 1

    assert denovo_gene_sets['phenotype']['name'] == 'Phenotype'
    assert denovo_gene_sets['phenotype']['source'] == 'phenotype'


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


def test_missing_people_group(variants_db_fixture):
    f1_trio_config = DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config('f1_study'))

    assert f1_trio_config is None
