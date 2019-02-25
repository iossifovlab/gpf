#!/usr/bin/env python
from configurable_entities.configuration import DAEConfig
from gene.gene_set_collections import GeneSetsCollections
from studies.factory import VariantsDb


def main():
    config = DAEConfig()
    variants_db = VariantsDb(config)
    gsc = GeneSetsCollections(variants_db.dataset_facade)
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    denovo.build_cache()


if __name__ == '__main__':
    main()
