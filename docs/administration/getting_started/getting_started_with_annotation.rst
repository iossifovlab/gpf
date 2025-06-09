Getting Started with Annotation
###############################

The import of genotype data into a GPF instance always runs the GPF
effect annotator.
It is easy to extend the annotation of genotype data during the import.

To define the annotation used during the import into a GPF instance, we have to
add a configuration that defines the pipeline of annotators and resources
to be used during the import.

In the `public GPF Genomic Resources Repository (GRR)
<https://grr.iossifovlab.com>`_
there is a collection of public genomic resources available for use with
GPF system.

Let's say that we want to annotate the genotype variants with
`GnomAD` and `ClinVar`. We need to find the appropriate resources in the
public GRR:

* ``hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL`` - this is
  an ``allele_score`` resource and the annotator by default
  produces one additional attribute ``gnomad_v4_genome_ALL_af`` that is the
  allele frequency for the variant (check the
  `hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
  <https://grr.iossifovlab.com/hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL/index.html>`_
  page for more information about the resource);

* ``hg38/scores/ClinVar_20240730`` - this is an ``allele_score``
  resource and the annotator by default produces two
  additional attribute ``CLNSIG`` that is the aggregate germline classification
  for the variant and ``CLNDN`` that is the preferred disease name (check the
  `hg38/scores/ClinVar_20240730 <https://grr.iossifovlab.com/hg38/scores/ClinVar_20240730/index.html>`_
  page for more information about the resource.

In order to use these resources in the GPF instance annotation, we need to
edit the GPF instance configuration (``minimal_instance/gpf_instance.yaml``)
and add lines 9-12 to it:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 9-12

    instance_id: minimal_instance

    reference_genome:
      resource_id: "hg38/genomes/GRCh38-hg38"

    gene_models:
      resource_id: "hg38/gene_models/MANE/1.3"

    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

When you start the GPF instance using the ``wgpf`` tool, it will automatically
re-annotate any genotype data that is not up to date:

.. code-block:: bash

    wgpf run

The variants in our `Example Dataset` will now have additional attributes
that come from the annotation with GnomAD and ClinVar:

- ``gnomad_v4_genome_ALL_af``
- ``CLNSIG``
- ``CLNDN``

By default, the additional attributes produced by the annotation are usable in 
the following ways:

* If you download the variants using the `Genotype Browser` download button,
  the additional attributes will be included in the downloaded file.

* We can query the variants using the ``gnomad_v4_genome_ALL_af``, ``CLNSIG`` 
  and ``CLNDN`` genomic scores.

Let's say we want to find all variants from `Example Dataset` that have gnomAD
frequency. Navigate to the `Genotype Browser` tab for the `Example Dataset`.
Select all checkboxes in the `Genotype Browser` filters. From the
`Genomic Score` filter selects the `gnomad_v4_genome_ALL_af` score.

.. figure:: getting_started_files/example-dataset-all-variants-with-gnomad-filter.png

    Genotype browser for `Example Dataset` with all filters selected

Then click on the `Download` button. This will download family variants matching
the selected filters in a tab-separated file similar to the one shown bellow.
Attributes from the annotation are included as the last columns in the
downloaded file.

.. csv-table::
    :file: ../getting_started_files/example-dataset-variants.tsv
    :delim: tab
    :header-rows: 1
    :align: left


.. note::

  The attributes produced by the annotation can be used in the
  `Genotype Browser` preview table as described in
  :ref:`getting_started_with_preview_columns`.

