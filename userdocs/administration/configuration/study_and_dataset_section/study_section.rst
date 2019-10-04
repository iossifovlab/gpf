.. _study_section:

Study Section
=============

The configuration section for a study follows the general INI format. Its name
must be ``study`` - this will indicate that it is a study configuration
section. This configuration section must properly describe one study. This is a
required section.

[study]
-------

The properties for this section are explained below.

name
____

.. code-block:: ini

  name = <study name>

Name which will be used as display name for the study. Default value for it is
the value of the ``id`` property from the study.

id
__

.. code-block:: ini

  id = <study identifier>

Identifier of the study.

description
___________

.. code-block:: ini

  description = <study description>

This property show if ``Dataset Description`` tab is enabled for the study. It
can contain description as a string in markdown format or as a absolute or
relative path to file in markdown format. You can see more about
``Dataset Description`` tab :ref:`here <dataset_description_ui>`.

prefix
______

.. code-block:: ini

  prefix = <directory of data>

This property show the location of the directory with study data files. It can
be absolute path or relative. If it is relative path it must be relative to the
directory contains study configuration file.

file_format
___________

.. code-block:: ini

  file_format = <study data file format - vcf / impala>

This property show file format of the study data files. Supported formats are
``impala`` and ``vcf``. In the ``impala`` format files are querying with the
help of ``Apache Impala`` and the expected file format is ``Apache Parquet``.
On the other hand if it is choosed ``vcf`` file format files are expected to be
valid ``tsv`` files which to be in the ``vcf`` format. Querying in ``vcf`` file
format is implemented with the help of ``pandas``.

authorizedGroups
________________

.. code-block:: ini

  authorizedGroups = <comma-separated list of user groups>

This property defines comma-separated list of user groups which are authorized
to access the study. You can more about groups
:ref:`here <user_dataset_groups>`.

phenoDB
_______

.. code-block:: ini

  phenoDB = <pheno db name>

The corresponding :ref:`pheno DB <pheno_db>` for the study. It must be valid
pheno DB id.

studyType
_________

.. code-block:: ini

  studyType = <study type WE / WG / TG>

This property gives the type of the study. Possible types are:

  * ``WE`` - Whole Exome

  * ``WG`` - Whole Genome

  * ``TG`` - Targeted Genome

year
____

.. code-block:: ini

  year = <year in YYYY format>

This property store release year of the study. Format of this property is
number in the YYYY format.

pubMed
______

.. code-block:: ini

  pubMed = <id of PubMed article>

This property contains id of an article from PubMed assosiated with the study.
You can see more about PubMed in there site - https://www.ncbi.nlm.nih.gov/pubmed/.

hasDenovo
_________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasDenovo = <boolean>

This property show if the study contains variants with ``denovo`` inheritance.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

hasTransmitted
______________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasTransmitted = <boolean>

This property show if the study contains variants with ``transmitted``
inheritance. This property takes a :ref:`boolean <allowed_values_booleans>`
value.

hasComplex
__________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasComplex = <boolean>

This property show if the study contains variants with ``complex`` variant
type. This property takes a :ref:`boolean <allowed_values_booleans>` value.

hasCNV
______

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasCNV = <boolean>

This property show if the study contains variants with ``CNV``, ``CNV+`` or
``CNV-`` effect types or ``CNV`` variant type. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

commonReport
____________

.. code-block:: ini

  commonReport = <boolean>

This property show if ``Dataset Statistics`` tab is enabled for the study. You
can see more about ``Dataset Statistics`` tab
:ref:`here <dataset_statistics_ui>`. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

genotypeBrowser
_______________

.. code-block:: ini

  genotypeBrowser = <boolean>

This property show if ``Genotype Browser`` tab is enabled for the study. You
can see more about ``Genotype Browser`` tab :ref:`here <genotype_browser_ui>`.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

phenotypeBrowser
________________

.. code-block:: ini

  phenotypeBrowser = <boolean>

This property show if ``Phenotype Browser`` tab is enabled for the study. You
can see more about ``Phenotype Browser`` tab
:ref:`here <phenotype_browser_ui>`. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

enrichmentTool
______________

.. code-block:: ini

  enrichmentTool = <boolean>

This property show if ``Enrichment Tool`` tab is enabled for the study. You
can see more about ``Enrichment Tool`` tab :ref:`here <enrichment_tool_ui>`.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

phenotypeTool
_____________

.. code-block:: ini

  phenotypeTool = <boolean>

This property show if ``Phenotype Tool`` tab is enabled for the study. You
can see more about ``Phenotype Tool`` tab :ref:`here <phenotype_tool_ui>`.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.


.. FIXME:
  Review this study properties:
    pedigree_file
    summary_files
    family_files
    effect_gene_files
    member_files
