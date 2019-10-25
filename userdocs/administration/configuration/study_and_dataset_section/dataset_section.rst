.. _dataset_section:

Dataset Section
===============

The configuration section for a dataset follows the general INI format. Its
name must be ``dataset`` - this will indicate that it is a dataset
configuration section. This configuration section must properly describe one
dataset. Either this section or the `ref:<study study_section>` section
must be present in the config file.


Example Configuration
---------------------

.. code-block:: ini

  [dataset]
  enabled = yes

  name = Dataset
  id = dataset

  studies = study

  description = %(work_dir)s/data/description.md

  authorizedGroups = any_user

  hasDenovo = yes
  hasTransmitted = no
  hasComplex = no
  hasCNV = no

  commonReport = True
  genotypeBrowser = True
  phenotypeBrowser = True
  enrichmentTool = False
  phenotypeTool = False

[dataset]
---------

The properties for this section are explained below.

name
____

.. code-block:: ini

  name = <dataset name>

Name which will be used as a display name for the dataset. The default value
is the value of the ``id`` property from the dataset.

id
__

.. code-block:: ini

  id = <dataset identifier>

Identifier of the dataset.

studies
_______

.. code-block:: ini

  studies = <comma-separated list of study ids>

This property defines which studies are in the dataset. It's format is a
comma-separated list of study ids. You can see the study section configuration
:ref:`here <study_section>`.

description
___________

.. code-block:: ini

  description = <study description>

This property shows if the ``Dataset Description`` tab is enabled for the
dataset.  It can contain a description as a string in markdown format or as an
absolute or relative path to a markdown file. You can see more about the
``Dataset Description`` tab :ref:`here <dataset_description_ui>`.

authorizedGroups
________________

.. code-block:: ini

  authorizedGroups = <comma-separated list of user groups>

This property defines a comma-separated list of user groups which are authorized
to access the dataset. It has a default value if and only if all of the defined
studies have this property. Its default value is a set of the the studies'
:ref:`authorizedGroups <study_section_authorized_groups>` properties. You can
more about groups :ref:`here <user_dataset_groups>`.

phenoDB
_______

.. code-block:: ini

  phenoDB = <pheno db name>

The corresponding :ref:`pheno DB <pheno_db>` for the dataset. It must be a
valid pheno DB id.

hasDenovo
_________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasDenovo = <boolean>

This property shows if the study contains variants with ``denovo`` inheritance.
It has default value if it is defined in all of the dataset's defined studies
and its value is ``True`` only if at least one of the studies'
:ref:`hasDenovo <study_section_has_denovo>` property is ``True`` as well. This
property takes a :ref:`boolean <allowed_values_booleans>` value.

hasTransmitted
______________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasTransmitted = <boolean>

This property shows if the study contains variants with ``transmitted``
inheritance. It has default value if it is defined in all of the dataset's
defined studies and its value is ``True`` only if at least one of the studies'
:ref:`hasTransmitted <study_section_has_transmitted>` property is ``True`` as
well. This property takes a :ref:`boolean <allowed_values_booleans>` value.

hasComplex
__________

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasComplex = <boolean>

This property shows if the study contains variants with ``complex`` variant
type. It has default value if it is defined in all of the dataset's defined
studies and its value is ``True`` only if at least one of the studies'
:ref:`hasComplex <study_section_has_complex>` property is ``True`` as well.
This property takes a :ref:`boolean <allowed_values_booleans>` value.

hasCNV
______

.. FIXME:
  Remove this property after implementing getting of its value from the study
  backend.

.. code-block:: ini

  hasCNV = <boolean>

This property shows if the study contains variants with ``CNV``, ``CNV+`` or
``CNV-`` effect types or ``CNV`` variant type. It has default value if it is
defined in all of the dataset's defined studies and its value is ``True`` only
if at least one of the studies' :ref:`hasCNV <study_section_has_CNV>` property
is ``True`` as well. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

commonReport
____________

.. code-block:: ini

  commonReport = <boolean>

This property shows if ``Dataset Statistics`` tab is enabled for the dataset.
You can see more about ``Dataset Statistics`` tab
:ref:`here <dataset_statistics_ui>`. It has default value if it is defined in
all of the dataset's defined studies and its value is ``True`` only if all of
the studies' :ref:`commonReport <study_section_common_report>` properties are
``True`` as well. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

genotypeBrowser
_______________

.. code-block:: ini

  genotypeBrowser = <boolean>

This property shows if ``Genotype Browser`` tab is enabled for the study. You
can see more about ``Genotype Browser`` tab :ref:`here <genotype_browser_ui>`.
It has default value if it is defined in all of the dataset's defined studies
and its value is ``True`` only if all of the studies'
:ref:`genotypeBrowser <study_section_genotype_browser>` properties are ``True``
as well. This property takes a :ref:`boolean <allowed_values_booleans>` value.

phenotypeBrowser
________________

.. code-block:: ini

  phenotypeBrowser = <boolean>

This property shows if ``Phenotype Browser`` tab is enabled for the study. You
can see more about ``Phenotype Browser`` tab
:ref:`here <phenotype_browser_ui>`. It has default value if it is defined in
all of the dataset's defined studies and its value is ``True`` only if all of
the studies' :ref:`phenotypeBrowser <study_section_phenotype_browser>`
properties are ``True`` as well. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

enrichmentTool
______________

.. code-block:: ini

  enrichmentTool = <boolean>

This property shows if ``Enrichment Tool`` tab is enabled for the study. You
can see more about ``Enrichment Tool`` tab :ref:`here <enrichment_tool_ui>`. It
has default value if it is defined in all of the dataset's defined studies and
its value is ``True`` only if all of the studies'
:ref:`enrichmentTool <study_section_enrichment_tool>` properties are ``True``
as well. This property takes a :ref:`boolean <allowed_values_booleans>` value.

phenotypeTool
_____________

.. code-block:: ini

  phenotypeTool = <boolean>

This property shows if ``Phenotype Tool`` tab is enabled for the study. You
can see more about ``Phenotype Tool`` tab :ref:`here <phenotype_tool_ui>`. It
has default value if it is defined in all of the dataset's defined studies and
its value is ``True`` only if all of the studies'
:ref:`phenotypeTool <study_section_phenotype_tool>` properties are ``True`` as
well. This property takes a :ref:`boolean <allowed_values_booleans>` value.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the dataset. This property takes a
:ref:`boolean <allowed_values_booleans>` value.
