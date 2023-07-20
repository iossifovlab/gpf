# pylint: disable=C0116

from dae.genomic_resources.testing import build_inmemory_test_resource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_cnv_collection_resource():
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
        """,
        "data.mem": """
            chrom  pos_begin  pos_end
            1      10         20
            1      50         100
            2      1          2
            2      16         20
            2      200        203
            15     16         20
        """
    })
    assert res.get_type() == "cnv_collection"
