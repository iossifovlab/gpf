Getting Started with Federation
###############################

Federation is a mechanism that allows you to combine multiple GPF instances
into a single system. This allows you to share data and resources across
multiple GPF instances, enabling you to work with larger datasets and
collaborate with other researchers more effectively.

In this section, we will show you how to set up a federation between  SFARI GPF
instance and your local GPF instance. This will allow you to access the data
and resources available on the SFARI GPF instance from your local GPF instance.

Federation tokens
+++++++++++++++++

Federation tokens are used to authenticate and authorize access to the
federated GPF instance.

Let us create a federation token for the SFARI GPF instance. You need to Log in
to the SFARI GPF instance, go to *User Profile*, select *Federation Tokens*,
and create a new federation token:

.. figure:: getting_started_files/federation_client_id_and_secret.png

   Federation client ID and secret from the `User Profile`


.. warning::

   The federation client ID and secret are shown only once. Make sure to
   copy them to a safe place. You will need them to configure the federation
   on your local GPF instance.


Configure federation on your local GPF instance
+++++++++++++++++++++++++++++++++++++++++++++++

To use the GPF federation, you need to install addigional ``gpf_federation``
conda package in your local conda environment. You can do this by running the
following command:

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
    :emphasize-lines: 31-36

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
        client_id: "Tqtgr2e3YPiDQS6CHvMdH7rPgTnxmoA46OWSbagV"
        client_secret: "22xKTkewcxyTnKdHou21LRikUU2Hea2tLRBBOaPm2UCIUWEqZFogWk0nRysDrXepieOWYUkTZvG1xVULtwEspWG2YQ71lH7Vow7dNTMzG9ELdVQcOY8YQOD3y9XwRw8T"


.. note::

   The `client_id` and `client_secret` values are the federation client ID
   and secret that you created in the previous step. Make sure to replace
   them with the actual values.

.. note::

    If you don't have a user account on the SFARI GPF instance, you can
    skip the ``client_id`` and ``client_secret`` lines. In this case your local
    instance will be able to access only the publicly available resources in
    the SFARI GPF instance.

When you are ready with the configuration, you can start the GPF instance using
the ``wgpf`` tool:

.. code-block:: bash

    wgpf run

In the home page of your local GPF instance, you should see studies loaded from
the ``sfari`` remote instance in the `Home Page`:

.. figure:: getting_started_files/federation_home_page.png

   Home page with studies from the SFARI GPF instance

.. note::

    The federation shows only the studies that you have access to.

.. warning::

   The federation loads a lot of data from the remote instance. When
   you start the GPF instance, it may take some time to load all the needed
   information.

Combine analysis using local and remote studies
+++++++++++++++++++++++++++++++++++++++++++++++

Having the federation configured, you can explore local and remote studies.
Moreover, you can combine local and remote studies using the available
tools.

For example, let us go to the `ssc_denovo` and select `Enrichment Tool`. From
`Gene Sets` choose `Denovo`:

.. figure:: getting_started_files/federation_enrichment_tool.png

   Enrichment Tool for `ssc_denovo` study

Then from the studies hierarchy choose `(sfari) SPARK Consortium iWES v1.1`
study and select `autism` phenotype.

.. figure:: getting_started_files/federation_enrichment_tool_denovo_gene_set.png

   Enrichment Tool for `ssc_denovo` study with selected remote study de Novo
   gene sets

Now you can choose a de Novo gene set computed for the remote study `SPARK
Consortium iWES v1.1`:

.. figure:: getting_started_files/federation_enrichment_tool_iwes_denovo_gene_sets.png

    De Novo gene set from SPARK Consortium iWES v1.1 study

Let us select the LGDs de Novo gene set and run the `Enrichment Tool`:

.. figure:: getting_started_files/federation_enrichment_tool_results.png

   Enrichment Tool for `ssc_denovo` result page
