
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

        from RegionOperations import Region

        vs = fvars.query_variants(regions=[Region("1", 878109, 878109)])

    You can specify list of regions in the query:

    .. code-block:: python

        from RegionOperations import Region

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
