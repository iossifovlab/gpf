'''
Created on Feb 29, 2016

@author: lubo
'''
import cPickle
import zlib

from DAE import vDB, phDB
from families.counters import FamilyFilterCounters
import precompute
from reports.variants import CounterBase
from pprint import pprint


# from helpers.logger import LOGGER
class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None
        self._trios = None
        self._quads = None
        self._families_buffer = None
        self._families_counters = None

    def serialize(self):
        result = {}
        result['prb'] = zlib.compress(cPickle.dumps(self._probands))
        result['sib'] = zlib.compress(cPickle.dumps(self._siblings))
        result['trios'] = zlib.compress(cPickle.dumps(self._trios))
        result['quads'] = zlib.compress(cPickle.dumps(self._quads))
        result['races'] = zlib.compress(cPickle.dumps(self._races))
        result['families_buffer'] = \
            zlib.compress(cPickle.dumps(self._families_buffer))
        result['families_counters'] = \
            zlib.compress(cPickle.dumps(self._families_counters))

        return result

    def deserialize(self, data):
        self._probands = cPickle.loads(zlib.decompress(data['prb']))
        self._siblings = cPickle.loads(zlib.decompress(data['sib']))
        self._trios = cPickle.loads(zlib.decompress(data['trios']))
        self._quads = cPickle.loads(zlib.decompress(data['quads']))
        self._races = cPickle.loads(zlib.decompress(data['races']))
        self._families_buffer = \
            cPickle.loads(zlib.decompress(data['families_buffer']))
        self._families_counters = \
            cPickle.loads(zlib.decompress(data['families_counters']))

    def _build_trios_and_quads(self):
        self._trios = set()
        self._quads = set()
        for fid, d in self.families_buffer().items():
            if len(d) == 1:
                self._trios.add(fid)
            if len(d) == 2:
                self._quads.add(fid)

    def precompute(self):
        self._siblings = {'M': set(),
                          'F': set()}
        self._probands = {'M': set(),
                          'F': set()}
        self._races = dict([(r, set()) for r in self.get_races()])

        studies = vDB.get_studies('ALL SSC')

        self._families_buffer = CounterBase.build_families_buffer(studies)
        self._families_counters = \
            FamilyFilterCounters.count_all(self._families_buffer)

        parent_races = self._parents_race()

        self._build_trios_and_quads()
        for fid, children in self._families_buffer.items():
            if fid in parent_races:
                self._races[parent_races[fid]].add(fid)
            prb_count = 0
            for ch in children.values():
                if ch.role == 'prb':
                    self._probands[ch.gender].add(fid)
                    prb_count += 1
                elif ch.role == 'sib':
                    self._siblings[ch.gender].add(fid)
            if prb_count == 2:
                print("family_id with 2 prb: {}".format(fid))
                pprint(children)

    def families_buffer(self):
        return self._families_buffer

    def families_counters(self):
        return self._families_counters

    def siblings(self, gender):
        assert self._siblings is not None
        assert gender == 'M' or gender == 'F'
        return self._siblings[gender]

    def probands(self, gender):
        assert self._probands is not None
        assert gender == 'M' or gender == 'F'
        return self._probands[gender]

    def trios(self):
        assert self._trios is not None
        return self._trios

    def quads(self):
        assert self._quads is not None
        return self._quads

    @staticmethod
    def get_races():
        return set(['african-amer',
                    'asian',
                    'more-than-one-race',
                    'native-american',
                    'native-hawaiian',
                    'white',
                    'other',
                    'not-specified'])

    @staticmethod
    def _parents_race():
        return dict([(k, f if f == m else 'more-than-one-race')
                     for (k, f, m) in
                     zip(phDB.families,
                         phDB.get_variable('mocuv.race_parents'),
                         phDB.get_variable('focuv.race_parents'))])

    def race(self, race):
        assert self._races is not None
        assert race in self.get_races()

        return self._races[race]
