import pytest
import os
import pysam
from contextlib import closing


@pytest.mark.xfail
def test_tabix():
    dirname = '/home/lubo/Work/seq-pipeline/data-hg19-parquet/'\
        'parquet/studies/w1202s766e611'

    summary_filename = os.path.join(
        dirname, 'transmissionIndex-HW-DNRM.txt.bgz')
    toomany_filename = os.path.join(
        dirname, 'transmissionIndex-HW-DNRM-TOOMANY.txt.bgz')

    region = "1:0-100000"
    region = None

    with closing(pysam.Tabixfile(summary_filename)) as sum_tbf, \
            closing(pysam.Tabixfile(toomany_filename)) as too_tbf:
        print("Region:", region)
        if region is None:
            summary_iterator = sum_tbf.fetch(
                region=region,
                parser=pysam.asTuple())
            toomany_iterator = too_tbf.fetch(
                region=region)
        else:
            summary_iterator = sum_tbf.fetch(
                region=region,
                parser=pysam.asTuple())
            toomany_iterator = too_tbf.fetch(
                region=region,
                parser=pysam.asTuple())
        assert summary_iterator is not None
        assert toomany_iterator is not None

        for v in summary_iterator:
            print(v)
            break

        for v in toomany_iterator:
            print(v)
            break
