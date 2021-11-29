
import os
import copy

from box import Box

from dae.effect_annotation.effect import AlleleEffects
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotator_factory import AnnotatorFactory

from dae.pedigrees.loader import FamiliesLoader

from dae.backends.dae.loader import DenovoLoader
from dae.genomic_resources.genomic_sequence_resource import \
    GenomicSequenceResource
from dae.genomic_resources.gene_models_resource import \
    GeneModelsResource


def test_effect_annotation_yuen(fixture_dirname, anno_grdb):
    variants_filename = os.path.join(
        fixture_dirname("denovo_import"), "YuenTest-variants.tsv")
    pedigree_filename = os.path.join(
        fixture_dirname("denovo_import"), "YuenTest-pedigree.ped")

    assert os.path.exists(variants_filename)
    assert os.path.exists(pedigree_filename)

    genome_id = \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"
    gene_models_id = \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/" \
        "gene_models/refGene_201309"

    families_loader = FamiliesLoader(
        pedigree_filename)
    families = families_loader.load()
    assert families is not None
    assert len(families) == 1

    genome = anno_grdb.get_resource(genome_id)
    genome.open()
    denovo_loader = DenovoLoader(
        families,
        variants_filename, genome=genome
    )
    assert denovo_loader is not None

    pipeline = AnnotationPipeline([], anno_grdb, None)
    config = Box({
        "annotator_type": "effect_annotator",
        "genome": genome_id,
        "gene_models": gene_models_id,
        "attributes": None,
    })

    effect_annotator = AnnotatorFactory.build(pipeline, config)

    variants = list(denovo_loader.full_variants_iterator())
    for sv, fvs in variants:
        print(sv, fvs)
        for sa in sv.alt_alleles:
            attributes = copy.deepcopy(sa.attributes)
            liftover_variants = {}
            effect_annotator.annotate(
                attributes, sa.get_annotatable(), liftover_variants)

            print(
                attributes["effect_gene_types"],
                attributes["effect_gene_genes"])
            print(100*"-")
            print(attributes)

            effect = attributes["allele_effects"]
            print("effect:", effect)
            print(effect.genes)
            assert isinstance(effect, AlleleEffects)

            assert len(effect.genes) == len(attributes["effect_gene_genes"]), \
                (effect.genes, attributes["effect_gene_genes"])
            assert len(effect.genes) == len(attributes["effect_gene_types"]), \
                (effect.genes, attributes["effect_gene_types"])

            assert set([g.symbol for g in effect.genes]) == \
                set(attributes["effect_gene_genes"])
            assert set([g.effect for g in effect.genes]) == \
                set(attributes["effect_gene_types"])


def test_effect_annotation_schema(anno_grdb):
    genome = anno_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome")
    assert genome is not None
    assert isinstance(genome, GenomicSequenceResource)

    gene_models = anno_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
        "gene_models/refGene_201309"
    )
    assert gene_models is not None
    assert isinstance(gene_models, GeneModelsResource)

    pipeline = AnnotationPipeline([], anno_grdb, None)
    config = Box({
        "annotator_type": "effect_annotator",
        "genome": genome.resource_id,
        "gene_models": gene_models.resource_id,
        "attributes": None,
    })

    effect_annotator = AnnotatorFactory.build(pipeline, config)

    schema = effect_annotator.annotation_schema
    assert schema is not None

    field = schema["effect_type"]
    assert field.type == "str"

    field = schema["effect_genes"]
    assert field.type == "str"

    field = schema["effect_details"]
    assert field.type == "str"
