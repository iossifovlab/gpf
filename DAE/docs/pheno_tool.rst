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

Then we are ready to create an PhenoTool instance::

    In [12]: from pheno_tool.tool import PhenoTool
    
    In [13]: tool = PhenoTool(phdb, studies, roles=['prb'])

Select a set of gene symbols to work with::

    In [15]: from DAE import get_gene_sets_symNS
    
    In [16]: gt = get_gene_sets_symNS('main')
    
    In [17]: gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

Create a variants query object::

    In [18]: from pheno_tool.tool import PhenoRequest
    
    In [19]: query = PhenoRequest(effect_types=['LGDs'], gene_syms=gene_syms)

Now we are ready to the actual computations::

    In [20]: res = tool.calc(query, 'ssc_commonly_used.head_circumference', 
        ...:     normalize_by=['pheno_common.age'],
        ...:     gender_split=False)

The returned object is of type :ref:`PhenoResult`. This class could be queried
about the results of the calculation::

    In [22]: res.positive_count
    Out[22]: 132
    
    In [23]: res.negative_count
    Out[23]: 2597
    
    In [24]: res.pvalue
    Out[24]: 0.016919098924661494

We also have access to phenotypes and genotypes as dataframes::

    In [27]: res.genotypes_df.head()
    Out[27]: 
      person_id gender role  variants
    0  11000.p1      M  prb         0
    1  11001.p1      M  prb         0
    2  11002.p1      F  prb         0
    3  11003.p1      M  prb         0
    4  11004.p1      M  prb         0

    In [26]: res.phenotypes_df.head()
    Out[26]: 
      person_id role gender  pheno_common.age  \
    0  11000.p1  prb      M             110.0   
    1  11001.p1  prb      M              93.0   
    2  11002.p1  prb      F              92.0   
    3  11003.p1  prb      M             133.0   
    4  11004.p1  prb      M             190.0   
    
       ssc_commonly_used.head_circumference  normalized  
    0                                  57.0    2.955663  
    1                                  56.2    2.844358  
    2                                  53.5    0.184869  
    3                                  56.0    1.023899  
    4                                  58.5    1.214746


and as dictionaries::


    In [29]: res.genotypes
    Out[29]: 
    Counter({u'11046.p1': 0,
             u'14398.p1': 0,
             u'11004.p1': 0,
             u'12607.p1': 0,
             u'13048.p1': 0,
             u'12547.p1': 1,
             ....
             })

    In [30]: res.phenotypes
    Out[30]: 
    {u'14566.p1': {'gender': u'M',
      'normalized': -2.231956286972789,
      'person_id': u'14566.p1',
      'pheno_common.age': 164.0,
      'role': u'prb',
      'ssc_commonly_used.head_circumference': 54.0},
     u'14398.p1': {'gender': u'M',
      'normalized': 2.5771970972035376,
      'person_id': u'14398.p1',
      'pheno_common.age': 107.0,
      'role': u'prb',
      'ssc_commonly_used.head_circumference': 56.5},
      ...
      }


 
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


Module contents
---------------

.. automodule:: pheno_tool
    :members:
    :undoc-members:
    :show-inheritance:
