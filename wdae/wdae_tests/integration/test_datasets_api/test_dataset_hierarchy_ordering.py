# pylint: disable=W0621,C0114,C0116,W0212,W0613
import time
import pathlib
import textwrap
from typing import Callable, ContextManager

import requests

from gpf_instance.gpf_instance import WGPFInstance
from wdae_tests.integration.testing import setup_wgpf_instance, LiveServer

from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository

from dae.studies.study import GenotypeData

from dae.testing import setup_pedigree, setup_vcf, setup_dataset, vcf_study, \
    setup_directories
from dae.testing.t4c8_import import t4c8_genome, t4c8_genes


def create_wgpf_fixture(
    root_path: pathlib.Path,
    visible_datasets: list[str]
) -> WGPFInstance:

    setup_directories(
        root_path / "gpf_instance", {
            "gpf_instance.yaml": textwrap.dedent(f"""
                gpfjs:
                  visible_datasets: { visible_datasets}
            """)
        }
    )
    t4c8_genome(root_path / "grr")
    t4c8_genes(root_path / "grr")

    grr = build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(root_path / "grr")
    })

    gpf_instance = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=grr)
    return gpf_instance


def create_study_1(root_path: pathlib.Path, gpf: WGPFInstance) -> GenotypeData:
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
        """)  # noqa

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            }
        },
    }
    study = vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        gpf,
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
                            "source": "status"
                        }
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
                                "affected"
                            ]
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected"
                            ]
                        },
                    ]
                },
                "selected_person_set_collections": [
                    "phenotype"
                ]
            }
        })
    return study


def create_study_2(root_path: pathlib.Path, gpf: WGPFInstance) -> GenotypeData:
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
        """)  # noqa

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            }
        },
    }
    study = vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        gpf,
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
                            "source": "status"
                        }
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
                                "affected"
                            ]
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected"
                            ]
                        },
                    ]
                },
                "selected_person_set_collections": [
                    "phenotype"
                ]
            }
        })
    return study


def create_dataset(
    root_path: pathlib.Path, gpf: WGPFInstance
) -> GenotypeData:
    (root_path / "dataset").mkdir(exist_ok=True)

    study_1 = create_study_1(root_path, gpf)
    study_2 = create_study_2(root_path, gpf)

    return setup_dataset(
        "dataset", gpf, study_1, study_2,
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


# @pytest.mark.skip
def test_datasets_order(
    tmp_path: pathlib.Path,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]]
) -> None:
    wgpf = create_wgpf_fixture(tmp_path, ["dataset", "study_1", "study_2"])
    assert wgpf is not None

    dataset = create_dataset(tmp_path, wgpf)
    assert dataset is not None

    with wdae_django_server(
            wgpf,
            "wdae_tests.integration.test_wgpf_instance."
            "wgpf_settings") as server:

        assert server.url.startswith("http://localhost")
        time.sleep(0.5)

        response = requests.get(
            f"{server.url}/api/v3/datasets", timeout=2.5)

        assert response.status_code == 200
        assert "data" in response.json()
        data = response.json()["data"]

        assert data is not None
        assert len(data) == 3

        dataset_ids = [st["id"] for st in data]
        assert dataset_ids == ["dataset", "study_1", "study_2"]
