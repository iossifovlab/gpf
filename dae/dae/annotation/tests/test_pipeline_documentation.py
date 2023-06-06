from dae.annotation.annotation_factory import build_annotation_pipeline


def test_basic():
    # pipeline = build_annotation_pipeline(pipeline_config_str="""
    #         - normalize_allele_annotator
    #         - debug_annotator
    #         """, grr_repository=build_inmemory_test_repository({}))
    pipeline = build_annotation_pipeline(pipeline_config_str="""
            - normalize_allele_annotator:
                genome: hg38/genomes/GRCh38-hg38
            - debug_annotator:
                input_annotatable: normalized_allele
            """)
    print("\n\nANNOTATOR DOCUMENTATION:")
    print(pipeline.annotators[1].get_info().documentation)
    print("++++++++++++++++++")
    print("ATTIBUTE DOCUMENTATION:")
    print(pipeline.annotators[1].get_info().attributes[0].documentation)
    print("++++++++++++++++++")
