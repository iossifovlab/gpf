Getting Started with Annotation
###############################

The import of genotype data into a GPF instance always runs effect annotation.
It is easy to extend the annotation of genotype data during the import.

To define the annotation used during the import into a GPF instance we have to
add a configuration that defines the pipeline of annotators and resources
to be used during the import.

There is a `public Genomic Resources Repository (GRR)
<https://iossifovlab.com/distribution/public/genomic-resources-repository/>`_
with a collection of public genomic resources available for use with
GPF system.

Example: Annotation with GnomAD 4.1.0 and ClinVar
+++++++++++++++++++++++++++++++++++++++++++++++++

To annotate the genotype variants with `GnomAD` and `ClinVar` allele 
frequencies, we should
find the GnomAD and ClinVar genomic resources in our public GRR. We will choose
to use the following resources:

* ``hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL``
* ``hg38/scores/ClinVar_20240730``

If we navigate to their resource pages, we will see that both resources
are of the ``allele_score`` type.
So in order to use it in the annotation, we will use the 
``allele_score`` annotator.

Edit the GPF instance configuration (``minimal_instance/gpf_instance.yaml``) to use this
annotation configuration by uncommenting the following lines:

.. code-block:: yaml

    # The annotation pipeline configuration to use. Uncomment to enable.
    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

Re-running GPF will automatically re-annotate any data that is not up to date:

.. code-block:: bash
  
    wgpf run

The variants in our ``Example Dataset`` will now have additional attributes that
come from the annotation with GnomAD and ClinVar. By default, the annotation 
adds the following attributes:

- ``gnomad_v4_genome_ALL_af`` - allele frequencies as a percent;
- ``CLNSIG`` - germline classification for variant;

If we browse our ``Example Dataset`` there is almost no difference.
The only difference is that now in the
genotype browser, the genomic scores section is not empty and we can query
our variants using the ``gnomad_v4_genome_ALL_af`` and ``CLNSIG`` genomic scores.

.. image:: getting_started_files/helloworld-gnomad-annotation-with-genomic-scores-filter.png

