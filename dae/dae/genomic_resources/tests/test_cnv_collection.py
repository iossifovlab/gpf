# pylint: disable=C0116

from dae.genomic_resources.cnv_collection import CnvCollection
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_resource


def test_cnv_collection_resource() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
            scores:
                - id: frequency
                  name: frequency
                  type: float
                  desc: some populaton frequency
                - id: collection
                  name: collection
                  type: str
                  desc: SSC or AGRE
                - id: affected_status
                  name: affected_status
                  type: str
                  desc: |
                    shows if the child that has the de novo
                    is affected or unaffected
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  frequency  collection affected_status
            1      10         20       0.02       SSC        affected
            1      50         100      0.1        SSC        affected
            2      1          2        0.00001    AGRE       unaffected
            2      16         20       0.3        SSC        affected
            2      200        203      0.0002     AGRE       unaffected
            15     16         20       0.2        AGRE       affected
        """,
    })
    assert res.get_type() == "cnv_collection"

    cnv_collection = CnvCollection(res)
    cnv_collection.open()
    aaa = cnv_collection.fetch_cnvs("1", 5, 15)
    assert len(aaa) == 1
    assert aaa[0].attributes["frequency"] == 0.02
    assert aaa[0].attributes["collection"] == "SSC"
