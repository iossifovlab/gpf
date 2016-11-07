'''
Created on Nov 7, 2016

@author: lubo
'''
import ConfigParser
from VariantAnnotation import get_effect_types
from query_prepare import build_effect_types_list
from collections import Counter
from DAE import vDB, Config

PHENOTYPES = [
    'autism',
    'congenital heart disease',
    'epilepsy',
    'intelectual disability',
    'schizophrenia',
    'unaffected',
]

EFFECT_TYPES = [
    'LGDs',
    'missense',
    'synonymous'
]


class DenovoStudies(object):

    def __init__(self):
        self.studies = vDB.get_studies('ALL WHOLE EXOME')

    def get_studies(self, phenotype):
        assert phenotype in PHENOTYPES
        if phenotype == 'unaffected':
            studies = [st for st in self.studies
                       if 'WE' == st.get_attr('study.type')]
            return studies
        else:
            studies = []
            for st in self.studies:
                if phenotype == st.get_attr('study.phenotype') and \
                        'WE' == st.get_attr('study.type'):
                    studies.append(st)
            return studies


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


class EnrichmentConfig(object):
    EFFECT_TYPES = get_effect_types(True, True)

    def __init__(self, phenotype, effect_type):
        assert phenotype in PHENOTYPES
        self.phenotype = phenotype

        et = build_effect_types_list([effect_type])
        assert 1 == len(et)
        assert all([e in self.EFFECT_TYPES for e in et])

        self.effect_type = ','.join(et)

        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'


class ChildrenStats(object):

    @staticmethod
    def count(studies, role):
        print([st.name for st in studies])
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

    @staticmethod
    def build(denovo_studies):
        res = {}
        for phenotype in PHENOTYPES:
            studies = denovo_studies.get_studies(phenotype)
            if phenotype == 'unaffected':
                stats = ChildrenStats.count(studies, 'sib')
            else:
                stats = ChildrenStats.count(studies, 'prb')
            res[phenotype] = stats
        return res
