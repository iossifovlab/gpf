'''
Created on Jul 6, 2016

@author: lubo
'''
import cPickle
import zlib
import precompute
from helpers.default_ssc_study import get_ssc_denovo_studies
from DAE import phDB
import itertools


class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None
        self._races = {}

    def is_precomputed(self):
        return self._probands is not None

    def serialize(self):
        result = {}
        result['probands'] = zlib.compress(cPickle.dumps(self._probands))
        result['siblings'] = zlib.compress(cPickle.dumps(self._siblings))
        result['probands_gender'] = \
            zlib.compress(cPickle.dumps(self._probands_gender))
        result['races'] = zlib.compress(cPickle.dumps(self._races))
        return result

    def deserialize(self, data):
        self._probands = cPickle.loads(zlib.decompress(data['probands']))
        self._probands_gender = \
            cPickle.loads(zlib.decompress(data['probands_gender']))
        self._siblings = cPickle.loads(zlib.decompress(data['siblings']))
        self._races = cPickle.loads(zlib.decompress(data['races']))

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

    def _precompute_races(self):
        self._races = dict([(r, set()) for r in self.get_races()])
        parent_races = self._parents_race()
        for fid in parent_races.keys():
            self._races[parent_races[fid]].add(fid)

    def _precompute_children_gender(self):
        self._siblings = {'M': set(),
                          'F': set()}
        self._probands = {'M': set(),
                          'F': set()}

        studies = get_ssc_denovo_studies()
        for st in studies:
            for fam in st.families.values():
                for p in fam.memberInOrder:
                    if p.role == 'prb':
                        self._probands[p.gender].add(p.personId)
                    if p.role == 'sib':
                        self._siblings[p.gender].add(p.personId)

        print("probands with both genders: {}".format(
            self._probands['M'] & self._probands['F']))
        print("siblings with both genders: {}".format(
            self._siblings['M'] & self._siblings['F']))

    def _precompute_probands_gender(self):
        self._probands_gender = \
            zip(itertools.cycle(['M']),
                self.probands('M'))
        self._probands_gender.extend(
            zip(itertools.cycle(['F']),
                self.probands('F')))

    def precompute(self):
        self._precompute_races()
        self._precompute_children_gender()
        self._precompute_probands_gender()

    def probands(self, gender):
        return self._probands[gender]

    def siblings(self, gender):
        return self._siblings[gender]

    def probands_gender(self):
        return self._probands_gender

    def race(self, race):
        assert self._races is not None
        assert race in self.get_races()

        return self._races[race]
