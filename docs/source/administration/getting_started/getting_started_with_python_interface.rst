Example Usage of GPF Python Interface
#####################################

The simplest way to start using GPF's Python API is to import the
``GPFInstance`` class and instantiate it:

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

    ['ssc_pheno', 'mini_pheno']

To get a specific phenotype data and query it, use:

.. code-block:: python3

    pd = gpf_instance.get_phenotype_data("mini_pheno")

We can see what instruments and measures are available in the data:

.. code-block:: python3

    pd.instruments

.. code-block:: python3

    >> {'basic_medical': Instrument(basic_medical, 4), 'iq': Instrument(iq, 3)}


.. code-block:: python3

    pd.measures

.. code-block:: python3

    >> {'basic_medical.age': Measure(basic_medical.age, MeasureType.continuous, 1, 50),
        'basic_medical.weight': Measure(basic_medical.weight, MeasureType.continuous, 15, 250),
        'basic_medical.height': Measure(basic_medical.height, MeasureType.continuous, 30, 185),
        'basic_medical.race': Measure(basic_medical.race, MeasureType.categorical, african american, asian, white),
        'iq.diagnosis-notes': Measure(iq.diagnosis-notes, MeasureType.categorical, excels at school, originally diagnosed as Asperger, sleep abnormality, walked late),
        'iq.verbal-iq': Measure(iq.verbal-iq, MeasureType.continuous, 60, 115),
        'iq.non-verbal-iq': Measure(iq.non-verbal-iq, MeasureType.continuous, 45, 115)}

We can then get specific measure values for specific individuals:

.. code-block:: python3

    from dae.variants.attributes import Role

    list(pd.get_people_measure_values(["iq.non-verbal-iq"], roles=[Role.prb], family_ids=["f1", "f2", "f3"]))

.. code-block:: python3

    >> [{'person_id': 'f1.p1',
         'family_id': 'f1',
         'role': 'prb',
         'status': 'affected',
         'sex': 'M',
         'iq.non-verbal-iq': 70},
        {'person_id': 'f2.p1',
         'family_id': 'f2',
         'role': 'prb',
         'status': 'affected',
         'sex': 'F',
         'iq.non-verbal-iq': 45},
        {'person_id': 'f3.p1',
         'family_id': 'f3',
         'role': 'prb',
         'status': 'affected',
         'sex': 'M',
         'iq.non-verbal-iq': 93}]
