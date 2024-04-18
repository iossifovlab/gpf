import pytest

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")

"""
Denovo Gene Sets are configured into study configuration. There is a section
'denovoGeneSets', that specifies available denovo gene sets.

People Groups, that are available for build denovo gene sets are specified in
'peopleGroups' list. Each entry in the list specifies a people group,
to be used for splitting the denovo gene set.

The configuration contains two groups of criteris, that could be used
for specifying denovo gene set:

* standardCriterias - criteria that could be used in searching variants
* recurrncyCriteria - criteria that could be use in counting events

The available denovo gene sets are specified in `geneSetsNames, that could
combine `standardCriteria` and `recurrencyCriteria` into signle denovo gene
set.

For example `LGDs.WE.Triple` combines `LGDs` effect criteria, `WE` study type
criteria and `Triple` recurrency criteria.

```
[denovoGeneSets]
peopleGroups = phenotype

standardCriterias.effectTypes.segments=LGDs:LGDs,Missense:missense,Synonymous:synonymous
standardCriterias.gender.segments=Female:F,Male:M,Unspecified:U

recurrencyCriteria.segments=Single:1:2,Triple:3:-1,Recurrent:2:-1

geneSetsNames=LGDs,LGDs.Male,LGDs.Female,LGDs.Recurrent,LGDs.Single,LGDs.Triple,
    Missense,Missense.Male,Missense.Female,Missense.Recurrent,Missense.Triple,
    Synonymous,Synonymous.Male,Synonymous.Female,Synonymous.Recurrent,Synonymous.Triple
```
"""


def test_example2_denovo_gene_set(denovo_gene_sets_db):
    denovo_sets = denovo_gene_sets_db.get_all_gene_sets(
        {"f1_group": {"phenotype": ["autism"]}},
    )
    assert denovo_sets
    print(denovo_sets)

    denovo_sets2 = denovo_gene_sets_db.get_all_gene_sets(
        {"f1_group": {"phenotype": ["autism", "unaffected"]}},
    )
    assert len(denovo_sets) <= len(denovo_sets2)
