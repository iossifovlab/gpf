
Getting Started with Enrichment Tool
####################################

For studies that include de Novo variants, you can enable the enrichment tool UI.
As an example, let us enable it for the ``helloworld`` dataset.

Navigate to the ``helloworld`` dataset folder:

.. code-block:: bash

    cd datasets/helloworld

and edit the ``helloworld.yaml`` file. Add the following section to the end:

.. code-block:: yaml

    enrichment:
      enabled: true
      default_background_model: enrichment/samocha_background
      default_counting_model: enrichment_events_counting
      selected_background_models:
          - enrichment/samocha_background
      selected_counting_models:
          - enrichment_events_counting
      counting:
          enrichment_events_counting:
            id: enrichment_events_counting
            name: Counting events
            desc: Counting events
      selected_person_set_collections:
          - status
      effect_types:
          - LGDs
          - missense
          - synonymous


Restart the GPF web server and select the ``helloworld`` dataset.
You should see the :ref:`Enrichment Tool` tab.
