.. _people_group_section:

People Group Section
====================

The configuration section for a people group follows the general INI format.
Its name must be ``peopleGroup`` - this will indicate that it is a
people group configuration section. This configuration section must properly
describe a people groups used by one study.

[peopleGroup]
-------------

Every defined people group represent group of peoples based on the values in
the pedigree file column ``<people group id>.source``.

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

Name of the people group indicates the dispay name of the people group.

<people group id>.domain
________________________

.. code-block:: ini

  <people group id>.domain = <<<people group element id>:<people group element name>:<people group element color>>,<...>>

Domain defines list of elements of the people group. In this property are
defined different values present in ``<people group id>.source`` column in the
pedigree file. ``<people group element id>`` indicates the value in the
pedigree file ``<people group id>.source`` column of the people group element,
``<people group element name>`` indicate the dispay name of the people group
element, ``<people group element color>`` indicate the dispay color of the
people group element.

<people group id>.default
_________________________

.. code-block:: ini

  <people group id>.default = <<<people group element id>:<people group element name>:people group element color>>

Default property of the people group is used for default people group element.
Structure is similar to one of the ``<people group id>.domain`` elements. This
default element is used when people value in the ``<people group id>.source``
column in the pedigree file can't be found in one of the
``<people group element id>`` of the people group's
``<people group id>.domain``.

<people group id>.source
________________________

.. code-block:: ini

  <people group id>.source = <source of people group>

This property define source of the people group. This source is one of the
columns from the pedigree file.
