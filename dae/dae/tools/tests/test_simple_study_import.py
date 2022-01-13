import pytest

from dae.tools.simple_study_import import main


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [("test_impala", "impala"), ("test_filesystem", "filesystem")],
)
def test_import_denovo_dae_style_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname("denovo_import/fake_pheno.ped")
    denovo_filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")

    study_id = f"test_denovo_dae_style_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        # "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 5


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_denovo_dae_style_denovo_sep(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    storage_config = default_dae_config.storage.test_impala
    assert storage_config.storage_type == "impala"
    pedigree_filename = fixture_dirname("denovo_import/fake_pheno.ped")
    denovo_filename = fixture_dirname(
        "denovo_import/variants_different_separator.dsv"
    )

    study_id = f"test_denovo_dae_style_denovo_sep_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-pos",
        "pos",
        "--denovo-chrom",
        "chrom",
        "--denovo-ref",
        "ref",
        "--denovo-alt",
        "alt",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--denovo-sep",
        "$",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 5


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_comp_vcf_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname("study_import/comp.ped")
    vcf_filename = fixture_dirname("study_import/comp.vcf")

    study_id = f"test_comp_vcf_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--vcf-files",
        vcf_filename,
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 30


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        # ("test_filesystem", "filesystem"),
    ],
)
def test_import_comp_denovo_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname("study_import/comp.ped")
    denovo_filename = fixture_dirname("study_import/comp.tsv")

    study_id = f"test_comp_denovo_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 5


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        # ("test_filesystem", "filesystem"),
    ],
)
def test_import_comp_all_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname("study_import/comp.ped")
    vcf_filename = fixture_dirname("study_import/comp.vcf")
    denovo_filename = fixture_dirname("study_import/comp.tsv")

    study_id = f"test_comp_all_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--skip-reports",
        "--id", study_id,
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files", vcf_filename,
        "--denovo-file", denovo_filename,
        "--denovo-location", "location",
        "--denovo-variant", "variant",
        "--denovo-family-id", "familyId",
        "--denovo-best-state", "bestState",
        "--genotype-storage", genotype_storage_id,
        "-o", temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 30


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_iossifov2014_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname(
        "dae_iossifov2014/iossifov2014_families.ped"
    )
    denovo_filename = fixture_dirname("dae_iossifov2014/iossifov2014.txt")

    study_id = f"test_denovo_iossifov2014_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16

    vs = list(study.query_variants(effect_types=["splice-site"]))
    assert len(vs) == 9

    vs = list(study.query_variants(effect_types=["no-frame-shift"]))
    assert len(vs) == 2


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_add_chrom_prefix_simple(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):
    pedigree_filename = fixture_dirname("study_import/comp.ped")
    vcf_filename = fixture_dirname("study_import/comp.vcf")
    denovo_filename = fixture_dirname("study_import/comp.tsv")

    study_id = f"test_comp_all_prefix_{genotype_storage_id}"
    genotype_storage_id = "test_filesystem"

    storage_config = default_dae_config.storage.test_filesystem
    assert storage_config.storage_type == "filesystem"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files",
        vcf_filename,
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
        "--add-chrom-prefix",
        "ala_bala",
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()

    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 30

    for v in vs:
        print(v)
        assert v.chromosome.startswith("ala_bala")
        for va in v.alleles:
            print("\t", va)
            assert va.chromosome.startswith("ala_bala")


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_comp_all_del_chrom_prefix(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    pedigree_filename = fixture_dirname("study_import/comp_chromprefix.ped")
    vcf_filename = fixture_dirname("study_import/comp_chromprefix.vcf")
    denovo_filename = fixture_dirname("study_import/comp_chromprefix.tsv")

    storage_config = default_dae_config.storage.test_filesystem
    assert storage_config.storage_type == "filesystem"
    study_id = f"test_comp_all_del_chrom_prefix_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        '--skip-reports',
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files",
        vcf_filename,
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "--del-chrom-prefix",
        "chr",
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 30
    for v in vs:
        assert v.chromosome == "1", v


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_transmitted_dae_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    families_filename = fixture_dirname(
        "dae_transmitted/transmission.families.txt"
    )
    summary_filename = fixture_dirname("dae_transmitted/transmission.txt.gz")
    study_id = f"test_dae_transmitted_{genotype_storage_id}"

    argv = [
        families_filename,
        "--ped-file-format",
        "simple",
        "--id",
        study_id,
        "--skip-reports",
        "--dae-summary-file",
        summary_filename,
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 33


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_import_wild_multivcf_into_genotype_storage(
    genotype_storage_id,
    storage_type,
    fixture_dirname,
    default_dae_config,
    gpf_instance_2013,
    temp_dirname,
):

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_missing1_[vc].vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_missing2_[vc].vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    study_id = f"test_wile_multivcf_{genotype_storage_id}"

    argv = [
        ped_file,
        "--id", study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files", vcf_file1, vcf_file2,
        "--vcf-chromosomes", "chr1;chr2",
        "--genotype-storage", genotype_storage_id,
        "-o", temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 48


def test_import_study_config_arg(
    fixture_dirname,
    gpf_instance_2013,
    temp_dirname,
):

    genotype_storage_id = "test_filesystem"
    pedigree_filename = fixture_dirname("study_import/comp.ped")
    vcf_filename = fixture_dirname("study_import/comp.vcf")
    study_config = fixture_dirname("study_import/study_config.conf")

    study_id = f"test_comp_vcf_{genotype_storage_id}"

    argv = [
        pedigree_filename,
        "--id", study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files", vcf_filename,
        "--genotype-storage", genotype_storage_id,
        "--study-config", study_config,
        "-F",
        "-o", temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None
    config = gpf_instance_2013.get_genotype_data_config(study_id)
    assert config.name == "asdf"
    assert config.description == "Description from study config given to tool"

    vs = list(study.query_variants())
    assert len(vs) == 30


@pytest.mark.parametrize(
    "genotype_storage_id,storage_type",
    [
        ("test_impala", "impala"),
        ("test_filesystem", "filesystem"),
    ],
)
def test_denovo_db_import(
        fixture_dirname, temp_dirname,
        genotype_storage_id, storage_type,
        gpf_instance_2013,
        ):

    families_filename = fixture_dirname("backends/denovo-db-person-id.ped")
    denovo_filename = fixture_dirname("backends/denovo-db-person-id.tsv")
    study_id = f"test_denovo_db_import_{genotype_storage_id}"

    argv = [
        "--study-id", study_id,
        families_filename,
        "-o", temp_dirname,
        "--skip-reports",
        "--denovo-chrom", "Chr",
        "--denovo-pos", "Position",
        "--denovo-ref", "Ref",
        "--denovo-alt", "Alt",
        "--denovo-person-id", "SampleID",
        "--denovo-file", denovo_filename,
        "--genotype-storage", genotype_storage_id,
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()
    study = gpf_instance_2013.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants(inheritance="denovo"))
    assert len(vs) == 17
