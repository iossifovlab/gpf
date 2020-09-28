############
Genotype browser
############

.. http:post:: /genotype_browser/preview

  Preview info for a dataset's variants

  **Example request**:

  .. sourcecode:: http

     POST /genotype_browser/preview HTTP/1.1
     Host: example.com
     Content-Type: application/json
     Accept: application/json

     {
       "datasetId": "iossifov_2014"
     }

  **Example response**:

  .. sourcecode:: http

     HTTP/1.1 200 OK
     Vary: Accept
     Content-Type: text/javascript

     {
       "cols": [],
       "legend": {},
       "maxVariantsCount": 1001
     }

   :statuscode 200: no error
   :statuscode 400: invalid dataset ID given
   :reqjson string datasetId: The ID of the dataset


.. http:post:: /genotype_browser/preview/variants

  Search a dataset's variants and retrieve them in a JSON stream of nested lists

  **Example request**:

  .. sourcecode:: http

     POST /genotype_browser/preview/variants HTTP/1.1
     Host: example.com
     Content-Type: application/json
     Accept: text/event-stream

     {
       "datasetId": "iossifov_2014",
       "maxVariantsCount": 1000
     }

  **Example response**:

  .. sourcecode:: http

     HTTP/1.1 200 OK
     Vary: Accept
     Content-Type: text/event-stream

     []

  :statuscode 200: no error
  :statuscode 400: invalid dataset ID given
  :reqjson string datasetId: The ID of the dataset
  :reqjson int maxVariantsCount: The maximum amount of variants to retrieve


.. http:post:: /genotype_browser/download

  Search all of a dataset's variants and retrieve them in a .csv file

  **Example request**:

  .. sourcecode:: http

     POST /genotype_browser/preview/variants HTTP/1.1
     Host: example.com
     Content-Type: application/json
     Accept: text/event-stream

     {
       "datasetId": "iossifov_2014",
     }

  **Example response**:

  .. sourcecode:: http

     HTTP/1.1 200 OK
     Vary: Accept
     Content-Type: text/event-stream

     []


  :statuscode 200: no error
  :statuscode 400: invalid dataset ID given
  :reqjson string datasetId: The ID of the dataset
