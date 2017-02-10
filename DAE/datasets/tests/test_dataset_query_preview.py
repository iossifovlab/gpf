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
    "pedigreeSelector": "phenotype"
}


def test_get_denovo_variants_sd(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SD['datasetId'])
    vs = query.get_variants_preview(dataset_descriptor, **EXAMPLE_QUERY_SD)
    v = vs.next()
    print(v)
    v = vs.next()
    print(v)
