# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


def test_enrichment_tool(
    f1_trio: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:
    enrichment_helper = EnrichmentHelper(gpf_fixture.grr)

    results = enrichment_helper.calc_enrichment_test(
        f1_trio,
        "phenotype",
        ["SAMD11", "PLEKHN1", "POGZ"],
        effect_groups=[["missense", "synonymous"]],
        background_id="enrichment/coding_len_testing",
        counter_id="enrichment_events_counting",
    )

    result = results["phenotype1"]["missense,synonymous"]

    assert result.all.events is not None
    assert result.all.events == 2
    assert result.all.expected == 2.0
    assert result.all.pvalue == 1.0

    assert result.rec.events is not None
    assert result.rec.events == 1
    assert result.rec.expected == 1.0
    assert result.rec.pvalue == 1.0

    assert result.male.events is not None
    assert result.male.events == 1
    assert result.male.expected == 1.0
    assert result.male.pvalue == 1.0

    assert result.female.events is not None
    assert result.female.events == 1
    assert result.female.expected == 1.0
    assert result.female.pvalue == 1.0

    assert result.unspecified.events is not None
    assert result.unspecified.events == 0
    assert result.unspecified.expected == 0
    assert result.unspecified.pvalue == 1.0
