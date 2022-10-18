Genomic resources repository (GRR)
==================================


Introduction
************

Configuration
*************

Genomic resources repository could be accessed via different protocols.
Currently supported protocols for GRR access are:

* File system (directory) protocol.

  .. code:: yaml

    id: <repo id>
    type: directory
    directory: <path to the local file system>

* HTTP/HTTPS protocol.

  .. code:: yaml

    id: <repo id>
    type: url
    url: <http(s) url>

* S3 protocol.
  
  .. code:: yaml

    id: <repo id>
    type: url
    url: <S3 url>
    endpoint_url: <endpoint url>

* In-memory (embedded) protocol.

  .. code:: yaml

    id: <repo id>
    type: embedded



Example configuration
#####################


.. code:: yaml

    id: "development"
    type: group
    children:
    - id: "grr_local"
      type: "directory"
      directory: "<path to local GRR directory>"

    - id: "default"
      type: "url"
      url: "https://www.iossifovlab.com/distribution/public/genomic-resources-repository"
      cache_dir: "<path to local filesystem cache>"


Browse available resources
**************************

.. code:: bash

    grr_browse --grr grr_definition.yaml


Management of genomic resources repository (GRR)
************************************************

Genomic resources and genomic resources repository
##################################################

The genomic resource is a set of files stored in a directory. To make given
directory a genomic resource, it should contain ``genomic_resource.yaml``
file.

A genomic resources repository is a directory that contains genomic resources.
To make a given directory into a repository, it should have a ``.CONTENTS``
file.


Create an empty GRR
###################

To create and empty GRR first create an empty directory. For example let us
create an empty directory named ``grr_test``, enter inside that directory and
run ``grr_manage repo-init`` command:

.. code-block:: bash

    mkdir grr_test
    cd grr_test
    grr_manage repo-init

After that the directory should contain an empty ``.CONTENTS`` file:

.. code-block:: bash

    ls -a

    .  ..  .CONTENTS

If we try to list all resources in this repository we should get an empty list:

.. code-block:: bash

    grr_manage list


Create an empty genomic resource
################################

Let us create our first genomic resource. Create a directory
``hg38/scores/score9`` inside
``grr_test`` repository and create an empty ``genomic_resource.yaml`` file
inside that directory:

.. code-block:: bash

    mkdir -p hg38/scores/score9
    cd hg38/scores/score9
    touch genomic_resource.yaml

This will create an empty genomic resource in our repository 
with ID ``hg38/scores/score9``.

If we list the resources in our repository we would get:

.. code-block:: bash

    grr_manage list

    working with repository: .../grr_test
    Basic                0        1            0 hg38/scores/score9


When we create or change a resource we need to repair the repository:

.. code-block:: bash

    grr_manage repo-repair

This command will create a ``.MANIFEST`` file for our new resource
``hg38/scores/score9`` and will update the repository ``.CONTENTS`` to include
the resource.


Add genomic score resources
+++++++++++++++++++++++++++

Add all score resource files (score file and Tabix index) inside
the created directory ``hg38/scores/score9``. Let's say these files are:

.. code-block:: 

   score9.tsv.gz
   score9.tsv.gz.tbi

Configure the resource ``hg38/scores/score9``. To this end create
a ``genomic_resource.yaml`` file, that contains the position score
configuration:

.. code-block:: yaml

    type: position_score
    table:
      filename: score9.tsv.gz
      format: tabix

      # defined by score_type
      chrom:
        name: chrom
      pos_begin:
        name: start
      pos_end:
        name: end

    # score values
    scores:
    - id: score9
        type: float
        desc: "score9"
        index: 3
    histograms:
    - score: score9
      bins: 100
      y_scale: "log"
      x_scale: "linear"
    default_annotation:
      attributes:
      - source: score9
        destination: score9
    meta: |
    ## score9
      TODO

When ready you should run ``grr_manage resource-repair`` from inside resource
directory:

.. code-block:: bash

    cd hg38/scores/score9
    grr_manage resource-repair

This command is going to calculate histograms for the score (if histograms
are configured) and create or update the resource manifest.

Once the resource is ready we need to regenerated the repository contents:

.. code-block:: bash

    grr_manage repo-repair


Usage of genomic resources repositories (GRRs)
++++++++++++++++++++++++++++++++++++++++++++++

The GPF system can use genomic resources from different repositories. The
default genomic resources repository used by GPF system is located at
`https://www.iossifovlab.com/distribution/public/genomic-resources-repository/ 
<https://www.iossifovlab.com/distribution/public/genomic-resources-repository/>`_.
You can browse the content of the repository using the ``grr_manage list``
command:

.. code-block::

    grr_manage list -R https://www.iossifovlab.com/distribution/public/genomic-resources-repository


If you have a repository on your local filesytem you can browse it by
providing the path to the root directory:

.. code-block::

    grr_manage list -R <path to the local repo>

You can store a genomic resource repository in an S3 storage and you can browse
its content with:

.. code-block::

    grr_manage list -R s3://grr-bucket-test/grr \
        --extra-args "endpoint_url=http://piglet.seqpipe.org:7480"

where ``grr-bucket-test`` is the bucket where you store the repository and
``--extra-args`` are used to specify the S3 endpoint.

