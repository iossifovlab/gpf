.. _genotype_browser_section:

Genotype Browser Section
========================

The configuration section for a genotype browser follows the general INI
format. Its name must be ``genotypeBrowser`` - this will indicate that it is a
genotype browser configuration section. This configuration section must
properly describe the genotype browser for the study. This is an optional
section.

Example Configuration
---------------------

.. code-block:: ini

  [genotypeBrowser]
  hasCNV = no
  hasComplex = no
  hasStudyTypes = no
  hasStudyFilters = no
  hasFamilyFilters = yes
  hasPresentInRole = no
  hasPresentInChild = no
  hasPresentInParent = no
  hasPedigreeSelector = yes
  hasGraphicalPreview = yes
  inheritanceTypeFilter = mendelian, denovo
  selectedInheritanceTypeFilterValues = mendelian, denovo

  selectedPhenoFiltersValues = continuous

  phenoFilters.continuous.name = Continuous
  phenoFilters.continuous.measureType = continuous
  phenoFilters.continuous.filter = multi:prb

  selectedPresentInRoleValues = parent

  presentInRole.parent.name = Parents
  presentInRole.parent.roles = mom,dad

  selectedGenotypeColumnValues = family,variant,inchild

  genotype.family.name = family
  genotype.family.slots = family:family id,studyName:study

  genotype.variant.name = variant
  genotype.variant.slots = location:location,variant:variant

  genotype.genotype.name = genotype
  genotype.genotype.source = pedigree
  genotype.genotype.slots = inChild:in child,fromParent:from parent

  genotype.inchild.name = in child
  genotype.inchild.source = inChS

  genotype.fromparent.name = from parent
  genotype.fromparent.source = fromParentS

  selectedPhenoColumnValues = pheno

  pheno.pheno.name = Measures
  pheno.pheno.slots = prb:i1.age:Age:%%.2f,
      prb:i1.iq:Iq:%%.2f

  selectedInRolesValues = inChild,fromParentS

  inRoles.inChild.destination = inChS
  inRoles.inChild.roles = prb,sib

  inRoles.fromParents.destination = fromParentS
  inRoles.fromParents.roles = mom,dad

  previewColumns = family,variant,pheno
  downloadColumns = family,variant,inchild

[genotypeBrowser]
-----------------

The properties for this section are explained below.

hasCNV
______

.. code-block:: ini

  hasCNV = <boolean>

This property determines:

  * if the ``CNV+`` and ``CNV*`` effect types (part of the ``CNV`` effect
    group) are present in the ``Effect Types`` filter in the
    ``Genotype Browser`` for the study.

  * if the ``CNV``, ``CNV+`` and ``CNV*`` effect types are present in the
    ``Effect Types`` filter in the ``Phenotype Tool`` for the study.

  * if the ``CNV`` variant type is present in the ``Variant Types`` filter in
    the ``Genotype Browser`` for the study.

This property takes a :ref:`boolean <allowed_values_booleans>` value.

hasComplex
__________

.. code-block:: ini

  hasComplex = <boolean>

This property determines whether the ``complex`` variant type is present in the
``Variant Types`` filter in the ``Genotype Browser`` for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.

hasStudyTypes
_____________

.. code-block:: ini

  hasStudyTypes = <boolean>

This property determines whether the ``Study Types`` filter is present in the
``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

hasStudyFilters
_______________

.. code-block:: ini

  hasStudyFilters = <boolean>

This property determines whether the ``Studies`` filter block is present in the
``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

hasFamilyFilters
________________

.. code-block:: ini

  hasFamilyFilters = <boolean>

This property determines if the ``Family`` filter block is present in the
``Genotype Browser`` and ``Phenotype Tool`` for the study. This property takes
a :ref:`boolean <allowed_values_booleans>` value.

hasPresentInRole
________________

.. code-block:: ini

  hasPresentInRole = <boolean>

This property determines if the ``Present in Role`` filter is present in the
``Genotype Browser`` for the study. This property takes
a :ref:`boolean <allowed_values_booleans>` value. You can see the configuration
of ``Present in Role`` :ref:`here <present_in_role_property>`.

