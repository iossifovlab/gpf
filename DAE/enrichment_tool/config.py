'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from future import standard_library
standard_library.install_aliases()  # noqa

from configparser import ConfigParser
from collections import Counter
from DAE import Config


class BackgroundConfig(object):

    def __init__(self, *args, **kwargs):
        super(BackgroundConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        data_dir = self.dae_config.data_dir

        self.config = ConfigParser({
            'wd': wd,
            'data': data_dir
        })
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


def children_stats_counter(studies, role):
    seen = set()
    counter = Counter()
    for st in studies:
        for fid, fam in list(st.families.items()):
            for p in fam.memberInOrder[2:]:
                iid = "{}:{}".format(fid, p.personId)
                if iid in seen:
                    continue
                if p.role != role:
                    continue

                counter[p.gender] += 1
                seen.add(iid)
    return counter
