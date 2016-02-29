'''
Created on Feb 29, 2016

@author: lubo
'''
import cPickle
import zlib
import precompute
from DAE import vDB
import itertools


class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None

    def serialize(self):
        result = {}
        result['prb'] = zlib.compress(cPickle.dumps(self._probands))
        result['sib'] = zlib.compress(cPickle.dumps(self._siblings))
        return result

    def deserialize(self, data):
        self._probands = cPickle.loads(zlib.decompress(data['prb']))
        self._siblings = cPickle.loads(zlib.decompress(data['sib']))

    def precompute(self):
        self._siblings = {'M': set(),
                          'F': set()}
        self._probands = {'M': set(),
                          'F': set()}

        studies = vDB.get_studies('ALL SSC')
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

    def siblings(self, gender):
        assert gender == 'M' or gender == 'F'
        return self._siblings[gender]

    def probadns(self, gender):
        assert gender == 'M' or gender == 'F'
        return self._probands[gender]
