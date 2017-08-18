'''
Created on Jul 7, 2016

@author: lubo
'''
import precompute
import cPickle
import zlib
from helpers.default_ssc_study import get_ssc_denovo_studies


class SSCFamiliesPrecompute(precompute.register.Precompute):

    def __init__(self):
        self._quads = None
        self._siblings = None
        self._probands = None
        self._families = None

    def is_precomputed(self):
        return self._quads is not None

    def serialize(self):
        result = {}
        result['quads'] = zlib.compress(cPickle.dumps(self._quads))
        result['prb'] = zlib.compress(cPickle.dumps(self._probands))
        result['sib'] = zlib.compress(cPickle.dumps(self._siblings))
        result['families'] = zlib.compress(cPickle.dumps(self._families))

        return result

    def deserialize(self, data):
        self._quads = cPickle.loads(zlib.decompress(data['quads']))
        self._probands = cPickle.loads(zlib.decompress(data['prb']))
        self._siblings = cPickle.loads(zlib.decompress(data['sib']))
        self._families = cPickle.loads(zlib.decompress(data['families']))

    @classmethod
    def _match_quad_families(cls, fam1, fam2):
        assert fam1.familyId == fam2.familyId
        if len(fam1.memberInOrder) != 4:
            return False
        assert len(fam2.memberInOrder) == 4

        prb1 = fam1.memberInOrder[2]
        prb2 = fam2.memberInOrder[2]
        if prb1.role != prb2.role or prb1.personId != prb2.personId or \
                prb1.gender != prb2.gender:
            return False

        sib1 = fam1.memberInOrder[3]
        sib2 = fam2.memberInOrder[3]
        if sib1.role != sib2.role or sib1.personId != sib2.personId or \
                sib1.gender != sib2.gender:
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
        nonquads = {}

        for st in studies:
            for fid, fam in st.families.items():
                if fid in nonquads:
                    nonquads[fid].append(fam)
                elif fid in quads:
                    prev = quads[fid]
                    if not self._match_quad_families(fam, prev):
                        nonquads[fid] = [prev, fam]
                        del quads[fid]

                elif self._is_quad_family(fam):
                    quads[fid] = fam
                else:
                    nonquads[fid] = [fam]
        quads = {fid: fid for fid in quads}
        return quads, nonquads

    def _build_all_quads(self):
        self._quads = {}
        self._nonquads = {}
        studies = get_ssc_denovo_studies()
        self._build_study_types(studies)
        self._quads['all'], self._nonquads[
            'all'] = self._build_quads(studies)

        for st in studies:
            self._quads[st.name], self._nonquads[
                st.name] = self._build_quads([st])

        for study_type in self._study_types:
            studies_by_type = self._filter_studies(studies, study_type)
            self._quads[study_type], \
                self._nonquads[study_type] = self._build_quads(
                    studies_by_type)

    def _build_all_children_gender(self):
        self._probands = {}
        self._siblings = {}
        studies = get_ssc_denovo_studies()
        self._build_study_types(studies)
        self._probands['all'], self._siblings['all'] = \
            self._build_children_gender(studies)
        for st in studies:
            self._probands[st.name], self._siblings[st.name] = \
                self._build_children_gender([st])

        for study_type in self._study_types:
            studies_by_type = self._filter_studies(studies, study_type)
            self._probands[study_type], self._siblings[study_type] = \
                self._build_children_gender(studies_by_type)

    def _build_children_gender(self, studies):
        siblings = {'M': set(),
                    'F': set()}
        probands = {'M': set(),
                    'F': set()}
        for st in studies:
            for fid, fam in st.families.items():
                for ch in fam.memberInOrder[2:]:
                    if ch.role == 'prb':
                        probands[ch.gender].add(fid)
                    elif ch.role == 'sib':
                        siblings[ch.gender].add(fid)

        print("mixed probands gender: {}".format(
            probands['M'] & probands['F']))
        print("mixed siblings gender: {}".format(
            siblings['M'] & siblings['F']))
        return probands, siblings

    def _build_families(self):
        studies = get_ssc_denovo_studies()
        families = set()
        for st in studies:
            for fid in st.families:
                families.add(fid)
        self._families = families

    def precompute(self):
        self._build_all_quads()
        self._build_all_children_gender()
        self._build_families()

    def quads(self, study='all'):
        return set(self._quads[study].keys())

    def nonquads(self, study='all'):
        return set(self._nonquads[study].keys())

    @staticmethod
    def _filter_gender(children, gender, study_type, study_name):
        if study_type is not None and study_name is None:
            return children[study_type][gender]
        elif study_name is not None and study_type is None:
            return children[study_name][gender]
        elif study_name is not None and study_type is not None:
            return children[study_name][gender] & \
                children[study_type][gender]
        else:
            return children['all'][gender]

    def probands(self, gender, study_type=None, study_name=None):
        return self._filter_gender(
            self._probands, gender, study_type, study_name)

    def siblings(self, gender, study_type=None, study_name=None):
        return self._filter_gender(
            self._siblings, gender, study_type, study_name)

    def families(self):
        return self._families
