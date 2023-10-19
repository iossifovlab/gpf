# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from dae.common_reports.common_report import CommonReport
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.tools.generate_denovo_gene_sets import main


# pytestmark = pytest.mark.usefixtures("gene_info_cache_dir")


def test_generate_denovo_gene_sets_script_passes(
    gpf_instance_2013: GPFInstance
) -> None:
    gpf_instance_2013.reload()
    main(gpf_instance=gpf_instance_2013, argv=[])
    main(gpf_instance=gpf_instance_2013, argv=["--show-studies"])


def test_generate_denovo_gene_sets_study_1(
    t4c8_instance: GPFInstance,
    t4c8_study_1: GenotypeData
) -> None:
    main(gpf_instance=t4c8_instance, argv=[])
    report_path = os.path.join(
        t4c8_instance.dae_dir,
        "studies",
        "study_1",
        "common_report.json"
    )
    print(t4c8_instance.dae_dir)
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
    t4c8_study_2: GenotypeData
) -> None:
    main(gpf_instance=t4c8_instance, argv=[])
    report_path = os.path.join(
        t4c8_instance.dae_dir,
        "studies",
        "study_2",
        "common_report.json"
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
