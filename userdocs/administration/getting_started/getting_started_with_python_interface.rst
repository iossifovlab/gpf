Example Usage of GPF Python Interface
#####################################

The simplest way to start using GPF's Python API is to import the ``GPFInstance``
class and instantiate it:

.. code-block:: python3

    from dae.gpf_instance.gpf_instance import GPFInstance
    gpf_instance = GPFInstance.build()

This ``gpf_instance`` object groups together a number of objects, each dedicated
to managing different parts of the underlying data. It can be used to interact
with the system as a whole.

For example, to list all studies configured in the startup GPF instance, use:

.. code-block:: python3

    gpf_instance.get_genotype_data_ids()

This will return a list with the IDs of all configured studies:

.. code-block:: python3

    ['denovo_example',
     'vcf_example',
     'example_dataset']

To get a specific study and query it, you can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('example_dataset')
    vs = list(st.query_variants())

.. note::
    The ``query_variants`` method returns a Python iterator.

To get the basic information about variants found by the ``query_variants`` method,
you can use:

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