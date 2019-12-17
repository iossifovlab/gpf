import pytest
import os
import tempfile
import shutil

import pandas as pd


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix='_eff', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    output = os.path.join(
        dirname,
        'annotation.tmp'
    )
    return os.path.abspath(output)


def test_annotate_variant_simple(temp_filename, default_gene_models):
    denovo_filename = relative_to_this_test_folder('fixtures/denovo.txt')
    assert os.path.exists(denovo_filename)

    expected_df = pd.read_csv(denovo_filename, sep='\t')
    assert expected_df is not None
    assert len(expected_df) == 8

    print(default_gene_models.location)

    command = "cut -f 1-3 {} " \
        "| annotate_variant.py -T RefSeq2013 " \
        "| head -n 9 > {}".format(
        denovo_filename, temp_filename
    )
    print(command)
    res = os.system(command)
    assert res == 0

    result_df = pd.read_csv(temp_filename, sep='\t')
    print(result_df.head())

    pd.testing.assert_frame_equal(
        result_df[['effectType', 'effectGene']],
        expected_df[['effectType', 'effectGene']]
    )


def test_gene_models_orig_transcript_id(genomes_db, default_gene_models):
    assert default_gene_models.location.endswith("refGene-201309.gz")

    gene_models = genomes_db.get_gene_models("RefSeq")
    assert gene_models.location.endswith("refGene-20190211.gz")

    for count, tr in enumerate(gene_models.transcriptModels.values()):
        # print(dir(tr))
        assert tr.trID != tr.trOrigId
        if count >= 1000:
            break
