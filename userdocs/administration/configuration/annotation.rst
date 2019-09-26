.. _annotation:

Annotation Configuration
========================

Annotation config files follow the INI file format and specify a list of
annotators and their options in the form of sections and properties.
The ``annotation.conf`` file which can be found in the data repository is
the default annotation config.

Each annotator is described in a single section. The name of the section
must be unique, but since it does not influence the annotation process, it
can be chosen freely. Lines starting with ``#`` are ignored.

All annotators are configured in a similar manner, using three main
properties - ``annotator``, ``options`` and ``columns``.
``annotator`` has a single value, but the other two properties
have sub-properties separated with a ``.``.

annotator
---------

.. code-block:: ini

  annotator = <annotator python file name>.<annotator class name>

This property indicates the type of the annotator.

=========================================== ===================================
Value                                       Description
=========================================== ===================================
annotator_base.CopyAnnotator                Duplicates the given columns.
cleanup_annotator.CleanupAnnotator          Removes the given columns from the
                                            output file.
dbnsfp_annotator.dbNSFPAnnotator            Annotate variants using scores from
                                            dbNSFP.
effect_annotator.VariantEffectAnnotator     Annotate variants with their
                                            effects.
frequency_annotator.FrequencyAnnotator      Annotate variants with a frequency
                                            score.
score_annotator.PositionScoreAnnotator      Annotate variants with a score file
                                            by the position/location of the
                                            variant.
score_annotator.PositionMultiScoreAnnotator Identical in function to
                                            PositionScoreAnnotator, but uses a
                                            directory with multiple score
                                            files.
score_annotator.NPScoreAnnotator            Annotate variants with a score file
                                            by the location *and* the type of
                                            the variant.
lift_over_annotator.LiftOverAnnotator       Create a column with the variant's
                                            location lifted over.
vcf_info_extractor.VCFInfoExtractor         Extract key-value pairs from a VCF
                                            file's INFO column as separate
                                            columns.
=========================================== ===================================

options.*
---------

.. code-block:: ini

  options.<option name> = value

These are custom options that will be passed to the annotator.
Each annotator provides different options that can be set.

.. FIXME
   Describe prom_len option of VariantEffectAnnotator

=================== =========================== ===============================
Option              Used by                     Description
=================== =========================== ===============================
scores_file         Variant annotators          The absolute path to the score
                                                file.
scores_config_file  Variant annotators          The absolute path to the score
                                                configuration file.
scores_directory    PositionMultiScoreAnnotator The absolute path to the
                                                directory containing the score
                                                files and their configs.
dbNSFP_path         dbNSFPAnnotator             The absolute path to the
                                                directory holding dbNSFP files,
                                                separated by chromosome.
dbNSFP_filename     dbNSFPAnnotator             A glob-like pattern of the
                                                generic dbNSFP file's name
                                                (e.g. dbNSFP_chr*).
dbNSFP_config       dbNSFPAnnotator             The name (not absolute path) of
                                                the score config inside the
                                                dbNSFP directory.
Graw                VariantEffectAnnotator      The absolute path to the genome
                                                file.
Traw                VariantEffectAnnotator      The absolute path to the gene
                                                models file.
chain_file          LiftOverAnnotator           The absolute path to the
                                                liftover chain to be used.
=================== =========================== ===============================

columns.*
---------

.. code-block:: ini

  columns.<raw/original column name> = <output column name>

This option simultaneously describes which columns must be added to
the output file and what their name will be. The pool of available
columns is determined by the annotator - for example, a copy annotator's
pool of available columns is the input file's own columns, while an annotator
that uses a score file will have the score file's columns available.

The following are some special cases, used by certain annotators.

================ ================ =============================================
Columns          Used by          Description
================ ================ =============================================
columns.cleanup  CleanupAnnotator Comma-separated list of columns to remove.
columns.*        CopyAnnotator    The pool of available columns are all columns
                                  in the input file.
columns.*        VCFInfoExtractor The pool of available columns are all keys in
                                  the INFO column.
================ ================ =============================================
