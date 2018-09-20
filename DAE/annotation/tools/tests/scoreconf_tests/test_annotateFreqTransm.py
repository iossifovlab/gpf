import pytest
import gzip
from annotation.tools.annotateFreqTransm \
        import FrequencyAnnotator
from StringIO import StringIO
from box import Box


def get_opts(score_file):
    options = {
        'c': 'chr',
        'p': 'position',
        'v': 'variant',
        'H': False,
        'scores_file': score_file,
        'direct': False,
        'frequency': 'all.altFreq'
    }
    return Box(options, default_box=True, default_box_attr=None)


def fake_gzip_open(filename, *args):
    return filename


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


@pytest.fixture
def freq_input():
    return [
        ['1', '69428', 'sub(T->G)'],
        ['1', '69438', 'sub(T->C)'],
        ['1', '69458', 'sub(T->C)'],
        ['1', '69511', 'sub(A->G)']
    ]


@pytest.fixture
def freq_annotations():
    return [['0.49'], ['0.03'], ['0.03'], ['98.00']]


@pytest.fixture
def freq_scores():
    score_lines = [
        ['chr', 'position', 'variant', 'familyData', 'all.nParCalled', 'all.prcntParCalled', 'all.nAltAlls', 'all.altFreq', 'effectType', 'effectGene', 'effectDetails', 'segDups', 'HW', 'SSC-freq', 'EVS-freq', 'E65-freq'],
        ['1', '69428', 'sub(T->G)', '11025:121/101:15 35 18/9 0 10/0 0 0;11563:2121/0101:11 27 34 13/0 26 0 15/0 0 0 0;11914:212/010:28 0 30/0 9 0/0 0 0;12478:1221/1001:39 14 68 25/18 0 0 19/0 0 0 0;14009:2122/0100:73 32 71 82/1 17 0 0/0 0 0 0;14028:2111/0111:21 33 33 42/0 20 20 22/0 0 0 0;14474:2121/0101:9 5 40 19/0 7 0 10/0 0 0 0;12046:121/101:24 30 0/7 0 10/0 0 0;12597:1100/1122:20 26 0 0/0 22 43 20/0 0 0 0;13066:1221/1001:23 33 40 26/27 0 0 24/0 0 0 0;13085:021/201:0 41 27/35 0 24/0 0 0', '1336', '27.03', '13', '0.49', 'missense', 'OR4F5:missense', '113/306(Phe->Cys)', '2', '0.0161', '0.49', '3.06', '2.47'],
        ['1', '69438', 'sub(T->C)', '11940:121/101:19 21 18/27 0 35/0 0 0', '1430', '28.94', '1', '0.03', 'synonymous', 'OR4F5:synonymous', '116/306', '2', '1.0000', '0.03', '', '0.00'],
        ['1', '69458', 'sub(T->C)', '11353:1222/1000:0 23 29 22/16 0 0 0/1 0 0 0', '1460', '29.54', '1', '0.03', 'missense', 'OR4F5:missense', '123/306(Leu->Pro)', '2', '1.0000', '0.03', '', ''],
        ['1', '69511', 'sub(A->G)', 'TOOMANY', '300', '6.07', '588', '98.00', 'missense', 'OR4F5:missense', '141/306(Thr->Ala)', '2', '0.0000', '98.00', '75.98', '94.02']
    ]
    return StringIO('\n'.join(map(lambda line: '\t'.join(line), score_lines)))


@pytest.fixture
def freq_annotator(freq_scores, mocker):
    freq_opts = get_opts(score_file=freq_scores)
    return FrequencyAnnotator(freq_opts,
                              header=['chr', 'position', 'variant'])


def test_freq_score(freq_input, freq_annotations, freq_annotator, mocker):
    all_line_annotations = [freq_annotator.line_annotations(line,
                                                            freq_annotator.new_columns)
                            for line in freq_input]

    assert (all_line_annotations == freq_annotations)
