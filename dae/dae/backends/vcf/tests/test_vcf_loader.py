import pytest
import os
import numpy as np

from dae.pedigrees.loader import FamiliesLoader

from dae.variants.attributes import Inheritance

from dae.backends.vcf.loader import VcfLoader


@pytest.mark.parametrize(
    "fixture_data",
    [
        "backends/effects_trio_dad",
        "backends/effects_trio",
        "backends/trios2",
        "backends/members_in_order1",
        "backends/members_in_order2",
        "backends/unknown_trio",
        "backends/trios_multi",
        "backends/quads_f1",
    ],
)
def test_vcf_loader(
    vcf_loader_data, variants_vcf, fixture_data, genomes_db_2013
):
    conf = vcf_loader_data(fixture_data)
    print(conf)

    families_loader = FamiliesLoader(conf.pedigree)
    families = families_loader.load()

    loader = VcfLoader(
        families,
        [conf.vcf],
        genomes_db_2013.get_genome(),
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
        },
    )
    assert loader is not None

    vars_new = list(loader.family_variants_iterator())

    for nfv in vars_new:
        print(nfv)


def test_simple_vcf_loader_multi(fixture_dirname, genomes_db_2013):
    vcf_filenames = [
        fixture_dirname("backends/multivcf_split1.vcf"),
        fixture_dirname("backends/multivcf_split2.vcf"),
    ]
    assert all([os.path.exists(fn) for fn in vcf_filenames])
    ped_filename = fixture_dirname("backends/multivcf.ped")
    assert os.path.exists(ped_filename)

    families = FamiliesLoader(ped_filename).load()

    vcf_loader = VcfLoader(
        families,
        vcf_filenames,
        genomes_db_2013.get_genome(),
        fill_missing_ref=False,
    )
    assert vcf_loader is not None
    vs = list(vcf_loader.full_variants_iterator())
    assert len(vs) == 6


@pytest.mark.parametrize(
    "multivcf_files",
    [
        ["multivcf_split1.vcf", "multivcf_split2.vcf"],
        ["multivcf_original.vcf"],
    ],
)
def test_vcf_loader_multi(fixture_dirname, multivcf_files, genomes_db_2013):
    ped_file = fixture_dirname("backends/multivcf.ped")

    multivcf_files = list(
        map(
            lambda x: os.path.join(fixture_dirname("backends"), x),
            multivcf_files,
        )
    )

    families = FamiliesLoader(ped_file).load()
    families_multi = FamiliesLoader(ped_file).load()

    multi_vcf_loader = VcfLoader(
        families_multi,
        multivcf_files,
        genomes_db_2013.get_genome(),
        fill_missing_ref=False,
    )
    assert multi_vcf_loader is not None

    # for sv, fvs in multi_vcf_loader.full_variants_iterator():
    #     print(sv, fvs)

    single_vcf = fixture_dirname("backends/multivcf_original.vcf")
    single_loader = VcfLoader(
        families, [single_vcf], genomes_db_2013.get_genome()
    )
    assert single_loader is not None

    single_it = single_loader.full_variants_iterator()
    multi_it = multi_vcf_loader.full_variants_iterator()
    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]
        assert len(s[1]) == 5
        assert len(m[1]) == 5

        s_gt_f1 = s[1][0].gt
        m_gt_f1 = m[1][0].gt
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1][0].gt
        m_gt_f2 = m[1][0].gt
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1][0].gt
        m_gt_f3 = m[1][0].gt
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1][0].gt
        m_gt_f4 = m[1][0].gt
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1][0].gt
        m_gt_f5 = m[1][0].gt
        assert all((s_gt_f5 == m_gt_f5).flatten())


