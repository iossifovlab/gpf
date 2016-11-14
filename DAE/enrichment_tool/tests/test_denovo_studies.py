'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.config import PHENOTYPES


def test_unaffected(unaffected_studies):
    studies = unaffected_studies

    for st in studies:
        assert 'WE' == st.get_attr('study.type')
        assert st.get_attr('study.phenotype') in PHENOTYPES


def test_autism(autism_studies):
    studies = autism_studies

    for st in studies:
        assert 'WE' == st.get_attr('study.type')
        assert 'autism' == st.get_attr('study.phenotype')


# def test_bad_phenotype(denovo_studies):
#     with pytest.raises(AssertionError):
#         denovo_studies.get_studies('ala bala')
