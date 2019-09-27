.. _enrichment_section:

Enrichment Section
==================

The configuration section for a enrichment follows the general INI format. Its
name must be ``enrichment`` - this will indicate that it is a enrichment
configuration section. This configuration section must properly describe a
enrichment tool for one study.

[enrichment]
------------

Down below are explained proprties of this section.

peopleGroups
____________

.. code-block:: ini

  peopleGroups = <comma-separated list of people groups>

``peopleGroups`` is a comma-separated list of ids of people groups (defined in
the :ref:`people_group_section` section in the study config), indicating which
people groups to be used by enrichment tool.

defaultBackgroundModel
______________________

.. code-block:: ini

  defaultBackgroundModel = <default background model id>

This property defines default background model used by gpfjs.

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

This property difines file path of the background model file. This is relative
path to the enrichment directory which is in the same location as the study
configuration file.

background.<background model id>.name
_____________________________________

.. code-block:: ini

  background.<background model id>.name = <background model name>

Name of the background model. This name override background id in the
enrichment configuration parser. This property is also used as mapper between
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

This property defines default counting model used by gpfjs.

selectedCountingValues
______________________

.. code-block:: ini

  selectedCountingValues = <comma-separated list of counting ids>

A comma-separated list of selected countings. If this property is missing then
all defined countings in this section are selected.

counting.<counting id>.name
___________________________

.. code-block:: ini

  counting.<counting id>.name = <counting name>

Name of the counting. This name override counting id in the enrichment
configuration parser. This property is also used as mapper between counting
configuration and counting class which defines the counting.

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

This property enables the enrichment functionality for the study. This
property takes a :ref:`boolean <allowed_values_booleans>` value.

