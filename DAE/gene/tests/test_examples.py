'''
Created on Apr 16, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import
from __future__ import unicode_literals

import pytest

pytestmark = pytest.mark.skip('removed used interface')
# pytestmark = pytest.mark.usefixtures("gene_info_cache_dir")

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
combine `standardCriteria` and `recurrencyCriteria` into signle denovo gene
set.

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


def test_example2_denovo_gene_sets(gscs):
    # gsc = DenovoGeneSetsCollection()
    # gsc.load()
    denovo = gscs.get_gene_sets_collection('denovo')

    denovo_sets = denovo.get_denovo_sets({
        'f1_group': ['autism']})
    assert denovo_sets
    print(list(denovo_sets.keys()))

    print(denovo_sets['Synonymous'])
    # print(denovo_sets['LGDs.Triple'])

    denovo_sets2 = denovo.get_denovo_sets({
        'f1_group': None})
    assert len(denovo_sets['Synonymous']) <= \
        len(denovo_sets2['Synonymous'])

    assert denovo_sets['Synonymous'].issubset(
        denovo_sets2['Synonymous'])


# def test_example3_meta_denovo_gene_sets():
#     meta_gsc = MetaDenovoGeneSetsCollection()
#     meta_gsc.load()
#
#     print(meta_gsc.get_dataset_phenotypes())
#
#     denovo_sets = meta_gsc.get_denovo_sets(['autism'])
#     assert denovo_sets
#     print(denovo_sets.keys())
#
#     print(denovo_sets['LGDs.Recurrent'])
#     print(denovo_sets['LGDs.Triple'])

