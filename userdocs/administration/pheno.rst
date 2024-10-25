Phenotype Database Tools
========================

Importing a phenotype database for use with the GPF system is accomplished with the help of the `pheno_import` tool.
The tool is given the raw phenotype data - a pedigree file, a directory containing instruments with measures and optionally, a data dictionary.
This will produce a DuckDB database containing the phenotype data.

Import a Phenotype Database
###########################

To import a phenotype database, you will need the following files:

* A pedigree file which contains information regarding evaluated individuals and their family.

* A directory containing instruments in the form of CSV (default) or TSV files (using the `-T` option).

* A data dictionary in the form of a TSV file. (Optional)

* A configuration for phenotype regressions. (Optional)

To import the phenotype database into the GPF system you need to use the
`pheno_import` tool:

.. code:: bash

    pheno_import \
        -p pedigree.ped \
        -i instruments/ \
        --data-dictionary data_dictionary.tsv \
        -o output_pheno_db.db

* `-p` option allows us to specify the pedigree file;

* `-i` option allows us to specify the directory where instruments
  are located; This directory can contain subdirectories which can contain
  more subdirectories or instrument files.
  The instrument name is determined by the filename of the instrument csv file.
  The tool looks for all .csv files under the given directory and will collect
  a list of files for every unique instrument found among all of the subdirectories.
  Multiple same named files in multiple directories will get merged and read as a single
  one by DuckDB's read_csv function;

* `-o` option specifies the output directory where the database and images will be created.
  The DB filename is the same as the output directory name. The output directory will also
  contain parquet files for each of the database tables created.

* `--pheno-id` option specifies the name of the dbfile and the phenotype data ID which will be generated.
  This parameter is required.

* `--data-dictionary` option specifies the name of the data dictionary file for the phenotype database;

* `--regression` option specifies the regression configuration file.
  
* `--person-column` specifies the name of the column containing the person ID in the instrument
  csv files. All files are expected to use the same column name for person IDs.

* `--tab-separated` option specifies that the instrument CSV files use tabs for separation.

* `-j` option specifies the amount of workers to create when running DASK tasks.

* `-d` option specifies the DASK task status directory used for storing task results and statuses.

* `--force` option forces DASK tasks to ignore cached task results and enables overwriting existing
  phenotype databases in the output directory.

You can use `-h` option to see all options supported by the `pheno_import`
tool.

The Data Dictionary
###################

The data dictionary is a file containing descriptions for measures.
It is a TSV file with 4 required columns and the header is also required.

The 4 columns are:

* `instrumentName`

* `measureName`

* `measureId`

* `description`

The measure ID is formed by joining the instrument name and the measure name
with a dot character (e.g. `instrument1.measure1`).

Measure Classification
######################

Each measure in the study is classified into one of four types: `continuous`, `ordinal`, `categorical` and `raw`.

The `raw` measure type is reserved for measures, which could not be classified or did not fit any classification or has no values.

The measure type is determined by the inference configuration that is used by the import tool.

The inference configuration file is a YAML dictionary of string based scopes to inference configurations.

The configuration format allows setting a scope for a specific rule to apply to different measures and instruments.

The format scopes follow an order of specificity to determine the final configuration used for a given measure.

The supported types of scopes (in order of specificity) are the following:

* `*.*` - Wildcard for all measures in all instruments
* `ala.*` - Affects all measures in the instrument `ala`.
* `*.bala` - Affects the measure `bala` in any instrument.
* `ala.bala` - Affects the measure `bala` in the instrument `ala`.

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
    "*.bala"
        non_numeric_cutoff: 0.12


In this example, any measure outside of the instrument `ala`, that is not named `bala`, will have
the confiugration under `"*.*"`.
Any measures named `bala` outside of `ala` will have a `non_numeric_cutoff` of 0.12 and
a `min_individuals` of 1, any inside `ala` will have `min_individuals` set to 2.

Inference parameters
####################

* `min_individuals` - The minimum amount of people in the instrument required for its measures to be classified,
  any amount under this will classify all instrument measures as `raw`.

* `non_numeric_cutoff` - The fraction of values required to be non-numeric in order for a measure to be considered non-numeric.
  A cutoff of 0.06 means that if the amount of non-numeric values in the measure is below 6%, then the measure is considered numeric.

* `continuous.min_rank` - The amount of unique numeric values in a measure required for a measure to be classified as `continuous`.

* `ordinal.min_rank` - The amount of unique numeric values in a measure required for a measure to be classified as `ordinal`. The
  check for ordinal is done after `continuous`, and the value of `continuous.min_rank` should be larger than `ordinal.min_rank`.

* `categorical.min_rank/max_rank` - In order for a measure to be classified as `categorical`,
  the measure first has to be determined as non-numeric and the amount of unique values
  in the measure must be between `cateogrical.min_rank` and `categorical.max_rank`.

* `skip` - Whether to skip this measure (Skipped measure are not imported at all and absent from the final table,
  unlike measures classified as `raw`)

* `measure_type`: Force a measure type onto the measure. This skips the classification step, but not the statistics.
  The value of measure type should be a string or left as null or preferably omitted from the configuration if unused,
  as the default value is null. The valid string values are: `raw`, `categorical`, `ordinal` and `continuous`


How The Classification Works
############################

The measure classification works through the `classification_reference_impl` function.

The function takes a list of string values and a merged inference configuration.

The classification first creates a classification report and then iterates through the entire list,
collecting unique values, counting `None` values and attempting to
cast every value into a `float`. On success, the value is added to the list of numeric values, otherwise `None` is added to the
list of numeric values.

Afterwards, with the collected values and counts through iteration, the following values are set in the report:

* The total count of non-null values

* The total count of null values

* The total count of numeric values

* The total count of non-numeric values

* The total amount of unique values

* The total amount of unique numeric values

The measure type is then classified according to the inference configuration:

* First, the amount of values is checked against `min_individuals`.
  If it has less values than `min_individuals`, the type is `raw`

* Then, the fraction of non-numeric values is calculated and compared against `non_numeric_cutoff`.

* If the measure is numeric, it is first checked for `continuous`, then `ordinal`, if both fail, then the measure type is `raw`.

* If the measure is non-numeric, it is checked for `categorical` and if it does not pass, the measure type is `raw`.

After determining the measure type, numeric measures will get `min_value`, `max_value` and `values_domain` values assigned
in the report, and non-numeric measures will get `values_domain` assigned.

If the measure is numeric, the function returns the list of numeric values and the report, otherwise it returns
the normal untransformed list of string values and the report.
