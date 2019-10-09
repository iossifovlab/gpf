annotation_pipeline
===================

Annotation pipeline is a tool for annotating data.

The :ref:`annotation_pipeline.py` help
--------------------------------------

The tool has a help info that can be shown using -h/--help option on the
command line.::

    usage: annotation_pipeline.py [-h] [-H] --config CONFIG [--always-add]
                                  [--region REGION] [--split SPLIT]
                                  [--separator SEPARATOR]
                                  [--options =OPTION:VALUE] [--skip-preannotator]
                                  [-a A] [-c C] [--Graw GRAW] [--vcf] [-v V]
                                  [-p P] [-r R] [-x X]
                                  [infile] [outfile]

    Program to annotate variants combining multiple annotating tools

    positional arguments:
      infile                path to input file; defaults to stdin
      outfile               path to output file; defaults to stdout

    optional arguments:
      -h, --help            show this help message and exit
      -H                    no header in the input file
      --config CONFIG       config file location
      --always-add          always add columns; default behavior is to replace
                            columns with the same label
      --region REGION       region to annotate (chr:begin-end) (input should be
                            tabix indexed)
      --split SPLIT         split variants based on given column
      --separator SEPARATOR
                            separator used in the split column; defaults to ","
      --options =OPTION:VALUE
                            add default arguments
      --skip-preannotator   skips preannotators
      -a A                  alternative column number/name
      -c C                  chromosome column number/name
      --Graw GRAW           genome file location
      --vcf                 if the variant position is in VCF semantics
      -v V                  variant (CSHL format) column number/name
      -p P                  position column number/name
      -r R                  reference column number/name
      -x X                  location (chr:position) column number/name

Typical invocation of `annotation_pipeline.py`
----------------------------------------------

To start `annotation_pipeline.py` you should pass some required parameters:

    * using ``--config`` option the user should pass the path of config file

Example annotating of de novo data with `annotation_pipeline.py`::

    ./annotation_pipeline.py --config file.conf input_file output_file

or::

    ./annotation_pipeline.py --config file.conf -x location -v variant input_file output_file

Example annotating of transmission data with `annotation_pipeline.py`::

    ./annotation_pipeline.py --config file.conf -c chromosome -p position input_file output_file

Example annotating of VCF data with `annotation_pipeline.py`::

    ./annotation_pipeline.py --config file.conf --vcf -c chromosome -p position -r reference -a alternative input_file output_file

We need `-x`, `-v`, `-c`, `-p`, `-r`, `-a`, `--vcf` options to describe the
input format so that we can support multiple formats. Preannotators use these
arguments to generate virtual columns.


Configuration file
------------------

Configuration file contain sections for different operations which contain
options for annotating data

Example annotation pipeline configuration file::

    # comment

    # DEFAULT section is to define variables who will be used in config file
    [DEFAULT]
    data_dir=/data-dir
    genome_dir=%(data_dir)s/genomes/GATK_ResourceBundle_5777_b37_phiX174
    graw=%(genome_dir)s/chrAll.fa
    traw=%(genome_dir)s/refGene-201309.gz

    ################################
    # Section name
    [Step-Effects]

    # Annotator class. Complete list of annotators can be seen below in dae.annotation.tools module
    annotator=annotate_variants.EffectAnnotator

    # Annotator options. Complete list of option for annotators can be seen below in dae.annotation.tools module
    options.c=CSHL:chr
    options.p=CSHL:position
    options.v=CSHL:variant
    options.Graw=%(graw)s
    options.Traw=%(traw)s

    # columns.<column_in_input>=<new_column_in_output> With columns you say to annotation_pipeline which columns to use in annotation and new labels of these columns.
    columns.effect_type=effectType
    columns.effect_gene=effectGene
    columns.effect_details=effectDetails

    ################################
    [Step-SSC-Frequency]

    annotator=annotateFreqTransm.FrequencyAnnotator

    options.c=CSHL:chr
    options.p=CSHL:position
    options.v=CSHL:variant
    options.scores_file=%(data_dir)s/cccc/w1202s766e611/transmissionIndex-HW-DNRM.txt.bgz
    options.direct = True

    columns.score=SSC-freq

    # with virtual_columns anotation_pipeline add new column which removes after annotation
    virtual_columns = score


Add Annotator or Preannotator
-----------------------------

To create `Annotator` or `Preannotator` you need to create a class who inherits
`dae.annotation.utilities.AnnotatorBase`. That class must implements methods
`new_columns()` and `line_annotations(line, new_columns)`. `new_columns` must
be a @property method who returns names of new columns, `line_annotations` must
be a method who takes `line` and `new_columns` and returns a list of values for
new_columns.

`Annotator` directory is `annotation/tools`. Except annotator you need to add
`get_argument_parser()` function and you must call `main` function from
`utilities` in annotator file. `get_argument_parser()` function must return an
argument parser with annotator options. `utilities.main()` function takes two
params first is argument parser and second is `Annotator`.
`Preannotator` directory is `annotation/preannotators`. Except preannotator you
need to add `get_arguments()` function in preannotator file. This function must
return dictionary with preannotator options. When you add preannotator in this
directory it is found by `MultiAnnotator` class.

dae.annotation.annotation_pipeline module
----------------------------------------------

.. automodule:: dae.annotation.annotation_pipeline
    :members:
    :undoc-members:
    :show-inheritance:

.. dae.annotation.preannotators module
.. -------------------------------

.. dae.annotation.preannotators.variant_format module
.. ++++++++++++++++++++++++++++++++++++++++++++++

.. .. automodule:: dae.annotation.preannotators.variant_format
..     :members:
..     :undoc-members:
..     :show-inheritance:

dae.annotation.tools module
---------------------------

dae.annotation.tools.annotator_base module
++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.annotator_base
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.annotator_config module
++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.annotator_config
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.cleanup_annotator module
+++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.cleanup_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.dbnsfp_annotator module
++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.dbnsfp_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.effect_annotator module
++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.effect_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.file_io_parquet module
+++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.file_io_parquet
    :members:
    :undoc-members:
    :show-inheritance:


dae.annotation.tools.file_io_tsv module
+++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.file_io_tsv
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.file_io module
+++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.file_io
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.frequency_annotator module
+++++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.frequency_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.lift_over_annotator module
+++++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.lift_over_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.schema module
++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.schema
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.score_annotator module
+++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.score_annotator
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.score_file_io_bigwig module
++++++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.score_file_io_bigwig
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.score_file_io module
+++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.score_file_io
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.utils module
+++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.utils
    :members:
    :undoc-members:
    :show-inheritance:

dae.annotation.tools.vcf_info_extractor module
++++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dae.annotation.tools.vcf_info_extractor
    :members:
    :undoc-members:
    :show-inheritance:
