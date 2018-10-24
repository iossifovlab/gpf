from __future__ import unicode_literals
import pytest
import pysam
import gzip
from io import StringIO
# from annotation.tools.annotateFreqTransm import FrequencyAnnotator
# from .utils import Dummy_tbi, dummy_gzip_open, get_test_annotator_opts


# @pytest.fixture(autouse=True)
# def mock(mocker):
#     mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
#     mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


# @pytest.fixture
# def input_():
#     return [
#         ['1', '69428', 'sub(T->G)'],
#         ['1', '69438', 'sub(T->C)'],
#         ['1', '69458', 'sub(T->C)'],
#         ['1', '69511', 'sub(A->G)']
#     ]


# @pytest.fixture
# def expected_annotations():
#     return [[0.49], [0.03], [0.03], [98.00]]


# @pytest.fixture
# def scores():
#     scores = (
#         '#chr\tposition\tvariant\tall.nParCalled\tall.prcntParCalled\t'
#         'all.nAltAlls\tall.altFreq\tsegDups\tHW\t'
#         'SSC-freq\tEVS-freq\tE65-freq\n'
#         '1\t69428\tsub(T->G)\t1336\t27.03\t'
#         '13\t0.49\t2\t0.0161\t0.49\t3.06\t2.47\n'
#         '1\t69438\tsub(T->C)\t1430\t28.94\t'
#         '1\t0.03\t2\t1.0000\t0.03\t\t0.00\n'
#         '1\t69458\tsub(T->C)\t1460\t29.54\t'
#         '1\t0.03\t2\t1.0000\t0.03\t\t\n'
#         '1\t69511\tsub(A->G)\t300\t6.07\t'
#         '588\t98.00\t2\t0.0000\t98.00\t75.98\t94.02\n')
#     return StringIO(scores)


# @pytest.fixture
# def annotator(scores):
#     opts = get_test_annotator_opts(scores)
#     return FrequencyAnnotator(opts, header=['chrom', 'pos', 'variant'])


# def test_freq_score(input_, expected_annotations, annotator):
#     annotations = [
#         annotator.line_annotations(line, annotator.new_columns)
#         for line in input_
#     ]
#     assert (annotations == expected_annotations)
