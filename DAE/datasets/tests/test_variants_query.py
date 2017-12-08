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
        "effectTypes": [
            'Frame-shift',
            'Nonsense',
            'Splice-site',
        ],
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
            "rangeStart": 16530,
            "rangeEnd": 16754
        },
        "regions": None
    }

    vs = sd.get_variants(**query)
    assert vs is not None
    assert 9 == count(vs)


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
    assert 3 == count(vs)


def test_get_variants_with_autism_and_unaffected(sd):
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
                "autism",
                "unaffected",
            ]
        },
        "geneSymbols": None,
        "geneSet": None,
        "geneWeights": None,
        "regions": None
    }
    vs = sd.get_variants(**query)
    assert vs is not None
    vs = list(vs)
    assert 5 == count(vs)


def test_get_variants_with_rarity(ssc):
    query = {
        "datasetId": "SSC",
        "effectTypes": [
            "Splice-site"
        ],
        "gender": [
            "female",
            "male"
        ],
        "variantTypes": [
            "del"
        ],
        "presentInChild": [
            "affected only",
            "affected and unaffected"
        ],
        "presentInParent": [
            "mother only",
            "neither"
        ],
        "rarity": {
            "ultraRare": None,
            "minFreq": None,
            "maxFreq": 0.001,
        },
        "pedigreeSelector": None,
        "geneSymbols": None,
        "geneSet": None,
        "geneWeights": None,
        "regions": None
    }
    vs = ssc.get_variants(**query)
    assert vs is not None
    assert 2 == count(vs)


def test_get_variants_with_rarity_interval(ssc):
    query = {
        "datasetId": "SSC",
        "effectTypes": [
            "Nonsense",
            "Frame-shift",
            "Splice-site"
        ],
        "presentInChild": [
            "neither"
        ],
        "presentInParent": [
            "mother only",
            "neither"
        ],
        "rarity": {
            "minFreq": 95,
        },
    }
    vs = ssc.get_variants(**query)
    assert vs is not None
    assert 3 == count(vs)

def test_get_complex_variants(denovodb):
    query = {
        "datasetId": "denovo-db",
        "effectTypes": [
            "Nonsense",
            "Frame-shift",
            "Splice-site"
        ],
        "variantTypes": [
            "complex"
        ],
    }
    vs = denovodb.get_variants(**query)
    assert vs is not None
    assert 7 == count(vs)

def test_get_unknown_gender_variants(denovodb):
    query = {
        "datasetId": "denovo-db",
        "effectTypes": [
            "Nonsense",
        ],
        "variantTypes": [
            "complex"
        ],
        "gender": [
            "unknown"
        ]
    }
    vs = denovodb.get_variants(**query)
    assert vs is not None
    assert 1 == count(vs)
