Genomic resources repository (GRR)
==================================


Introduction
************

Genomic Resource Repository (GRR) is a collection of genomic resources, 
like reference genomes, gene models, etc. One can use one or more GRRs at the 
same time. By default (or without any configuration), you will use the 
public GRR build by Iossifov lab and accessible through  
https://storage.googleapis.com/iossifovlab-grr/.

.. note::

    To browse the conent of the default GRR follow this link:
    https://storage.googleapis.com/iossifovlab-grr/index.html

If you want to use additional genomic resources, you can build your own GRR 
(see Management of GRR below) and add it to the GRRs you use. The set of GRR 
that are accessible can be configured in several ways. 

To configure the GRRs to be used by default for your user you can create 
the file ~/.grr_definition.yaml. An example of what the contents of this file 
can be is:

.. code:: yaml

    id: "development"
    type: group
    children:
    - id: "grr_local"
      type: "directory"
      directory: "~/my_grr"

    - id: "default"
      type: "url"
      url: "https://storage.googleapis.com/iossifovlab-grr/"
      cache_dir: "~/default_grr_cache"

This configures a group of two repositories with ids the 'grr_local' and 
the 'default'. When you search for a resource, the system will first try 
to find in the grr_local repository, because it is listed first and, if 
it doesn't find it there, it will try the default GRR. The default GRR is  
a remote GRR at the given URL and its configuration specified that resources 
used from it will be cached in the "~/default_grr_cache" directory. It is 
significantly faster to use cached resources, but it takes some time to cache
them the first time they are used and they occupy substantial disk space.

Alternatively, the system will use GRR configuration file pointed to by 
the GRR_DEFINITION_FILE environment variable.

Finally, most command line tools that use GRRs have a --grr <file name> argument 
that overrides the defaults.

Configuration
*************

Genomic resources repository could be accessed via different protocols.
Currently supported protocols for GRR access are:

* File system (directory) protocol.

  .. code:: yaml

    id: <repo id>
    type: directory
    directory: <path to the local file system>

* HTTP/HTTPS protocol.

  .. code:: yaml

    id: <repo id>
    type: http
    url: <http:// or https:// url>

  
  .. code:: yaml

    id: <repo id>
    type: url
    url: <http(s) url>

* S3 protocol.
  
  .. code:: yaml

    id: <repo id>
    type: url
    url: <S3 url>
    endpoint_url: <endpoint url>

* In-memory (embedded) protocol.

  .. code:: yaml

    id: <repo id>
    type: embedded
    content:


Browse available resources
**************************

.. code:: bash

    grr_browse [--grr grr_definition.yaml]


Management of genomic resources repository (GRR)
************************************************

Genomic resources and genomic resources repository
##################################################

The genomic resource is a set of files stored in a directory. To make given
directory a genomic resource, it should contain ``genomic_resource.yaml``
file.

A genomic resources repository is a directory that contains genomic resources.
To make a given directory into a repository, it should have a ``.CONTENTS``
file.


Create an empty GRR
###################

To create and empty GRR first create an empty directory. For example let us
create an empty directory named ``grr_test``, enter inside that directory and
run ``grr_manage repo-init`` command:

.. code-block:: bash

    mkdir grr_test
    cd grr_test
    grr_manage repo-init

After that the directory should contain an empty ``.CONTENTS`` file:

.. code-block:: bash

    ls -a

    .  ..  .CONTENTS

If we try to list all resources in this repository we should get an empty list:

.. code-block:: bash

    grr_manage list


Create an empty genomic resource
################################

Let us create our first genomic resource. Create a directory
``hg38/scores/score9`` inside
``grr_test`` repository and create an empty ``genomic_resource.yaml`` file
inside that directory:

.. code-block:: bash

    mkdir -p hg38/scores/score9
    cd hg38/scores/score9
    touch genomic_resource.yaml

This will create an empty genomic resource in our repository 
with ID ``hg38/scores/score9``.

If we list the resources in our repository we would get:

.. code-block:: bash

    grr_manage list

    working with repository: .../grr_test
    Basic                0        1            0 hg38/scores/score9


When we create or change a resource we need to repair the repository:

.. code-block:: bash

    grr_manage repo-repair

This command will create a ``.MANIFEST`` file for our new resource
``hg38/scores/score9`` and will update the repository ``.CONTENTS`` to include
the resource.


Add genomic score resources
+++++++++++++++++++++++++++

Add all score resource files (score file and Tabix index) inside
the created directory ``hg38/scores/score9``. Let's say these files are:

.. code-block:: 

   score9.tsv.gz
   score9.tsv.gz.tbi

Configure the resource ``hg38/scores/score9``. To this end create
a ``genomic_resource.yaml`` file, that contains the position score
configuration:

