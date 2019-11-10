.. _study_section:

Study Section
=============

The configuration section for a study follows the general INI format. Its name
must be ``study`` - this will indicate that it is a study configuration
section. This configuration section must properly describe one study.
Either this section or the `ref:<dataset dataset_section>` section must
be present in the config file.

Example Configuration
---------------------

.. code-block:: ini

  [study]
  enabled = yes

  name = Study
  id = study

  prefix = data
  file_format = vcf
  description = %(work_dir)s/data/description.md

  studyType = WE
  year = 2019

  hasDenovo = yes
  hasTransmitted = no
  hasComplex = no
  hasCNV = no

  commonReport = True
  genotypeBrowser = True
  phenotypeBrowser = True
  enrichmentTool = False
  phenotypeTool = False

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

This property shows if the ``Dataset Description`` tab is enabled for the
study. It can contain a description as a string in markdown format or as an
absolute or relative path to a markdown file. You can see more about the
``Dataset Description`` tab :ref:`here <dataset_description_ui>`.

prefix
______

.. code-block:: ini

  prefix = <directory of data>

This property shows the location of the directory that contains the study's
data files. It can be an absolute or relative path. If it is a relative path,
it must be relative to the directory containing the study's configuration file.

file_format
___________

.. code-block:: ini

  file_format = <vcf / impala>

This property shows the file format of the study data files. Supported formats
are ``impala`` and ``vcf``. In the ``impala`` format, files are queried with
the help of ``Apache Impala`` and the expected file format is ``Apache
Parquet``.  On the other hand, if ``vcf`` is the chosen file format, files are
expected to be valid ``tsv`` files in the VCF format. Querying in the VCF file
format is implemented with the help of ``pandas``.

phenoDB
_______

.. code-block:: ini

  phenoDB = <pheno db name>

The corresponding :ref:`pheno DB <pheno_db>` for the study. It must be a valid
pheno DB id.

studyType
_________

.. code-block:: ini

  studyType = <WE / WG / TG>

This property gives the type of the study. Possible types are:

  * ``WE`` - Whole Exome

  * ``WG`` - Whole Genome

  * ``TG`` - Targeted Genome

year
____

.. code-block:: ini

  year = <YYYY>

This property specifies the release year of the study.

pubMed
______

.. code-block:: ini

  pubMed = <id of PubMed article>

This property contains the id of an article from PubMed associated with the
study. You can see more about PubMed on their website -
https://www.ncbi.nlm.nih.gov/pubmed/.

.. _study_section_has_denovo:

hasDenovo
_________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasDenovo = <boolean>

This property specifies if the study contains variants with ``denovo``
inheritance. This property takes a :ref:`boolean <allowed_values_booleans>`
value.

.. _study_section_has_transmitted:

hasTransmitted
______________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasTransmitted = <boolean>

This property specifies if the study contains variants with ``transmitted``
type inheritance.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

.. _study_section_has_complex:

hasComplex
__________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasComplex = <boolean>

This property specifies if the study contains variants with ``complex`` variant
type. This property takes a :ref:`boolean <allowed_values_booleans>` value.

.. _study_section_has_CNV:

hasCNV
______

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasCNV = <boolean>

This property shows if the study contains variants with ``CNV``, ``CNV+`` or
``CNV-`` effect types or ``CNV`` variant type. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

.. _study_section_common_report:

commonReport
____________

.. code-block:: ini

  commonReport = <boolean>

This property specifies if the ``Dataset Statistics`` tab is enabled for the
study. You can see more about the ``Dataset Statistics`` tab
:ref:`here <dataset_statistics_ui>`. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

.. _study_section_genotype_browser:

genotypeBrowser
_______________

.. code-block:: ini

  genotypeBrowser = <boolean>

This property specifies if the ``Genotype Browser`` tab is enabled for the
study. You can see more about the ``Genotype Browser`` tab
:ref:`here <genotype_browser_ui>`.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

.. _study_section_phenotype_browser:

phenotypeBrowser
________________

.. code-block:: ini

  phenotypeBrowser = <boolean>

This property specifies if the ``Phenotype Browser`` tab is enabled for the
study. You can see more about the ``Phenotype Browser`` tab
:ref:`here <phenotype_browser_ui>`. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

.. _study_section_enrichment_tool:

enrichmentTool
______________

.. code-block:: ini

  enrichmentTool = <boolean>

This property specifies if the ``Enrichment Tool`` tab is enabled for the
study. You can see more about the ``Enrichment Tool`` tab
:ref:`here <enrichment_tool_ui>`. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

.. _study_section_phenotype_tool:

phenotypeTool
_____________

.. code-block:: ini

  phenotypeTool = <boolean>

This property specifies if the ``Phenotype Tool`` tab is enabled for the study.
You can see more about the ``Phenotype Tool``
tab :ref:`here <phenotype_tool_ui>`.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.
