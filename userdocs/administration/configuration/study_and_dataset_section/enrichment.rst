.. _enrichment_section:

Enrichment Section
==================

The configuration section for enrichment data follows the general INI
format. Its name must be ``enrichment`` - this will indicate that it is an
enrichment data configuration section. This configuration section must properly
configure enrichment data for one study. This is an optional section.

[enrichment]
------------

The properties for this section are explained below.

peopleGroups
____________

.. code-block:: ini

  peopleGroups = <comma-separated list of people groups>

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
:ref:`people_group_section`), indicating which people groups to be used by
enrichment tool.

defaultBackgroundModel
______________________

.. code-block:: ini

  defaultBackgroundModel = <default background model id>

This property defines the default background model used by gpfjs.

selectedBackgroundValues
________________________

.. code-block:: ini

  selectedBackgroundValues = <comma-separated list of background ids>

A comma-separated list of selected background models. If this property is
missing then all defined background models in this section are selected.

background.<background model id>.file
_____________________________________

.. code-block:: ini

  background.<background model id>.file = <background model filename>

This property defines the filepath of the background model file. This is a
relative path to the enrichment directory which is in the same location as
the study configuration file.

background.<background model id>.name
_____________________________________

.. code-block:: ini

  background.<background model id>.name = <background model name>

Name of the background model. This name overrides the background id in the
enrichment configuration parser. This property is also used as a mapper between
background configuration and background class which defines the background
model.

background.<background model id>.desc
_____________________________________

.. FIXME:
  Fill me

.. code-block:: ini

  background.<background model id>.desc = <>

defaultCountingModel
____________________

.. code-block:: ini

  defaultCountingModel = <default counting model id>

This property defines the default counting model used by gpfjs.

selectedCountingValues
______________________

.. code-block:: ini

  selectedCountingValues = <comma-separated list of counter ids>

A comma-separated list of selected counters. If this property is missing then
all defined counters in this section are selected.

counting.<counting id>.name
___________________________

.. code-block:: ini

  counting.<counting id>.name = <counting name>

Name of the counter. This name overrides the counter id in the enrichment
configuration parser. This property is also used as mapper between counting
configuration and counting class which defines the counter.

counting.<counting id>.desc
___________________________

.. FIXME:
  Fill me

.. code-block:: ini

  counting.<counting id>.desc = <>

effect_types
____________

.. code-block:: ini

  effect_types = <comma-separated list of effect types>

This property defines a list of effect types for the enrichment tool groups.
The effect types are part of the variants query. Possible options for effect
types are listed :ref:`here <allowed_values_gene_effect_types>`.

enabled
_______

.. code-block:: ini

  enabled = <boolean>

DEFAULT
  ``True``

This property enables the enrichment functionality for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.

