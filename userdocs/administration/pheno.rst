Phenotype Database Tools
========================

Importing a phenotype database for use with the GPF system can be done either with an import project configuration or
with the help of the ``pheno_import`` tool.

Either of these will produce a DuckDB database containing the phenotype data.

Importing via import project configuration
******************************************

The import project configuration is a YAML-formatted text file which describes how the phenotype data should be imported.
This configuration is then passed to the ``import_tools_pheno`` CLI tool, which will take care of carrying out the import.

Import project configuration format
###################################

* ``id`` - the name of the produced DB file and the phenotype data ID which will be generated.
* ``input_dir`` - the root directory to which all other paths in the config (with the exception of ``output_dir``) are considered relative to.
* ``output_dir`` - the directory in which to produce the output.
* ``instrument_files`` - a list of paths to instrument files and/or directories that contain instrument files. Shell-like wildcards with ``*`` can be used.
* ``pedigree`` - path to the pedigree file to use for import.
* ``person_column`` - the name of the column containing the person ID in the instrument CSV files. All files are expected to use the same column name for person IDs.
* ``tab_separated`` - whether the instrument files use tabs for delimiters. The default value is ``False``.
* ``skip_pedigree_measure`` - flag to skip the building of the pheno common instrument. The default value is ``False``.
* ``data_dictionary`` - a nested configuration specifying the sources for measure descriptions. Optional.
* ``inference_config`` - the configuration to use for measure type inference. Can be either a path to a YAML-formatted configuration file or a directly embedded configuration. Optional.
* ``regression_config`` - the configuration to use for building regressions. Can be either a path to a YAML or TOML-formatted configuration file or a directly embedded configuration. Optional.

Data dictionary config fields
+++++++++++++++++++++++++++++

* ``file`` - path to a data dictionary file. Optional.
* ``instrument_files`` - list of paths to separate data dictionary files. Optional.
* ``dictionary`` - directly-embedded data dictionary. Optional.

If the same measure is found in multiple sources, the priority is in the following order: ``dictionary``, ``instrument_files``, ``file``.

Regression config fields
++++++++++++++++++++++++

* ``instrument_name``
* ``measure_name``
* ``jitter``
* ``display_name``

Inference config fields
+++++++++++++++++++++++

For further information about each field, see :ref:`Measure classification` and :ref:`Inference parameters`.

* ``min_individuals``
* ``non_numeric_cutoff``
* ``value_max_len``
* ``continuous``
* ``ordinal``
* ``categorical``
* ``skip``
* ``value_type``
* ``histogram_type``

Example import project configuration
++++++++++++++++++++++++++++++++++++

.. code:: yaml

    id: pheno_data_id
    input_dir: /home/user/pheno_data
    instrument_files:
      - work/instruments
      - work/some_instrument.csv
      - work/more_instruments/**/*.txt
    pedigree: work/pedigree.ped
    person_column: subject_id
    tab_separated: False
    skip_pedigree_measures: False
    data_dictionary:
      file: work/data_dictionary.csv
      instrument_files:
        - work/instruments/data_dict_1.csv
        - work/instruments/data_dict_2.csv
      dictionary:
        instrument_1:
          measure_1: "description of a measure"
        instrument_2:
          measure_2: "another description of a measure"
    inference_config: work/inference.conf
    regression_config:
      age:
        display_name: age
        instrument_name: pheno_common
        jitter: 0.1
        measure_name: age_measure
      measure_1:
        display_name: measure number one
        instrument_name: instrument_1
        jitter: 0.1
        measure_name: measure_1
    output_dir: /home/user/pheno_result


Running the ``import_tools_pheno`` CLI tool
###########################################

The ``import_tools_pheno`` tool accepts the YAML-formatted import project configuration,
as well as parameters relating to the usage of Dask:

.. runblock:: console

    $ import_tools_pheno --help


Importing via ``pheno_import`` tool
***********************************

Alternatively, the ``pheno_import`` CLI tool can be used to import phenotype data. It takes a number of parameters
to describe and configure the data being imported, but is less flexible compared to the import project configuration.

To import a phenotype database, you will need the following files:

* A pedigree file which contains information regarding evaluated individuals and their family.
* A directory containing instruments in the form of CSV (default) or TSV files (using the ``-T`` option).
* A data dictionary in the form of a TSV file. (Optional)
* A configuration for phenotype regressions. (Optional)

To import the phenotype database into the GPF system you need to use the
``pheno_import`` tool:

.. code:: bash

    pheno_import \
        -p pedigree.ped \
        -i instruments/ \
        --data-dictionary data_dictionary.tsv \
        -o output_pheno_db.db

* ``-p`` option specifies the pedigree file to use.

* ``-i`` option specifies the directory where instruments
  are located; This directory can contain subdirectories which can contain
  more subdirectories or instrument files.
  The instrument name is determined by the filename of the instrument CSV file.
  The tool looks for all ``.csv`` files under the given directory and will collect
  a list of files for every unique instrument found among all of the subdirectories.
  Multiple same named files in multiple directories will get merged and read as a single
  one by DuckDB's read_csv function.

* ``-o`` option specifies the output directory where the database and images will be created.
  The output directory will also contain Parquet files for each of the database tables created.

* ``--pheno-id`` option specifies the name of the produced DB file and the phenotype data ID which
  will be generated. This parameter is required.

* ``--data-dictionary`` option specifies the name of a data dictionary file for the phenotype database.

* ``--regression`` option specifies the regression configuration file.
  
* ``--person-column`` specifies the name of the column containing the person ID in the instrument
  CSV files. All files are expected to use the same column name for person IDs.

