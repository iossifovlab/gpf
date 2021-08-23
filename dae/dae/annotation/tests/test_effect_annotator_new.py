
import os
import copy

from dae.annotation.tools.effect_annotator import VariantEffectAnnotator
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

    effect_annotator = VariantEffectAnnotator(
        gene_models=gene_models, genome=genome)

    variants = list(denovo_loader.full_variants_iterator())
    for sv, fvs in variants:
        print(sv, fvs)
        for sa in sv.alt_alleles:
            attributes = copy.deepcopy(sa.attributes)
            liftover_variants = {}
            effect_annotator.annotate(attributes, sa, liftover_variants)

            print(
                attributes["effect_gene_types"],
                attributes["effect_gene_genes"])
