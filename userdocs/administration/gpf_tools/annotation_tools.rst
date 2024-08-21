Annotation tools
================

Three annotation tools are provided with GPF - ``annotate_columns``, ``annotate_vcf`` and ``annotate_schema2_parquet``.
Each of these handles a different format, but apart from some differences in the arguments that can be passed, they work in a similar way.
Across all three, input data and a pipeline configuration file are the mandatory arguments that must be provided.
Additionally, a number of optional arguments exist, which can be used to modify much of the behaviour of these tools.

All three tools are capable of parallelizing their workload, and will attempt to do so by default.

Notes on usage
##############

- When parallelizing is used, a directory for storing task flags and task logs will be created in your working directory. If you wish to re-run the annotation, it is necessary to remove this directory as the flags inside it will prevent the tasks from running.
- The option to reannotate data is provided. This is useful when you wish to modify only specific columns of an already annotated piece of data - for example to update a score column whose score resource has received a new version.
  To carry this out in the ``annotate_columns`` and ``annotate_vcf`` tools, you will have to use to provide the old annotation pipeline through the ``--reannotate`` flag. For ``annotate_schema2_parquet``, this is done automatically, as the annotation pipeline is stored in its metadata.

annotate_columns
################

This tool is used to annotate DSV (delimiter-separated values) formats - CSV, TSV, etc. It expects a header to be provided, from which it will attempt to identify relevant columns - chromosome, position, reference, alternative, etc.
If the file has been indexed using Tabix, the tool will parallelize its workload by splitting it into tasks by region size.

Example usage of annotate_columns
+++++++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_columns.py input.tsv annotation.yaml

Options for annotate_columns
++++++++++++++++++++++++++++

.. runblock:: console

    $ annotate_columns --help

annotate_vcf
############

This tool is used to annotate files in the VCF format.
If the file has been indexed using Tabix, the tool will parallelize its workload by splitting it into tasks by region size.

Example usage of annotate_vcf
+++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_vcf.py input.vcf.gz annotation.yaml

Options for annotate_vcf
++++++++++++++++++++++++

.. runblock:: console

    $ annotate_vcf --help

annotate_schema2_parquet
########################

This tool is used to annotate Parquet datasets partitioned according to GPF's ``schema2`` format. It expects a directory of the dataset as input.
The tool will always parallelize the annotation, unless explicitly disabled using the ``-j 1`` argument.

Unlike the other tools, reannotation will be carried out automatically if a previous annotation is detected in the dataset.

Example usage of annotate_schema2_parquet
+++++++++++++++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_schema2_parquet.py input_parquet_dir annotation.yaml

Options for annotate_schema2_parquet
++++++++++++++++++++++++++++++++++++

.. runblock:: console

    $ annotate_schema2_parquet --help
