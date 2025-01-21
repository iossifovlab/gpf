Phenotype Database Tools
========================

Importing a phenotype database for use with the GPF system can be done either with an import project configuration or
with the help of the ``pheno_import`` tool. Either of these will produce a DuckDB database containing the phenotype data.

A derivative database is used to provide a summary of the phenotype data, as well as regressions by certain measures, for use
with the web application GPFJS. This derivative database is called a "phenotype browser database" or "phenotype browser cache"
and is created with a separate tool - ``build_pheno_browser``.

Importing via import project configuration
******************************************

The import project configuration is a YAML-formatted text file which describes how the phenotype data should be imported.
This configuration is then passed to the ``import_tools_pheno`` CLI tool, which will take care of carrying out the import.

Import project configuration format
###################################

.. code:: yaml

    # Required. The ID to use for the output phenotype data. Also determines the name of the produced .db file.
    id: pheno_data_id  

    # Optional. The root directory to which all other paths in the config, are considered relative to (except `output_dir`).
    # Accepts both relative and absolute paths. Relative paths will be resolved from the location of the import configuration.
    # If omitted, the directory in which the config is located will be considered as the input dir.
    input_dir: /home/user/pheno_data

    # Required. The directory in which to produce the output.
    # Accepts both relative and absolute paths. Relative paths will be resolved from the location of the import configuration.
    output_dir: /home/user/pheno_result

    # Required. A list of string paths or nested configurations; these will be the sources from which instruments are read.
    # * String paths can be files, directories or glob-style patterns with wildcards. Valid instrument files are files which
    #   end with a ".csv" or ".txt" extension. These instruments will receive a name according to their filename (without the file extension)
    #   and the expected delimiter and person ID column will be the defaults from the configuration.
    # * Nested configurations allow for overriding the instrument name, delimiter and person ID column, but can only point
    #   to a single file. None of the override options are mandatory.
    instrument_files:
      - work/instruments
      - work/some_instrument.csv
      - work/more_instruments/**/*.txt
      - path: work/other_instruments/i1.tsv
        instrument: instrument_1
        delimiter: "\t"
        person_column: p_id
      - path: work/other_instruments/i1_part_two.csv
        instrument: instrument_1

    # Required. Path to the pedigree file to use for import.
    pedigree: work/pedigree.ped

    # Required. The default name of the column containing the person ID in the instrument CSV files.
    person_column: subject_id

    # Optional. The default delimiter to expect in instrument files. The default value is ",".
    delimiter: ","

    # Optional. Flag to skip the building of the pheno common instrument. The default value is `False`.
    skip_pedigree_measures: False

    # Optional. A nested configuration that specifies the sources for measure descriptions.
    # Two fields are provided: `files` and `dictionary`:
    # * `files` is a list of nested configurations for each file containing measure descriptions.
    #   Unless overriden, files are expected to be comma-separated files with columns "instrumentName", "measureName" and "description".
    # * `dictionary` is used for manual input of measure descriptions. These will override any measure descriptions from `files`.
    data_dictionary:
      files:
        - path: "work/instruments/data_dict_1.csv"
        - path: "work/instruments/data_dict_2.tsv"
          delimiter: "\t"
          instrument_column: "i_mame"
          measure_column: "m_name"
          descritpion_column: "desc"
          # This override will ignore any instrument name column in the file and use the value provided below for ALL rows in the file.
          instrument: "some_instrument_name"

      dictionary:
        instrument_1:
          measure_1: "description of a measure"
        instrument_2:
          measure_2: "another description of a measure"

    # Optional. The configuration to use for measure type inference. Can be either a path to a YAML-formatted configuration file or a directly embedded configuration.
    inference_config: work/inference.conf
    # Nested configuration usage example below. (This is only for the purposes of an example, you CANNOT specify both a file and a nested configuration at the same time.)
    inference_config:
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

    # Optional. The contents of this section will be written to the output data's config file.
    study_config:
      # A dictionary of measures against which to calculate regressions with other measures in the study.
      regressions:
        age:
          measure_names:                 # The measures' names
            - age_measure      
          instrument_name: pheno_common  # From which instrument to select the measures
          display_name: age              # How to display the regression in the produced plot
          jitter: 0.1                    # Jitter to spread out similar/identical values on the plot
        measure_1:
          measure_names:
            - measure_1
          instrument_name: instrument_1
          display_name: measure number one
          jitter: 0.1

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

Building the phenotype browser database
***************************************

The ``build_pheno_browser`` tool is used to create the phenotype browser database.

This tool is also capable of determining whether an existing phenotype browser database is in
need of re-calculation - if the DB file is up-to-date, it will not be rebuilt.

.. runblock:: console

    $ build_pheno_browser --help

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
####################

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
########################

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
