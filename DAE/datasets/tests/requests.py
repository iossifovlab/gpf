'''
Created on Feb 10, 2017

@author: lubo
'''


EXAMPLE_QUERY_SSC = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
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
    "family_race": "All",
    "family_quad_trio": "All",
    "family_prb_gender": "All",
    "family_sib_gender": "All",
    "family_study_type": "All",
    "family_studies": "All",
    "family_pheno_measure_min": 1.08,
    "family_pheno_measure_max": 40,
    "family_pheno_measure": "abc.subscale_ii_lethargy",
    "datasetId": "SSC",
    "pedigreeSelector": {
        'id': "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}

EXAMPLE_QUERY_VIP = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
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
    "datasetId": "VIP",
    "pedigreeSelector": {
        'id': "16pstatus",
        'checkValues': ['duplication', 'triplication']
    },
}

EXAMPLE_QUERY_SD = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
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
