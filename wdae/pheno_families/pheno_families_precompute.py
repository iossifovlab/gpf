'''
Created on Jul 6, 2016

@author: lubo
'''
import cPickle
import zlib
import precompute
from api.default_ssc_study import get_ssc_denovo_studies


class FamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._siblings = None
        self._probands = None

    def serialize(self):
        result = {}
        result['probands'] = zlib.compress(cPickle.dumps(self._probands))
        result['siblings'] = zlib.compress(cPickle.dumps(self._siblings))
        return result

    def deserialize(self, data):
        self._probands = cPickle.loads(zlib.decompress(data['probands']))
        self._siblings = cPickle.loads(zlib.decompress(data['siblings']))

    def precompute(self):
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

        print("probands with both geners: {}".format(
            self._probands['M'] & self._probands['F']))
        print("siblings with both geners: {}".format(
            self._siblings['M'] & self._siblings['F']))

    def probands(self, gender):
        return self._probands[gender]

    def siblings(self, gender):
        return self._siblings[gender]
