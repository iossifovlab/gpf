#!/usr/bin/env python
from gene.gene_set_collections import GeneSetsCollections

from DAE import variants_db


def main():
    gsc = GeneSetsCollections(variants_db.dataset_facade)
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    denovo.build_cache()


if __name__ == '__main__':
    main()
