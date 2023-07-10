# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable
import pathlib
import textwrap
import pytest

from dae.testing import setup_pedigree, setup_vcf, \
    setup_dae_transmitted, setup_denovo, setup_directories

from dae.import_tools.import_tools import ImportProject
from dae.tools.simple_study_import import main
from dae.genotype_storage.genotype_storage import GenotypeStorage

from dae.testing.foobar_import import foobar_gpf


def test_del_loader_prefix() -> None:
    params = {"ped_alabala": "alabala", "portokala": "portokala"}
    res = ImportProject.del_loader_prefix(params, "ped_")
    assert res["alabala"] == "alabala"
    assert res["portokala"] == "portokala"


@pytest.fixture
def pedigree_data(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("pedigree")
    return setup_pedigree(
        root_path / "pedigree_data" / "in.ped",
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     2   1      sib
            f2       m2       0      0      2   1      mom
            f2       d2       0      0      1   1      dad
            f2       p2       d2     m2     2   2      prb
        """
    )


@pytest.fixture
def denovo_dae_data(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("denovo_dae_path")
    return setup_denovo(
        root_path / "denovo_dae_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:10    sub(A->G)  2||2||1||1/0||0||1||0
          f1        foo:11    sub(T->A)  2||2||1||2/0||0||1||0
          f1        bar:10    sub(G->A)  2||2||2||1/0||0||0||1
          f2        bar:11    sub(G->A)  2||2||1/0||0||1
          f2        bar:12    sub(G->A)  2||2||1/0||0||1
        """
    )


def test_import_denovo_dae_style_into_genotype_storage(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path, denovo_dae_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:
    root_path = tmp_path_factory.mktemp(
        genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    study_id = f"test_denovo_dae_style_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--id",
        study_id,
        # "--skip-reports",
        "--denovo-file",
        str(denovo_dae_data),
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert study.has_denovo
    assert not study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 5


def test_import_denovo_dae_style_sep(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    in_var = textwrap.dedent("""
          familyId$chrom$pos$ref$alt$bestState
          f1$foo$10$A$G$2 2 1 1/0 0 1 0
          f1$foo$11$T$A$2 2 1 2/0 0 1 0
          f1$bar$10$G$A$2 2 2 1/0 0 0 1
          f2$bar$11$G$A$2 2 1/0 0 1
          f2$bar$12$G$A$2 2 1/0 0 1
        """)

    setup_directories(root_path, {
        "denovo_separator_data": {
            "in.dsv": in_var,
        }
    })

    denovo_filename = str(root_path / "denovo_separator_data" / "in.dsv")
    study_id = f"test_denovo_dae_style_sep_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
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
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert study.has_denovo
    assert not study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 5


@pytest.fixture
def vcf_data(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("vcf_data")

    return setup_vcf(root_path / "vcf_data" / "in.vcf.gz", textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        """))


def test_import_comp_vcf_into_genotype_storage(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path, vcf_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:

    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    study_id = f"test_comp_vcf_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--id",
        study_id,
        "--skip-reports",
        "--vcf-files",
        str(vcf_data),
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert not study.has_denovo
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 2


def test_import_vcf_and_denovo_into_genotype_storage(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path,
        denovo_dae_data: pathlib.Path, vcf_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    study_id = f"test_comp_all_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--skip-reports",
        "--id", study_id,
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files", str(vcf_data),
        "--denovo-file", str(denovo_dae_data),
        "--denovo-location", "location",
        "--denovo-variant", "variant",
        "--denovo-family-id", "familyId",
        "--denovo-best-state", "bestState",
        "--genotype-storage", genotype_storage.storage_id,
        "-o", str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert study.has_denovo
    assert study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 7


def test_add_chrom_prefix_simple(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path,
        denovo_dae_data: pathlib.Path, vcf_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    study_id = f"test_comp_all_prefix_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--id",
        study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files",
        str(vcf_data),
        "--denovo-file",
        str(denovo_dae_data),
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
        "--add-chrom-prefix",
        "ala_bala",
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()

    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert study.has_denovo
    assert study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 7

    for v in vs:
        print(v)
        assert v.chromosome.startswith("ala_bala")
        for fa in v.alleles:
            print("\t", fa)
            assert fa.chromosome.startswith("ala_bala")


def test_import_del_chrom_prefix(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path, vcf_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    study_id = f"test_comp_all_del_chrom_prefix_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--id",
        study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files",
        str(vcf_data),
        "--genotype-storage",
        genotype_storage.storage_id,
        "--del-chrom-prefix",
        "fo",
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert not study.has_denovo
    assert study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 2
    for v in vs:
        assert v.chromosome == "o", v


def test_import_transmitted_dae_into_genotype_storage(
        tmp_path_factory: pytest.TempPathFactory,
        pedigree_data: pathlib.Path,
        genotype_storage: GenotypeStorage) -> None:

    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    study_id = f"test_dae_transmitted_{genotype_storage.storage_id}"

    summary_data, _toomany_data = setup_dae_transmitted(
        root_path,
        textwrap.dedent("""
chr position variant   familyData all.nParCalled all.prcntParCalled all.nAltAlls all.altFreq
foo 10       sub(T->G) TOOMANY    1400           27.03              13           0.49
bar 10       sub(T->C) TOOMANY    1460           29.54              1            0.03
bar 11       sub(A->G) TOOMANY    300            6.07               588          98.00
        """),  # noqa
        textwrap.dedent("""
chr position variant   familyData
foo 10       sub(T->G) f1:0000/2222:0||0||0||0/71||38||36||29/0||0||0||0
bar 10       sub(T->C) f1:0110/2112:0||63||67||0/99||56||57||98/0||0||0||0
bar 11       sub(A->G) f1:1121/1101:38||4||83||25/16||23||0||16/0||0||0||0;f2:211/011:13||5||5/0||13||17/0||0||0
        """)  # noqa
    )

    argv = [
        str(pedigree_data),
        "--id",
        study_id,
        "--skip-reports",
        "--dae-summary-file",
        str(summary_data),
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert not study.has_denovo
    assert study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 4


def test_import_wild_multivcf_into_genotype_storage(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage,
        pedigree_data: pathlib.Path) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    setup_vcf(
        root_path / "vcf_data" / "multivcf_f1_foo.vcf.gz",
        content=textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        """))
    setup_vcf(
        root_path / "vcf_data" / "multivcf_f1_bar.vcf.gz",
        content=textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        bar    10  .  C   A   .    .      .    GT     0/1 0/0 0/1 0/0
        bar    11  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        """))
    setup_vcf(
        root_path / "vcf_data" / "multivcf_f2_foo.vcf.gz",
        content=textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m2  d2  p2
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        foo    11  .  G   T   .    .      .    GT     0/0 0/1 0/1
        """))
    setup_vcf(
        root_path / "vcf_data" / "multivcf_f2_bar.vcf.gz",
        content=textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m2  d2  p2
        bar    11  .  C   A   .    .      .    GT     0/1 0/0 0/1
        bar    12  .  A   T   .    .      .    GT     0/0 0/1 0/1
        """))

    study_id = f"test_wile_multivcf_{genotype_storage.storage_id}"
    argv = [
        str(pedigree_data),
        "--id", study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files",
        str(root_path / "vcf_data" / "multivcf_f1_[vc].vcf.gz"),
        str(root_path / "vcf_data" / "multivcf_f2_[vc].vcf.gz"),
        "--vcf-chromosomes", "foo;bar",
        "--genotype-storage", genotype_storage.storage_id,
        "-o", str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert not study.has_denovo
    assert study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants())
    assert len(vs) == 8


def test_import_study_config_arg(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage,
        pedigree_data: pathlib.Path,
        vcf_data: pathlib.Path) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    study_config = root_path / "study_import" / "study_config.conf"
    study_config.parent.mkdir()
    with open(study_config, "wt", encoding="utf8") as outfile:
        outfile.write("""name="asdf"\n""")

    study_id = f"test_comp_vcf_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_data),
        "--id", study_id,
        "--skip-reports",
        "--vcf-denovo-mode", "possible_denovo",
        "--vcf-omission-mode", "possible_omission",
        "--vcf-files", str(vcf_data),
        "--genotype-storage", genotype_storage.storage_id,
        "--study-config", str(study_config),
        "-F",
        "-o", str(root_path / "output"),
    ]
    with pytest.raises(SystemExit):
        main(argv, gpf_instance)


@pytest.mark.xfail(reason="denovo-db import does not work on impala2")
def test_denovo_db_import(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage,
        fixture_dirname: Callable[[str], str]) -> None:
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    families_filename = fixture_dirname("backends/denovo-db-person-id.ped")
    denovo_filename = fixture_dirname("backends/denovo-db-person-id.tsv")
    study_id = f"test_denovo_db_import_{genotype_storage.storage_id}"

    argv = [
        "--study-id", study_id,
        families_filename,
        "-o", str(root_path / "output"),
        "--skip-reports",
        "--denovo-chrom", "Chr",
        "--denovo-pos", "Position",
        "--denovo-ref", "Ref",
        "--denovo-alt", "Alt",
        "--denovo-person-id", "SampleID",
        "--denovo-file", denovo_filename,
        "--genotype-storage", genotype_storage.storage_id,
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None
    assert study.has_denovo
    assert not study.has_transmitted
    assert not study.has_cnv

    vs = list(study.query_variants(inheritance="denovo"))
    assert len(vs) == 17
