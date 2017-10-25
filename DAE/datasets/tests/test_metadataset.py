import pytest

from datasets.dataset import Dataset
from datasets.metadataset import MetaDataset
from VariantsDB import Study
from Variant import Variant

@pytest.fixture
def metadataset():
    return MetaDataset({}, [])

def test_id():
    assert MetaDataset.ID == 'META'

def test_columns(mocker, metadataset):
    get_pheno_columns = mocker.patch('datasets.dataset.Dataset.get_columns', autospec=True)
    get_pheno_columns.return_value = []
    assert ['dataset'] == metadataset.get_columns()

def test_get_legend(mocker, metadataset):
    ds1, ds2 = Dataset({ 'id': 'DS1' }), Dataset({ 'id': 'DS2' })
    metadataset.datasets = [ds1, ds2]
    
    mocker.patch.object(ds1, 'get_legend')
    ds1.get_legend.return_value = ['legend1', 'repeating_legend', 'legend2', 'repeating_legend']
    mocker.patch.object(ds2, 'get_legend')
    ds2.get_legend.return_value = ['not-included']

    legend = metadataset.get_legend(dataset_ids=['DS1'])
    assert  set(legend).issubset(['legend1', 'repeating_legend', 'legend2'])
    assert 3 == len(legend)

def test_get_variants(mocker, metadataset):
    ds1, ds2 = Dataset({ 'id': 'DS1' }), Dataset({ 'id': 'DS2' })
    st1, st2 = mocker.MagicMock(), mocker.MagicMock()
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

    metadataset.datasets = [ds1, ds2]

    mocker.patch.object(ds1, 'get_studies')
    ds1.get_studies.return_value = [st1]
    mocker.patch.object(ds2, 'get_studies')
    ds2.get_studies.return_value = [st1, st2]

    mocker.patch.object(st1, 'name', 'study1')
    mocker.patch.object(st2, 'name', 'study2')
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
    mocker.patch.object(st2, 'get_denovo_variants')
    st2.get_transmitted_variants.return_value = (v for v in variants[3:])

    mocker.patch('datasets.dataset.Dataset._get_var_augmenter', autospec=True)\
        .return_value=lambda value: value
    mocker.patch('datasets.dataset.Dataset.get_pedigree_selector', autospec=True)\
        .return_value=None

    variant_generator = metadataset.get_variants(safe=True,
        dataset_ids = ['DS1', 'DS2'])

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
