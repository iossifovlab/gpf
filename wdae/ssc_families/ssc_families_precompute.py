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

    def _build_study_types(self, studies):
        stypes = set()
        for st in studies:
            stypes.add(st.get_attr('study.type').lower())
        self._study_types = list(stypes)
        self._study_types.sort()

    @staticmethod
    def _filter_studies(studies, study_type):
        return [st for st in studies
                if st.get_attr('study.type').lower() == study_type]

    def _build_quads(self, studies):
        quads = {}
        mismatched = {}

        for st in studies:
            for fid, fam in st.families.items():
                if fid in mismatched:
                    mismatched[fid].append(fam)
                elif fid in quads:
                    prev = quads[fid]
                    if not self._match_quad_families(fam, prev):
                        mismatched[fid] = [prev, fam]
                        del quads[fid]
                elif self._is_quad_family(fam):
                    quads[fid] = fam
        return quads, mismatched

    def precompute(self):
        self._quads = {}
        self._mismatched = {}

        studies = get_ssc_denovo_studies()
        self._build_study_types(studies)

        self._quads['all'], self._mismatched['all'] = \
            self._build_quads(studies)
        for st in studies:
            self._quads[st.name], self._mismatched[st.name] = \
                self._build_quads([st])

        for study_type in self._study_types:
            studies_by_type = self._filter_studies(studies, study_type)
            self._quads[study_type], self._mismatched[study_type] = \
                self._build_quads(studies_by_type)

    def quads(self, study='all'):
        return set(self._quads[study].keys())

    def mismatched_quads(self, study='all'):
        return set(self._mismatched[study].keys())
