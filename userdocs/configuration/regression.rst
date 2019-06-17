Phenotype Regression Configuration
==================================

A phenotype regression configuration file is used when generating
the phenotype browser's database files for a given study or dataset.
It determines which measures to construct regressions against.
The format follows the general INI style.
Regression configurations can be created as a separate file or
embedded in a phenotype database's own configuration file for ease of access.

Each regression is configured by a section with a name such as ``[regression.{regression_name}]``,
where ``regression_name`` is a user-selected name for the regression. The key-value pairs of
a regression section are as follows -

instrument_name
---------------

.. code-block:: ini

  instrument_name = {pheno instrument name}

This is the name of the instrument to which the regressor (or exogenous/independent)
measure belongs to. It can be left empty to indicate that the measure is present in all
instruments.

measure_name
------------

.. code-block:: ini

  measure_name = {pheno measure name}

This is the name of the regressor measure.

jitter
------

.. code-block:: ini

  jitter = {jitter float value}

A float value that determines the amount of jitter to apply
to points when drawing the regression plot. The default value is 0.1.
