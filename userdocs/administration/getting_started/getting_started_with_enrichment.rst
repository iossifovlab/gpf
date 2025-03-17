
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
      selected_background_models:
          - enrichment/samocha_background


Restart the GPF web server and select the ``helloworld`` dataset.
You should see the :ref:`Enrichment Tool` tab.
