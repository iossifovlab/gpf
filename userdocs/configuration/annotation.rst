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

  annotator = {annotator python file name}.{annotator class name}

This property indicates the type of the annotator.

=========================================== ===========
Value                                       Description
=========================================== ===========
annotator_base.CopyAnnotator                todo
cleanup_annotator.CleanupAnnotator          todo
dbnsfp_annotator.dbNSFPAnnotator            todo
effect_annotator.VariantEffectAnnotator     todo
frequency_annotator.FrequencyAnnotator      todo
score_annotator.PositionScoreAnnotator      todo
score_annotator.PositionMultiScoreAnnotator todo
score_annotator.NPScoreAnnotator            todo
=========================================== ===========

options.*
---------

.. code-block:: ini

  options.{option name} = value

These are custom options that will be passed to the annotator.
Each annotator provides different options that can be set.

=========================================== ======= ===========
Option                                      Used by Description
=========================================== ======= ===========
todo                                        todo    todo
=========================================== ======= ===========

columns.*
---------

.. code-block:: ini

  columns.{raw/original column name} = {output column name}

This option simultaneously describes which columns must be added to
the output file and what their name will be. The pool of available
columns is determined by the annotator - for example, a copy annotator's
pool of available columns is the input file's own columns, while an annotator
that uses a score file will have the score file's columns available.
