Genomic resources repository (GRR)
==================================



Genomic resources and genomic resources repository
--------------------------------------------------

Genomic resource is a set files stored in a directory. To make given
directory a genomic resource it should contain ``genomic_resource.yaml``
file.

Genomic resources repository is a directory, that contains genomic resources.
To make a give directory into a repository it should contain a ``.CONTENTS``
file.


Management of genomic resources repository (GRR)
------------------------------------------------

Create an empty GRR
*******************

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
********************************

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


Usage of genomic resources repositories (GRRs)
----------------------------------------------


