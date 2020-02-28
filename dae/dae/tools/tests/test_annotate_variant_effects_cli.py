import pytest
import os
import tempfile
import shutil

import pandas as pd


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix="_eff", prefix="variants_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    output = os.path.join(dirname, "annotation.tmp")
    return os.path.abspath(output)


def test_annotate_variant_simple(temp_filename, genomes_db_2013):
    denovo_filename = relative_to_this_test_folder("fixtures/denovo.txt")
    assert os.path.exists(denovo_filename)

    expected_df = pd.read_csv(denovo_filename, sep="\t")
    assert expected_df is not None
    assert len(expected_df) == 8

    command = (
        "cut -f 1-3 {} "
        "| annotate_variant.py -T RefSeq2013 "
        "| head -n 9 > {}".format(denovo_filename, temp_filename)
    )
    print(command)
    res = os.system(command)
    assert res == 0

    result_df = pd.read_csv(temp_filename, sep="\t")
    check_columns = ["effectType", "effectGene"]

    pd.testing.assert_frame_equal(
        result_df[check_columns], expected_df[check_columns]
    )


def test_gene_models_orig_transcript_id(genomes_db_2019):

    gene_models = genomes_db_2019.get_gene_model(
        "RefSeq", genomes_db_2019.default_genome
    )
    assert gene_models.location.endswith(
        "refGene-20190211.gz"
    ), gene_models.location

    for count, tr in enumerate(gene_models.transcriptModels.values()):
        # print(dir(tr))
        assert tr.trID != tr.trOrigId
        if count >= 1000:
            break
