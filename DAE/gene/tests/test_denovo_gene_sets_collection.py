'''
Created on Feb 16, 2017

@author: lubo
'''


def test_denovo_gene_sets_exist(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    assert denovo is not None


def test_denovo_get_gene_set_sd_lgds_autism(gscs):
    lgds = gscs.get_gene_set('denovo', 'LGDs', {'SD_TEST': ['autism']})
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 546
    assert lgds['count'] == 551
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_set_sd_missense_autism(gscs):
    lgds = gscs.get_gene_set('denovo', 'Missense', {'SD_TEST': ['autism']})
    assert lgds is not None
    assert lgds['count'] == 2585
    assert lgds['name'] == 'Missense'


def test_denovo_get_gene_set_sd_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs', {'SD_TEST': ['autism', 'epilepsy']})
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 576
    assert lgds['count'] == 581
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_set_sd_syn_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set('denovo', 'Synonymous', {
                             'SD_TEST': ['autism', 'epilepsy']})
    assert lgds is not None
    assert lgds['count'] == 1168
    assert lgds['name'] == 'Synonymous'


def test_denovo_get_gene_sets_sd_autism(gscs):
    gene_sets = gscs.get_gene_sets('denovo', {'SD_TEST': ['autism']})
    assert gene_sets is not None
    assert len(gene_sets) == 19
    gs = gene_sets[0]
    # FIXME: changed after rennotation
    # assert gs['count'] == 546
    assert gs['count'] == 551
    assert gs['name'] == 'LGDs'


def test_denovo_get_gene_sets_sd_unaffected(gscs):
    gene_sets = gscs.get_gene_sets('denovo', {'SD_TEST': ['unaffected']})
    assert gene_sets is not None
    assert len(gene_sets) == 17
    gs = gene_sets[0]
    assert gs['count'] == 222
    assert gs['name'] == 'LGDs'


def test_denovo_get_gene_sets_sd_autism_and_epilepsy(gscs):
    gene_sets = gscs.get_gene_sets(
        'denovo',
        gene_sets_types={'SD_TEST': ['autism', 'epilepsy']})
    assert gene_sets is not None
    assert len(gene_sets) == 19
    gs = gene_sets[0]
    # FIXME: changed after rennotation
    # assert gs['count'] == 576
    assert gs['count'] == 581
    assert gs['name'] == 'LGDs'


def test_denovo_sd_lgds_recurrent(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set(
        'LGDs.Recurrent', gene_sets_types={'SD_TEST': ['autism']})
    assert gs is not None
    assert gs['count'] == 45


def test_denovo_sd_lgds_single(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set(
        'LGDs.Single', gene_sets_types={'SD_TEST': ['autism']})
    assert gs is not None
    # FIXME: changed after rennotation
    # assert gs['count'] == 501
    assert gs['count'] == 506


def test_denovo_get_gene_set_sd_ssc_lgds_autism(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs', {'SD_TEST': ['autism'], 'SSC': ['autism']})
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 546
    assert lgds['count'] == 551
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_set_sd_svip_lgds_autism(gscs):
    lgds = gscs.get_gene_set(
        'denovo',
        'LGDs',
        {
            'SD_TEST': ['autism'],
            'SVIP': ['ASD and other neurodevelopmental disorders']
        })
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 582
    assert lgds['count'] == 585
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_set_sd_svip_missense_autism(gscs):
    lgds = gscs.get_gene_set(
        'denovo',
        'Missense',
        {
            'SD_TEST': ['autism'],
            'SVIP': ['ASD and other neurodevelopmental disorders']
        })
    assert lgds is not None
    assert lgds['count'] == 2721
    assert lgds['name'] == 'Missense'


def test_denovo_get_gene_set_ssc_lgds_epilepsy(gscs):
    lgds = gscs.get_gene_set('denovo', 'LGDs', {'SSC': ['epilepsy']})
    assert lgds is None


def test_denovo_get_gene_set_sd_svip_syn_autism_and_epilepsy(gscs):
    syns = gscs.get_gene_set(
        'denovo',
        'Synonymous',
        {
            'SD_TEST': ['autism', 'epilepsy'],
            'SVIP': ['ASD and other neurodevelopmental disorders']
        })
    assert syns is not None
    assert syns['count'] == 1169
    assert syns['name'] == 'Synonymous'


def test_denovo_get_gene_sets_sd_ssc_autism(gscs):
    gene_sets = gscs.get_gene_sets(
        'denovo', {'SD_TEST': ['autism'], 'SSC': ['autism']})
    assert gene_sets is not None
    assert len(gene_sets) == 19
    gs = gene_sets[0]
    # FIXME: changed after rennotation
    # assert gs['count'] == 546
    assert gs['count'] == 551
    assert gs['name'] == 'LGDs'


def test_denovo_get_gene_sets_sd_ssc_autism_and_epilepsy(gscs):
    gene_sets = gscs.get_gene_sets(
        'denovo',
        gene_sets_types={'SD_TEST': ['autism', 'epilepsy'], 'SSC': ['autism']})
    assert gene_sets is not None
    assert len(gene_sets) == 19
    gs = gene_sets[0]
    # FIXME: changed after rennotation
    # assert gs['count'] == 576
    assert gs['count'] == 581
    assert gs['name'] == 'LGDs'


def test_denovo_sd_ssc_missense_recurrent(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('Missense.Recurrent', gene_sets_types={
                             'SD_TEST': ['autism'], 'SSC': ['autism']})
    assert gs is not None
    assert gs['count'] == 389


def test_denovo_sd_ssc_missense_we_recurrent(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('Missense.WE.Recurrent', gene_sets_types={
                             'SD_TEST': ['autism'], 'SSC': ['autism']})
    assert gs is not None
    assert gs['count'] == 386


def test_denovo_sd_ssc_missense_single(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('Missense.Single', gene_sets_types={
                             'SD_TEST': ['autism'], 'SSC': ['autism']})
    assert gs is not None
    assert gs['count'] == 2196
