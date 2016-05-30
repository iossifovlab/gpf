'''
Created on Feb 29, 2016

@author: lubo
'''
import cPickle
import zlib

from DAE import phDB
from families.counters import FamilyFilterCounters
import precompute
from reports.variants import CounterBase
from api.default_ssc_study import get_ssc_denovo_studies


# from helpers.logger import LOGGER
class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None
        self._study_types = None
        self._trios = None
        self._quads = None
        self._families_buffer = None
        self._families_counters = None
        self._probands_gender = None

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
        result['study_types'] = zlib.compress(cPickle.dumps(self._study_types))
        result['probands_gender'] = zlib.compress(
            cPickle.dumps(self._probands_gender))
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
        self._study_types = cPickle.loads(zlib.decompress(data['study_types']))
        self._probands_gender = cPickle.loads(
            zlib.decompress(data['probands_gender']))

    def _build_trios_and_quads(self):
        self._trios = {}
        self._quads = {}
        stypes = self._study_types
        stypes.append("ALL")
        for stype in stypes:
            self._trios[stype] = set()
            self._quads[stype] = set()
            for fid, d in self.families_buffer(stype).items():
                if len(d) == 1:
                    [ch] = d.values()
                    if ch.role == 'prb':
                        self._trios[stype].add(fid)

                if len(d) == 2:
                    [ch1, ch2] = d.values()
                    if ch1.role != ch2.role:
                        self._quads[stype].add(fid)

    def _build_family_buffer(self, studies):
        self._families_buffer = {}
        self._families_counters = {}
        self._families_buffer[
            'ALL'] = CounterBase.build_families_buffer(studies)
        self._families_counters['ALL'] = FamilyFilterCounters.count_all(
            self._families_buffer['ALL'])

        for stype in self._study_types:
            tsts = [st for st in studies
                    if st.get_attr("study.type").upper() == stype]
            self._families_buffer[stype] = \
                CounterBase.build_families_buffer(tsts)
            self._families_counters[stype] = FamilyFilterCounters.count_all(
                self._families_buffer[stype])

    def _build_study_types(self, studies):
        stypes = set()
        for st in studies:
            stypes.add(st.get_attr('study.type'))
        self._study_types = list(stypes)
        self._study_types.sort()

    def _build_proband_gender(self):
        stds = get_ssc_denovo_studies()
        self._probands_gender = {
            fmid: pd.gender for st in stds
            for fmid, fd in st.families.items()
            for pd in fd.memberInOrder if pd.role == 'prb'}

    def precompute(self):
        self._siblings = {'M': set(),
                          'F': set()}
        self._probands = {'M': set(),
                          'F': set()}
        self._races = dict([(r, set()) for r in self.get_races()])

        studies = get_ssc_denovo_studies()
        self._build_study_types(studies)
        self._build_family_buffer(studies)

        self._build_trios_and_quads()
        self._build_proband_gender()

        parent_races = self._parents_race()
        for fid, children in self.families_buffer().items():
            if fid in parent_races:
                self._races[parent_races[fid]].add(fid)
            for ch in children.values():
                if ch.role == 'prb':
                    self._probands[ch.gender].add(fid)
                elif ch.role == 'sib':
                    self._siblings[ch.gender].add(fid)

    def families_buffer(self, study_type="ALL"):
        return self._families_buffer[study_type]

    def families_counters(self, study_type="ALL"):
        return self._families_counters[study_type]

    def study_types(self):
        return self._study_types

    def siblings(self, gender):
        assert self._siblings is not None
        assert gender == 'M' or gender == 'F'
        return self._siblings[gender]

    def probands(self, gender):
        assert self._probands is not None
        assert gender == 'M' or gender == 'F'
        return self._probands[gender]

    def trios(self, study_type="ALL"):
        assert self._trios is not None
        return self._trios[study_type]

    def quads(self, study_type="ALL"):
        assert self._quads is not None
        return self._quads[study_type]

    def probands_gender(self):
        assert self._probands_gender is not None
        return self._probands_gender

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
