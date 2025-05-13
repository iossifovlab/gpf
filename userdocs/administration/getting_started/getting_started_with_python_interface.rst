Example Usage of GPF Python Interface
#####################################

The simplest way to start using GPF's Python API is to import the ``GPFInstance``
class and instantiate it:

.. code-block:: python3

    from dae.gpf_instance.gpf_instance import GPFInstance
    gpf_instance = GPFInstance.build()

This ``gpf_instance`` object groups several interfaces, each dedicated
to managing different parts of the underlying data. It can be used to interact
with the system as a whole.

Querying genotype data
++++++++++++++++++++++

For example, to list all studies configured in the startup GPF instance, use:

.. code-block:: python3

    gpf_instance.get_genotype_data_ids()

This will return a list with the IDs of all configured studies:

.. code-block:: python3

    ['ssc_denovo', 'denovo_example', 'vcf_example', 'ssc_cnv', 'example_dataset']

To get a specific study and query it, you can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('example_dataset')
    vs = list(st.query_variants())

.. note::
    The ``query_variants`` method returns a Python iterator.

To get the basic information about variants found by the ``query_variants``
method, you can use:

.. code-block:: python3

    for v in vs:
        for aa in v.alt_alleles:
            print(aa)

will produce the following output:

.. code-block:: python3

    chr14:21391016 A->AT f2
    chr14:21393484 TCTTC->T f2
    chr14:21402010 G->A f1
    chr14:21403019 G->A f2
    chr14:21403214 T->C f1
    chr14:21431459 G->C f1
    chr14:21385738 C->T f1
    chr14:21385738 C->T f2
    chr14:21385954 A->C f2
    chr14:21393173 T->C f1
    chr14:21393702 C->T f2
    chr14:21393860 G->A f1
    chr14:21403023 G->A f1
    chr14:21403023 G->A f2
    chr14:21405222 T->C f2
    chr14:21409888 T->C f1
    chr14:21409888 T->C f2
    chr14:21429019 C->T f1
    chr14:21429019 C->T f2
    chr14:21431306 G->A f1
    chr14:21431623 A->C f2
    chr14:21393540 GGAA->G f1

The ``query_variants`` interface allows you to specify what kind of variants
you are interested in. For example, if you only need "synonymous" variants, you
can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('example_dataset')
    vs = st.query_variants(effect_types=['synonymous'])
    vs = list(vs)
    len(vs)

.. code-block:: python3

    >> 4

Or, if you are interested in "synonymous" variants only in people with
"prb" role, you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['synonymous'], roles='prb')
    vs = list(vs)
    len(vs)

.. code-block:: python3

    >> 1

Querying phenotype data
+++++++++++++++++++++++

To list all available phenotype data, use:

.. code-block:: python3

    gpf_instance.get_phenotype_data_ids()

This will return a list with the IDs of all configured phenotype data:

.. code-block:: python3

    ['mini_pheno']

To get a specific phenotype data and query it, use:

.. code-block:: python3

    pd = gpf_instance.get_phenotype_data("comp_pheno")

We can see what instruments and measures are available in the data:

.. code-block:: python3

    pd.instruments

    >> {'i1': Instrument(i1, 7)}

.. code-block:: python3

    pd.measures

    >> {'i1.age': Measure(i1.age, MeasureType.continuous, [68.00148724003327, 606.2292731817272]),
        'i1.iq': Measure(i1.iq, MeasureType.continuous, [-11.109304318239424, 174.2897342432941]),
        'i1.m1': Measure(i1.m1, MeasureType.continuous, [28.876821569323646, 143.02866815069675]),
        'i1.m2': Measure(i1.m2, MeasureType.continuous, [17.650256211303596, 69.72059461639753]),
        'i1.m3': Measure(i1.m3, MeasureType.continuous, [20.34949100410408, 122.8324621617449]),
        'i1.m4': Measure(i1.m4, MeasureType.continuous, [0, 10]),
        'i1.m5': Measure(i1.m5, MeasureType.categorical, val1, val2, val3, val4, val5)}

We can then get specific measure values for specific individuals:

.. code-block:: python3

    from dae.variants.attributes import Role

    list(pd.get_people_measure_values(["i1.iq"], roles=[Role.prb], family_ids=["f1", "f2", "f3"]))

    >> [{'person_id': 'f1.p1',
         'family_id': 'f1',
         'role': 'prb',
         'status': 'affected',
         'sex': 'M',
         'i1.iq': 104.9118881225586},
        {'person_id': 'f2.p1',
         'family_id': 'f2',
         'role': 'prb',
         'status': 'affected',
         'sex': 'M',
         'i1.iq': 66.6941146850586},
        {'person_id': 'f3.p1',
         'family_id': 'f3',
         'role': 'prb',
         'status': 'affected',
         'sex': 'M',
         'i1.iq': 69.3330078125}]