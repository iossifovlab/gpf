'''
Created on Feb 7, 2017

@author: lubo
'''


EXAMPLE_QUERY_SD = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
    "gender": "female,male",
    "presentInChild": "affected and unaffected,affected only",
    "presentInParent": "neither",
    "variantTypes": "CNV,del,ins,sub",
    "genes": "All",
    "datasetId": "SD",
    "pedigreeSelector": {
        'id': "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}


def test_get_denovo_variants_sd(sd):
    vs = sd.get_variants_preview(**EXAMPLE_QUERY_SD)
    v = vs.next()
    print(v)
    v = vs.next()
    print(v)
