import itertools


class Dataset(object):

    def __init__(self, name, variants):
        self.name = name
        self._variants = variants

    def get_variants(self, **kwargs):
        return self._variants.query_variants(**kwargs)


class DatasetWrapper(Dataset):

    def __init__(self, *args, **kwargs):
        super(DatasetWrapper, self).__init__(*args, **kwargs)

    FILTER_RENAMES_MAP = {
        'familyIds': 'family_ids',
        'gender': 'sexes',
        'variantTypes': 'variant_type',
        'effectTypes': 'effect_types',
        'regionS': 'regions',
    }

    # inChild
    # presentInChild
    # presentInParent
    # genomicScores
    # geneSyms
    # limit
    # callSet
    # minParentsCalled
    # maxAltFreqPrcnt
    # minAltFreqPrcnt
    # ultraRareOnly
    # TMM_ALL
    def get_variants(self, **kwargs):
        limit = None
        if 'limit' in kwargs:
            limit = kwargs['limit']

        return itertools.islice(
            super(DatasetWrapper, self).get_variants(**kwargs), limit)
