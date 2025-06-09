Genotype Storage
================

To store and query genomic variants, we use genotype storage.

There are two interfaces that define genotype storage:

* :class:`dae.genotype_storage.genotype_storage.GenotypeStorage`  that defines
  how to use the storage for querying genomic variants;

* :class:`dae.import_tools.import_tools.ImportStorage` that defines how to
  import genomic variants into the storage.


When you want to create new genotype storage, you have to create two classes - 
a genotype storage class that inherits the 
:class:`dae.genotype_storage.genotype_storage.GenotypeStorage`
and an import storage class that inherits 
:class:`dae.import_tools.import_tools.ImportStorage`.
Once created, you should register these classes in the two extension points
defined in the `setup.py`:

* for genotype storage class use `[dae.genotype_storage.factories]` extenstion
  point;

* for import storage class use `[dae.import_tools.storages]` extenstion point.

As an example of genotype storage definitions, you can check the following pairs
of classes:

* Filesystem storage (`filesystem` storage type):
   * genotype storage
     :class:`dae.filesystem_storage.in_memory.filesystem_genotype_storage.FilesystemGenotypeStorage`

   * import storage: 
     :class:`dae.filesystem_storage.in_memory.filesystem_import_storage.FilesystemImportStorage`

* Impala schema 1 storage (`impala` storage type):
   * genotype storage
     :class:`dae.impala_storage.schema1.impala_genotype_storage.ImpalaGenotypeStorage`

   * import storage: 
     :class:`dae.impala_storage.schema1.impala_schema1.ImpalaSchema1ImportStorage`


* Impala schema 2 storage (`impala2` storage type):
   * genotype storage
     :class:`dae.impala_storage.schema2.schema2_genotype_storage.Schema2GenotypeStorage`

   * import storage: 
     :class:`dae.impala_storage.schema1.schema2_import_storage.Schema2ImportStorage`

.. toctree::
   :maxdepth: 3

   modules/dae.genotype_storage
