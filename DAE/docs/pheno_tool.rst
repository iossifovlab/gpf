pheno_tool package
==================

Example usage of :ref:`PhenoTool` class
---------------------------------------

First prepare studies to work with::

    In [1]: from DAE import vDB
    
    In [2]: studies = vDB.get_studies('ALL SSC')
    
    In [3]: studies.append(vDB.get_study('w1202s766e611'))

Create an instance of :ref:`PhenoDB` to access phenotype database::

    In [4]: from pheno.pheno_db import PhenoDB
    
    In [5]: phdb = PhenoDB()
    
    In [6]: phdb.load()

Now we can create an instance of `PhenoTool` class to work with given set
of individuals::

    In [8]: from pheno_tool.tool import PhenoTool
    
    In [9]: tool = PhenoTool(
       ...:         phdb, studies, roles=['prb', 'mom', 'dad'],
       ...:         measure_id='ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
       ...: )

We can check the list of individuals that are subject to computation by this
particular instance of `PhenoTool` by using `list_of_subjects()` method::

    In [10]: tool.list_of_subjects()
    Out[10]: 
    {u'14566.p1': Person(14566.p1; prb; M),
     u'14398.p1': Person(14398.p1; prb; M),
     u'14524.p1': Person(14524.p1; prb; M),
     u'12607.p1': Person(12607.p1; prb; M),
     ...
    }

We also have access to a `Pandas` data frame representing these subjects::

    In [18]: persons.head()
    Out[18]: 
       person_id family_id role gender  ssc_core_descriptive.ssc_diagnosis_nonverbal_iq
    2   11000.p1     11000  prb      M                                             78.0
    5   11001.p1     11001  prb      M                                            123.0
    8   11002.p1     11002  prb      F                                            111.0
    11  11003.p1     11003  prb      M                                            108.0
    14  11004.p1     11004  prb      M                                             74.0


Now we are ready to the actual computations. Let first get some set of gene
symbols::

    In [19]: from DAE import get_gene_sets_symNS
    
    In [20]: gt = get_gene_sets_symNS('main')
    
    In [21]: gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

To perform the actual computation we use `calc` method of `PhenoTool`. We need to
pass to this method the specification of the variants::

    In [22]: res = tool.calc(
        ...:     effect_types=['LGDs'],
        ...:     gene_syms=gene_syms,
        ...:     present_in_child=['autism only', 'autism and unaffected'],
        ...:     present_in_parent=['neither'],
        ...: )


The returned object is of type :ref:`PhenoResult`. This class could be queried
about the results of the calculation::

    In [23]: res.positive_count
    Out[23]: 135
    
    In [24]: res.negative_count
    Out[24]: 2626
    
    In [25]: res.pvalue
    Out[25]: 1.5345885574583403e-07

We also have access to phenotypes and genotypes as dataframes::

    In [26]: res.genotypes_df.head()
    Out[26]: 
       person_id gender role  variants
    2   11000.p1      M  prb         0
    5   11001.p1      M  prb         0
    8   11002.p1      F  prb         0
    11  11003.p1      M  prb         0
    14  11004.p1      M  prb         0
    
    In [27]: res.phenotypes_df.head()
    Out[27]: 
       person_id role gender  ssc_core_descriptive.ssc_diagnosis_nonverbal_iq  normalized
    2   11000.p1  prb      M                                             78.0        78.0
    5   11001.p1  prb      M                                            123.0       123.0
    8   11002.p1  prb      F                                            111.0       111.0
    11  11003.p1  prb      M                                            108.0       108.0
    14  11004.p1  prb      M                                             74.0        74.0


and as dictionaries::


    In [28]: res.genotypes
    Out[28]: 
    Counter({u'11046.p1': 0,
             u'14398.p1': 0,
             u'12547.p1': 1,
             u'14021.p1': 0,
             u'11264.p1': 0,
             u'11925.p1': 1,
             u'11249.p1': 0,
             ....
             })

    In [29]: res.phenotypes
    Out[29]: 
    {u'14566.p1': {'gender': u'M',
      'normalized': 44.0,
      'person_id': u'14566.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 44.0},
     u'14398.p1': {'gender': u'M',
      'normalized': 111.0,
      'person_id': u'14398.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 111.0},
     u'14524.p1': {'gender': u'M',
      'normalized': 76.0,
      'person_id': u'14524.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 76.0},
      ...
      }


Example usage of :ref:`PhenoTool` class with pheno filters
-----------------------------------------

The `PhenoTool` class supports different ways to specify which individuals are
subject to the calculations. We can use `roles`, `measure_id`, `normalize_by` and 
`pheno_filters` arguments in the `PhenoTool` constructor. For example if we
specify `roles` and `measure_id` the tool will use individuals of the specified
roles and has the specified measurement::

    In [40]: tool = PhenoTool(phdb, studies, roles=['prb', 'sib'], 
                measure_id="ssc_commonly_used.head_circumference")
    
    In [41]: len(tool.list_of_subjects())
    Out[41]: 5166
 
If we specify a normalization, then the list of individuals should have 
measurements for normalization too::

    In [44]: tool = PhenoTool(phdb, studies, roles=['prb', 'sib'], 
                measure_id="ssc_commonly_used.head_circumference", 
                normalize_by=['pheno_common.age'])
    
    In [45]: len(tool.list_of_subjects())
    Out[45]: 4869

Additionally we can use `pheno_filters` argument. Let us specify only individuals
that are of `white` race::

    In [46]: tool = PhenoTool(phdb, studies, roles=['prb', 'sib'], 
                measure_id="ssc_commonly_used.head_circumference",  
                pheno_filters={
                    'pheno_common.race': set(['white'])
                })
    
    In [47]: len(tool.list_of_subjects())
    Out[47]: 3983

or::

    In [50]: tool = PhenoTool(phdb, studies, roles=['prb', 'sib'], 
        ...:     measure_id="ssc_commonly_used.head_circumference",  
        ...:     pheno_filters={
        ...:        'pheno_common.race': set(['white', 'asian']),
        ...:     })
    
    In [51]: len(tool.list_of_subjects())
    Out[51]: 4174


Using `pheno_filters` we can also specify ranges of values for given measurement::

    In [52]: tool = PhenoTool(phdb, studies, roles=['prb', 'sib'], 
        ...:      measure_id="ssc_commonly_used.head_circumference",  
        ...:      pheno_filters={
        ...:         'pheno_common.race': set(['white', 'asian']),
        ...:         'pheno_common.age': (200, 220),
        ...:      })
    
    In [53]: len(tool.list_of_subjects())
    Out[53]: 145


..
    pheno_tool.family_filters module
    --------------------------------
    
    .. automodule:: pheno_tool.family_filters
        :members:
        :undoc-members:
        :show-inheritance:

pheno_tool.tool module
----------------------

.. automodule:: pheno_tool.tool
    :members:
    :undoc-members:
    :show-inheritance:

pheno_tool.genotype_helper module
----------------------

.. automodule:: pheno_tool.genotype_helper
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: pheno_tool
    :members:
    :undoc-members:
    :show-inheritance:
