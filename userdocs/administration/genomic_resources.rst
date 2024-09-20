=============================================
 Genomic resources and resource repositories
=============================================

The GPF system uses genomic resources such as reference genomes, gene models, genomic scores, etc.
These resources are provided by resource repositories which can be accessed remotely or locally.
The system can use multiple repositories at a time.

Genomic resources and resource repositories are fundamentally a collection of directories and files with special YAML configurations.

The following documentation will explain what genomic resources are available and how they can be configured,
how resource repositories are configured and discovered by the system, and a short tutorial on creating a local repository
with a custom resource.

Genomic resources
=================

A genomic resource is a directory containing a special ``genomic_resource.yaml`` configuration and an arbitrary number of files.
Additionally, GPF will create additional files (``.MANIFEST``, the ``.grr`` subdirectory) which are used internally to track changes to the resource.

genomic_resource.yaml
---------------------

.. code:: yaml

    type: <genomic resource type>
    # ...
    meta:
        description: <resource description>
        summary: <resource summary>
        labels:
            <custom label>: <custom label value>
            # ...

This is the configuration file for a genomic resource. Directories containing this file will be treated as genomic resources by the system.
It **must** be named ``genomic_resource.yaml``, as this is how the system will search for it.

Below are some the common fields that can be found in every config. Depending on the resource type, other fields may be present.

=================  ================
Field              Description
=================  ================
type               String. Sets the type of the resource.
meta               Subsection. Contains fields with information about the resource.
labels             Dictionary. Can contain arbitrary key/values.
=================  ================


Below are the fields in the ``meta`` section:

=================  ================
Field              Description
=================  ================
description        String. Description of the resource.
summary            String. Short summary of the resource.
=================  ================

Types of genomic resources and their configurations
---------------------------------------------------

Genomic scores
^^^^^^^^^^^^^^

==================  ================
Field               Description
==================  ================
type                One of ``position_score``, ``np_score``, ``allele_score``.
table               Subsection. :ref:`Describes the file containing the scores, what columns/fields are present in it, etc.<Genomic position table configuration>`
scores              :ref:`List of dictionaries that describes each score column available in the resource.<Score configuration fields>`
default_annotation  Subsection. The default :ref:`annotation configuration<Annotation Infrastructure>` to use with this resource.
==================  ================


Gene models
^^^^^^^^^^^

=================  ================
Field              Description
=================  ================
type               ``gene_models``
filename           String. Path to the models file. Relative to the resource directory.
format             String. Sets the expected format of the gene models. One of ``default``, ``refflat``, ``refseq``, ``ccds``, ``knowngene``, ``gtf``, ``ucscgenepred``.
=================  ================

Reference genome
^^^^^^^^^^^^^^^^

=================  ================
Field              Description
=================  ================
type               ``genome``
filename           String. Path to the genome file. Relative to the resource directory.
PARS               Subsection. Configures the pseudoautosomal regions of the genome.
chrom_prefix       String. Configures the prefix contig names are **expected to have** in the genome.
=================  ================

The format for the ``PARS`` subsection is as follows:

.. code:: yaml

    PARS:
      "X":
          - "chrX:10000-2781479"
          - "chrX:155701382-156030895"
      "Y":
          - "chrY:10000-2781479"
          - "chrY:56887902-57217415"


Liftover chain
^^^^^^^^^^^^^^

=================  ================
Field              Description
=================  ================
type               ``liftover_chain``
filename           String. Path to the chain file. Relative to the resource directory.
=================  ================

Annotation pipeline
^^^^^^^^^^^^^^^^^^^

=================  ================
Field              Description
=================  ================
type               ``annotation_pipeline``
filename           String. Path to the annotation configuration file. Relative to the resource directory.
=================  ================

Histograms and statistics
-------------------------

Each resource type defines a set of statistics that can be calculated for the 
resource. These statistics are calculated by the ``grr_manage`` command line tools
and stored in the resource directory under ``statistics`` subdirectory.

For genomic and gene score resources the ``grr_manage`` command line tool 
calculates and
draws histograms for each of the scrores defined in the resource.

Here were are going to describe the common behavior for calculation and drawing
of histograms for genomic and gene score resources. Other statistics are specific
for the resource type and should be described in the resource type documentation.

Histograms
^^^^^^^^^^

Histograms are calculated for each of the scores defined in a gene score or
genomic score resource. The GPF supports three types of histograms:

* ``NumberHistogram`` - supported for scores of type ``int`` and ``float``. By default
  the histogram is calculated with 100 bins and is linear on both axes.

* ``CategoricalHistogram`` - supported for scores of type ``str`` and ``int``. This is a
  histogram that shows the distribution of the unique values in the score. It
  is supported only for scores with less than 100 unique values.
    
* ``NullHistogram`` - this histogram type defines a missing histogram. It is used
  when calculating a histogram is not possible or does not make sense.

Number Histograms Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each score defined in a genomic or gene score resource ``genomic_resource.yaml``
file a histogram configuration can be defined. The number histogram configuration
supports the following fields:

* ``type`` - the type of the histogram. This should be set to ``number``.
* ``number_of_bins`` - the number of bins in the histogram. By default this is set
  to 100.
* ``view_range`` - the range of values that areshown in the histogram. This range
  could differ from the actual range of the score values. This is useful for
  adjustements of the histogram view.
* ``y_log_scale`` - if set to ``True`` the y axis of the histogram will be 
  logarithmic.
* ``x_log_scale`` - if set to ``True`` the x axis of the histogram will be 
  logarithmic.
* ``x_min_log`` - when ``x_log_scale`` is set to ``True`` this value defines the
  minimum value of the x axis.
* ``plot_function`` - user defined plot function. When the default plot function is
  not suitable for the score, a user defined function can be used.


Example 1: Number histogram configuration
"""""""""""""""""""""""""""""""""""""""""

Here is a full example of a number histogram configuration comming from
the 
`hg38/score/phyloP100way <https://grr.seqpipe.org/hg38/scores/phyloP100way/index.html>`_ 
genomic score resource:

.. code:: yaml

    type: position_score

    table:
    filename: hg38.phyloP100way.bw 
    header_mode: none   # this makes no sense and should be removed

    # score values
    scores:
    - id: phyloP100way
      type: float
      desc: "The score is a number that reflects the conservation at a position."
      large_values_desc: "more conserved"
      small_values_desc: "less conserved"
      index: 3    # this makes no sense and should be removed
      histogram:
        type: number
        number_of_bins: 100
        view_range:
            min: -20.0
            max: 10.0
        y_log_scale: True


Example 2: Number histogram configuration
"""""""""""""""""""""""""""""""""""""""""

Here is a full example of a number histogram configuration comming from
the 
`hg38/variant_frequencies/gnomAD_v3 <https://grr.seqpipe.org/hg38/variant_frequencies/gnomAD_v3/genomes/index.html>`_ 
genomic score resource:


.. code:: yaml

  type: allele_score
  
  table:
    filename: gnomad.genomes.r3.0.extract.tsv.gz
    format: tabix
  
    chrom:
      name: CHROM
    pos_begin:
      name: POS
    pos_end:
      name: POS
    reference:
      name: REF
    alternative:
      name: ALT
  
  scores:
    ...

    - id: AF
      name: AF
      type: float
      desc: "Alternative allele frequency in the all gnomAD v3.0 genome samples."
      histogram:
        type: number
        number_of_bins: 126
        view_range:
          min: 0.0
          max: 1.0
        y_log_scale: True
        x_log_scale: True
        x_min_log: 0.00001
  
    ...


Categorical Histograms Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Categorical histograms are suitable for scores that have limited (less than 100)
number of unique values. By default the values are displayed in the order of 
their frequency. By default the top 20 values are displayed in the histogram. 
Other values are grouped into the ``Other`` category.

