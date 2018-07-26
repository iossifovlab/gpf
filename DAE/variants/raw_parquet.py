from functools import reduce

from variants.configure import Configure
from variants.family import FamiliesBase, Family
from variants.raw_df import DfFamilyVariantsBase
from variants.parquet_io import read_summary_from_parquet, \
    read_family_variants_df_from_parquet, read_family_allele_df_from_parquet, \
    read_ped_df_from_parquet

class DfFilter(object):

    def __init__(self):
        self.all_predicates = []

    def and_all(self, *predicates):
        self.all_predicates.extend(predicates)

    def and_any(self, *predicates):
        self.and_all(reduce(lambda a, b: lambda x: a(x) | b(x), predicates))

    def to_single(self):
        if len(self.all_predicates) == 0:
            return None
        return reduce(lambda a, b: lambda x: a(x) & b(x), self.all_predicates)

class ParquetFamilyVariants(DfFamilyVariantsBase, FamiliesBase):

    def __init__(self, config=None, prefix=None):
        super(ParquetFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix_parquet(prefix)

        assert isinstance(config, Configure)

        self.config = config.parquet
        assert self.config is not None

        pedigree_df, summary_variants_df, family_variants_df, \
            family_alleles_df = self._load()

        self.families_build(pedigree_df, Family)
        self.summary_variants_df = summary_variants_df
        self.family_variants_df = family_variants_df
        self.family_alleles_df = family_alleles_df

        self.variants_df = (self.family_variants_df
            .merge(
                self.summary_variants_df,
                how='outer',
                suffixes=('', ''),
                sort=True)
            .merge(
                self.family_alleles_df,
                how='outer',
                suffixes=('', ''),
                sort=True))

    def _load(self):
        return (read_ped_df_from_parquet(self.config.pedigree),
            read_summary_from_parquet(self.config.summary_variants),
            read_family_variants_df_from_parquet(self.config.family_variants),
            read_family_allele_df_from_parquet(self.config.family_alleles))

    def query_variants(self, **kwargs):
        print(self.variants_df.columns)
        filters = self._filters(**kwargs)
        if filters is not None:
            result_df = self.variants_df.loc[filters, :]
        else:
            result_df = self.variants_df

        return self.wrap_variants(self.families, result_df)

    @staticmethod
    def _filters(**kwargs):
        df_filter = DfFilter()

        if 'regions' in kwargs and kwargs['regions'] is not None:
            df_filter.and_any(*[(lambda x: (x.chrom == region.chr) & \
                                   (x.position >= region.start) & (x.position <= region.stop))
                               for region in kwargs['regions']])

        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            df_filter.and_any(*[lambda x: x.family_id == family_id
                               for family_id in kwargs['family_ids']])

        return df_filter.to_single()
