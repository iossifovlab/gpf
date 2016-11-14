'''
Created on Nov 7, 2016

@author: lubo
'''
import ConfigParser
from VariantAnnotation import get_effect_types
from query_prepare import build_effect_types_list
from collections import Counter
from DAE import vDB, Config


class BackgroundConfig(object):

    def __init__(self, *args, **kwargs):
        super(BackgroundConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        self.config = ConfigParser.SafeConfigParser({'wd': wd})
        self.config.read(self.dae_config.enrichmentConfFile)

    def __getitem__(self, args):
        return self.config.get(*args)

    @property
    def backgrounds(self):
        return [
            n.strip() for n in self['enrichment', 'backgrounds'].split(',')
        ]

    @property
    def cache_dir(self):
        return self['enrichment', 'cache_dir']


# class ChildrenStats(object):

def children_stats_counter(studies, role):
    seen = set()
    counter = Counter()
    for st in studies:
        for fid, fam in st.families.items():
            for p in fam.memberInOrder[2:]:
                iid = "{}:{}".format(fid, p.personId)
                if iid in seen:
                    continue
                if p.role != role:
                    continue

                counter[p.gender] += 1
                seen.add(iid)
    return counter

#     @staticmethod
#     def build(denovo_studies):
#         res = {}
#         for phenotype in PHENOTYPES:
#             studies = denovo_studies.get_studies(phenotype)
#             if phenotype == 'unaffected':
#                 stats = ChildrenStats.count(studies, 'sib')
#             else:
#                 stats = ChildrenStats.count(studies, 'prb')
#             res[phenotype] = stats
#         return res
