pheno package
=============

The main class that ensures access to SSC the phenotype database is 
:ref:`PhenoDB`. To start using the phenotype database you need to create an
instance of this class::

    In [1]: from pheno.pheno_db import PhenoDB
    In [2]: phdb = PhenoDB()
    In [3]: phdb.load()


To access values of given measure use::

    In [8]: df = phdb.get_measure_values_df('ssc_commonly_used.head_circumference')
    
    In [9]: df.head()
    Out[9]: 
      person_id  ssc_commonly_used.head_circumference
    0  11000.p1                                  57.0
    1  11001.p1                                  56.2
    2  11002.p1                                  53.5
    3  11003.p1                                  56.0
    4  11004.p1                                  58.5

You can get a data frame with value for multiple measures by using::

    In [12]: df = phdb.get_values_df(['pheno_common.age', 
        'ssc_commonly_used.head_circumference'])
    
    In [13]: df.head()
    Out[13]: 
      person_id  pheno_common.age  ssc_commonly_used.head_circumference
    0  11000.fa             550.0                                  63.5
    1  11000.mo             536.0                                  56.0
    2  11000.p1             110.0                                  57.0
    3  11000.s1             201.0                                  58.0
    4  11001.fa             478.0                                  59.0


To access data for individuals in the database use::

    In [10]: psdf = phdb.get_persons_df()
    
    In [11]: psdf.head()
    Out[11]: 
          person_id family_id role gender
    0      11000.mo     11000  mom      F
    1      11000.fa     11000  dad      M
    2      11000.p1     11000  prb      M
    3      11000.s1     11000  sib      F
    10764  11000.s2     11000  sib      F


.. automodule:: pheno
    :members:
    :undoc-members:
    :show-inheritance:

Submodules
----------

pheno.pheno_db module
---------------------

.. automodule:: pheno.pheno_db
    :members:
    :undoc-members:
    :show-inheritance:


