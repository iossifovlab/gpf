from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_basic():
    grr_repo = GenomicResourceEmbededRepo("r", {
        "one": {
            GR_CONF_FILE_NAME: '''
                type: PositionScore
                table:
                    filename: data.mem
                scores:
                  - id: s1
                    type: float
                    name: s1''',
            "data.mem": '''
                chrom  pos_begin  s1
                1      10         0.02
                1      11         0.03
                1      15         0.46
                2      8          0.01
                '''
        }
    })
    annotation_cofiguration = AnnotationPipeline.parse_config("""
    score_annotators:
    - annotator: position_score
      resource: one
    """)
    context = {}
    ann_pipe = AnnotationPipeline.build(
        annotation_cofiguration,
        grr_repo,
        context=context)
    assert grr_repo
    assert ann_pipe

    # class annotation.VariantAllele:
    #     def get_chrom()
    #     def get_possition()
    #     def get_end_position()
    #     def get_ref()
    #     def get_alt()

    #     def get_variant_type_helper()

    #     def update_attributes()

    # va = BasicVariantSubstitution("1", 11, "G", "A")
    # annPipe.annotate_summary_variant(va)
    # assert va.get_attribute("s1") == 0.03
    # assert set(annPipe.get_ordered_attributes_names()) = set(["s1"])
