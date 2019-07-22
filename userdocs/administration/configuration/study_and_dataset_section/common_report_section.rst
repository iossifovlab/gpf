Common Report Section
=====================

The configuration section for a common report follows the general INI format.
Its name must be ``commonReport`` - this will indicate that it is a common
report configuration section. This configuration section must properly describe
a common report for one study. Its properties , which must belong to the
``commonReport`` section, are explained below.

peopleGroups
------------

.. code-block:: ini

  peopleGroups = {comma separated list of people groups}

``peopleGroups`` is a comma separated list of ids of people groups (defined in
the :ref:`peopleGroup` section in the study config) indicating for which people
groups to generate ``Families by pedigree`` part of common report.

groups
------

.. code-block:: ini

  groups = {<column1>,<column2>:<name of common report group>|<column3>:<name of common report group>}

Format of this property is list of common report groups separated by ``|``.
Each group is composed of two parts, separated by ``:`` - the first part is
comma separated list of pedigree columns and the second is the name of the
common report group.

This property defines the common report groups for the ``Families by number``
and ``De Novo Variants`` sections.

effect_groups
-------------

.. code-block:: ini

  effect_groups = {comma separated list of effect groups}

This property defines list of effect groups for the ``De Novo Variants``
section of the common report. This effect groups are part of the variants
query. Possible options for effect groups and effect types that they contain
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

  effect_types = {comma separated list of effect types}

This property defines list of effect types for the ``De Novo Variants`` section
of the common report. This effect types are part of the variants query.
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

  draw_all_families = {whether to draw all families in families report}

This property defines whether to draw or not to draw all families in the
``Families by pedigree`` section of the common report. This property takes
boolean values (Boolean values can be ``yes/no``, ``Yes/No``, ``true/false``,
``True/False``).

count_of_families_for_show_id
-----------------------------

.. code-block:: ini

  count_of_families_for_show_id = {the maximum number of families with all families to display list ids for}

This property shows maximum number of families in ``Families by number``
section of the common report for which to display list of all family ids. This
property takes integer value.

enabled
-------

.. code-block:: ini

  enabled = {whether common report is enabled for this study}

This property shows whether common report is enabled in the study to which it
belong. This property takes boolean values (Boolean values can be ``yes/no``,
``Yes/No``, ``true/false``, ``True/False``).
