variants package
================

Variants in families
--------------------


Example usage of :ref:`variants`
--------------------------------

Example usage of `variants` package::

    import os
    from utils.vcf_utils import mat2str
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
        for aa in v.alt_alleles:
            print(aa.effect.worst, aa.effect.genes)
            print(aa['af_allele_count'], aa['af_allele_freq'])



.. include:: variants_query.rst


VariantBase - a base class for variants
---------------------------------------

.. autoclass:: dae.variants.variant.VariantBase
    :members:
    :undoc-members:
    :special-members: __init__, __eq__, __ne__, __lt__, __gt__


SummaryAllele - a base class for representing alleles
-----------------------------------------------------

.. autoclass:: dae.variants.variant.SummaryAllele
    :members:
    :undoc-members:
    :special-members: __init__
    :inherited-members:


SummaryVariant - representation of summary variants
---------------------------------------------------

.. autoclass:: dae.variants.variant.SummaryVariant
    :members:
    :special-members: __init__, __getitem__, __contains__
    :undoc-members:
    :inherited-members:

FamilyDelegate - common inheritance methods
-------------------------------------------

.. autoclass:: dae.variants.family_variant.FamilyDelegate
    :members:
    :undoc-members:
    :inherited-members:



FamilyAllele - representation of family allele
----------------------------------------------

.. autoclass:: dae.variants.family_variant.FamilyAllele
    :members:
    :special-members: __getattr__
    :undoc-members:
    :inherited-members:

FamilyVariant - representation of family variants
-------------------------------------------------

.. autoclass:: dae.variants.family_variant.FamilyVariant
    :members:
    :special-members: __getattr__
    :undoc-members:
    :inherited-members:



variants.family module
----------------------

.. automodule:: dae.variants.family
    :members:
    :undoc-members:
    :show-inheritance:

Family - representation of a family
-----------------------------------

.. autoclass:: dae.variants.family.Family
    :members:
    :undoc-members:
    :special-members: __init__, __len__


VcfFamily - family specialization for VCF variants
--------------------------------------------------

.. autoclass:: dae.backends.vcf.raw_vcf.VcfFamily
    :members:
    :undoc-members:
    :special-members: __init__
    :inherited-members:


RawFamilyVariants - query interface for VCF variants
----------------------------------------------------

.. autoclass:: dae.backends.vcf.raw_vcf.RawFamilyVariants
    :members:
    :undoc-members:
    :inherited-members:


Apache Parquet variants schema
------------------------------

Summary Variants/Alleles flat schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


* **chrom** (string) -
    chromosome where variant is located
* **position** (int64) -
    1-based position of the start of the variant
* **reference** (string) -
    reference DNA string 
* **alternative** (string) -
    alternative DNA string (None for reference allele)
* **summary_index** (int64) -
    index of the summary variant
* **allele_index** (int16) -
    index of the allele inside given summary variant
* **variant_type** (int8) -
    variant type in CSHL nottation
* **cshl_variant** (string) -
    variant description in CSHL notation
* **cshl_position** (int64) -
    variant position in CSHL notation
* **cshl_length** (int32) -
    variant length in CSHL notation
* **effect_type** (string) -
    worst effect of the variant (None for reference allele)
* **effect_gene_genes** (list_(string)) -
    list of all genes affected by
    the variant allele (None for reference allele)
* **effect_gene_types** (list_(string)) -
    list of all effect types
    corresponding to the `effect_gene_genes` (None for reference allele)
* **effect_details_transcript_ids** (list_(string)) -
    list of all transcript ids
    affected by the variant allele (None for reference allele)
* **effect_details_details** (list_(string)) -
    list of all effected details
    corresponding to the `effect_details_transcript_ids`
    (None for reference allele)
* **af_parents_called_count** (int32) -
    count of independent parents that has
    well specified genotype for this allele
* **af_parents_called_percent** (float64) -
    parcent of independent parents
    corresponding to `af_parents_called_count`
* **af_allele_count** (int32) -
    count of this allele in the independent parents
* **af_allele_freq** (float64) -
    allele frequency


Family Variants schema
^^^^^^^^^^^^^^^^^^^^^^


* **chrom** (`string`)
* **position** (`int64`)
* **family_index** (`int64`) -
    index of the family variant
* **summary_index** (`int64`) -
    index of the summary variant
* **family_id** (`string`) -
    family ID
* **genotype** (`list_(int8)`) -
    genotype of the variant for the specified family
* **inheritance** (`int32`) -
    inheritance type of the variant


Family Alleles schema
^^^^^^^^^^^^^^^^^^^^^


* **family_index** (`int64`)
* **summary_index** (`int64`)
* **allele_index** (`int16`)

* **variant_in_members** (`list_(string)`) -
    list of members of the family that
    have this allele
* **variant_in_roles** (`list_(int32)`) -
    list of family members' roles that
    have this allele
* **variant_in_sexes** (`list_(int8)`) -
    list of family members' sexes that
    have this allele


Variant Scores schema
^^^^^^^^^^^^^^^^^^^^^

* **summary_index** (`int64`)
* **allele_index** (`int16`)
* **score_id** (`string` or `int64`)
* **score_value** (`float64`)


Pedigree file schema
^^^^^^^^^^^^^^^^^^^^

* **familyId** (`string`)
* **personId** (`string`)
* **dadId** (`string`)
* **momId** (`string`)
* **sex** (`int8`)
* **status** (`int8`)
* **role** (`int32`)
* **sampleId** (`string`)
* **order** (`int32`)


Functions from `parquet_io` module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. automodule:: dae.variants
    :members:
    :undoc-members:


