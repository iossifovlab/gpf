
import os
import copy

import pyarrow as pa

from dae.variants.effects import Effect
from dae.annotation.tools.effect_annotator import EffectAnnotator
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

    genome = anno_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome")
    assert genome is not None
    assert isinstance(genome, GenomicSequenceResource)

    gene_models = anno_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309"
    )
    assert gene_models is not None
    assert isinstance(gene_models, GeneModelsResource)

    families_loader = FamiliesLoader(
        pedigree_filename)
    families = families_loader.load()
    assert families is not None
    assert len(families) == 1

    genome.open()
    denovo_loader = DenovoLoader(
        families,
        variants_filename, genome=genome
    )
    assert denovo_loader is not None

    effect_annotator = EffectAnnotator(
        gene_models=gene_models, genome=genome)

    variants = list(denovo_loader.full_variants_iterator())
    for sv, fvs in variants:
        print(sv, fvs)
        for sa in sv.alt_alleles:
            attributes = copy.deepcopy(sa.attributes)
            liftover_variants = {}
            effect_annotator.annotate_allele(
                attributes, sa, liftover_variants)

            print(
                attributes["effect_gene_types"],
                attributes["effect_gene_genes"])

            effect_types = sa.get_attribute("effectGene")
            print(effect_types)
            effect = Effect.from_string(
                "!".join([
                    sa.get_attribute("effectType"),
                    sa.get_attribute("effectGene"),
                    sa.get_attribute("effectDetails")
                ])
            )
            print(effect)
            print(effect.genes)

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
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome")
    assert genome is not None
    assert isinstance(genome, GenomicSequenceResource)

    gene_models = anno_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309"
    )
    assert gene_models is not None
    assert isinstance(gene_models, GeneModelsResource)

    effect_annotator = EffectAnnotator(
        gene_models=gene_models, genome=genome)

    schema = effect_annotator.annotation_schema
    assert schema is not None

    field = schema["effect_type"]
    assert field.pa_type == pa.string()

    field = schema["effect_gene_genes"]
    assert field.pa_type == pa.list_(pa.string())

    field = schema["effect_gene_types"]
    assert field.pa_type == pa.list_(pa.string())