The categorical histogram configuration supports the following fields:

* ``type`` - the type of the histogram. This should be set to ``categorical``.
* ``number_of_bins`` - the number of bins in the histogram. By default this is set
  to 100.
* ``y_log_scale`` - if set to ``True`` the y axis of the histogram will be 
  logarithmic.
* ``displayed_values_count`` - the number of unique values that will be displayed in
  the histogram. Default value for this field is 20. The rest of the values
    are grouped into the ``Other`` category.
* ``displayed_values_percent`` - the percentage of total mass of unique values 
  that will be displayed. Other values are grouped into the ``Other`` category.
  **Only one of** ``displayed_values_count`` and ``displayed_values_percent`` can be set.
* ``values_order`` - the order in which the unique values are displayed in the 
  histogram.
* ``plot_function`` - user defined plot function. When the default plot function is
  not suitable for the score, a user defined function can be used.


Example 1: Categorical histogram configuration
""""""""""""""""""""""""""""""""""""""""""""""

Here is a full example of a number and categorical histogram configuration 
comming from the 
`hg38/scores/AlphaMissense <https://grr.seqpipe.org/hg38/scores/AlphaMissense/index.html>`_ 
genomic score resource:

.. code:: yaml

  type: np_score
  
  table:
    filename: AlphaMissense_hg38_modified.tsv.gz
    format: tabix
  
    chrom:
      name: chrom
    pos_begin:
      name: pos
    pos_end:
      name: pos
    reference:
      name: ref
    alternative:
      name: alt
  
  scores:
    - id: am_pathogenicity
      name: am_pathogenicity
      type: float
      desc: |
        AlphaMissense Pathogenicity score is a deleteriousness score for missense variants
      large_values_desc: "more pathogenic"
      small_values_desc: "less pathogenic"
      histogram:
        type: number
        number_of_bins: 100
        view_range:
          min: 0.0
          max: 1.0
        y_log_scale: True
        
    - id: am_class
      name: am_class
      type: str
      desc: |
        AlphaMissense Class is a deleteriousness category for missense variants
      histogram:
        type: categorical
        y_log_scale: True
  

Example 2: Categorical histogram configuration
""""""""""""""""""""""""""""""""""""""""""""""

Here is an example of a categorical histogram configuration displaying usage
of `plot_function`, `display_values_count`, and `display_values_percent` fields.
Note that `plot_function` uses the following format: 
``<python module>:<python function>``. The path to the python module should be
relative to the resource directory.

.. code:: yaml

	type: allele_score 
	table:
	  filename: clinvar_20221105_chr.vcf.gz
	  index_filename: clinvar_20221105_chr.vcf.gz.tbi
	scores:
	  - id: CLNSIG
	    name: CLNSIG
	    type: str
	    desc: |
	      Clinical significance for this single variant; multiple values 
          are separated by a vertical bar
	    histogram:
	      type: categorical
	      y_log_scale: True
	      plot_function: "clinvar_plots.py:plot_clnsig"
	  - id: CLNREVSTAT
	    name: CLNREVSTAT
	    type: str
	    desc: |
	      ClinVar review status for the Variation ID
	    histogram:
	      type: categorical
	      y_log_scale: True      
	      displayed_values_count: 35
	  - id: CLNVC
	    name: CLNVC
	    type: str
	    desc: |
	      Variant type
	    histogram:
	      type: categorical
	      y_log_scale: True
	      displayed_values_percent: 85.0

Here is the content of the `clinvar_plots.py` file:

