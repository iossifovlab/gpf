Genomic Variants
================


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


Family variants query interface
-------------------------------


Once you have family variants interface created, you can use it to search for
variants you are interested in. The variants interface supports query by
various attributes of the family variants:

    - query by genome regions
    - query by genes and variant effect types
    - query by inheritance types
    - query by family IDs
    - query by person IDs
    - query by sexes
    - query by family roles
    - query by variant types
    - query by real value variant attributes (scores).
    - query using general purpose filter function

In the following examples we will assume that `fvars` is an instance of
family variants query interface that allows searching for variants by
various criteria.

Query by regions
^^^^^^^^^^^^^^^^

The query interface support searching of variants in given genome region or
list of regions.

:Example: The following example will return variants that are at one
    single position on chromosome `1:878109`:

    .. code-block:: python

        from dae.utils.regions import Region

        vs = fvars.query_variants(regions=[Region("1", 878109, 878109)])

    You can specify list of regions in the query:

    .. code-block:: python

        from dae.utils.regions import Region

        vs = fvars.query_variants(
            regions=[Region("1", 11539, 11539), Region("1", 11550, 11550)])


Query by genes and effect types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Example: The following example will return only variants with effect type
    `frame-shift`:

    .. code-block:: python

        vs = fvars.query_variants(
            effects=["frame-shift"])

    You can specify multiple effects in the query. The following example
    will return variants that with effect type `frame-shift` or `missense`:

    .. code-block:: python

        vs = fvars.query_variants(
            effects=["frame-shift", "missense"])


    You can search for variants in specific gene:

    .. code-block:: python

        vs = fvars.query_variants(
            genes=["PLEKHN1"])

    or list of genes:

    .. code-block:: python

        vs = fvars.query_variants(
            genes=["PLEKHN1", "SAMD11"])

    You can specifye combination of effect types and genes in which case the
    query will return only variants that match both criteria:


    .. code-block:: python

        vs = fvars.query_variants(
            effect_types=["synonymous", "frame-shift"],
            genes=["PLEKHN1"])


Query by inheritance
^^^^^^^^^^^^^^^^^^^^

:Example: The following example will return only variants that have inheritance
    type `denovo`:

    .. code-block:: python

        vs = fvars.query_variants(
            inheritance="denovo")

    You can inheritance type using `or`:

    .. code-block:: python

        vs = fvars.query_variants(
            inheritance="denovo or omission")

    You can use `not` to get all family variants that has non reference
    inheritance type:

    .. code-block:: python

        vs = fvars.query_variants(inheritance="not reference")


Query by family IDs
^^^^^^^^^^^^^^^^^^^

:Example: The following example will return only variants that affect
    specified families:

    .. code-block:: python

        vs = fvars.query_variants(family_ids=['f1', 'f2'])

    where `f1` and `f2` are family IDs.


Query by person IDs
^^^^^^^^^^^^^^^^^^^

:Example: The following example will return only variants that affect
    specified individuals:

    .. code-block:: python

        vs = fvars.query_variants(person_ids=['mom2', 'ch2'])

    where `mom2` and `ch2` are persons (individuals) IDs.


Query by sexes
^^^^^^^^^^^^^^

:Example: The following example will return only variants that affect
    male individuals:

    .. code-block:: python

        vs = fvars.query_variants(sexes="male")

    You can use `or` to combine sexes and `not` to negate. For example:

    .. code-block:: python

        vs = fvars.query_variants(sexes="male and not female")

    will return only family variants that affect male individuals in family, but
    not female.


Query by roles
^^^^^^^^^^^^^^

:Example: The following example will return only variants that affect
    probands in families:

    .. code-block:: python

        vs = fvars.query_variants(roles="prb")

    You can use `or`, `and` and `not` to combine roles. For example:

    .. code-block:: python

        vs = fvars.query_variants(roles="prb and not sib")

    will return only family variants that affect probands in family, but
    not siblings.


Query by variant types
^^^^^^^^^^^^^^^^^^^^^^

:Example: The following example will return only variants that are of type
    `sub`:

    .. code-block:: python

        vs = fvars.query_variants(variant_types="sub")

    You can use `or`, `and` and `not` to combine variant types. For example:

    .. code-block:: python

        vs = fvars.query_variants(roles="sub or del")

    will return only family variants that are of type `sub` or `del`.


Query with real value variant attributes (scores)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Not fully implemented yet*

Query with filter function
^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Not fully implemented yet*


Genomic Variants Classes and Functions
--------------------------------------

.. toctree::
   :maxdepth: 3

   modules/dae.variants


