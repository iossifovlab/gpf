enrichment_tool package
=======================

Example usage of :ref:`EnrichmentTool` class
-------------

Example usage of enrichment tool package::

    # load WE denovo studies
    studies = vDB.get_studies('ALL WHOLE EXOME')
    denovo_studies = [
        st for st in studies if 'WE' == st.get_attr('study.type')]

    autism_studes = [
        st for st in denovo_studies
        if 'autism' == st.get_attr('study.phenotype')]

    # create background
    background = SamochaBackground()

    # load a gene set
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()

    # create enrichment tool
    tool = EnrichmentTool(background, GeneEventsCounter())

    events, overlapped, stats = tool.calc(
        autism_studes,
        'prb',
        'LGDs',
        gene_set)

    print(events)
    print(overlapped)
    print(stats)

    events, overlapped, stats = tool.calc(
        denovo_studies,
        'sib',
        'LGDs',
        gene_set)

    print(events)
    print(overlapped)
    print(stats)


Submodules
----------

enrichment_tool.background module
---------------------------------

.. automodule:: enrichment_tool.background
    :members:
    :undoc-members:
    :show-inheritance:

enrichment_tool.config module
-----------------------------

.. automodule:: enrichment_tool.config
    :members:
    :undoc-members:
    :show-inheritance:

enrichment_tool.event_counters module
-------------------------------------

.. automodule:: enrichment_tool.event_counters
    :members:
    :undoc-members:
    :show-inheritance:

enrichment_tool.tool module
---------------------------

.. automodule:: enrichment_tool.tool
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: enrichment_tool
    :members:
    :undoc-members:
    :show-inheritance:
