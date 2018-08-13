import pytest

from datasets.dataset import Dataset
from datasets.metadataset import MetaDataset
from VariantsDB import Study
from Variant import Variant

@pytest.fixture
def metadataset(mocker):
    datasets = [Dataset({ 'id': 'DS1', 'phenoDB' : {} }), Dataset({ 'id': 'DS2', 'phenoDB' : {} })]
    mocker.patch('datasets.dataset.Dataset._get_var_augmenter', autospec=True)\
        .return_value=lambda value: value
    mocker.patch('datasets.dataset.Dataset.get_pedigree_selector', autospec=True)\
        .return_value=None
    return MetaDataset({ 'id': 'META', 'phenoDB' : {} }, datasets)

@pytest.fixture
def studies(mocker):
    st1, st2 = mocker.MagicMock(), mocker.MagicMock()
    mocker.patch.object(st1, 'name', 'study1')
    mocker.patch.object(st2, 'name', 'study2')

    variants = [
        Variant({ 'location': '1:100', 'variant': 'var1', 'familyId': '1' }),
        Variant({ 'location': '3:120', 'variant': 'var2', 'familyId': '1' }),
        Variant({ 'location': '5:200', 'variant': 'var2', 'familyId': '2' }),
        Variant({ 'location': '2:100', 'variant': 'var3', 'familyId': '1' }),
        Variant({ 'location': '3:121', 'variant': 'var4', 'familyId': '1' }),
        Variant({ 'location': '5:200', 'variant': 'var2', 'familyId': '2' }),
    ]
    for i in range(0, len(variants)):
        variants[i].study = st1 if i < 3 else st2

    mocker.patch.object(st1, 'has_denovo')
    st1.has_denovo.return_value = True
    mocker.patch.object(st1, 'has_transmitted')
    st1.has_transmitted.return_value = False
    mocker.patch.object(st1, 'get_denovo_variants')
    st1.get_denovo_variants.return_value = (v for v in variants[:3])
    mocker.patch.object(st2, 'has_denovo')
    st2.has_denovo.return_value = False
    mocker.patch.object(st2, 'has_transmitted')
    st2.has_transmitted.return_value = True
    mocker.patch.object(st2, 'get_transmitted_variants')
    st2.get_transmitted_variants.return_value = (v for v in variants[3:])

    return [st1, st2]

def test_id():
    assert MetaDataset.ID == 'META'

def test_get_variants(mocker, metadataset, studies):
    ds1, ds2 = metadataset.datasets

    mocker.patch.object(ds1, 'get_studies')
    ds1.get_studies.return_value = [studies[0]]
    mocker.patch.object(ds2, 'get_studies')
    ds2.get_studies.return_value = studies

    variant_generator = metadataset.get_variants(safe=True,
        dataset_ids = ['DS1', 'DS2'],
        presentInParent = ["mother only", "father only",
            "mother and father", "neither"]
    )

    variants = list(variant_generator)
    assert 5 == len(variants)
    for idx, data in enumerate([
            ('1:100', 'DS1; DS2', 'study1'),
            ('2:100', 'DS2', 'study2'),
            ('3:120', 'DS1; DS2', 'study1'),
            ('3:121', 'DS2', 'study2'),
            ('5:200', 'DS1; DS2', 'study1; study2')]):
        assert variants[idx].location == data[0]
        assert variants[idx].atts['dataset'] == data[1]
        assert variants[idx].studyName == data[2]

def test_get_variants_skips_transmitted_when_not_needed(mocker, metadataset, studies):
    ds1, ds2 = metadataset.datasets

    mocker.patch.object(ds1, 'get_studies')
    ds1.get_studies.return_value = [studies[1]]

    variant_generator = metadataset.get_variants(safe=True,
        dataset_ids = ['DS1'],
        presentInParent = ["neither"]
    )

    variants = list(variant_generator)
    assert 0 == len(variants)

    mocker.patch.object(metadataset, 'get_transmitted_filters');
    metadataset.get_transmitted_filters.return_value = { 'familyIds' : [] }

    variant_generator = metadataset.get_variants(safe=True,
        dataset_ids = ['DS1'],
        presentInParent = ["mother only", "father only",
            "mother and father", "neither"]
    )

    variants = list(variant_generator)
    assert 0 == len(variants)

    assert not studies[1].get_transmitted_variants.called

def test_if_pedigree_selector_is_used(mocker, metadataset, studies):
    ds1, ds2 = metadataset.datasets

    mocker.patch.object(ds1, 'get_studies')
    ds1.get_studies.return_value = [studies[0]]
    mocker.patch.object(ds2, 'get_studies')
    ds2.get_studies.return_value = [studies[1]]

    fuck = mocker.patch.object(metadataset, 'filter_families_by_pedigree_selector',
        wraps=lambda **kwargs: {'1', '2'})

    phenotype_filter_mock = mocker.patch.object(metadataset, '_phenotype_filter',
                                                wraps=metadataset._phenotype_filter)
    variant_generator = metadataset.get_variants(safe=True,
        dataset_ids = ['DS1', 'DS2'],
        pedigreeSelector = {'id': 'phenotype', 'checkedValues':['autism']}
    )
    variants = list(variant_generator)
    phenotype_filter_mock.assert_called_with(mocker.ANY, dataset_ids = ['DS1', 'DS2'],
        pedigreeSelector = {'id': 'phenotype', 'checkedValues':['autism']})