* ``--tab-separated`` option specifies that the instrument CSV files use tabs as delimiters.

* ``-j`` option specifies the amount of workers to create when running Dask tasks.

* ``-d`` option specifies the Dask task status directory used for storing task results and statuses.

* ``--force`` option forces Dask tasks to ignore cached task results and enables overwriting existing
  phenotype databases in the output directory.

You can use ``-h`` option to see all options supported by the ``pheno_import`` tool.

The data dictionary file
************************

The data dictionary is a file containing descriptions for measures.
It must be a TSV file with a header row and the following four columns:

* ``instrumentName``
* ``measureName``
* ``measureId``
* ``description``

The measure ID is formed by joining the instrument name and the measure name
with a dot character (e.g. ``instrument1.measure1``).

Measure classification
**********************

Each measure in the study is classified into one of four types: ``continuous``, ``ordinal``, ``categorical`` and ``raw``.
The ``raw`` measure type is reserved for measures, which could not be classified or did not fit any classification or has no values.
The measure type is determined by the inference configuration that is used by the import tool.
The inference configuration file is a YAML dictionary of string based scopes to inference configurations.
The configuration format allows setting a scope for a specific rule to apply to different measures and instruments.
The format scopes follow an order of specificity to determine the final configuration used for a given measure.
The supported types of scopes (in order of specificity) are the following:

* ``*.*`` - Wildcard for all measures in all instruments
* ``ala.*`` - Affects all measures in the instrument ``ala``.
* ``*.bala`` - Affects the measure ``bala`` in any instrument.
* ``ala.bala`` - Affects the measure ``bala`` in the instrument ``ala``.

Example configuration (default configuration):


.. code:: yaml

    "*.*":
        min_individuals: 1
        non_numeric_cutoff: 0.06
        value_max_len: 32
        continuous:
          min_rank: 10
        ordinal:
          min_rank: 1
        categorical:
          min_rank: 1
          max_rank: 15
        skip: false
        measure_type: null


A more advanced example:


.. code:: yaml

    "*.*":
        min_individuals: 1
        non_numeric_cutoff: 0.06
        value_max_len: 32
        continuous:
          min_rank: 10
        ordinal:
          min_rank: 1
        categorical:
          min_rank: 1
          max_rank: 15
        skip: false
        measure_type: null
    "ala.*":
        min_individuals: 2
    "*.bala":
        non_numeric_cutoff: 0.12


In this example, any measure outside of the instrument ``ala``, that is not named ``bala``, will have
the confiugration under ``"*.*"``.
Any measures named ``bala`` outside of ``ala`` will have a ``non_numeric_cutoff`` of 0.12 and
a ``min_individuals`` of 1, any inside ``ala`` will have ``min_individuals`` set to 2.

Inference parameters
********************

* ``min_individuals`` - The minimum amount of people in the instrument required for its measures to be classified,
  any amount under this will classify all instrument measures as ``raw``.

* ``non_numeric_cutoff`` - The fraction of values required to be non-numeric in order for a measure to be considered non-numeric.
  A cutoff of 0.06 means that if the amount of non-numeric values in the measure is below 6%, then the measure is considered numeric.

* ``continuous.min_rank`` - The amount of unique numeric values in a measure required for a measure to be classified as ``continuous``.

* ``ordinal.min_rank`` - The amount of unique numeric values in a measure required for a measure to be classified as ``ordinal``. The
  check for ordinal is done after ``continuous``, and the value of ``continuous.min_rank`` should be larger than ``ordinal.min_rank``.

* ``categorical.min_rank/max_rank`` - In order for a measure to be classified as ``categorical``,
  the measure first has to be determined as non-numeric and the amount of unique values
  in the measure must be between ``cateogrical.min_rank`` and ``categorical.max_rank``.

* ``skip`` - Whether to skip this measure (Skipped measure are not imported at all and absent from the final table,
  unlike measures classified as ``raw``)

* ``value_type``: Force a value type onto the measure. This skips the classification step, but not the statistics.
  The value of measure type should be a string or left as null or preferably omitted from the configuration if unused,
  as the default value is null. The valid string values are: ``raw``, ``categorical``, ``ordinal`` and ``continuous``.


How classification works
************************

The measure classification works through the ``inference_reference_impl`` function.

The function takes a list of string values and a merged inference configuration.

The classification first creates a classification report and then iterates through the entire list,
collecting unique values, counting ``None`` values and attempting to
cast every value into a ``float``. On success, the value is added to the list of numeric values, otherwise ``None`` is added to the
list of numeric values.

Afterwards, with the collected values and counts through iteration, the following values are set in the report:

* The total count of non-null values
* The total count of null values
* The total count of numeric values
* The total count of non-numeric values
* The total amount of unique values
* The total amount of unique numeric values

The measure type is then classified according to the inference configuration:

* First, the amount of values is checked against ``min_individuals`` - if it has less values than ``min_individuals``, the type is ``raw``.
* Then, the fraction of non-numeric values is calculated and compared against ``non_numeric_cutoff``.
* If the measure is numeric, it is first checked for ``continuous``, then ``ordinal``, if both fail, then the measure type is ``raw``.
* If the measure is non-numeric, it is checked for ``categorical`` and if it does not pass, the measure type is ``raw``.

After determining the measure type, numeric measures will get ``min_value``, ``max_value`` and ``values_domain`` values assigned
in the report, and non-numeric measures will get ``values_domain`` assigned.

If the measure is numeric, the function returns the list of numeric values and the report, otherwise it returns
the normal untransformed list of string values and the report.
