'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import
from __future__ import unicode_literals

# from DAE import vDB
# from itertools import groupby
# # import pytest


# def recSingleGenes(studies, inChild, effectTypes, phenotype):
#     vs = vDB.get_denovo_variants(
#         studies, effectTypes=effectTypes, inChild=inChild)

#     gnSorted = sorted([[ge['sym'], v]
#                        for v in vs for ge in v.requestedGeneEffects
#                        if v.phenotype == phenotype])
#     sym2Vars = {sym: [t[1] for t in tpi]
#                 for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
#     sym2FN = {sym: len({v.familyId for v in vs})
#               for sym, vs in list(sym2Vars.items())}
#     return {g for g, nf in list(sym2FN.items()) if nf > 1}, \
#         {g for g, nf in list(sym2FN.items()) if nf == 1}


# def test_ssc_recurrent(ssc, gscs):
#     assert ssc is not None
#     studies = ssc.get_denovo_studies()
#
#     recurrent, single = recSingleGenes(studies, 'prb', 'LGDs', 'autism')
#     print(recurrent)
#     print(single)
#
#     denovo = gscs.get_gene_sets_collection('denovo')
#     gs = denovo.get_gene_set(
#         'LGDs.Recurrent', gene_sets_types={'SSC': ['autism']})
#
#     assert len(recurrent) == gs['count']
#     assert set(recurrent) == gs['syms']
#
#
# def test_denovo_db_recurrent(denovodb, gscs):
#     assert denovodb is not None
#     studies = denovodb.get_denovo_studies()
#
#     recurrent, single = recSingleGenes(studies, 'prb', 'LGDs', 'autism')
#     print(recurrent)
#     print(single)
#
#     denovo = gscs.get_gene_sets_collection('denovo')
#     gs = denovo.get_gene_set(
#         'LGDs.Recurrent', gene_sets_types={'TESTdenovo_db': ['autism']})
#
#     print(recurrent)
#     print(gs)
#
#     assert set(recurrent) == gs['syms']
#
#
# def test_ssc_sd_recurrent_combined(ssc, sd, gscs):
#     studies = sd.get_denovo_studies()
#     studies.extend(ssc.get_denovo_studies())
#
#     recurrent, single = recSingleGenes(studies, 'prb', 'LGDs', 'autism')
#
#     print(recurrent)
#     print(single)
#
#     denovo = gscs.get_gene_sets_collection('denovo')
#     gs = denovo.get_gene_set(
#         'LGDs.Recurrent', gene_sets_types={
#             'SD': ['autism'], 'SSC': ['autism']})
#
#     assert set(recurrent) == gs['syms']
#
#
# def test_spark_recurrent(spark, gscs):
#     assert spark is not None
#     studies = spark.get_denovo_studies()
#
#     recurrent, single = recSingleGenes(studies, 'prb', 'LGDs', 'autism')
#     print(recurrent)
#     print(single)
#
#     denovo = gscs.get_gene_sets_collection('denovo')
#     gs = denovo.get_gene_set(
#         'LGDs.Recurrent', gene_sets_types={'SPARKv1': ['autism']})
#
#     assert set(recurrent) == gs['syms']
#     assert len(recurrent) == gs['count']
#
#
# def test_ssc_spark_recurrent_combined(ssc, spark, gscs):
#     studies = ssc.get_denovo_studies()
#     studies.extend(spark.get_denovo_studies())
#
#     recurrent, single = recSingleGenes(studies, 'prb', 'LGDs', 'autism')
#
#     print(recurrent)
#     print(single)
#
#     denovo = gscs.get_gene_sets_collection('denovo')
#     gs = denovo.get_gene_set(
#         'LGDs.Recurrent', gene_sets_types={
#             'SSC': ['autism'],
#             'SPARKv1': ['autism']
#         })
#
#     assert set(recurrent) == gs['syms']
