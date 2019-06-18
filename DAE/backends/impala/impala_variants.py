from variants.family import FamiliesBase, Family
from backends.impala.parquet_io import ParquetSerializer


class ImpalaFamilyVariants(FamiliesBase):

    def __init__(self, config, impala_backend):

        super(ImpalaFamilyVariants, self).__init__()

        assert config is not None
        self.config = config

        self.backend = impala_backend
        self.ped_df = self.backend.load_pedigree(self.config)
        self.families_build(self.ped_df, family_class=Family)
        self.schema = self.backend.variants_schema(self.config)
        self.serializer = ParquetSerializer(self.families)

    def query_variants(self, **kwargs):

        for row in self.backend.query_variants(self.config, **kwargs):
            print(row)
            chrom, position, reference, alternatives_data, \
                effect_data, family_id, genotype_data, \
                matched_alleles = row

            print(genotype_data)
            family = self.families.get(family_id)
            v = self.serializer.deserialize_variant(
                family,
                chrom, position, reference, alternatives_data,
                effect_data, genotype_data
            )

            matched_alleles = [int(a) for a in matched_alleles.split(',')]
            v.set_matched_alleles(matched_alleles)
            yield v