.. code:: python

  from typing import IO
  from dae.genomic_resources.histogram import CategoricalHistogram
  import matplotlib
  import matplotlib.pyplot as plt
  matplotlib.use("agg")


  def plot_clnsig(
      outfile: IO,
      histogram: CategoricalHistogram,
      xlabel: str,
      _small_values_description: str | None = None,
      _large_values_description: str | None = None,
  ) -> None:
      """Plot histogram and save it into outfile."""
      # pylint: disable=import-outside-toplevel
      values = list(sorted(histogram.raw_values.items(), key=lambda x: -x[1]))
      values = [v for v in values if "|" not in v[0]]
      labels = [v[0] for v in values]
      counts = [v[1] for v in values]
   
      plt.figure(figsize=(40, 80), tight_layout=True)
      _, ax = plt.subplots()
      ax.bar(
          x=labels,
          height=counts,
          tick_label=[str(v) for v in labels],
          log=histogram.config.y_log_scale,
          align="center",
      )
      plt.xlabel(f"\n{xlabel}")
      plt.ylabel("count")
      plt.tick_params(axis="x", labelrotation=90, direction="out")
      plt.tight_layout()
      plt.savefig(outfile)
      plt.clf()

Null Histograms Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Null histograms are used when calculating a histogram is not possible or does not
make sense. The null histogram configuration supports the following fields:

* ``type`` - the type of the histogram. This should be set to ``null``.
* ``reason`` - the reason why the histogram is disabled. This field is required.


Resource repositories
=====================

Resource repositories are collections of genomic resources hosted either 
locally or remotely.

Repository discovery
--------------------

The GPF system will by default look for a ``.grr_definition.yaml`` file in the home directory of your user.

Alternatively, the system will use a repository configuration file pointed to by
the ``GRR_DEFINITION_FILE`` environment variable if it has been set.

Finally, most CLI tools that use GRRs have a ``--grr <filename>`` argument
that overrides the defaults.

To configure the GRRs to be used by default for your user, you can create
the file ``~/.grr_definition.yaml``. An example of what the contents of this file
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
      url: "https://grr.iossifovlab.com"
      cache_dir: "~/default_grr_cache"

Repository configuration
------------------------

=================  ================
Field              Description
=================  ================
id                 String. The id of the repository.
type               String. One of ``directory``, ``http``, ``url``, ``embedded`` or ``group``. These values are explained below.
children           List of repository configurations for ``group`` type repositories' children.
url                String. URL of the remote repository for ``http`` and ``url`` type repositories.
directory          String. Path to the directory of resources for ``directory`` type repositories.
content            Dictionary describing files and directories for ``embedded`` type repositories. Directories' values are further nested dictionaries, while files' values are the file contents.
cache_dir          String. Path to a directory in which the resources from this repository will be cached. 
=================  ================

``directory``
  A local filesystem repository.

``http``
  A remote HTTP repository.

``url``
  A remote S3 repository.

``embedded``
  An in-memory repository.

``group``
  A group of a number of repositories.


Caching of repositories
-----------------------

When a repository is configured with a ``cache_dir`` option, it will cache resources locally before using them.
It is significantly faster to use cached resources, but it takes some time to cache them the first time they are used and they occupy substantial disk space.

Management of resources and repositories with CLI tools
-------------------------------------------------------

The GPF system provides two CLI tools for management of genomic resources and repositories. Their usage is outlined below:

grr_manage
^^^^^^^^^^

.. runblock:: console

    $ grr_manage --help

grr_browse
^^^^^^^^^^

.. runblock:: console

    $ grr_browse --help

Tutorial: Create a local repository with a custom resource
==========================================================

The genomic resource is a set of files stored in a directory. To make given
directory a genomic resource, it should contain ``genomic_resource.yaml``
file.

A genomic resources repository is a directory that contains genomic resources.
To make a given directory into a repository, it should have a ``.CONTENTS``
file.

Create an empty GRR
-------------------

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
--------------------------------

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

This command is going to calculate histograms for the score (if they
are configured) and create or update the resource manifest.

Once the resource is ready we need to regenerate the repository contents:

.. code-block:: bash

    grr_manage repo-repair
