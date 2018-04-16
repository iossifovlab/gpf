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
"""
Denovo Gene Sets are configured into 'geneInfo.conf'. There is a section
'geneTerms.denovo', that specifies available denovo gene sets.

Dataset, that are available for build denovo gene sets are specified in
'dataset.pedigreeSelectors' list. Each entry in the list specifies a dataset,
a pedigree selector to be used for splitting the denovo gene set.

The configuration contains two groups of criteris, that could be used
for specifying denovo gene set:

* startdCriteria - criteria that could be used in serching variants
* recurrncyCriteria - criteria that could be use in counting events

The available denovo gene sets are specified in `geneSetsNames, that could
combine `standardCriteria` and `recurrencyCriteria` into signle denovo gene set.

For example `LGDs.WE.Triple` combines `LGDs` effect criteria, `WE` study type
criteria and `Triple` recurrency criteria.

```
[geneTerms.denovo]
file=%(wd)s/geneInfo/cache/denovo-cache.cache
webFormatStr=key| (|count|)
webLabel=Denovo

datasets.pedigreeSelectors=SD:phenotype:phenotype,SSC:phenotype:phenotype,
    SPARK:phenotype:phenotype,VIP:phenotype:phenotype,denovo_db:phenotype:phenotype

standardCriterias=effectTypes,gender,studyTypes
standardCriterias.effectTypes.segments=LGDs:LGDs,Missense:missense,Synonymous:synonymous
standardCriterias.gender.segments=Female:F,Male:M,Unspecified:U
standardCriterias.studyTypes.segments=WE:WE,Non WE:WG.TG.CNV

recurrencyCriteria.segments=Single:1:2,Triple:3:-1,Recurrent:2:-1

geneSetsNames=LGDs,LGDs.Male,LGDs.Female,LGDs.Recurrent,LGDs.Single,LGDs.Triple,
    LGDs.WE.Recurrent,LGDs.WE.Triple,
    Missense,Missense.Male,Missense.Female,
    Missense.Recurrent,Missense.Triple,Missense.WE.Recurrent,Missense.WE.Triple,
    Synonymous,Synonymous.WE,Synonymous.WE.Recurrent,Synonymous.WE.Triple
```
"""



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
    meta_gsc = MetaDenovoGeneSetsCollection()
    meta_gsc.load()

    print(meta_gsc.get_dataset_phenotypes())

    denovo_sets = meta_gsc.get_denovo_sets(['autism'])
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