hasPresentInChild
_________________

.. code-block:: ini

  hasPresentInChild = <boolean>

This property determines if the ``Present in Child`` filter is present in the
``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

hasPresentInParent
__________________

.. code-block:: ini

  hasPresentInParent = <boolean>

This property determines if the ``Present in Parent`` filter is present in the
``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

hasPedigreeSelector
___________________

.. code-block:: ini

  hasPedigreeSelector = <boolean>

This property determines if the ``Pedigree Selector`` filter is present in the
``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value. The ``Pedigree Selector``
filter presents the configured people groups and their values as options to
filter variants by.

hasGraphicalPreview
___________________

.. code-block:: ini

  hasGraphicalPreview = <boolean>

This property determines if the user can make a ``Graphical Preview`` request
in the ``Genotype Browser`` for the study. This property takes a
:ref:`boolean <allowed_values_booleans>` value.

inheritanceTypeFilter
_____________________

.. code-block:: ini

  inheritanceTypeFilter = <comma-separated list of inheritance types>

This is a list of inheritance types that will be available as filters in the
``Genotype Browser`` for the study. You can see the available values
:ref:`here <allowed_values_inheritance>`.

selectedInheritanceTypeFilterValues
___________________________________

.. code-block:: ini

  selectedInheritanceTypeFilterValues = <comma-separated list of inheritance types>

This is a list of inheritance type filters that will be selected by default on
a study's page in the ``Genotype Browser``. Note that these values must
be present in the ``inheritanceTypeFilter`` property. You can see the available
values :ref:`here <allowed_values_inheritance>`.

familyFilters
_____________

.. FIXME:
  Fill me

.. code-block:: ini

  familyFilters = <>

selectedPhenoFiltersValues
__________________________

.. code-block:: ini

  selectedPhenoFiltersValues = <comma-separated list of pheno filter ids>

A comma-separated list of selected pheno filters. If this property is
missing then all defined pheno filters in this section are selected.

phenoFilters.<pheno filter id>.name
___________________________________

.. FIXME:
  Fill me

.. code-block:: ini

  phenoFilters.<pheno filter id>.name = <>

phenoFilters.<pheno filter id>.measureType
__________________________________________

.. FIXME:
  Fill me

.. code-block:: ini

  phenoFilters.<pheno filter id>.measureType = <>

phenoFilters.<pheno filter id>.filter
_____________________________________

.. code-block:: ini

  phenoFilters.<pheno filter id>.filter = <<filter_type>:<role>:<optional: measure>>

.. FIXME:
  Fill me

.. _present_in_role_property:

selectedPresentInRoleValues
___________________________

.. code-block:: ini

  selectedPresentInRoleValues = <comma-separated list of presentInRole ids>

A comma-separated list of selected presentInRole values. If this property is
missing then all defined presentInRole values in this section are selected.

presentInRole.<present in role id>.id
______________________________________

.. code-block:: ini

  presentInRole.<present in role id>.id = <present in role identifier>

Identifier of present in role. Default value is ``<present in role id>`` from
the present in role property name.

presentInRole.<present in role id>.name
_______________________________________

.. code-block:: ini

  presentInRole.<present in role id>.name = <present in role name>

This property defines the display name of the ``Present in Role`` filter in the
``Genotype Browser`` for the study.

presentInRole.<present in role id>.roles
________________________________________

.. code-block:: ini

  presentInRole.<present in role id>.roles = <comma-separated list of roles>

This property defines which roles are available to the ``Present in Role``
filter in the ``Genotype Browser`` for the study.

selectedGenotypeColumnValues
____________________________

.. code-block:: ini

  selectedGenotypeColumnValues = <comma-separated list of genotype column ids>

A comma-separated list of selected genotype columns. If this property is
missing, then all defined genotype columns in this section are selected.

genotype.<genotype columns id>.id
_________________________________

.. code-block:: ini

  genotype.<genotype columns id>.id = <genotype column identifier>

Identifier of the genotype column. Default value is ``<genotype column id>``
from the genotype column property name.

genotype.<genotype columns id>.name
___________________________________

