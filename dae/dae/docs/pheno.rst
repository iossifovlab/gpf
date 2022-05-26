Phenotype Data
==============

Pheno DB access
---------------





Example usage of :class:`PhenoDB <dae.pheno.pheno_db.PhenoDB>`
--------------------------------------------------------------

To access a pheno DB you need to import DAE and use a factory object named
`pheno`::

    In [1]: from DAE import pheno

    In [2]: pheno.get_pheno_db_names()
    Out[2]: ['ssc', 'vip', 'spark', 'agre']

    In [3]: phdb = pheno.get_pheno_db('agre')

The result of `get_pheno_db` is an instance of
:class:`PhenoDB <dae.pheno.pheno_db.PhenoDB>` class. This is the main class
that provides access to the phenotype database.


To access values of given measure use::

    In [8]: df = phdb.get_measure_values_df('ADOS21.CSB9')
    In [9]: df.head()
    Out[9]:
      person_id  ADOS21.CSB9
    0  AU011105          1.0
    1  AU014005          2.0
    2  AU015904          2.0
    3  AU024704          2.0
    4  AU025005          1.0

You can get a data frame with value for multiple measures by using::

    In [12]: df = phdb.get_values_df(['ADOS21.CSB9', 'Raven1.B12'])
    In [13]: df.head()
    Out[13]:
      person_id  ADOS21.CSB9  Raven1.B12
    0  AU011105          1.0         5.0
    1  AU014005          2.0        -1.0
    2  AU015904          2.0         NaN
    3  AU024704          2.0         NaN
    4  AU025005          1.0        -1.0


To access data for individuals in the database use::

    In [10]: psdf = phdb.get_persons_df()
    In [11]: psdf.head()
    Out[11]:
        person_id family_id      role    gender             status
     0  AU2275201    AU2275  Role.dad  Gender.M  Status.unaffected
     1  AU2275202    AU2275  Role.mom  Gender.F  Status.unaffected
     2  AU2275301    AU2275  Role.prb  Gender.M    Status.affected
     3  AU2275302    AU2275  Role.sib  Gender.M    Status.affected
     4  AU0966201    AU0966  Role.dad  Gender.M  Status.unaffected

You can access individuals and measures values as a joined data frame by using
**get_persons_values_df**::

    In [17]: df = phdb.get_persons_values_df(['ADIR1.EHFMAN', 'Raven1.B12'])
    In [18]: df.head()
    Out[18]:
        person_id family_id      role    gender           status  \
    2   AU2275301    AU2275  Role.prb  Gender.M  Status.affected
    3   AU2275302    AU2275  Role.sib  Gender.M  Status.affected
    6   AU0966301    AU0966  Role.prb  Gender.M  Status.affected
    7   AU0966302    AU0966  Role.sib  Gender.M  Status.affected
    10  AU0965301    AU0965  Role.prb  Gender.M  Status.affected

        ADIR1.EHFMAN  Raven1.B12
    2            3.0         5.0
    3            0.0         5.0
    6            2.0        -1.0
    7            2.0        -1.0
    10           1.0        -1.0



Classes and Functions
---------------------
.. toctree::
   :maxdepth: 3

   modules/dae.pheno
