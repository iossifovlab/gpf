Phenotype Regression Configuration
==================================

A phenotype regression configuration file is used when generating
the phenotype browser's database files for a given study or dataset.
It determines which measures to construct regressions against.
The format follows the general INI style.
Regression configurations can be created as a separate file or
embedded in a phenotype database's own configuration file for ease of access.

[regression.<regression_name>]
------------------------------

Each regression is configured by a section with a name such as
``[regression.<regression_name>]``, where ``regression_name`` is a
user-selected name for the regression. The key-value pairs of a regression
section are as follows.

instrument_name
_______________

.. code-block:: ini

  instrument_name = <pheno instrument name>

This is the name of the instrument to which the regressor
(or exogenous/independent) measure belongs to. It can be left empty to indicate
that the measure is present in all instruments.

measure_name
____________

.. code-block:: ini

  measure_name = <pheno measure name>

This is the name of the regressor measure.

jitter
______

.. code-block:: ini

  jitter = <jitter float value>

A float value that determines the amount of jitter to apply
to points when drawing the regression plot. The default value is 0.1.


display_name
____________

.. code-block:: ini

  display_name = <pheno regression display name>

Determines the name of the regression's column in the phenotype browser.
