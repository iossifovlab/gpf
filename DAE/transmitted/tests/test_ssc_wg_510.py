'''
Created on Nov 22, 2016

@author: lubo
'''
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from DAE import vDB
import pytest
from transmitted.mysql_query import MysqlTransmittedQuery
import time
from .mysql_transmitted_std_queries import get_gene_set_syms
from tests.pytest_marks import slow, veryslow, ssc_wg


@pytest.fixture(scope='session')
def wg_study(request):
    study = vDB.get_study('SSC_WG_510')
    return study


def report_time(start, res):
    print(": {:.3}s (count={})".format(time.time() - start, len(res)))


@ssc_wg
def test_wg_study():
    study = vDB.get_study('SSC_WG_510')
    assert study is not None

    assert study.has_transmitted


@ssc_wg
def test_q101_get_everything_in_single_gene(wg_study):
    start = time.time()
    m = MysqlTransmittedQuery(wg_study)

    vs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['CHD8'],
    )
    res = [v for v in vs]
    assert 18884 == len(res)

    report_time(start, res)


@ssc_wg
def test_q201_limit_get_everything_in_a_family(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13884'],
        limit=2000,
    )

    res = [v for v in vs]
    assert 2000 == len(res)

    report_time(start, res)


@ssc_wg
@veryslow
def test_q201_get_everything_in_a_family(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13884'],
    )

    res = [v for v in vs]
    # assert 2000 == len(res)

    report_time(start, res)


@ssc_wg
def test_q301_get_interesting_in_a_family(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop',
                     'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS'],
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 1607 == len(res)

    report_time(start, res)


@ssc_wg
def test_q401_limit_get_all_ultra_rare_lgds(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        limit=2000,
    )

    res = [v for v in vs]
    assert 2000 == len(res)

    report_time(start, res)


@ssc_wg
def test_q401_get_all_ultra_rare_lgds(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
    )

    res = [v for v in vs]
    assert 10228 == len(res)

    report_time(start, res)


@ssc_wg
def test_q501_get_ultra_rare_lgds_in_fmrp_genes(wg_study):
    gene_syms = get_gene_set_syms('main', 'FMRP Tuschl')

    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        geneSyms=list(gene_syms),
    )

    res = [v for v in vs]
    assert 456 == len(res)

    report_time(start, res)


@ssc_wg
def test_q601_get_all_ultra_rare_lgds_in_proband(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs',
        inChild='prb'
    )

    res = [v for v in vs]
    assert 5293 == len(res)

    report_time(start, res)


@ssc_wg
def test_q701_limit_quads(wg_study):
    effectTypes = ['splice-site', 'nonsense', 'missense', 'frame-shift']
    familyIds = ['14174', '14178', '12656', '11543', '13735', '13734', '13732', '11549', '14071', '14070', '13739', '13089', '13083', '13169', '11918', '13166', '11855', '14351', '12931', '12937', '14357', '14359', '12938', '12939', '14211', '11142', '14213', '14212', '14215', '12065', '13602', '13601', '13609', '13608', '14185', '12661', '13012', '13544', '14454', '14321', '11132', '14598', '13543', '14040', '14329', '14328', '14458', '14043', '12799', '12790', '11765', '12596', '13900', '13901', '12598', '11000', '14525', '11004', '14334', '13335', '11110', '14444', '12123', '14031', '14032', '14130', '14132', '14137', '11347', '11349', '12447', '12441', '12231', '14623', '14629', '12624', '13163', '13576', '13116', '13054', '12057', '14241', '12942', '13502', '13503', '13504', '14366', '14453', '14490', '12691', '14397', '14391', '13948', '11189', '12497', '13942', '12695', '11047', '14566', '14561', '13374', '13371', '14404', '14405', '14407', '11716', '12655', '13837', '13830', '13832', '13833', '13838', '11309', '13934', '12839', '12838', '12373', '12407', '12271', '12274', '14103', '14106', '13721', '13723', '12879', '14068', '14065', '13154', '11378', '13097', '13095', '13092', '13258', '11905', '11089', '13311', '14209', '14203', '14616', '14206', '14610', '14613', '14612', '14198', '13618', '13619', '12651', '13611', '13612', '14195', '14290', '14297', '13028', '11285', '13945', '14336', '13533', '14443', '13535', '14333', '14446', '14448', '13538', '14338', '14681', '12006', '14536', '12875', '13975', '13870', '13876', '14531', '14435', '13447', '11158', '14533', '11625', '11629', '13709', '13808', '11230', '13210', '11201', '12579', '12572', '12220', '12340', '12343', '14320', '14652', '14201', '14096', '14092', '13064', '13063',  # @IgnorePep8
                 '13061', '13891', '14592', '13069', '13265', '13267', '14480', '12951', '14482', '14483', '12888', '12048', '14376', '12680', '11417', '12763', '13629', '12481', '14571', '14574', '14576', '14578', '14579', '14478', '14317', '13568', '14470', '13565', '11115', '11114', '12473', '13842', '12435', '13928', '14505', '14503', '14502', '11029', '13498', '13497', '13694', '14114', '14115', '11800', '11568', '11569', '11206', '14053', '13993', '13148', '13385', '12318', '14233', '14232', '14230', '12643', '14604', '12723', '11519', '13660', '13663', '11512', '14283', '14280', '13136', '13034', '13036', '12728', '14300', '14306', '12964', '14309', '13529', '11581', '13961', '13966', '12869', '13355', '13290', '14427', '14425', '13593', '14423', '12101', '13456', '14544', '11638', '13793', '13795', '14015', '14014', '14011', '13180', '11324', '11325', '13816', '13666', '12358', '12210', '14642', '14643', '11611', '11078', '14169', '11491', '11496', '13073', '11393', '13890', '11964', '11966', '11277', '13171', '11845', '11842', '14346', '14343', '13898', '14265', '11075', '13815', '13680', '13631', '11946', '13001', '13000', '13412', '13559', '14463', '11107', '14464', '11472', '11773', '11775', '13851', '13855', '12859', '13555', '12851', '12582', '12581', '12854', '12857', '14514', '14513', '13307', '12953', '14046', '11959', '14041', '14042', '12568', '12302', '14122', '12517', '12510', '13236', '14225', '14227', '14384', '12636', '12731', '14631', '14636', '13776', '13774', '13670', '13563', '13048', '13123', '11818', '13129', '14254', '14257', '13515', '12184', '14258', '13952', '12369', '12850', '14413', '13581', '14411', '12719', '13584', '14416', '14550', '11077', '14555', '11729', '14001', '13788', '14004', '12550', '11316', '12492', '12368']  # @IgnorePep8

    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=effectTypes,
        familyIds=familyIds,
        presentInParent=["mother only", "father only",
                         "mother and father", "neither"],
        presentInChild=["autism only", "autism and unaffected"],
        limit=2000,
    )

    res = [v for v in vs]
    assert 2000 == len(res)

    report_time(start, res)


