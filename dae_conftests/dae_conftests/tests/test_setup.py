import logging

logger = logging.getLogger(__name__)


def test_setup(data_import, iossifov2014_impala):
    logger.info("just setup imports")
