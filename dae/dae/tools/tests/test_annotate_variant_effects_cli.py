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


# def test_annotate_variant_simple(temp_filename, genomes_db_2013):
#     denovo_filename = relative_to_this_test_folder("fixtures/denovo.txt")
#     assert os.path.exists(denovo_filename)

#     expected_df = pd.read_csv(denovo_filename, sep="\t")
#     assert expected_df is not None
#     assert len(expected_df) == 8

#     genome_id = genomes_db_2013.config.genomes.default_genome
#     genome_config = getattr(genomes_db_2013.config.genome, genome_id)
#     ref_seq_gene_model = getattr(genome_config.gene_models, "RefSeq2013")
#     gene_model_file = ref_seq_gene_model.file

#     command = (
#         f"cut -f 1-3 {denovo_filename} "
#         f"| annotate_variants.py --Traw {gene_model_file} --TrawFormat default"
#         f"| head -n 9 > {temp_filename}"
#     )
#     print(command)
#     res = os.system(command)
#     assert res == 0

#     result_df = pd.read_csv(temp_filename, sep="\t")
#     check_columns = ["effectType", "effectGene"]

#     pd.testing.assert_frame_equal(
#         result_df[check_columns], expected_df[check_columns]
#     )


# def test_gene_models_orig_transcript_id(genomes_db_2019):

#     gene_models = genomes_db_2019.get_gene_models("RefSeq")
#     assert gene_models.filename.endswith(
#         "refGene-20190211.gz"
#     ), gene_models.filename

#     for count, tr in enumerate(gene_models.transcript_models.values()):
#         # print(dir(tr))
#         assert tr.tr_id != tr.tr_name
#         assert tr.tr_name in tr.tr_id

#         if count >= 1000:
#             break


# def test_gene_models_load_default(genomes_db_2019):

#     genome_id = genomes_db_2019.config.genomes.default_genome
#     genome_config = getattr(genomes_db_2019.config.genome, genome_id)
#     ref_seq_gene_model = getattr(genome_config.gene_models, "RefSeq")

#     assert ref_seq_gene_model is not None
#     # gene_models = load_gene_models(ref_seq_gene_model.file, format="default")
#     # assert gene_models is not None
