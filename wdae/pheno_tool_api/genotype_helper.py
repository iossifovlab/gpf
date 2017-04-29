'''
Created on Nov 21, 2016

@author: lubo
'''
import pandas as pd
from collections import Counter
from Variant import variantInMembers


class GenotypeHelper(object):
    @classmethod
    def to_persons_variants(cls, vs):
        seen = set([])
        result = Counter()
        for v in vs:
            persons = variantInMembers(v)
            for p in persons:
                vid = "{}:{}:{}".format(p, v.location, v.variant)
                if vid not in seen:
                    seen.add(vid)
                    result[p] += 1
                else:
                    print("skipping {}".format(vid))
        return result

    @classmethod
    def to_persons_variants_df(cls, vs):
        vs = cls.to_persons_variants(vs)
        df = pd.DataFrame(
            data=[(k, v) for (k, v) in vs.items()],
            columns=['person_id', 'variants'])
        df.set_index('person_id', inplace=True, verify_integrity=True)
        return df

    @classmethod
    def to_families_variants(cls, vs):
        seen = set([])
        result = Counter()
        for v in vs:
            vid = "{}:{}:{}".format(v.familyId, v.location, v.variant)
            if vid not in seen:
                seen.add(vid)
                result[v.familyId] += 1
        return result
