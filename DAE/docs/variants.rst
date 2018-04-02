variants package
================

Variants in families
--------------------



Example usage of :ref:`variants`
--------------------------------

Example usage of `variants` package::

    from __future__ import print_function
    
    import os
    from variants.vcf_utils import mat2str
    from variants.builder import variants_builder as VB
    
    prefix = "ivan-tiny/a"
    # prefix = "spark/nspark"
    prefix = 'fixtures/effects_trio'
    
    genome_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "chrAll.fa")
    print(genome_file)
    
    gene_models_file = os.path.join(
        os.environ.get("DAE_DB_DIR"),
        "genomes/GATK_ResourceBundle_5777_b37_phiX174",
        "refGene-201309.gz")
    print(gene_models_file)
    
    
    fvars = VB(prefix=prefix, genome_file=genome_file,
               gene_models_file=gene_models_file)
    
    vs = fvars.query_variants()
    
    
    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), sep='\t')
        for aa in v.falt_alleles:
            print(v.effect[aa].worst, v.effect[aa].gene)
            print(v['all.nAltAlls'][aa], v['all.altFreq'][aa])


.. automodule:: variants
    :members:
    :undoc-members:
    :show-inheritance:

    
variants.variant module
-----------------------
    
.. autoclass:: variant.VariantBase
    :members:
    :inherited-members:

SummaryVariant - representation of summary variants
---------------------------------------------------

.. autoclass:: variant.SummaryVariant
    :members:
    :inherited-members:


variants.family module
----------------------

.. automodule:: variants.family
    :members:
    :undoc-members:
    :show-inheritance:
