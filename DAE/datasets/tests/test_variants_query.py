'''
Created on Mar 3, 2017

@author: lubo
'''


def count(vs):
    c = 0
    for _v in vs:
        c += 1
    return c


def test_get_variants_with_gene_weights(sd):
    query = {
        "datasetId": "SD",
        "effectTypes": None,
        "gender": None,
        "variantTypes": None,
        "presentInChild": None,
        "presentInParent": None,
        "rarity": None,
        "pedigreeSelector": {
            "id": "phenotype",
            "checkedValues": [
                "autism"
            ]
        },
        "geneSymbols": None,
        "geneSet": None,
        "geneWeights": {
            "weight": "RVIS_rank",
            "rangeStart": 0,
            "rangeEnd": 1
        },
        "regions": None
    }

    vs = sd.get_variants(**query)
    assert vs is not None
    assert 5 == count(vs)


def test_get_variants_with_null_gene_weights(sd):
    query = {
        "datasetId": "SD",
        "effectTypes": [
            "Splice-site"
        ],
        "gender": None,
        "variantTypes": ["del"],
        "presentInChild": None,
        "presentInParent": None,
        "rarity": None,
        "pedigreeSelector": {
            "id": "phenotype",
            "checkedValues": [
                "autism"
            ]
        },
        "geneSymbols": None,
        "geneSet": None,
        "geneWeights": None,
        "regions": None
    }
    vs = sd.get_variants(**query)
    assert vs is not None
    assert 5 == count(vs)
