import textwrap
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.annotation.annotation_factory import build_annotation_pipeline


reannotation_grr = build_genomic_resource_repository({
    "id": "test_annotation",
    "type": "embedded",
    "content": {
        "LGD_rank": {
            "genomic_resource.yaml": """
                type: gene_score
                filename: LGD.csv
                gene_scores:
                  - id: LGD_rank
                    desc: LGD rank
                histograms:
                  - score: LGD_rank
                    bins: 150
                    x_scale: linear
                    y_scale: linear
            """,
            "LGD.csv": textwrap.dedent("""
                "gene","LGD_score","LGD_rank"
                "LRP1",0.000014,1
                "TRRAP",0.00016,3
                "ANKRD11",0.0004,5
                "ZFHX3",0.000925,8
                "HERC2",0.003682,25
                "TRIO",0.001563,11
                "MACF1",0.000442,6
                "PLEC",0.004842,40
                "SRRM2",0.004471,35
                "SPTBN1",0.002715,19.5
                "UBR4",0.007496,59
            """)
        },
        "dummyChain": {
            "genomic_resource.yaml": """
                type: liftover_chain
                filename: test.chain
            """,
            "test.chain": "blabla",
        },
        "dummyGenome": {
            "genomic_resource.yaml": """
                type: genome
                filename: chrAll.fa
                chrom_prefix: "chr"
            """,
            "chrAll.fa": f"""
            >chrA
            {100 * "A"}
            """
        },
    }
})


def test_reannotation_utilities():
    """Test various reannotation functionalities."""
    pipeline_config = """
    - liftover_annotator:
        chain: dummyChain
        target_genome: dummyGenome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: LGD_rank
        input_gene_list: my_genes
    """
    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=reannotation_grr
    )
    result = {
        annotator_id: annotator.used_context_attributes
        for annotator_id, annotator in pipeline.annotator_ids.items()
    }
    assert result == {
        "A1": (),
        "A2": ("hgX_annotatable",),
        "A3": ("my_genes",),
    }
