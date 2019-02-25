GPF Getting Started Guide
=========================


Prerequisites
#############

    git
    wget
    gcc
    zlib

If you are using Ubuntu, you can run:

.. code-block:: bash

    sudo apt-get install git wget build-essential zlib1g-dev


Clone the GPF Repository
########################

To start using GPF system you need to clone the GPF source code repository
from Github:

.. code-block:: bash

    git clone --single-branch --branch variants git@github.com:seqpipe/gpf.git


Setup GPF Development Environment
#################################

The GPF system is developed in Python and supports both Python 2.7 and
Python 3.6. The recommended way to setup GPF development environment is to
use Anaconda.

Setup Anaconda Environment
++++++++++++++++++++++++++

Download and install Anaconda
*****************************

Download Anaconda from  Anaconda distribution page (https://www.anaconda.com/distribution/)

.. code-block:: bash

        wget -c https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh

and install it in your local environment following the installer instructions:

    sh Anaconda3-2018.12-Linux-x86_64.sh

Create GPF environment
**********************

Most of dependencies for GPF are described into Anaconda environmet description
files located inside of the GPF source repository:

.. code-block:: bash

    gpf/python2-environment.yml
    gpf/python3-environment.yml

You can use these files to create an GPF python development environment.
For example if you want to create Python 3 development conda environment, use::

.. code-block:: bash

    conda env create -n gpf3 -f gpf/python3-environment.yml

To use this environment you need to execute the following command:

.. code-block:: bash

    conda activate gpf3

Install ``pyarrow`` and ``pandas`` from Anaconda ``conda-forge`` channel:

.. code-block:: bash

    conda install -c conda-forge pyarrow pandas


Additionally you will need to install `cyvcf2`. To this end clone this repo:

.. code-block:: bash

    git clone https://github.com/seqpipe/cyvcf2.git

Enter inside `cyvcf2` directory and run pip install:

.. code-block:: bash

    cd cyvcf2
    pip install .
    cd ..


Install Spark
+++++++++++++

After creating a GPF environmet you should have Java JDK 8 installed into your
environment. Since Apache Spark runs on Java JDK 8, please verify your
version of Java JDK:

.. code-block:: bash

    java -version

should display something similar to the following:

.. code-block:: bash

    openjdk version "1.8.0_152-release"
    OpenJDK Runtime Environment (build 1.8.0_152-release-1056-b12)
    OpenJDK 64-Bit Server VM (build 25.152-b12, mixed mode)


Download Apache Spark distribution and unarchive it:

.. code-block:: bash

    wget -c https://www-us.apache.org/dist/spark/spark-2.4.0/spark-2.4.0-bin-hadoop2.7.tgz
    tar zxvf spark-2.4.0-bin-hadoop2.7.tgz


Get Startup Data Instance
+++++++++++++++++++++++++

Get Genomic Scores Database
+++++++++++++++++++++++++++

Update `setenv.sh` Script
+++++++++++++++++++++++++

Inside GPF source directory there is a file named
``setenv_template.sh``:

.. code-block:: bash

    # specifies where Apache Spark is installed
    export SPARK_HOME=<path to spark distribution>/spark-2.4


    # specifies where is the source directory for GPF DAE
    export DAE_SOURCE_DIR=<path to gpf>/gpf/DAE
    # specifies the location of GPF data instance
    export DAE_DB_DIR=<path to work data>/data-hg19

    # activates GPF conda environment
    conda activate gpf3

    # setups GPF paths
    source $DAE_SOURCE_DIR/setenv.sh

You shoud copy it as ``setenv.sh`` file and edit it according you own setup.
When you are ready you need to source your ``setenv.sh`` file:

.. code-block:: bash

    source ./setenv.sh


Example Usage of GPF Python Interface
#####################################


Start GPF Web UI
################

Initial Setup of GPF Web UI
+++++++++++++++++++++++++++

Start GPF Web UI
++++++++++++++++

Import a Demo Dataset
#####################

Import a VCF Dataset
++++++++++++++++++++

Configure VCF Dataset
+++++++++++++++++++++

Generate Variant Reports and Denovo Gene Sets
+++++++++++++++++++++++++++++++++++++++++++++

Start GPF Web UI
++++++++++++++++