.. code-block:: yaml

    type: position_score
    table:
      filename: score9.tsv.gz
      format: tabix

      # defined by score_type
      chrom:
        name: chrom
      pos_begin:
        name: start
      pos_end:
        name: end

    # score values
    scores:
    - id: score9
        type: float
        desc: "score9"
        index: 3
    histograms:
    - score: score9
      bins: 100
      y_scale: "log"
      x_scale: "linear"
    default_annotation:
      attributes:
      - source: score9
        destination: score9
    meta: |
    ## score9
      TODO

When ready you should run ``grr_manage resource-repair`` from inside resource
directory:

.. code-block:: bash

    cd hg38/scores/score9
    grr_manage resource-repair

This command is going to calculate histograms for the score (if histograms
are configured) and create or update the resource manifest.

Once the resource is ready we need to regenerated the repository contents:

.. code-block:: bash

    grr_manage repo-repair


Usage of genomic resources repositories (GRRs)
++++++++++++++++++++++++++++++++++++++++++++++

The GPF system can use genomic resources from different repositories. The
default genomic resources repository used by GPF system is located at
`https://www.iossifovlab.com/distribution/public/genomic-resources-repository/ 
<https://www.iossifovlab.com/distribution/public/genomic-resources-repository/>`_.
You can browse the content of the repository using the ``grr_manage list``
command:

.. code-block::

    grr_manage list -R https://www.iossifovlab.com/distribution/public/genomic-resources-repository


If you have a repository on your local filesytem you can browse it by
providing the path to the root directory:

.. code-block::

    grr_manage list -R <path to the local repo>

You can store a genomic resource repository in an S3 storage and you can browse
its content with:

.. code-block::

    grr_manage list -R s3://grr-bucket-test/grr \
        --extra-args "endpoint_url=http://piglet.seqpipe.org:7480"

where ``grr-bucket-test`` is the bucket where you store the repository and
``--extra-args`` are used to specify the S3 endpoint.

Genomic Resource types
**********************

position_score
##############

Two formats are accepted in GPF

Format A

.. code-block::

  chr1   pos    score1 score2
  # pos is assumed to be 1-based

  # how do we index with tabix!!!!
  Tabix -s 1 -b 2 -e 2

Format B

.. code-block::

  chr1 beg end score1 score2
  # all positions in [beg, end] are assigned the same scores
  # beg and end are  assumed to be 1-based
  # end is included (the interval is closed on both end)
  tabix -s 1 -b 2 -e 3

NOTE: We should never use tabix -p bed!!

np_score
########

allele_score
############

gene_models
###########

Example genomic_resource.yaml:

.. code:: yaml

    type: gene_models 
    filename: refGeneMito-201309.gz
    format: "default"

The available formats are:

* default  -- this is a GPF internal format
* refflat
* refseq
* ccds
* knowngene
* gtf
* ucscgenepred

reference_genome
################

liftover
########

Annotation pipeline
###################

Example genomic_resource.yaml:

.. code:: yaml

    type: annotation_pipeline
    filename: annotation.yaml

The ``annotation.yaml`` config must be placed inside the resource's directory.


Aggregators
***********

- mean
- median
- max
- min
- mode
- join (i.e., join(;))
- list
- dict
- concatenate


Genomic position table
**********************

Example table configuration for a genomic score resource.
This configuration is embedded in the score's ``genomic_resource.yaml`` config.

.. code:: yaml
    # Example genomic_resource.yaml for a score resource.
    # Contains both a genomic position table configuration under 'table',
    # and configuration for scores under 'scores'.

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


Table configuration fields
##########################

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
##########################

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
  type
    The type of histogram to build. Takes one of the following valeus - ``number``, ``categorical``, ``null``.


  number_of_bins
    The amount of bins to create. The default value is 100.


  view_range
    Restricts which score values to use for the histogram.

    min
      The minimum value.

    max
      The maximum value.


  x_log_scale
    Boolean. If true, the X scale will be logarithmic.


  y_log_scale
    Boolean. If true, the Y scale will be logarithmic.


  x_min_log
    Takes a float value. Values less than this will not be included in logarithmic scales, and will instead be separated into their own bin.


  value_order
    The ordering of values for categorical histograms.


  reason
    Used when type is ``null``. Explanation why no histogram has been constructed.


number_hist
  Specific configuration for ``number`` type histograms.

  number_of_bins
    See above, under ``histogram``.


  view_range
    See above, under ``histogram``.


  x_log_scale
    See above, under ``histogram``.


  y_log_scale
    See above, under ``histogram``.


  x_min_log
    See above, under ``histogram``.


categorical_hist
  Specific configuration for ``categorical`` type histograms.

  y_log_scale
    See above, under ``histogram``.


  value_order
    See above, under ``histogram``.


null_hist
  Specific configuration for skipping the calculation of a histogram.

  reason
    See above, under ``histogram``.


large_values_desc
  Text that will be included in the histogram image as description for large values.


small_values_desc
  Text that will be included in the histogram image as description for small values.


Zero-based / BED format scores
##############################

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