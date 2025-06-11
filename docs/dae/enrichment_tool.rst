Enrichment Tool
===============

Example usage of :class:`EnrichmentTool <dae.enrichment_tool.tool.EnrichmentTool>` class
----------------------------------------------------------------------------------------

First select studies to use::

    In [1]: from DAE import vDB

    In [2]: studies = vDB.get_studies('ALL WHOLE EXOME')

    In [3]: denovo_studies = [st for st in studies if 'WE' ==
    st.get_attr('study.type')]

    In [4]: autism_studies = [st for st in denovo_studies if 'autism' ==
    st.get_attr('study.phenotype')]

Then create a background model object::

    In [5]: from enrichment_tool.background import SamochaBackground

    In [6]: background = SamochaBackground()

After that create a counter object::

    In [7]: from enrichment_tool.event_counters import GeneEventsCounter

    In [8]: counter = GeneEventsCounter()

Create an enrichment tool::

    In [9]: from enrichment_tool.tool import EnrichmentTool

    In [10]: tool = EnrichmentTool(background, counter)


Select a gene set to work with::

    In [11]: from DAE import get_gene_sets_symNS

    In [12]: gt = get_gene_sets_symNS('main')

    In [13]: gene_set = gt.t2G['chromatin modifiers'].keys()

And then we are ready to perform the actual calculations::

    In [14]: res = tool.calc(autism_studies, 'prb', 'LGDs', gene_set)

The result is a dictionary. The keys in the dictionary are::

    In [16]: res.keys()
    Out[16]: ['rec', 'all', 'male', 'female']

Each value in the dictionary is an instance of the class
:class:`EnrichmentResult <dae.enrichment_tool.event_counters.EnrichmentResult>`::

    In [19]: r = res['rec']

    In [20]: len(r.events)
    Out[20]: 39

    In [21]: len(r.overlapped)
    Out[21]: 9

    In [22]: r.expected
    Out[22]: 0.8992414922169882

    In [23]: r.pvalue
    Out[23]: 9.4660348870512223e-07


Classes and Functions
---------------------
.. toctree::
   :maxdepth: 3

   modules/dae.pheno_tool
