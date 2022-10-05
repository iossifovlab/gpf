# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
import pytest

from dae.utils.variant_utils import mat2str
from dae.genomic_resources.testing import convert_to_tab_separated

from dae.variants.core import Allele
from dae.variants_loaders.cnv.flexible_cnv_loader import flexible_cnv_loader


@pytest.fixture
def genome(gpf_instance_2013):
    return gpf_instance_2013.reference_genome


@pytest.mark.parametrize(
    # params: (cnv_family_id, cnv_location, cnv_variant_type, cnv_best_state)
    "content,params", [
        (
            """
            family_id  location               variant  best_state
            f1         1:1590681-1628197      CNV+     2||2||2||3
            """, (None, None, None, None)
        ),
        (
            """
            family_id  location               variant  best_state
            f1         1:1590681-1628197      CNV+     2||2||2||3
            """, ("family_id", "location", "variant", "best_state")
        ),
        (
            """
            familyId   Location               Variant  bestState
            f1         1:1590681-1628197      CNV+     2||2||2||3
            """, ("familyId", "Location", "Variant", "bestState")
        ),
    ]
)
def test_legacy_dae_cnv_variants(families, genome, content, params):
    data = io.StringIO(convert_to_tab_separated(textwrap.dedent(content)))
    cnv_family_id, cnv_locatioin, cnv_variant_type, cnv_best_state = params

    loader = flexible_cnv_loader(
        data, families, genome, regions=[],
        cnv_location=cnv_locatioin,
        cnv_family_id=cnv_family_id,
        cnv_best_state=cnv_best_state,
        cnv_variant_type=cnv_variant_type,
    )

    result = list(loader)
    assert len(result) == 1
    rec = result[0]
    assert rec["chrom"] == "1"
    assert rec["pos"] == 1590681
    assert rec["pos_end"] == 1628197
    assert rec["variant_type"] == Allele.Type.large_duplication
    assert mat2str(rec["best_state"]) == "2221/0001"


@pytest.mark.parametrize(
    # params: (cnv_person_id, cnv_chrom, cnv_start, cnv_end, cnv_variant_type)
    "content,params", [
        (
            """
            person_id  chrom  pos      pos_end  variant
            f1.s2      1      1590681  1628197  CNV+
            """, ("person_id", "chrom", None, None, None)
        ),
        (
            """
            person_id  chrom  pos      pos_end  variant
            f1.s2      1      1590681  1628197  CNV+
            """, ("person_id", "chrom", "pos", "pos_end", "variant")
        ),
        (
            """
            personId   Chrom  Start    End      Variant
            f1.s2      1      1590681  1628197  CNV+
            """, ("personId", "Chrom", "Start", "End", "Variant")
        ),
    ]
)
def test_vcf_like_cnv_variants(families, genome, content, params):
    data = io.StringIO(convert_to_tab_separated(textwrap.dedent(content)))
    (cnv_person_id, cnv_chrom, cnv_start, cnv_end, cnv_variant_type) = params

    loader = flexible_cnv_loader(
        data, families, genome, regions=[],
        cnv_person_id=cnv_person_id,
        cnv_chrom=cnv_chrom,
        cnv_start=cnv_start,
        cnv_end=cnv_end,
        cnv_variant_type=cnv_variant_type,
    )

    result = list(loader)
    assert len(result) == 1
    rec = result[0]
    assert rec["chrom"] == "1"
    assert rec["pos"] == 1590681
    assert rec["pos_end"] == 1628197
    assert rec["variant_type"] == Allele.Type.large_duplication
    assert mat2str(rec["best_state"]) == "2221/0001"


@pytest.mark.parametrize(
    "header,params", [
        # # mix family_id/best_state with person_id
        # (
        #     "family_id  person_id  location  variant  best_state",
        #     {
        #         "cnv_family_id": "family_id",
        #         "cnv_person_id": "person_id"
        #     }
        # ),

        # # mix family_id/best_state with person_id
        # (
        #     "family_id  person_id  location  variant  best_state",
        #     {
        #         "cnv_best_state": "best_state",
        #         "cnv_person_id": "person_id"
        #     }
        # ),

        # mix location with vcf-like position
        (
            "person_id  location chrom pos pos_end variant  best_state",
            {
                "cnv_person_id": "person_id",
                "cnv_chrom": "chrom",
                "cnv_location": "location",
            }
        ),
        # mix location with vcf-like position
        (
            "person_id  location chrom pos pos_end variant  best_state",
            {
                "cnv_person_id": "person_id",
                "cnv_start": "pos",
                "cnv_location": "location",
            }
        ),
        # mix location with vcf-like position
        (
            "person_id  location chrom pos pos_end variant  best_state",
            {
                "cnv_person_id": "person_id",
                "cnv_end": "pos_end",
                "cnv_location": "location",
            }
        ),
        # missing cnv_variant_type column
        (
            "family_id  location  best_state",
            {}
        ),
        # missing cnv_variant_type column
        (
            "family_id  location  Variant  best_state",
            {}
        ),
        # missing cnv_best_state column
        (
            "family_id  location  variant",
            {}
        ),
        # missing cnv_best_state column
        (
            "family_id  location  variant  bestState",
            {}
        ),
        # missing cnv_location column
        (
            "family_id  Location  variant  best_state",
            {}
        ),
        # missing cnv_location column
        (
            "family_id  variant  best_state",
            {}
        ),
        # missing cnv_family_id column
        (
            "familyId  location  variant  best_state",
            {}
        ),
        # missing cnv_family_id column
        (
            "location  variant  best_state",
            {}
        ),
        # missing chv_chrom column
        (
            "family_id  chrom  pos  pos_end  variant  best_state",
            {
                "cnv_chrom": "Chrom",
            }
        ),
        # missing cnv_start column
        (
            "family_id  chrom  pos  pos_end  variant  best_state",
            {
                "cnv_start": "Start",
            }
        ),
        # missing cnv_end column
        (
            "family_id  chrom  pos  pos_end  variant  best_state",
            {
                "cnv_end": "End",
            }
        ),

    ]
)
def test_flexible_cnv_variants_bad_configs(header, params, families, genome):
    content = io.StringIO(convert_to_tab_separated(header))
    with pytest.raises(ValueError):
        next(
            flexible_cnv_loader(
                content,
                families,
                genome,
                regions=[],
                **params)
        )
