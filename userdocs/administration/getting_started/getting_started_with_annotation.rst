Getting Started with Annotation
###############################

The import of genotype data into a GPF instance always runs effect annotation.
It is easy to extend the annotation of genotype data during the import.

To define the annotation used during the import into a GPF instance we have to
add a configuration that defines the pipeline of annotators and resources
to be used during the import.

In the `public GPF Genomic Resources Repository (GRR)
<https://iossifovlab.com/distribution/public/genomic-resources-repository/>`_
there is a collection of public genomic resources available for use with
GPF system.

Let say that we want to annotate the genotype variants with
`GnomAD` and `ClinVar`. We need to find the appropriate resources in the
public GRR:

* ``hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL`` - this is
  an ``allele_score`` resource and the annotator by default
  produces one additional attribute ``gnomad_v4_genome_ALL_af`` that is the
  allele frequency for the variant (check the
  `hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL <https://grr.iossifovlab.com/hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL/index.html>`_
  page for more information about the resource);

* ``hg38/scores/ClinVar_20240730`` - this is an ``allele_score``
  resource and the annotator by default produces two
  additional attribute ``CLNSIG`` that is the aggregate germline classification
  for the variant and ``CLNDN`` that is preferred disease name (check the
  `hg38/scores/ClinVar_20240730 <https://grr.iossifovlab.com/hg38/scores/ClinVar_20240730/index.html>`_
  page for more information about the resource).

In order to use these resources in the GPF instance annotation, we need to
edit the GPF instance configuration (``minimal_instance/gpf_instance.yaml``)
and add the following snipped the configuration file:

.. code-block:: yaml

    # The annotation pipeline configuration to use. Uncomment to enable.
    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

Re-running GPF will automatically re-annotate any genotype data that is not up
to date:

.. code-block:: bash

    wgpf run

The variants in our ``Example Dataset`` will now have additional attributes
that come from the annotation with GnomAD and ClinVar:

- ``gnomad_v4_genome_ALL_af``;
- ``CLNSIG``;
- ``CLNDN``.

If we browse our ``Example Dataset`` there is almost no difference.
The only difference is that now in the
genotype browser, the genomic scores section is not empty and we can query
our variants using the ``gnomad_v4_genome_ALL_af``, ``CLNSIG`` and ``CLNDN``
genomic scores.

.. figure:: getting_started_files/example-dataset-genotype-browser-gnomics-scores.png

    Genotype browser using GnomAD and ClinVar genomic scores

.. note::

    The attributes produced by the annotation can be used in the
    `Genotype Browser` preview table as described in
    :ref:`getting_started_with_preview_columns`.
