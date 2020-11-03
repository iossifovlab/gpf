.. _common_report_section:

Common Reports Section
======================

The configuration section for a common report follows the general INI format
and must properly describe a common report for a single study. Its name must be
``commonReport`` - this will indicate that it is a common report section. This
is an optional section.

Example Configuration
---------------------

.. code-block:: ini

  [commonReport]
  enabled = yes

  peopleGroups = status
  groups = role:Role|status:Status|role,status:Role and Status

  effect_groups = LGDs,nonsynonymous,UTRs
  effect_types = Nonsense,Frame-shift,Splice-site,Missense,No-frame-shift
      noStart,noEnd,Synonymous,Non coding,Intron,Intergenic,3'-UTR,5'-UTR

  draw_all_families = False
  families_count_show_id = 3

[commonReport]
--------------

The properties for this section are explained below.

peopleGroups
____________

.. code-block:: ini

  peopleGroups = <comma-separated list of people groups>

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
the :ref:`people_group_section` section in the study config), indicating for
which people groups to generate the ``Families by pedigree`` part of common
report.

groups
______

.. code-block:: ini

  groups = <<column1>,<column2>:<name of common report group>|<column3>:<name of common report group>>

The format of this property is a list of common report groups separated by
``|``. Each group is composed of two parts, separated by ``:`` - the first part
is a comma-separated list of pedigree columns and the second is the name of the
common report group.

This property defines the common report groups for the ``Families by number``
and ``De Novo Variants`` sections.

effect_groups
_____________

.. code-block:: ini

  effect_groups = <comma-separated list of effect groups>

This property defines a list of effect groups for the ``De Novo Variants``
section of the common report. The effect groups are part of the variants
query. Possible options for the effect groups and effect types that they
contain are listed :ref:`here <allowed_values_gene_effect_groups>`.

effect_types
____________

.. code-block:: ini

  effect_types = <comma-separated list of effect types>

This property defines a list of effect types for the ``De Novo Variants``
section of the common report. The effect types are part of the variants query.
Possible options for effect types are listed
:ref:`here <allowed_values_gene_effect_types>`.

draw_all_families
_________________

.. code-block:: ini

  draw_all_families = <boolean>

This property defines whether to draw all families in the
``Families by pedigree`` section of the common report. This property takes
a :ref:`boolean <allowed_values_booleans>` value.

DEFAULT
  .. code-block::
    from dae.common_reports.config import CommonReportsConfigParser

    print(f'``{CommonReportsConfigParser.DRAW_ALL_FAMILIES_DEFAULT}``')

families_count_show_id
______________________

.. code-block:: ini

  families_count_show_id = <max amount of family pedigrees with a family ids list>

This property defines the maximum number of family pedigrees in the
``Families by number`` section of the common report for which to display a list
of all family ids. Other family pedigrees will only have the amount of such
families displayed. This property takes an integer value.

file_path
_________

.. code-block:: ini

  file_path = <string>

This property difines file path of the common report file.

DEFAULT
  ``<directory of the config file>/common_report.json``

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the common report functionality for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.
