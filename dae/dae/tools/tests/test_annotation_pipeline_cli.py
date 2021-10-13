import pytest
import os
import tempfile
import shutil

# import pandas as pd


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


# def test_annotation_pipeline_simple(temp_filename, genomes_db_2013):
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
#         f"| annotation_pipeline.py --Traw {gene_model_file} "
#         f"| head -n 9 > {temp_filename}"
#     )
#     print(command)
#     res = os.system(command)
#     assert res == 0

#     result_df = pd.read_csv(temp_filename, sep="\t")
#     print(result_df.head())
#     print(expected_df.head())

#     result_df = result_df.rename(columns={
#         "effect_type": "effectType",
#         "effect_genes": "effectGene"
#     })

#     pd.testing.assert_frame_equal(
#         result_df[["effectType", "effectGene"]],
#         expected_df[["effectType", "effectGene"]]
#     )
