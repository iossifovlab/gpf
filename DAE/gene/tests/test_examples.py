'''
Created on Apr 16, 2018

@author: lubo
'''
from __future__ import print_function
from gene.gene_set_collections import DenovoGeneSetsCollection,\
    MetaDenovoGeneSetsCollection
# from datasets.datasets_factory import DatasetsFactory
from datasets.config import DatasetsConfig


# def test_example1_denovo_gene_sets():
#     gsc = DenovoGeneSetsCollection()
#     gsc.build_cache(datasets=['SD', 'denovo_db'])
#     gs = gsc.get_gene_set("LGDs.Recurrent", {'SD': ['autism']})
#     assert gs
#
#     print("SD: autism rec lgds:", gs)
#
#     gss = gsc.get_gene_sets({'SD': ['autism']})
#     gss = {g['name']: g['syms'] for g in gss}
#
#     print("SD: autism gene sets keys: ", gss.keys())
#
#     gss = gsc.get_gene_sets({'SSC': ['autism']})
#     print(gss)


def test_example2_denovo_gene_sets():
    gsc = DenovoGeneSetsCollection()
    gsc.load()

    print(gsc.get_dataset_phenotypes('SD'))
    print(gsc.get_dataset_phenotypes('denovo_db'))

    denovo_sets = gsc.get_denovo_sets({
        'SD': ['autism'],
        'denovo_db': ['autism']})
    assert denovo_sets
    print(denovo_sets.keys())

    print(denovo_sets['LGDs.Recurrent'])
    print(denovo_sets['LGDs.Triple'])

    denovo_sets2 = gsc.get_denovo_sets({
        'SD': None,
        'denovo_db': None})
    assert len(denovo_sets['LGDs.Recurrent']) <= \
        len(denovo_sets2['LGDs.Recurrent'])

    assert denovo_sets['LGDs.Recurrent'].issubset(
        denovo_sets2['LGDs.Recurrent'])


def test_example3_meta_denovo_gene_sets():
    gsc = MetaDenovoGeneSetsCollection()
    gsc.load()

    print(gsc.get_dataset_phenotypes())

    denovo_sets = gsc.get_denovo_sets(['autism'])
    assert denovo_sets
    print(denovo_sets.keys())

    print(denovo_sets['LGDs.Recurrent'])
    print(denovo_sets['LGDs.Triple'])


def test_example4_dataset_factory():
    ds_config = DatasetsConfig()
    print(ds_config.get_dataset_ids())

#     ds_factory = DatasetsFactory()
#     print(ds_factory.get_dataset("SD"))
#     print(ds_factory.get_dataset("denovo_db"))
