.. _denovo_gene_sets_section:

Denovo Gene Sets Section
========================

The configuration section for denovo gene sets follows the general INI format.
Its name must be ``denovoGeneSets`` - this will indicate that it is a denovo
gene sets configuration section. This configuration section must properly
describe one or more denovo gene sets for one study. This is an optional
section.

Example Configuration
---------------------

.. code-block:: ini

  [denovoGeneSets]
  enabled = yes

  peopleGroups = status

  standardCriterias.effect_types.segments=LGDs:LGDs,Missense:missense,Synonymous:synonymous
  standardCriterias.sexes.segments=Female:F,Male:M,Unspecified:U

  recurrencyCriteria.segments=Single:1:2,Triple:3:-1,Recurrent:2:-1

  geneSetsNames=LGDs,LGDs.Male,LGDs.Female,LGDs.Recurrent,LGDs.Single,LGDs.Triple,
      Missense,Missense.Male,Missense.Female,Missense.Recurrent,Missense.Triple,
      Synonymous,Synonymous.Male,Synonymous.Female,Synonymous.Recurrent,Synonymous.Triple

[denovoGeneSets]
----------------

The properties for this section are explained below.

peopleGroups
____________

.. code-block:: ini

  peopleGroups = <comma-separated list of people groups>

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
the :ref:`people_group_section` section in the study config), indicating
which people groups to generate denovo gene sets for.

standardCriterias.<standard criteria id>.segments
_________________________________________________

.. FIXME:
  Add link to `here` reference for variants querying filters.

.. code-block:: ini

  standardCriterias.<standard criteria id>.segments = <<<standard criteria name 1>:<standard criteria value 1>>,<<standard criteria name 2>:<standard criteria value 2>>,<...>>

This property defines standard criteria segments indicating a group of genes
and their families. The configured standard criterias can be combined together,
or with ``recurrencyCriteria``, in the ``geneSetsNames`` property in this
section. The combinations will then be added as groups of denovo gene sets
(which will be available in the ``Gene Sets`` filter in the
``Genotype Browser`` of the study).

Elements of the standard criteria segments are:

  * ``<standard criteria id>`` indicates the id of the standard criteria.
    The id must be one of the defined filters by which you can query variants
    in the backend. The possible filters are defined here.

  * ``<standard criteria name>`` indicates the display name of the group
    defined by this standard criteria.

  * ``<standard criteria value>`` indicates the value used when querying
    variants for the denovo gene set group defined by this standard criteria.

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

The names of denovo gene set combinations which are defined by combining
``standardCriterias`` and/or ``recurrencyCriteria``. This name represents the
configuration of the denovo gene set. All combinations listed here will be
available in the ``Gene Sets`` filter in the ``Genotype Browser`` of
the study.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the denovo gene sets functionality for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.
