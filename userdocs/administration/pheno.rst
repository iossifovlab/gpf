Phenotype Database Tools
========================

Importing a phenotype database for use with the GPF system is accomplished with the help of two tools.
The first tool is given the raw phenotype data - a pedigree file, a directory containing instruments with measures and optionally, a data dictionary.
This will produce an SQLite3 database, which can then be utilised with the second tool to produce data that can be used with the GPF Phenotype Browser.

Import a Phenotype Database
###########################

To import a phenotype database, you will need the following files:

* A pedigree file which contains information regarding evaluated individuals and their family.

* A directory containing instruments in the form of CSV (default) or TSV files (using the `-T` option).

* A data dictionary in the form of a TSV file. (Optional)

To import the phenotype database into the GPF system you need to use the
`pheno2DAE.py` tool:

.. code:: bash

    pheno2dae.py \
        -p pedigree.ped \
        -i instruments/ \
        -d data_dictionary.tsv \
        -o output_pheno_db.db

* `-p` option allows us to specify the pedigree file;

* `-i` option allows us to specify the directory where instruments
  are located;

* `-d` option specifies the name of the data dictionary file for the phenotype database;

* `-o` option specifies the name of the output file;

You can use `-h` option to see all options supported by the `pheno2dae.py`
tool.

Generate Pheno Browser Data
###########################

To generate the data needed for the GPF Phenotype Browser you can use
`pheno2browser.py` tool. Example usage of the tools is shown below:

.. code:: bash

    pheno2browser.py \
        -d ./pheno_db.db \
        -p pheno_db_name \
        -o browser/pheno_db_name \
        --regression pheno_reg.conf

* ``-d`` option specifies path to already imported phenotype database file;

* ``-p`` option specifies the name of the phenotype database that will be
  used in phenotype browser;

* ``-o`` option specifies the output directory where all the generated
  file will be stored;

* ``--regression`` option specifies an absolute path to a pheno regression
  config file

Measure Classification
######################

In order to be inserted into an SQLite3 database, each measure is classified into one of four types: continuous, ordinal, categorical and raw.

The default non-numeric cutoff value is 6%. That is, a measure with more than 6% non-numeric values will be considered a non-numeric measure.

If a measure does not contain any values, it will be classified as a raw measure.

A numeric measure with 10 or more unique values will be classified as a continuous measure. Numeric measures with less than 10 unique values will be classified as ordinal measures.

Non-numeric measures with between 1 to 15 (including) unique values with a maximum length of 32 characters will be classified as categorical measures.

Any other measure will be classified as a raw measure.

The values which determine measure classification can be tweaked - see the help option of the pheno2dae tool.
