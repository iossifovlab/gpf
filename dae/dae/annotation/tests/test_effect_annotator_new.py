from dae.pedigrees.loader import FamiliesLoader
import os

from dae.backends.dae.loader import DenovoLoader
from dae.genomic_resources.genomic_sequence_resource import \
    GenomicSequenceResource


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

    for sv, fvs in denovo_loader.full_variants_iterator():
        print(sv, fvs)
