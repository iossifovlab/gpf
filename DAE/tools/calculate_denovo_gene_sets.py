#!/usr/bin/env python
from gene.gene_set_collections import GeneSetsCollections

if __name__ == '__main__':
    gsc = GeneSetsCollections()
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    denovo.build_cache()
