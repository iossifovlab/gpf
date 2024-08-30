# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap

import pytest

from dae.common_reports.common_report import CommonReport
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData, GenotypeDataGroup
from dae.testing import setup_dataset, setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.tools.generate_denovo_gene_sets import main


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "study_group_person_set_queries")
    return t4c8_gpf(root_path)


@pytest.fixture(scope="module")
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   1   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   2   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   3   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        study_config_update={
            "conf_dir": str(root_path / "study_1"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status",
                        },
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "autism",
                            "name": "autism",
                            "values": [
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        })


@pytest.fixture(scope="module")
def t4c8_study_2(t4c8_instance: GPFInstance) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f2.1     mom1     0     0     2   1      mom
f2.1     dad1     0     0     1   1      dad
f2.1     ch1      dad1  mom1  2   2      prb
f2.3     mom3     0     0     2   1      mom
f2.3     dad3     0     0     1   1      dad
f2.3     ch3      dad3  mom3  2   2      prb
f2.3     ch4      dad3  mom3  2   0      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3 ch4
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0 0/1
chr1   6   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1 0/0
chr1   7   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0 0/1
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        study_config_update={
            "conf_dir": str(root_path / "study_2"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status",
                        },
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "epilepsy",
                            "name": "epilepsy",
                            "values": [
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        })


@pytest.fixture()
def t4c8_dataset(
    t4c8_instance: GPFInstance,
    t4c8_study_1: GenotypeData,
    t4c8_study_2: GenotypeData,
) -> GenotypeDataGroup:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    (root_path / "dataset").mkdir(exist_ok=True)

    return setup_dataset(
        "dataset", t4c8_instance, t4c8_study_1, t4c8_study_2,
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: { root_path / "dataset "}
            person_set_collections:
                phenotype:
                  id: phenotype
                  name: Phenotype
                  sources:
                  - from: pedigree
                    source: status
                  domain:
                  - color: '#4b2626'
                    id: developmental_disorder
                    name: developmental disorder
                    values:
                    - affected
                  - color: '#ffffff'
                    id: unaffected
                    name: unaffected
                    values:
                    - unaffected
                  default:
                    color: '#aaaaaa'
                    id: unspecified
                    name: unspecified
                selected_person_set_collections:
                - phenotype"""))


def test_generate_denovo_gene_sets_script_passes(
    t4c8_instance: GPFInstance,
) -> None:
    t4c8_instance.reload()
    main(gpf_instance=t4c8_instance, argv=[])
    main(gpf_instance=t4c8_instance, argv=["--show-studies"])


def test_generate_denovo_gene_sets_study_1(
    t4c8_instance: GPFInstance,
    t4c8_study_1: GenotypeData,  # noqa: ARG001
) -> None:
    main(gpf_instance=t4c8_instance, argv=[])
    report_path = os.path.join(
        t4c8_instance.dae_dir,
        "studies",
        "study_1",
        "common_report.json",
    )
    assert os.path.exists(report_path)

    report = CommonReport.load(report_path)
    assert report is not None
    assert report.denovo_report is not None

    denovo_report = report.denovo_report.to_dict()

    assert denovo_report["tables"][0]["rows"][0]["effect_type"] == "Intergenic"
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "number_of_observed_events"
    ] == 2
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "number_of_children_with_event"
    ] == 2
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "observed_rate_per_child"
    ] == 1.0
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "column"
    ] == "autism (2)"


def test_generate_denovo_gene_sets_study_2(
    t4c8_instance: GPFInstance,
    t4c8_study_2: GenotypeData,  # noqa: ARG001
) -> None:
    main(gpf_instance=t4c8_instance, argv=[])
    report_path = os.path.join(
        t4c8_instance.dae_dir,
        "studies",
        "study_2",
        "common_report.json",
    )
    print(t4c8_instance.dae_dir)
    assert os.path.exists(report_path)

    report = CommonReport.load(report_path)
    assert report is not None
    assert report.denovo_report is not None

    denovo_report = report.denovo_report.to_dict()

    assert denovo_report["tables"][0]["rows"][0]["effect_type"] == "UTRs"
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "number_of_observed_events"
    ] == 1
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "number_of_children_with_event"
    ] == 1
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "observed_rate_per_child"
    ] == 0.5
    assert denovo_report["tables"][0]["rows"][0]["row"][0][
        "column"
    ] == "epilepsy (2)"