@pytest.mark.parametrize(
    "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
)
def test_multivcf_loader_fill_missing(
    fixture_dirname, fill_mode, fill_value, genomes_db_2013
):
    ped_file = fixture_dirname("backends/multivcf.ped")

    multivcf_files = [
        fixture_dirname("backends/multivcf_missing1.vcf"),
        fixture_dirname("backends/multivcf_missing2.vcf"),
    ]
    families = FamiliesLoader(ped_file).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_multi_loader_fill_in_mode": fill_mode,
    }
    multi_vcf_loader = VcfLoader(
        families, multivcf_files, genomes_db_2013.get_genome(), params=params
    )

    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.full_variants_iterator()
    svs_fvs = [sum_fvs for sum_fvs in multi_it]
    print(svs_fvs)
    first_present = svs_fvs[0]
    second_missing = svs_fvs[1]
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1][0].genotype
    gt1_f1_expected = np.array([[1, 1], [0, 0], [0, 1], [0, 1]], dtype=np.int8)
    gt1_f5 = first_present[1][4].genotype
    gt1_f5_expected = np.array([[1, 1], [0, 0], [1, 0], [0, 1]], dtype=np.int8)
    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())
    print(second_missing[1][0], " ", second_missing[1][0].genotype)
    print(second_missing[1][1], " ", second_missing[1][1].genotype)

    gt2_f1 = second_missing[1][0].genotype
    gt2_f2 = second_missing[1][1].genotype
    gt2_f3 = second_missing[1][2].genotype
    gt2_f5 = second_missing[1][4].genotype

    gt2_f1_f2_f3_expected = np.array([[fill_value] * 2] * 4, dtype=np.int8)
    gt2_f5_expected = np.array([[0, 0], [1, 1], [1, 0], [0, 1]], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
    assert svs_fvs[0][0].ref_allele.position == 865582
    assert svs_fvs[1][0].ref_allele.position == 865583
    assert svs_fvs[2][0].ref_allele.position == 865624
    assert svs_fvs[3][0].ref_allele.position == 865627
    assert svs_fvs[4][0].ref_allele.position == 865664
    assert svs_fvs[5][0].ref_allele.position == 865691


# def test_transform_vcf_genotype():
#     genotypes = [
#         [0, 0, False],
#         [0, 1, False],
#         [1, 0, False],
#         [1, 1, False],
#         [0, True],
#         [1, True],
#     ]
#     expected = np.array([
#         [0, 0, 1, 1, 0, 1],
#         [0, 1, 0, 1, -2, -2],
#         [False, False, False, False, True, True]
#     ], dtype=GENOTYPE_TYPE)

#     assert np.array_equal(
#         expected, VcfLoader.transform_vcf_genotypes(genotypes)
#     )


@pytest.mark.parametrize(
    "denovo_mode, total, unexpected_inheritance",
    [
        ("denovo", 3, {Inheritance.possible_denovo}),
        ("possible_denovo", 3, {Inheritance.denovo}),
        ("ignore", 1, {Inheritance.possible_denovo, Inheritance.denovo}),
        ("ala_bala", 3, {Inheritance.denovo}),
    ],
)
def test_vcf_denovo_mode(
    denovo_mode,
    total,
    unexpected_inheritance,
    fixture_dirname,
    genomes_db_2013,
):
    prefix = fixture_dirname("backends/inheritance_trio_denovo_omission")
    families = FamiliesLoader(f"{prefix}.ped").load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": denovo_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{prefix}.vcf"],
        genomes_db_2013.get_genome(),
        params=params,
    )

    assert vcf_loader is not None
    vs = list(vcf_loader.family_variants_iterator())
    assert len(vs) == total
    for fv in vs:
        for fa in fv.alleles:
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members
            ) & unexpected_inheritance == set([])


@pytest.mark.parametrize(
    "omission_mode, total, unexpected_inheritance",
    [
        ("omission", 3, {Inheritance.possible_omission}),
        ("possible_omission", 3, {Inheritance.omission}),
        ("ignore", 2, {Inheritance.possible_omission, Inheritance.omission}),
        ("ala_bala", 3, {Inheritance.omission}),
    ],
)
def test_vcf_omission_mode(
    omission_mode,
    total,
    unexpected_inheritance,
    fixture_dirname,
    genomes_db_2013,
):
    prefix = fixture_dirname("backends/inheritance_trio_denovo_omission")
    families = FamiliesLoader(f"{prefix}.ped").load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_omission_mode": omission_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{prefix}.vcf"],
        genomes_db_2013.get_genome(),
        params=params,
    )

    assert vcf_loader is not None
    vs = list(vcf_loader.family_variants_iterator())
    assert len(vs) == total
    for fv in vs:
        for fa in fv.alleles:
            print(20 * "-")
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members
            ) & unexpected_inheritance == set([])


