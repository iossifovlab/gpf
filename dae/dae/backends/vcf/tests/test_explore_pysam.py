import pytest
import pysam


@pytest.mark.parametrize(
    "fixture_data",
    [
        # "backends/effects_trio_dad",
        # "backends/effects_trio",
        # "backends/trios2",
        # "backends/members_in_order1",
        # "backends/members_in_order2",
        # "backends/trios_multi",
        # "backends/quads_f1",
        "backends/explore_pysam",
    ],
)
def test_vcf_loader(
        vcf_loader_data, fixture_data):

    conf = vcf_loader_data(fixture_data)
    print(conf)

    with pysam.VariantFile(conf.vcf) as vcfinput:
        print(vcfinput, dir(vcfinput))
        print(dir(vcfinput.header))
        print(dir(vcfinput.header.samples))
        print(list(vcfinput.header.samples))

        for rec in vcfinput.fetch():
            print(dir(rec))
            print(rec)
            print(rec.chrom, rec.pos, rec.ref, rec.alts)

            print(dir(rec.samples))
            print(list(rec.samples.keys()))
            # print(rec.alleles)
        #     for key, value in rec.samples.items():
        #         print(key, value)
        #         print(dir(value))
        #         print(list(value.keys()))
        #         print(value['GT'], value.allele_indices, value.phased)
        #         print(value.alleles)
