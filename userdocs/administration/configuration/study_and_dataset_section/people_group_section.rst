.. _people_group_section:

People Group Section
====================

The configuration section for a people group follows the general INI format.
Its name must be ``peopleGroup`` - this will indicate that it is a
people group configuration section. This configuration section must properly
describe a people groups used by one study. This is an optional section.

Example Configuration
---------------------

.. code-block:: ini

  [peopleGroup]
  selectedPeopleGroupValues = status

  status.name = Affected Status
  status.domain = affected:affected:#e35252,
      unaffected:unaffected:#ffffff
  status.default = unspecified:unspecified:#aaaaaa
  status.source = status

[peopleGroup]
-------------

Every defined people group represents a group of people based on the values in
the pedigree file column ``<people group id>.source``. The properties for this
section are explained below.

selectedPeopleGroupValues
_________________________

.. code-block:: ini

  selectedPeopleGroupValues = <comma-separated list of people group ids>

A comma-separated list of selected people groups. If this property is
missing then all defined people groups in this section are selected.

<people group id>.id
____________________

.. code-block:: ini

  <people group id>.id = <people group identifier>

Identifier of the people group. Default value is ``<people group id>`` from the
people group property name.

<people group id>.name
______________________

.. code-block:: ini

  <people group id>.name = <people group name>

Indicates the display name of the people group.

<people group id>.domain
________________________

.. code-block:: ini

  <people group id>.domain = <<<people group element id>:<people group element name>:<people group element color>>,<...>>

The domain property maps display names and colors to the set of values present
in the ``<people group id>.source`` column in the pedigree file. These are the
elements of each mapping:

  * ``<people group element id>`` selects the value from the column.

  * ``<people group element name>`` indicates the display name of the people
    group element.

  * ``<people group element color>`` indicates the display color of the people
    group element.

<people group id>.default
_________________________

.. code-block:: ini

  <people group id>.default = <<<people group element id>:<people group element name>:people group element color>>

This property is defined in the same way as a single mapping from the
``<people group id>.domain`` property. It is applied to any value in the column
from the pedigree file for which there is no mapping defined in the
``<people group id>.domain`` property.

<people group id>.source
________________________

.. code-block:: ini

  <people group id>.source = <source of people group>

This property defines the source of the people group. This source is one of the
columns from the pedigree file.