@pytest.mark.parametrize(
    "vcf_include_reference_genotypes,"
    "vcf_include_unknown_family_genotypes,"
    "vcf_include_unknown_person_genotypes,count",
    [
        (True, True, True, 7),
        (True, True, False, 4),
        (True, False, True, 6),
        (False, True, True, 7),
        (True, False, False, 4),
        (False, False, False, 4),
    ],
)
def test_vcf_loader_params(
    vcf_variants_loaders,
    vcf_include_reference_genotypes,
    vcf_include_unknown_family_genotypes,
    vcf_include_unknown_person_genotypes,
    count,
):
    params = {
        "vcf_include_reference_genotypes":
        vcf_include_reference_genotypes,
        "vcf_include_unknown_family_genotypes":
        vcf_include_unknown_family_genotypes,
        "vcf_include_unknown_person_genotypes":
        vcf_include_unknown_person_genotypes,
    }

    variants_loader = vcf_variants_loaders(
        "backends/f1_test", params=params)[0]
    vs = list(variants_loader.family_variants_iterator())
    assert len(vs) == count


# @pytest.mark.parametrize(
#     "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
# )
# def test_multivcf_loader_handle_all_unknown(
#     fixture_dirname, fill_mode, fill_value, genomes_db_2013
# ):
#     ped_file = fixture_dirname("backends/multivcf.ped")

#     multivcf_files = [
#         fixture_dirname("backends/multivcf_unknown1.vcf"),
#         fixture_dirname("backends/multivcf_unknown2.vcf"),
#     ]
#     families = FamiliesLoader(ped_file).load()
#     params = {
#         "vcf_include_reference_genotypes": True,
#         "vcf_include_unknown_family_genotypes": True,
#         "vcf_include_unknown_person_genotypes": True,
#         "vcf_multi_loader_fill_in_mode": fill_mode,
#     }
#     multi_vcf_loader = VcfLoader(
#         families, multivcf_files, genomes_db_2013.get_genome(), params=params
#     )

#     assert multi_vcf_loader is not None
#     vs = list(multi_vcf_loader.family_variants_iterator())
#     assert len(vs) == 30


def test_collect_filenames_local(fixture_dirname):
    vcf_filenames = [fixture_dirname("backends/multivcf_split[vc].vcf")]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == fixture_dirname("backends/multivcf_split1.vcf")
    assert all_filenames[1] == fixture_dirname("backends/multivcf_split2.vcf")


def test_collect_filenames_s3(fixture_dirname, s3, mocker):
    s3.put(fixture_dirname("backends/multivcf_split1.vcf"),
           "s3://test-bucket/dir/multivcf_split1.vcf")
    s3.put(fixture_dirname("backends/multivcf_split2.vcf"),
           "s3://test-bucket/dir/multivcf_split2.vcf")

    mocker.patch("dae.backends.vcf.loader.url_to_fs", return_value=(s3, None))

    vcf_filenames = ["s3://test-bucket/dir/multivcf_split[vc].vcf"]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == "s3://test-bucket/dir/multivcf_split1.vcf"
    assert all_filenames[1] == "s3://test-bucket/dir/multivcf_split2.vcf"


# Code copy/pasted from
# https://github.com/fsspec/s3fs/blob/main/s3fs/tests/test_s3fs.py#L67
port = 5555
endpoint_uri = "http://127.0.0.1:%s/" % port


@pytest.fixture()
def s3_base():
    import time
    import requests

    # writable local S3 system
    import shlex
    import subprocess

    try:
        # should fail since we didn't start server yet
        r = requests.get(endpoint_uri)
    except:  # NOQA
        pass
    else:
        if r.ok:
            raise RuntimeError("moto server already up")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    proc = subprocess.Popen(shlex.split("moto_server s3 -p %s" % port))

    timeout = 5
    while timeout > 0:
        try:
            r = requests.get(endpoint_uri)
            if r.ok:
                break
        except:  # NOQA
            pass
        timeout -= 0.1
        time.sleep(0.1)
    yield
    proc.terminate()
    proc.wait()


def get_boto3_client():
    from botocore.session import Session

    # NB: we use the sync botocore client for setup
    session = Session()
    return session.create_client("s3", endpoint_url=endpoint_uri)


@pytest.fixture()
def s3(s3_base):
    from s3fs.core import S3FileSystem

    client = get_boto3_client()
    client.create_bucket(Bucket='test-bucket', ACL="public-read")

    S3FileSystem.clear_instance_cache()
    s3 = S3FileSystem(anon=False, client_kwargs={"endpoint_url": endpoint_uri})
    s3.invalidate_cache()
    yield s3
