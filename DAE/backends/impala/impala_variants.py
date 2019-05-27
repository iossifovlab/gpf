from variants.family import FamiliesBase, Family
from backends.impala.serializers import FamilyVariantSerializer


class ImpalaFamilyVariants(FamiliesBase):

    def __init__(self, config, impala_backend):

        super(ImpalaFamilyVariants, self).__init__()

        self.config = config
        assert self.config is not None
        self.backend = impala_backend
        self.ped_df = self.backend.load_pedigree(self.config)
        self.families_build(self.ped_df, family_class=Family)
        self.schema = self.backend.variants_schema(self.config)
        self.serializer = FamilyVariantSerializer(self.families)

    def query_variants(self, **kwargs):
        for row in self.backend.query_variants(self.config, **kwargs):
            v = self.serializer.deserialize(row[0])
            matched_alleles = [int(a) for a in row[1].split(',')]
            v.set_matched_alleles(matched_alleles)

            yield v
