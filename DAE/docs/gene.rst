gene package
============

Example usage of :ref:`Weights` class
-------------------------------------

Create an instance of a :ref:`Weights` class::

    In [1]: from gene.weights import Weights
    
    In [2]: w = Weights('RVIS_rank')
    
    In [3]: w.get_genes(wmax=5)
    Out[3]: {'CSMD1', 'LRP1', 'PLEC', 'RYR1', 'UBR4'}
    

The `get_genes` method returns a set of genes which weight is in the specified
range.

Using `to_dict` method one can get a dictionary with all gene weights::

    In [4]: w.to_dict()
    Out[4]: 
    {'UBE2Q1': 5413.0,
     'RNF14': 6682.0,
     'RNF17': 10848.0,
     'RNF10': 3020.5,
     'RNF11': 9644.5,
     ...
     }

Using `to_df` method we can get a data frame represenging all gene weights::

    In [5]: df = w.to_df()
    In [6]: df.head()
    Out[6]: 
          gene  RVIS_rank
    0     LRP1        3.0
    1    TRRAP        6.0
    2  ANKRD11       15.0
    3    ZFHX3       19.0
    4    HERC2        8.0



gene.weights module
-------------------

.. automodule:: gene.weights
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: gene
    :members:
    :undoc-members:
    :show-inheritance:
