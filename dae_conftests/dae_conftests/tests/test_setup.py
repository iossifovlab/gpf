# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging

logger = logging.getLogger(__name__)


def test_setup(
        data_import,
        iossifov2014_impala,
        dae_calc_gene_sets,
        agp_gpf_instance):
    logger.info("just setup imports")
