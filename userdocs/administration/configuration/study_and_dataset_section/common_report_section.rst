[commonReport]
==============

The configuration section for a common report follows the general INI format
and must properly describe a common report for a single study. Its properties are explained below.

peopleGroups
------------

.. code-block:: ini

  peopleGroups = {comma-separated list of people groups}

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
the :ref:`peopleGroup` section in the study config), indicating for which people
groups to generate the ``Families by pedigree`` part of common report.

groups
------

.. code-block:: ini

  groups = {<column1>,<column2>:<name of common report group>|<column3>:<name of common report group>}

The format of this property is a list of common report groups separated by ``|``.
Each group is composed of two parts, separated by ``:`` - the first part is
a comma-separated list of pedigree columns and the second is the name of the
common report group.

This property defines the common report groups for the ``Families by number``
and ``De Novo Variants`` sections.

effect_groups
-------------

.. code-block:: ini

  effect_groups = {comma-separated list of effect groups}

This property defines a list of effect groups for the ``De Novo Variants``
section of the common report. The effect groups are part of the variants
query. Possible options for the effect groups and effect types that they contain
are:

* Coding
    * Nonsense
    * Frame-shift
    * Splice-site
    * No-frame-shift-newStop
    * Missense
    * No-frame-shift
    * noStart
    * noEnd
    * Synonymous

* Noncoding
    * Non coding
    * Intron
    * Intergenic
    * 3'-UTR
    * 5'-UTR

* CNV
    * CNV+
    * CNV

* LGDs
    * Frame-shift
    * Nonsense
    * Splice-site
    * No-frame-shift-newStop

* Nonsynonymous
    * Nonsense
    * Frame-shift
    * Splice-site
    * No-frame-shift-newStop
    * Missense
    * No-frame-shift
    * noStart
    * noEnd

* UTRs
    * 3'-UTR
    * 5'-UTR

effect_types
------------

.. code-block:: ini

  effect_types = {comma-separated list of effect types}

This property defines a list of effect types for the ``De Novo Variants`` section
of the common report. The effect types are part of the variants query.
Possible options for effect types are:

* 3'UTR

* 3'UTR-intron

* 5'UTR

* 5'UTR-intron

* frame-shift

* intergenic

* intron

* missense

* no-frame-shift

* no-frame-shift-newStop

* noEnd

* noStart

* non-coding

* non-coding-intron

* nonsense

* splice-site

* synonymous

* CDS

* CNV+

* CNV-

draw_all_families
-----------------

.. code-block:: ini

  draw_all_families = {<yes/Yes/true/True> or <no/No/false/False>}

This property defines whether to draw all families in the
``Families by pedigree`` section of the common report. This property takes
one of the boolean values shown above.

count_of_families_for_show_id
-----------------------------

.. code-block:: ini

  count_of_families_for_show_id = {max amount of family pedigrees with a family ids list}

This property defines the maximum number of family pedigrees in the ``Families by number``
section of the common report for which to display a list of all family ids. Other
family pedigrees will only have the amount of such families displayed. This
property takes an integer value.

enabled
-------

.. code-block:: ini

  enabled = {<yes/Yes/true/True> or <no/No/false/False>}

This property enables the common report functionality for the study.
It takes one of the boolean values shown above.
