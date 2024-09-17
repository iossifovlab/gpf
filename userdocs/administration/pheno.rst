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

In order to be inserted into an SQLite3 database, each measure is classified into one of four types: continuous, ordinal, categorical and raw.

The default non-numeric cutoff value is 6%. That is, a measure with more than 6% non-numeric values will be considered a non-numeric measure.

If a measure does not contain any values, it will be classified as a raw measure.

A numeric measure with 10 or more unique values will be classified as a continuous measure. Numeric measures with less than 10 unique values will be classified as ordinal measures.

Non-numeric measures with between 1 to 15 (including) unique values with a maximum length of 32 characters will be classified as categorical measures.

Any other measure will be classified as a raw measure.

The values which determine measure classification can be tweaked - see the help option of the pheno2dae tool.

How The Tool Works
##################

* First the tool reads and imports the pedigree into the DuckDB database.

* Then it collects all instruments and their associated files.

* Then it loads the data dictionary file (if provided) and reads
  the measure descriptions from it.

* Then it creates the `instrument` and `measure` tables in the database.

* Then it creates the special `pheno_common` instrument if the `build-pheno-common` flag is set
  and imports it into instrument and measure. The other parts of the `pheno-common` import are
  the same as the following steps done for every other instrument import.

* Then for every instrument, the data gets loaded into a temporary data table.
  DuckDB automatically handles type inference for the values of the table by reading
  a specific amount of lines first. In the case of a column turning out to be a different
  table later during the full data read, any rows that failed to read are stored in a rejects
  table. If a rejects table was created, any columns that had rejected values are changed to
  a VARCHAR type and the table is reimported.

* After loading the data tables, the tool will clean up the table if it has any rows with
  a person ID not in the provided pedigree.

* The tool will then create 4 parallel tasks for measure classification.

* During measure classification, the data dictionary descriptions are applied to
  the measures.

* After classification, the tool will insert the instrument entry into the `instrument` table and
  a measure entry for each measure into the `measure` table and
  create the `{instrument_name}_measure_values` table.
  Each instrument will have a table of this type.
  The table contains all of the data from the temporary data tables, joined with the person's information:
  family id, role, status and sex.

* After importing every measure, the tool will save the measure and instrument tables to
  parquet in the output directory

* At this point, the database has all of the data imported and can be loaded as a phenotype study.

* The next and final big step is to generate images, regressions and the phenotype browser table.

* The current DB gets loaded as a phenotype study and the tool reads the
  regression configuration if provided.

* First, if pheno regressions are given, the tool will first fully populate the
  `regression` table. This table contains a row describing every regression that
  will be built for every measure in the phenotype DB. It has 4 columns: `regression_id`,
  `instrument_name`, `measure_name` and `display_name`. Practically, this step only
  adds the regression configuration file data to the database.

* A task graph is now created along with a temporary copy of the DuckDB database in
  the output directory. This is done, because every worker will have to open a connection
  to the database, but it is currently open in write mode and you can only open multiple
  connections in read only or only open 1 connection in write mode.

* For every measure in every instrument, a task is created. In this task, the worker will
  generate images for the measure values and regressions, if any.

* Each worker returns a tuple of dicts with values for the `variable_browser` and `regression_values`
  tables respectively.

* Each worker starts by getting the entire DB dataframe for the given measure. The columns of this
  dataframe are all of the person columns in the respective `_measure_values` table plus the specific
  measure column.

* Then it draws an image depending on the measure type. If the current measure has regressions, the
  regression values are calculated and the image is also built.

* When done with every worker, the `variable_browser` and `regression_values` tables are populated with
  the results of the workers

* As a final step, the tool generates a phenotype study configuration.

* The phenotype study is now fully prepared and ready in the output directory.

How Measure Classification Works
################################

* When creating a measure classification task, a classification and inference configuration is merged if
  an inference configuration file is provided, otherwise, the tool will work with the default configuration.

* Every measure classification task starts with creating a read-only connection to a temporary
  dbfile, provided by the previous steps in the import.

* If the inference configuration provides the exact measure type, then the import will collect
  min and max values for numeric types and all unique values for string types. String types
  have null min and max values. Once min, max and values_domain are collected,
  the classification is complete.

* If an exact measure type is not provided, a classification report is constructed.
  This report contains a bunch of different statistics for determining the measure type.

* First, the total amount of measure values is collected.

* Then, the total amount of non-null measure values is collected and with it,
  the amount of null values is calculated by subtracting from the total.

* Afterwards, we get the column's DB datatype and determine whether it is a text
  or numeric measure stored in the DB.

  * In the case of numeric measures, we collect the total count and the total
    non-null count to determine the total count with values, total count with numeric values,
    total count with non-numeric values and the total count without values. In this case, the
    total count of non-numeric values is always 0.

  * After this, we count the total amount of unique values and total amount of unique numeric values,
    both the same in this case.

  * We also collect a list of every unique and and a list of every real numeric value.

  * In the case of text measures, we collect the total count of null values. Then we count the
    amount of numeric values and then the count of non-numeric values. After this we count
    and collect all unique values. And after this, we collect all numeric values and
    from the list of numeric values we get the count of all of the unique numeric values too.

* Once this is done, we proceed with classification.

* First, if the amount of values in the measure table is less than the minimum individuals
  in the inference configuration, we determine the measure type as `raw`.

* Next, we get the percentage of non-numeric values in the table.

  * If this percentage is less than the non-numeric cutoff in the configuration, we look at the amount
    of unique numeric values in the table. If it is more than the minimum for continuous measures,
    we determine the measure type to be `continuous`. Otherwise if it is more than the minimum 
    for ordinal measures, we determine it as `ordinal`. Otherwise, we determine the measure as `raw`.

  * If the percentage is more than the non-numeric cutoff, we look if the amount of unique values
    falls within the range defined in the configuration for categorical measures. If it does,
    then we determine the measure as `categorical`, otherwise the measure will be determined as `raw`.

* If a range is not defined for categorical measures in the configuration, 
  then all text measures will be classified as `raw`. The default configuration has a default range.

* If minimums are not defined for continuous and ordinal measures, then the respective type
  will be skipped to the next one until `raw`.
