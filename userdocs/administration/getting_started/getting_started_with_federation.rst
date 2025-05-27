Getting Started with Federation
###############################

Federation is a mechanism that allows you to combine multiple GPF instances
into a single system. This allows you to share data and resources across
multiple GPF instances, enabling you to work with larger datasets and
collaborate with other researchers more effectively.

In this section, we will show you how to set up a federation between the
SFARI GPF instance and your local GPF instance. This will allow you to access
the data and resources you have access to on the SFARI GPF instance from your
local GPF instance.


Configure federation on your local GPF instance
+++++++++++++++++++++++++++++++++++++++++++++++

To use the GPF federation, you need to install the additional
``gpf_federation`` conda package in your local conda environment. You can do
this by running the following command:

.. code-block:: bash

    mamba install \
        -c conda-forge \
        -c bioconda \
        -c iossifovlab \
        gpf_federation

Once the package is installed, you need to configure the federation on your
local GPF instance. You can do this by editing the
``minimal_instacne/gpf_instance.yaml`` file:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 31-34

    instance_id: minimal_instance

    reference_genome:
      resource_id: "hg38/genomes/GRCh38-hg38"

    gene_models:
      resource_id: "hg38/gene_models/MANE/1.3"

    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

    gene_sets_db:
      gene_set_collections:
      - gene_properties/gene_sets/autism
      - gene_properties/gene_sets/relevant
      - gene_properties/gene_sets/GO_2024-06-17_release

    gene_scores_db:
      gene_scores:
      - gene_properties/gene_scores/Satterstrom_Buxbaum_Cell_2020
      - gene_properties/gene_scores/Iossifov_Wigler_PNAS_2015
      - gene_properties/gene_scores/LGD
      - gene_properties/gene_scores/RVIS
      - gene_properties/gene_scores/LOEUF

    gene_profiles_config:
      conf_file: gene_profiles.yaml

    remotes:
      - id: "sfari"
        host: "gpf.sfari.org"
        gpf_prefix: "hg38"


.. note::

    This configuration will allow your local
    instance to access only the publicly available resources in
    the SFARI GPF instance.

    In case you have a user account on the SFARI GPF instance, you can
    create federation tokens and use them to access the remote instance
    as described in the :ref:`Federation tokens`.


When you are ready with the configuration, you can start the GPF instance using
the ``wgpf`` tool:

.. code-block:: bash

    wgpf run

On the home page of your local GPF instance, you should see studies loaded from
the SFARI remote instance in the `Home Page`:

.. figure:: getting_started_files/federation_home_page.png

   Home page with studies from the SFARI GPF instance

.. warning::

   The federation loads a lot of data from the remote instance. When
   you start the GPF instance, it may take some time to load all the needed
   information.

Combine analysis using local and remote studies
+++++++++++++++++++++++++++++++++++++++++++++++

Having the federation configured, you can explore local and remote studies.
Moreover, you can combine local and remote studies using the available
tools.

For example, let's go to the `ssc_denovo` and select the `Enrichment Tool`.
From `Gene Sets` choose `Denovo`:

.. figure:: getting_started_files/federation_enrichment_tool.png

   Enrichment Tool for `ssc_denovo` study

Then from the studies hierarchy choose `(sfari) Sequencing de Novo /
(sfari) SD Autism / (sfari) SD SPARK Autism /
(sfari) SD iWES_v1_1_genotypes_DENOVO`
study and select the `autism` phenotype.

.. figure:: getting_started_files/federation_enrichment_tool_denovo_gene_set.png

   Enrichment Tool for `ssc_denovo` study with selected remote study de Novo
   gene sets

Now you can choose a de Novo gene set computed for the remote study
`SD_iWES_v1_1_genotypes_DENOVO`:

.. figure:: getting_started_files/federation_enrichment_tool_iwes_denovo_gene_sets.png

    De Novo gene set from SD_iWES_v1_1_genotypes_DENOVO study

Let us select the LGDs de Novo gene set and run the `Enrichment Tool`:

.. figure:: getting_started_files/federation_enrichment_tool_results.png

   Enrichment Tool for `ssc_denovo` result page


Federation tokens
+++++++++++++++++

Federation tokens are used to authenticate and authorize access to the
federated GPF instance.

Let us create a federation token for the SFARI GPF instance. You need to log in
to the SFARI GPF instance, go to *User Profile*, select *Federation Tokens*,
and create a new federation token:

.. figure:: getting_started_files/federation_client_id_and_secret.png

   Federation client ID and secret from the `User Profile`


.. warning::

   The federation client ID and secret are shown only once. Make sure to
   copy them to a safe place. You will need them to configure the federation
   on your local GPF instance.

Once you have the federation client ID and secret, you can configure your local
GPF instance to use them. You need to edit the
``minimal_instacne/gpf_instance.yaml`` file and add the lines 5-6 to the
``remotes`` section:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 5-6

    remotes:
      - id: "sfari"
        host: "gpf.sfari.org"
        gpf_prefix: "hg38"
        client_id: "Tqtgr2e3YPiDQS6CHvMdH7rPgTnxmoA46OWSbagV"
        client_secret: "22xKTkewcxyTnKdHou21LRikUU2Hea2tLRBBOaPm2UCIUWEqZFogWk0nRysDrXepieOWYUkTZvG1xVULtwEspWG2YQ71lH7Vow7dNTMzG9ELdVQcOY8YQOD3y9XwRw8T"

This will allow your local GPF instance to have access to the resources in
SFARI GPF instance that you have access to.

.. warning::

    The federation client ID and secret in the example above are
    placeholders and should not be used. You need to replace them with
    your own federation client ID and secret.
