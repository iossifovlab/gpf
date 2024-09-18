======================================
 Genomic position table configuration
======================================

Table configuration fields
==========================

filename
  Path to the file containing the data, relative to the genomic resource's directory.


format
  Format of the file configured in ``filename``. Currently supported formats are ``tabix``, ``vcf_info``, ``tsv``, ``csv`` and ``bw``.
  Auto-detection of the format works for the following filename extensions:

  ============================  ======
  Extension                     Format
  ============================  ======
  .bgz                          tabix
  .vcf.gz                       vcf_info
  .txt, .txt.gz, .tsv, .tsv.gz  tsv
  .csv, .csv.gz                 csv
  .bw                           bw
  ============================  ======

header_mode
  The default value is ``file``.

  =====  ======
  Value  Effect
  =====  ======
  file   Will attempt to extract a header from the provided file.
  list   Will take the list of strings provided with the configuration field ``header`` as header.
  none   No header. Columns will only be able to be configured via index.
  =====  ======

header
  Used for providing a header when ``header_mode`` is set to ``list``. Example:

  .. code:: yaml

      header_mode: list
      header: ["chrom", "start", "end", "score_value"]

chrom_mapping
  Allows transformation of the values in the chromosome column. Three options are available:

  add_prefix
    Takes a string value and adds it as a prefix.

  del_prefix
    Takes a string value to remove from the start of each chromosome.

  filename
    Takes a filepath, relative to the genomic resource's directory.
    The file's contents must contain two columns delimited by whitespace.
    The first line must be the header, containing ``chrom`` and ``file_chrom`` as values.
    The ``file_chrom`` column contains values that will be found in the file, while the ``chrom`` column contains what they will be mapped to.
    An example is given below:

    .. code::

        chrom           file_chrom
        Chromosome_1    1
        Chromosome_22   22


{column}
  Generic configuration for a column in the genomic position table.

  column_name
    Takes a string value. The name of the column as it appears in the file's header. Cannot be used if no header has been provided for the table.

  column_index
    Takes an integer value. The index of the column in the file.

  name
    Deprecated version of ``column_name``.

  index
    Deprecated version of ``column_index``.


chrom
  Column configuration for the chromosome column. See explanation for {column} above.


pos_begin
  Column configuration for the start position column. See explanation for {column} above.


pos_end
  Column configuration for the end position column. See explanation for {column} above.


reference
  Column configuration for the reference column. See explanation for {column} above.


alternative
  Column configuration for the alternative column. See explanation for {column} above.


Score configuration fields
==========================

id
  Takes a string value. The identifier the system will use to refer to this score column in annotation configurations.


type
  Type of the column's values. Takes one of the following values - ``str``, ``float``, ``int``.


column_name
  Takes a string value. The name of the column as it appears in the file's header. Cannot be used if no header has been provided for the table.


column_index
  Takes an integer value. The index of the column in the file.


name
  Deprecated version of ``column_name``.


index
  Deprecated version of ``column_index``.


desc
  A string describing the score column.


na_values
  Takes a string or list of strings value. Which score values to consider as ``na``.


histogram
  Histogram configuration. See :ref:`Histograms and statistics <Histograms and statistics>` for more info.


Zero-based / BED format scores
==============================

.. code:: yaml

    table:
      filename: data.txt.gz
      format: tabix
      zero_based: True
    scores:
    - id: score_1
      name: score 1
      type: float

The ``zero_based`` argument controls how the score file will be read.

| Setting it to true will read the score as a BED-style format - with 0-based, half-open intervals.
| By default it is set to false, which will read the score in GPF's internal format - with 1-based, closed intervals.


Example configurations
======================

Example table configuration for a genomic score resource.
This configuration is embedded in the score's ``genomic_resource.yaml`` config.

.. code:: yaml

    # Example genomic_resource.yaml for an NP score resource.

    table:
      filename: whole_genome_SNVs.tsv.gz
      format: tabix

      # how to modify the values found when reading the chromosome column
      chrom_mapping:
        add_prefix: chr

      # configuration for essential columns
      chrom:
        name: Chrom
      pos_begin:
        name: Pos
      reference:
        name: Ref
      alternative:
        name: Alt

    # score values
    scores:
      - id: cadd_raw
        type: float
        name: RawScore
        desc: |
          CADD raw score for functional prediction of a SNP. The larger the score
          the more likely the SNP has damaging effect
        large_values_desc: "more damaging"
        small_values_desc: "less damaging"
        histogram:
          type: number
          number_of_bins: 100
          view_range:
            min: -8.0
            max: 36.0
          y_log_scale: True

.. code:: yaml

    # Example genomic_resource.yaml for a position score resource with multiple scores
    # with different histogram configurations.

    table:
      filename: scorefile.tsv.gz
      format: tabix

      # configuration for essential columns
      chrom:
        name: chromosome
      pos_begin:
        name: start
      pos_end:
        name: stop

    # score values
    scores:
      # float score
      - id: score_A
        type: float
        name: NumericScore
        number_hist:
          number_of_bins: 120
          view_range:
            min: -10.0
            max: 225.0
          x_log_scale: True
          x_min_log: 0.05
      # integer score
      - id: score_B
        type: int
        name: IntegerScore
        number_hist:
          number_of_bins: 10
      # string score with categorical histogram
      - id: score_C
        type: str
        name: CategoricalScore
        categorical_hist:
          value_order: ["alpha", "beta", "gamma", "delta"]
      # string score with no histogram
      - id: score_D
        type: str
        name: WeirdScore
        null_hist:
          reason: "Don't care about this score"


.. code:: yaml

    # Example bigWig score configuration.

    type: position_score

    table:
      filename: hg38.phyloP7way.bw
      # header mode must be set to none for bigWig scores
      header_mode: none

    # currently, it's necessary to explicitly configure the score with its index set to 3
    scores:
      - id: phyloP7way
        type: float
        column_index: 3

    default_annotation:
      - source: phyloP7way
        name: phylop7way
