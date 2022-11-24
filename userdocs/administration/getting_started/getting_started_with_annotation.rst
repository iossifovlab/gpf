Getting Started with Annotation
###############################

The import of genotype data into a GPF instance always runs effect annotation.
It is easy to extend the annotation of genotype data during the import.

To define the annotation used during the import into a GPF instance we have to add
a configuration file that defines the pipeline of annotators. After that,
we need to configure the GPF instance to use this annotation pipeline.

There is a `public Genomic Resources Repository (GRR)
<https://iossifovlab.com/distribution/public/genomic-resources-repository/>`_
with a collection of public genomic resources available for use with
GPF system.

Example: Annotation with GnomAD 3.0
+++++++++++++++++++++++++++++++++++

To annotate the genotype variants with `GnomAD` allele frequencies we should
find the GnomAD genomic resource in our public GRR. We will choose to use
``hg38/variant_frequencies/gnomAD_v3/genomes`` resource. If we navigate
to the resource page we will see that this is an ``allele_score`` resource.
So to use it in the annotation we should use the ``allele_score`` annotator.

The minimal configuration of annotation with this GnomAD resource is the 
following:

.. code-block:: yaml

    - allele_score: hg38/variant_frequencies/gnomAD_v3/genomes

Store this annotation configuration in a file named ``annotation.yaml`` and
configure the GPF instance to use this annotation configuration:

.. code-block:: yaml

    reference_genome:
      resource_id: "hg38/genomes/GRCh38-hg38"
    
    gene_models:
      resource_id: "hg38/gene_models/refSeq_v20200330"
    
    annotation:
      conf_file: annotation.yaml

Now we can re-run the import for our ``helloworld`` examples:

* Go to the ``denovo-helloworld`` project directory and re-run the import:

  .. code-block:: bash
  
      import_tools -f denovo_helloworld.yaml
  
* Go to the ``vcf-helloworld`` project directory and re-run the import:

  .. code-block:: bash
  
      import_tools -f vcf_helloworld.yaml

Once the re-import finishes, the variants in our ``Hello World Dataset`` have
additional attributes that come from the annotation with ``GnomAD v3.0``. By
default annotation adds the following three attributes:

- ``genome_gnomad_v3_af_percent`` - allele frequencies as a percent;
- ``genome_gnomad_v3_ac`` - allele count;
- ``genome_gnomad_v3_an`` - number of sequenced alleles.

If we run the GPF development server and browse our ``Hello World Dataset``
there are almost no difference. The only difference is that now in the
genotype browse the genomic scores section is not empty and we can query
our variants using the ``genome_gnomad_v3_af_percent`` genomic score.

.. image:: getting_started_files/helloworld-gnomad-annotation-with-genomic-scores-filter.png

To make the new annotation attributes available in the variants preview table
and in the variants download we need to change the study configuration. Check
the `Getting Started with Preview and Download Columns`_ section for 
additional information.
