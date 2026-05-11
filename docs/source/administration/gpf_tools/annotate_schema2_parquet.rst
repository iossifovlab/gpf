annotate_schema2_parquet
========================

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
