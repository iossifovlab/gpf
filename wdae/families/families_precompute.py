'''
Created on Feb 29, 2016

@author: lubo
'''
import cPickle
import zlib
import precompute
from DAE import vDB, phDB
import itertools
from helpers.logger import LOGGER


class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None
        self._trios = None
        self._quads = None

    def serialize(self):
        result = {}
        result['prb'] = zlib.compress(cPickle.dumps(self._probands))
        result['sib'] = zlib.compress(cPickle.dumps(self._siblings))
        result['trios'] = zlib.compress(cPickle.dumps(self._trios))
        result['quads'] = zlib.compress(cPickle.dumps(self._quads))
        result['races'] = zlib.compress(cPickle.dumps(self._races))
        return result

    def deserialize(self, data):
        self._probands = cPickle.loads(zlib.decompress(data['prb']))
        self._siblings = cPickle.loads(zlib.decompress(data['sib']))
        self._trios = cPickle.loads(zlib.decompress(data['trios']))
        self._quads = cPickle.loads(zlib.decompress(data['quads']))
        self._races = cPickle.loads(zlib.decompress(data['races']))

    def precompute(self):
        self._siblings = {'M': set(),
                          'F': set()}
        self._probands = {'M': set(),
                          'F': set()}
        self._trios = set()
        self._quads = set()
        self._races = dict([(r, set()) for r in self.get_races()])

        studies = vDB.get_studies('ALL SSC')
        parent_races = self._parents_race()
        seen = set()
        for st in itertools.chain(studies):
            for fid, family in st.families.items():
                if fid in seen:
                    continue
                seen.add(fid)
                prb = family.memberInOrder[2]
                self._probands[prb.gender].add(fid)

                for sib in family.memberInOrder[3:]:
                    self._siblings[sib.gender].add(fid)

                if len(family.memberInOrder) == 3:
                    self._trios.add(fid)
                if len(family.memberInOrder) == 4:
                    self._quads.add(fid)

                if fid in parent_races:
                    self._races[parent_races[fid]].add(fid)
                else:
                    LOGGER.warn("family {} parent race not found".format(fid))

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
