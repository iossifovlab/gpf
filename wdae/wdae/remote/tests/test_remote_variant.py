# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
import pytest
from remote.remote_variant import RemoteFamilyVariant, RemoteFamilyAllele
from dae.pedigrees.family import Family, Person


@pytest.fixture()
def sample_family():
    members = [
        Person(
            person_id="id1",
            family_id="fam1",
            mom_id="mom1",
            dad_id="dad1",
            sex="2",
            status="2",
            role="prb",
            layout="error",
            generated=False,
        ),
        Person(
            person_id="mom1",
            family_id="fam1",
            mom_id="0",
            dad_id="0",
            sex="2",
            status="1",
            role="mom",
            layout="error",
            generated=False,
        ),
        Person(
            person_id="dad1",
            family_id="fam1",
            mom_id="0",
            dad_id="0",
            sex="1",
            status="1",
            role="dad",
            layout="error",
            generated=False,
        ),
        Person(
            person_id="id2",
            family_id="fam1",
            mom_id="mom1",
            dad_id="dad1",
            sex="1",
            status="0",
            role="sib",
            layout="error",
            generated=False,
        )
    ]
    return Family.from_persons(members)


@pytest.fixture()
def sample_attributes_columns():
    attributes = [
        ["5:140391002"],
        ["5"],
        ["140391002"],
        ["-"],
        ["G"],
        ["A"],
        ["-"],
        ["1"],
        ["TransmissionTiie.denovo"],
        [
            "3'UTR!PCDHAC1:3'UTR|PCDHAC2:3'UTR|PCDHA1:3'UTR|PCDHA10:3'UTR|PCD"
            "HA11:3'UTR|PCDHA12:3'UTR|PCDHA13:3'UTR|PCDHA2:3'UTR|PCDHA3:3'UTR"
            "|PCDHA4:3'UTR|PCDHA5:3'UTR|PCDHA6:3'UTR|PCDHA7:3'UTR|PCDHA8:3'UT"
            "R|PCDHA6:3'UTR|PCDHA9:3'UTR!NM_018898:PCDHAC1:3'UTR:1480|NM_0188"
            "99:PCDHAC2:3'UTR:1480|NM_018900:PCDHA1:3'UTR:1480|NM_031411:PCDH"
            "A1:3'UTR:1480|NM_018901:PCDHA10:3'UTR:1480|NM_031860:PCDHA10:3'U"
            "TR:1480|NM_018902:PCDHA11:3'UTR:1480|NM_018903:PCDHA12:3'UTR:148"
            "0|NM_018904:PCDHA13:3'UTR:1480|NM_018905:PCDHA2:3'UTR:1480|NM_01"
            "8906:PCDHA3:3'UTR:1480|NM_018907:PCDHA4:3'UTR:1480|NM_018908:PCD"
            "HA5:3'UTR:1480|NM_018909:PCDHA6:3'UTR:1480|NM_018910:PCDHA7:3'UT"
            "R:1480|NM_018911:PCDHA8:3'UTR:1480|NM_031849:PCDHA6:3'UTR:1480|N"
            "M_031857:PCDHA9:3'UTR:1480"
        ],
        ["-"],
        ["-"],
        ["-"],
        ["-"],
        ["12628"],
        ["0/0;0/0;1/0;0/0"],
        ["2212/0010"],
        ["-"]
    ]
    columns = [
        "location",
        "chrom",
        "position",
        "end_position",
        "reference",
        "alternative",
        "summary_index",
        "allele_index",
        "transmission_type",
        "raw_effects",
        "effect_types",
        "effect_genes",
        "effect_gene_symbols",
        "frequency",
        "family",
        "genotype",
        "best_st",
        "genetic_model"]

    return (attributes, columns)


def test_remote_variant_alleles(sample_attributes_columns, sample_family):
    attributes, columns = sample_attributes_columns
    variant = RemoteFamilyVariant(attributes, sample_family, columns)

    assert isinstance(variant.family_genotype, np.ndarray)
    assert (variant.family_genotype == [[0, 0], [0, 0], [1, 0], [0, 0]]).all()

    assert isinstance(variant.best_state, np.ndarray)
    assert (variant.best_state == [[2, 2, 1, 2], [0, 0, 1, 0]]).all()

    print(variant.alt_alleles[0])
    print(type(variant.alt_alleles[0]))
    allele = variant.alt_alleles[0]
    assert isinstance(allele, RemoteFamilyAllele)
    assert isinstance(allele.genotype, np.ndarray)
    assert (allele.genotype == [[0, 0], [0, 0], [1, 0], [0, 0]]).all()
    assert isinstance(allele.best_state, np.ndarray)
    assert (allele.best_state == [[2, 2, 1, 2], [0, 0, 1, 0]]).all()