@slow
@ssc_wg
def test_q701_quads(wg_study):
    effectTypes = ['splice-site', 'nonsense', 'missense', 'frame-shift']
    familyIds = ['14174', '14178', '12656', '11543', '13735', '13734', '13732', '11549', '14071', '14070', '13739', '13089', '13083', '13169', '11918', '13166', '11855', '14351', '12931', '12937', '14357', '14359', '12938', '12939', '14211', '11142', '14213', '14212', '14215', '12065', '13602', '13601', '13609', '13608', '14185', '12661', '13012', '13544', '14454', '14321', '11132', '14598', '13543', '14040', '14329', '14328', '14458', '14043', '12799', '12790', '11765', '12596', '13900', '13901', '12598', '11000', '14525', '11004', '14334', '13335', '11110', '14444', '12123', '14031', '14032', '14130', '14132', '14137', '11347', '11349', '12447', '12441', '12231', '14623', '14629', '12624', '13163', '13576', '13116', '13054', '12057', '14241', '12942', '13502', '13503', '13504', '14366', '14453', '14490', '12691', '14397', '14391', '13948', '11189', '12497', '13942', '12695', '11047', '14566', '14561', '13374', '13371', '14404', '14405', '14407', '11716', '12655', '13837', '13830', '13832', '13833', '13838', '11309', '13934', '12839', '12838', '12373', '12407', '12271', '12274', '14103', '14106', '13721', '13723', '12879', '14068', '14065', '13154', '11378', '13097', '13095', '13092', '13258', '11905', '11089', '13311', '14209', '14203', '14616', '14206', '14610', '14613', '14612', '14198', '13618', '13619', '12651', '13611', '13612', '14195', '14290', '14297', '13028', '11285', '13945', '14336', '13533', '14443', '13535', '14333', '14446', '14448', '13538', '14338', '14681', '12006', '14536', '12875', '13975', '13870', '13876', '14531', '14435', '13447', '11158', '14533', '11625', '11629', '13709', '13808', '11230', '13210', '11201', '12579', '12572', '12220', '12340', '12343', '14320', '14652', '14201', '14096', '14092', '13064', '13063',  # @IgnorePep8
                 '13061', '13891', '14592', '13069', '13265', '13267', '14480', '12951', '14482', '14483', '12888', '12048', '14376', '12680', '11417', '12763', '13629', '12481', '14571', '14574', '14576', '14578', '14579', '14478', '14317', '13568', '14470', '13565', '11115', '11114', '12473', '13842', '12435', '13928', '14505', '14503', '14502', '11029', '13498', '13497', '13694', '14114', '14115', '11800', '11568', '11569', '11206', '14053', '13993', '13148', '13385', '12318', '14233', '14232', '14230', '12643', '14604', '12723', '11519', '13660', '13663', '11512', '14283', '14280', '13136', '13034', '13036', '12728', '14300', '14306', '12964', '14309', '13529', '11581', '13961', '13966', '12869', '13355', '13290', '14427', '14425', '13593', '14423', '12101', '13456', '14544', '11638', '13793', '13795', '14015', '14014', '14011', '13180', '11324', '11325', '13816', '13666', '12358', '12210', '14642', '14643', '11611', '11078', '14169', '11491', '11496', '13073', '11393', '13890', '11964', '11966', '11277', '13171', '11845', '11842', '14346', '14343', '13898', '14265', '11075', '13815', '13680', '13631', '11946', '13001', '13000', '13412', '13559', '14463', '11107', '14464', '11472', '11773', '11775', '13851', '13855', '12859', '13555', '12851', '12582', '12581', '12854', '12857', '14514', '14513', '13307', '12953', '14046', '11959', '14041', '14042', '12568', '12302', '14122', '12517', '12510', '13236', '14225', '14227', '14384', '12636', '12731', '14631', '14636', '13776', '13774', '13670', '13563', '13048', '13123', '11818', '13129', '14254', '14257', '13515', '12184', '14258', '13952', '12369', '12850', '14413', '13581', '14411', '12719', '13584', '14416', '14550', '11077', '14555', '11729', '14001', '13788', '14004', '12550', '11316', '12492', '12368']  # @IgnorePep8

    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=effectTypes,
        familyIds=familyIds,
        presentInParent=["mother only", "father only",
                         "mother and father", "neither"],
        presentInChild=["autism only", "autism and unaffected"],
    )

    res = [v for v in vs]
    assert 66348 == len(res)

    report_time(start, res)


@ssc_wg
def test_q801_limit_get_interesting_rare_variants(wg_study):
    effectTypes = ['splice-site', 'nonsense', 'missense', 'frame-shift']

    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=effectTypes,
        presentInParent=["mother only", "father only",
                         "mother and father", "neither"],
        presentInChild=["autism only", "autism and unaffected"],
        limit=2000,
    )

    res = [v for v in vs]
    assert 2000 == len(res)

    report_time(start, res)


@slow
@ssc_wg
def test_q801_get_interesting_rare_variants(wg_study):
    effectTypes = ['splice-site', 'nonsense', 'missense', 'frame-shift']

    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=effectTypes,
        presentInParent=["mother only", "father only",
                         "mother and father", "neither"],
        presentInChild=["autism only", "autism and unaffected"],
    )

    res = [v for v in vs]
    # assert 2000 == len(res)

    report_time(start, res)


@ssc_wg
def test_get_family_rare_lgds_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop'],
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 75 == len(res)

    report_time(start, res)


@ssc_wg
def test_get_family_ultra_rare_lgds_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense', ],
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 44 == len(res)

    report_time(start, res)


@ssc_wg
def test_get_ultra_rare_lgds_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense', ],
    )

    res = [v for v in vs]
    assert 10228 == len(res)

    report_time(start, res)


@veryslow
@ssc_wg
def test_get_family_ultra_rare_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 141213 == len(res)

    report_time(start, res)
