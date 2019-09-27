.. _denovo_gene_sets_section:

Denovo Gene Sets Section
========================

The configuration section for a denovo gene sets follows the general INI
format. Its name must be ``denovoGeneSets`` - this will indicate that it is a
denovo gene sets configuration section. This configuration section must
properly describe a denovo gene sets for one study.

[denovoGeneSets]
----------------

Down below are explained proprties of this section.

peopleGroups
____________

.. code-block:: ini

  peopleGroups = <comma-separated list of people groups>

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
the :ref:`people_group_section` section in the study config), indicating for
which people groups to generate denovo gene sets.

standardCriterias.<standard criteria id>.segments
_________________________________________________

.. code-block:: ini

  standardCriterias.<standard criteria id>.segments = <<<standard criteria name 1>:<standard criteria value 1>>,<<standard criteria name 2>:<standard criteria value 2>>,<...>>

This properly defines standard criteria segments indicating group in denovo
gene sets. ``<standard criteria id>`` indicates filter used in quering variants
for denovo gene set group defined by this standard criteria,
``<standard criteria name>`` indicates display name of group defined by this
standard criteria and ``<standard criteria value>`` indicates value used in
quering variants for denovo gene set group defined by this standard criteria.

recurrencyCriteria.segments
___________________________

.. FIXME:
 Fill me

.. code-block:: ini

  recurrencyCriteria.segments = <>

geneSetsNames
_____________

.. code-block:: ini

  geneSetsNames = <<<standard or recurrency criteria 1>.<standard or recurrency criteria 2>.<...>>,<...>>

Name of denovo gene set combination which is defined by standard or recurrency
criterias. This name represent configuration of denovo gene set.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

This property enables the common report functionality for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.
