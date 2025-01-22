# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from collections.abc import Callable
from typing import Any

import pytest

from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
)
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import vcf_study
from dae.testing.alla_import import alla_gpf


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_genomic_scores")
    genotype_storage = genotype_storage_factory(root_path)

    setup_directories(
        root_path / "alla_gpf", {
            "allele_score": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: allele_score
                    allele_score_mode: alleles
                    table:
                      filename: data.txt
                      reference:
                        name: reference
                      alternative:
                        name: alternative
                    scores:
                    - id: cat
                      type: str
                      desc: "variant ID"
                      name: cat
                    - id: icat
                      type: int
                      desc: "integer category"
                      name: icat
                    - id: freq
                      type: float
                      desc: ""
                      name: freq
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  reference  alternative cat    icat freq
                    chr1   1          A          C           ac1_1  1    0.1
                    chr1   2          A          C           ac1_2  2    0.2
                    chr1   3          A          C           ac1_3  3    0.3
                    chr1   4          A          C           ac1_4  4    0.4
                    chr2   1          A          C           ac2_1  1    1.0
                    chr2   2          A          C           ac2_2  2    2.0
                    chr2   3          A          C           ac2_3  3    3.0
                    chr2   4          A          C           ac2_4  4    4.0
                """),
            },
        })

    setup_directories(
        root_path / "gpf_instance", {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: "test_instance"
                annotation:
                  conf_file: 'annotation.yaml'
            """),
            "annotation.yaml": textwrap.dedent("""
                - allele_score:
                    resource_id: allele_score
            """),
        },
    )

    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
##contig=<ID=bar>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
chr1   1   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr1   2   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr1   3   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr1   4   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr1   5   .  A   C     .    .      .    GT     1/1  1/1  0/1
chr1   6   .  A   C     .    .      .    GT     1/1  1/1  0/1
chr2   1   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr2   2   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr2   3   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr2   4   .  A   C     .    .      .    GT     0/0  0/1  0/1
chr2   5   .  A   C     .    .      .    GT     1/1  1/1  0/1
chr2   6   .  A   C     .    .      .    GT     1/1  1/1  0/1
        """)

    return vcf_study(
        root_path,
        "test_query_by_genomic_scores", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance)


@pytest.mark.no_gs_inmemory
@pytest.mark.no_gs_impala
@pytest.mark.parametrize(
    "query, count",
    [
        (None, 12),
        ({
            "real_attr_filter": [
                ("freq", (0.1, 0.1)),
            ],
         }, 1),
        ({
            "real_attr_filter": [
                ("freq", (0.4, 0.4)),
            ],
         }, 1),
        ({
            "real_attr_filter": [
                ("freq", (0.4, 1.0)),
            ],
         }, 2),
        ({
            "categorical_attr_filter": [
                ("cat", ["ac1_4"]),
            ],
         }, 1),
        ({
            "categorical_attr_filter": [
                ("cat", ["ac2_1"]),
            ],
         }, 1),
        ({
            "categorical_attr_filter": [
                ("cat", ["ac1_4", "ac2_1"]),
            ],
         }, 2),
        ({
            "categorical_attr_filter": [
                ("cat", None),
            ],
         }, 4),
        ({
            "categorical_attr_filter": [
                ("cat", []),
            ],
         }, 8),
        ({
            "categorical_attr_filter": [
                ("icat", [4]),
            ],
         }, 2),
        ({
            "categorical_attr_filter": [
                ("icat", [3]),
            ],
         }, 2),
        ({
            "categorical_attr_filter": [
                ("icat", [3, 4]),
            ],
         }, 4),
    ],
)
def test_query_by_genomic_scores(
    imported_study: GenotypeData,
    query: dict[str, Any] | None, count: int,
) -> None:
    if query is None:
        vs = list(imported_study.query_variants())
    else:
        vs = list(imported_study.query_variants(**query))
    assert len(vs) == count
