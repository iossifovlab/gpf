'''
Created on Feb 10, 2017

@author: lubo
'''


EXAMPLE_QUERY_SSC = {
    'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
    ],
    "presentInParent": [
        "neither"
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "datasetId": "SSC",
    "pedigreeSelector": {
        'id': "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}

EXAMPLE_QUERY_VIP = {
    'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
    ],
    "presentInParent": [
        'mother only', "neither"
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "VIP",
    "pedigreeSelector": {
        'id': "16pstatus",
        'checkedValues': ['duplication', 'triplication']
    },
}

EXAMPLE_QUERY_SD = {
    'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
    ],
    "presentInParent": [
        "neither"
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "SD",
    "pedigreeSelector": {
        'id': "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}