.. code-block:: ini

  genotype.<genotype columns id>.name = <genotype column name>

Display name of the genotype column used in the header of the table in the
``Table Preview`` query in ``Genotype Browser`` for the study.

genotype.<genotype columns id>.source
_____________________________________

.. code-block:: ini

  genotype.<genotype columns id>.source = <genotype column source>

This property defines the source of the values for this column. This is
selected from the raw study data column names.

genotype.<genotype columns id>.slots
____________________________________

.. code-block:: ini

  genotype.<genotype columns id>.slots = <<source>:<label>:<label_format>>

A genotype column can be split up into multiple sub-columns. These are called
slots. Each slot is defined by:

  * ``<source>`` - analogous to the ``genotype.<genotype columns id>.source``
    property above.

  * ``<label>`` - display name of this slot in the genotype column in the
    preview table in the ``Genotype Browser``.

  * ``<label format>`` - format of the values in this slot. This property is
    optional and default value for it is ``%s``.

selectedPhenoColumnValues
_________________________

.. code-block:: ini

  selectedPhenoColumnValues = <comma-separated list of phenotype column ids>

A comma-separated list of selected phenotype columns. If this property is
missing then all defined phenotype columns in this section are selected.

pheno.<phenotype column id>.id
______________________________

.. code-block:: ini

  pheno.<phenotype column id>.id = <phenotype column identifier>

Identifier of the phenotype column. Default value is ``<phenotype column id>``
from the phenotype column property name.

pheno.<phenotype column id>.name
________________________________

.. code-block:: ini

  pheno.<phenotype column id>.name = <phenotype column name>

Display name of the phenotype column used in the header of the preview table in
the ``Genotype Browser`` for the study.

pheno.<phenotype column id>.slots
_________________________________

.. code-block:: ini

  pheno.<phenotype column id>.slots = <<role>:<source>:<label>:<label format>>

Slots of the phenotype column in the header of the preview table in the
``Genotype Browser`` for the study. Each slot is defined by:

  * ``<role>`` - apply the filter for people with this role.

  * ``<source>`` - the id of the phenotype measure whose values will be
    displayed.

  * ``<label>`` - display name of this slot.

  * ``<label format>`` - format of the values in this slot. This property is
    optional and the default value for it is ``%s``.

inRoles
_______

Each of the defined ``inRoles`` will be added to the variant as a new,
generated column. This new column will contain information about defined roles
in the ``inRoles.<in role column id>.roles``. The resulting list will be all
possible combinations of the role from roles list with the gender of the people
with this role. The newly generated column can be optionally defined as a
genotype column.

selectedInRolesValues
.....................

.. code-block:: ini

  selectedInRolesValues = <comma-separated list of in role column ids>

A comma-separated list of selected ``inRoles`` columns. If this property is
missing, then all defined ``inRoles`` columns in this section are selected.

inRoles.<in role column id>.id
..............................

.. code-block:: ini

  inRoles.<in role column id>.id = <in role column identifier>

Identifier of the ``inRoles`` column. Default value is ``<in role column id>``
from the ``inRoles`` column property name.

inRoles.<in role column id>.destination
.......................................

.. code-block:: ini

  inRoles.<in role column id>.destination = <destination column name>

The name of the column in the variant which will contain the generated values.
Default value for this property is ``inRoles.<in role column id>.id``.

inRoles.<in role column id>.roles
.................................

.. code-block:: ini

  inRoles.<in role column id>.roles = <comma-separated list of roles>

A comma-separated list of roles which will be used for the generation of the
new column.

previewColumns
______________

.. code-block:: ini

  previewColumns = <comma-separated list of genotype or phenotype column ids>

Which columns to display in the preview table of the ``Genotype Browser`` of
the study. Possible values in this list are genotype or phenotype column ids.

downloadColumns
_______________

.. code-block:: ini

  downloadColumns = <comma-separated list of genotype or phenotype column ids>


Which columns to include in the download table file of the ``Genotype Browser``
of the study. Possible values in this list are genotype or phenotype column
ids. Slots will be expanded into independent columns.
