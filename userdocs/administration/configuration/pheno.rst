.. _pheno_db:

Phenotype Database Configuration
================================

The configuration file for a single phenotype database follows the general
INI format. Its filename can be freely chosen, however, it **must** contain a
``phenoDB`` section - this will indicate that it is a phenotype database
configuration file.  This configuration file must properly describe a single
phenotype database. Its properties, which must belong to the ``phenoDB``
section, are explained below.

[phenoDB]
---------

name
____

.. code-block:: ini

  name = {pheno db name}

This is the unique name of the phenotype database. It can be used in the
configuration files of studies and datasets to attach the phenotype
database to them.

dbfile
______

.. code-block:: ini

  dbfile = {sqlite3 pheno db path}

The path to the SQLite3 phenotype database file, relative to the
configuration file.

browser_dbfile
______________

.. code-block:: ini

  browser_dbfile = {sqlite3 pheno browser db path}

The path to the SQLite3 phenotype **browser** database file, relative to the
configuration file.

browser_images_dir
__________________

.. code-block:: ini

  browser_images_dir = {images directory path}

The path to the directory containing the measure images for the browser,
relative to the configuration file.

browser_images_url
__________________

.. code-block:: ini

  browser_images_url = /static/{images directory path}/

The path to the directory containing the measure images for the browser,
relative to the *static root directory*. The trailing slash is required.
