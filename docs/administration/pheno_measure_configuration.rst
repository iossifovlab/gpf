Measure Configuration
=====================

Measure configuration format
----------------------------
.. code-block:: yaml

    classification:
      "instrument1.measure1":
          type:
          missing_values:
          float_conversion_cutoff_ratio:
      "*.*":
          float_conversion_cutoff_ratio:
      "*.some_special_measure":
          type: string
