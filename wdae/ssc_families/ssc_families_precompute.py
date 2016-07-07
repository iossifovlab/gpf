'''
Created on Jul 7, 2016

@author: lubo
'''
import precompute
import cPickle
import zlib
from api.default_ssc_study import get_ssc_denovo_studies


class SSCFamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._quads = None

    def serialize(self):
        result = {}
        result['quads'] = zlib.compress(cPickle.dumps(self._quads))

        return result

    def deserialize(self, data):
        self._quads = cPickle.loads(zlib.decompress(data['quads']))

    @staticmethod
    def _match_quad_families(fam1, fam2):
        if len(fam1.memberInOrder) != len(fam2.memberInOrder):
            return False
        if len(fam1.memberInOrder) != 4:
            return False

        ch1 = fam1.memberInOrder[2]
        ch2 = fam2.memberInOrder[2]
        if ch1.role != ch2.role and ch1.personId != ch2.personId:
            return False

        ch1 = fam1.memberInOrder[3]
        ch2 = fam2.memberInOrder[3]
        if ch1.role != ch2.role and ch1.personId != ch2.personId:
            return False

        return True

    @staticmethod
    def _is_quad_family(fam):
        if len(fam.memberInOrder) != 4:
            return False
        ch1 = fam.memberInOrder[2]
        ch2 = fam.memberInOrder[3]

        return ch1.role == 'prb' and ch2.role == 'sib'

    def _build_quads(self):
        quads = {}
        mismatched_quads = {}

        studies = get_ssc_denovo_studies()
        for st in studies:
            for fid, fam in st.families.items():
                if fid in mismatched_quads:
                    mismatched_quads[fid].append(fam)
                elif fid in quads:
                    prev = quads[fid]
                    if not self._match_quad_families(fam, prev):
                        mismatched_quads[fid] = [prev, fam]
                        del quads[fid]
                elif self._is_quad_family(fam):
                    quads[fid] = fam
        return quads, mismatched_quads

    def precompute(self):
        self._quads = {}
        self._mismatched_quads = {}

        self._quads['all'], self._mismatched_quads['all'] = self._build_quads()

    def quads(self, study='all'):
        return self._quads[study].keys()

    def mismatched_quads(self, study='all'):
        return self._mismatched_quads[study].keys()
