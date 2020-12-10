from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader


def test_cnv_loader(fixture_dirname, genomes_db_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants.txt")

    loader = CNVLoader(families, variants_file, genomes_db_2013.get_genome())
    assert loader is not None

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 12


def test_cnv_loader_alt(fixture_dirname, genomes_db_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants_alt_1.txt")

    loader = CNVLoader(families, variants_file, genomes_db_2013.get_genome())
    assert loader is not None

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 35


def test_cnv_loader_alt_2(fixture_dirname, genomes_db_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants_alt_2.txt")

    loader = CNVLoader(families, variants_file, genomes_db_2013.get_genome())
    assert loader is not None

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 30
