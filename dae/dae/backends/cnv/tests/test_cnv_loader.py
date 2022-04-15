from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader


def test_cnv_loader(fixture_dirname, gpf_instance_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants.txt")

    loader = CNVLoader(
        families, variants_file, gpf_instance_2013.reference_genome,
        params={
            "cnv_family_id": "familyId",
            "cnv_best_state": "bestState"
        })

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 12


def test_cnv_loader_avoids_duplication(fixture_dirname, gpf_instance_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants_dup.txt")

    loader = CNVLoader(
        families, variants_file, gpf_instance_2013.reference_genome,
        params={
            "cnv_family_id": "familyId",
            "cnv_best_state": "bestState"
        })

    svs = []
    fvs = []
    for sv, fvs_ in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in fvs_:
            fvs.append(fv)

    print(len(fvs))
    assert len(svs) == 4
    assert len(fvs) == 5


def test_cnv_loader_alt(fixture_dirname, gpf_instance_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None
    variants_file = fixture_dirname("backends/cnv_variants_alt_1.txt")

    loader = CNVLoader(
        families, variants_file, gpf_instance_2013.reference_genome,
        params={
            "cnv_chrom": "Chr",
            "cnv_start": "Start",
            "cnv_end": "Stop",
            "cnv_variant_type": "Del/Dup",
            "cnv_plus_values": ["Dup", "Dup_Germline"],
            "cnv_minus_values": ["Del", "Del_Germline"],
            "cnv_person_id": "personId"
        }
    )

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 35


def test_cnv_loader_alt_best_state(fixture_dirname, gpf_instance_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None
    variants_file = fixture_dirname(
        "backends/cnv_variants_alt_1_best_state.txt")

    loader = CNVLoader(
        families, variants_file, gpf_instance_2013.reference_genome,
        params={
            "cnv_chrom": "Chr",
            "cnv_start": "Start",
            "cnv_end": "Stop",
            "cnv_variant_type": "Del/Dup",
            "cnv_plus_values": ["Dup", "Dup_Germline"],
            "cnv_minus_values": ["Del", "Del_Germline"],
            "cnv_person_id": "personId"
        }
    )

    svs = []
    fvs = []
    for sv, _fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in _fvs:
            fvs.append(fv)

    assert len(svs) == 1
    assert len(fvs) == 4
    print(fvs[0].best_state)


def test_cnv_loader_alt_2(fixture_dirname, gpf_instance_2013):
    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None

    variants_file = fixture_dirname("backends/cnv_variants_alt_2.txt")

    loader = CNVLoader(
        families, variants_file, gpf_instance_2013.reference_genome,
        params={
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["duplication"],
            "cnv_minus_values": ["deletion"],
            "cnv_person_id": "personId"
        }
    )

    svs = []
    fvs = []
    for sv, _fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in _fvs:
            fvs.append(fv)

    assert len(svs) == 29
    assert len(fvs) == 30
