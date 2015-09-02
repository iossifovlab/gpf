'''
Created on Jul 27, 2015

@author: lubo
'''
from collections import defaultdict, Counter

from api.common.effect_types import EFFECT_GROUPS, build_effect_types
from DAE import vDB
from api.precompute.register import Precompute
import cPickle
import zlib
from api.studies import get_denovo_studies_names, get_transmitted_studies_names


class CommonBase(object):

    @staticmethod
    def effect_types():
        et = []
        et.extend(EFFECT_GROUPS['coding'])
        et.extend(EFFECT_GROUPS['noncoding'])
        et.extend(EFFECT_GROUPS['cnv'])

        return et

    @staticmethod
    def effect_groups():
        return ['LGDs', 'nonsynonymous', 'UTRs']

    @staticmethod
    def phenotypes():
        return ['autism',
                'congenital heart disease',
                'epilepsy',
                'intelectual disability',
                'schizophrenia',
                'unaffected']

    @staticmethod
    def family_configuration(family):
        return "".join([family[pid].role + family[pid].gender
                        for pid in sorted(family.keys(),
                                          key=lambda x: (family[x].role, x))])

    @staticmethod
    def family_configuration_to_pedigree(family_configuration):
        pedigree = [[family_configuration[i: i + 3],
                     family_configuration[i + 3: i + 4],
                     0] for i in range(0, len(family_configuration), 4)]
        result = [['mom', 'F', 0], ['dad', 'M', 0]]
        result.extend(pedigree)
        return result


class CounterBase(CommonBase):
    @staticmethod
    def build_families_buffer(studies):
        families_buffer = defaultdict(dict)
        for st in studies:
            for f in st.families.values():
                children = [f.memberInOrder[c]
                            for c in range(2, len(f.memberInOrder))]
                for p in children:
                    if p.personId in families_buffer[f.familyId]:
                        pass
                    else:
                        families_buffer[f.familyId][p.personId] = p
        return families_buffer

    def __init__(self, phenotype):
        super(CommonBase, self).__init__()
        self.phenotype = phenotype
        if phenotype not in self.phenotypes():
            raise ValueError("unexpected phenotype '{}'".format(phenotype))

    def filter_studies(self, all_studies):
        if self.phenotype == 'unaffected':
            return all_studies
        studies = [st for st in all_studies
                   if st.get_attr('study.phenotype') == self.phenotype]
        return studies


class ChildrenCounter(CounterBase):
    def __init__(self, phenotype):
        super(ChildrenCounter, self).__init__(phenotype)

        self.children_male = 0
        self.children_female = 0

    @property
    def children_total(self):
        return self.children_male + self.children_female

    def check_phenotype(self, person):
        if self.phenotype == 'unaffected':
            return person.role == 'sib'
        else:
            return person.role == 'prb'

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        families_buffer = self.build_families_buffer(studies)
        children_counter = Counter()

        for family in families_buffer.values():
            for person in family.values():
                if self.check_phenotype(person):
                    children_counter[person.gender] += 1

        self.children_female = children_counter['F']
        self.children_male = children_counter['M']


class FamiliesCounters(CounterBase):
    def __init__(self, phenotype):
        super(FamiliesCounters, self).__init__(phenotype)
        if phenotype == 'unaffected':
            raise ValueError("unexpected phenotype '{}'".format(phenotype))
        self.total = 0

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        families_buffer = self.build_families_buffer(studies)
        family_type_counter = Counter()

        for family in families_buffer.values():
            family_configuration = self.family_configuration(family)
            family_type_counter[family_configuration] += 1

        self.data = {}
        for (fconf, count) in family_type_counter.items():
            pedigree = [self.phenotype,
                        self.family_configuration_to_pedigree(fconf)]
            self.data[fconf] = (pedigree, count)
            self.total += count

    def get_counter(self, fconf):
        return self.data.get(fconf, 0)

    def type_counters(self):
        return self.data.values()

    @property
    def counters(self):
        return self.data.values()


class ReportBase(CommonBase):
    def __init__(self, study_name):
        super(ReportBase, self).__init__()
        self.study_name = study_name
        self.study_description = None
        self.studies = vDB.get_studies(self.study_name)

    @property
    def phenotypes(self):
        phenotypes = set([st.get_attr('study.phenotype')
                          for st in self.studies])
        phenotypes = list(phenotypes)
        phenotypes.sort()
        phenotypes.append('unaffected')
        return phenotypes


class FamiliesReport(ReportBase, Precompute):

    def __init__(self, study_name):
        super(FamiliesReport, self).__init__(study_name)
        self.families_counters = []
        self.children_counters = []
        self.families_total = 0

    def build(self):
        self.families_total = 0
        for phenotype in self.phenotypes[:-1]:
            assert phenotype != 'unaffected'
            fc = FamiliesCounters(phenotype)
            fc.build(self.studies)
            self.families_counters.append(fc)
            self.families_total += fc.total

        for phenotype in self.phenotypes:
            cc = ChildrenCounter(phenotype)
            cc.build(self.studies)
            self.children_counters.append(cc)

    def get_children_counters(self, phenotype):
        for cc in self.children_counters:
            if phenotype == cc.phenotype:
                return cc
        return None

    def get_families_counters(self, phenotype):
        for fc in self.families_counters:
            if phenotype == fc.phenotype:
                return fc
        return None

    def precompute(self):
        self.build()

    def serialize(self):
        fc = zlib.compress(cPickle.dumps(self.families_counters))
        cc = zlib.compress(cPickle.dumps(self.children_counters))
        ft = zlib.compress(cPickle.dumps(self.families_total))
        return {'families_counters': fc,
                'families_total': ft,
                'children_counters': cc}

    def deserialize(self, data):
        fc = data['families_counters']
        self.families_counters = cPickle.loads(zlib.decompress(fc))
        ft = data['families_total']
        self.families_total = cPickle.loads(zlib.decompress(ft))
        cc = data['children_counters']
        self.children_counters = cPickle.loads(zlib.decompress(cc))


class DenovoEventsCounter(CounterBase):
    def __init__(self, phenotype, children_counter, effect_type):
        super(DenovoEventsCounter, self).__init__(phenotype)
        self.effect_type = effect_type
        if self.phenotype != children_counter.phenotype:
            raise ValueError("wrong phenotype in children counter")
        self.children_counter = children_counter

        self.events_count = 0
        self.events_rate_per_child = 0.0
        self.events_children_count = 0
        self.events_children_percent = 0.0

    @property
    def child_type(self):
        if self.phenotype == 'unaffected':
            return 'sib'
        else:
            return 'prb'

    @property
    def effect_types_filter(self):
        return build_effect_types(self.effect_type)

    def filter_vs(self, vs):
        ret = []
        seen = set()
        for v in vs:
            hasNew = False
            for ge in v.requestedGeneEffects:
                sym = ge['sym']
                kk = v.familyId + "." + sym
                if kk not in seen:
                    hasNew = True
                    seen.add(kk)
            if hasNew:
                ret.append(v)
        return ret

    def is_zeroes(self):
        return self.events_count == 0 and self.events_children_count == 0

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        vs = vDB.get_denovo_variants(studies,
                                     inChild=self.child_type,
                                     effectTypes=self.effect_types_filter)
        vs = self.filter_vs(vs)
        self.events_count = len(vs)
        self.events_children_count = len(set(v.familyId for v in vs))
        if self.children_counter.children_total != 0:

            self.events_children_percent = \
                round((1.0 * self.events_children_count) /
                      self.children_counter.children_total, 3)

            self.events_rate_per_child = \
                round((1.0 * self.events_count) /
                      self.children_counter.children_total, 3)


class DenovoEventsReport(ReportBase, Precompute):

    def __init__(self, study_name, families_report):
        super(DenovoEventsReport, self).__init__(study_name)
        self.families_report = families_report
        self.rows = {}
        self._effect_groups = super(DenovoEventsReport, self).effect_groups()
        self._effect_types = super(DenovoEventsReport, self).effect_types()

    def effect_groups(self):
        return self._effect_groups

    def effect_types(self):
        return self._effect_types

    def build_row(self, effect_type):
        row = {}
        for pheno in self.phenotypes:
            cc = self.families_report.get_children_counters(pheno)
            ec = DenovoEventsCounter(pheno, cc, effect_type)
            ec.build(self.studies)
            row[pheno] = ec
        return row

    def clear_empty_rows(self):
        effect_groups = self.effect_groups()
        effect_types = self.effect_types()
        for et, row in self.rows.items():
            all_zeroes = True
            for ec in row.values():
                if not ec.is_zeroes():
                    all_zeroes = False
                    break
            if all_zeroes:
                if et in effect_groups:
                    effect_groups.remove(et)
                elif et in effect_types:
                    effect_types.remove(et)
        self.effect_groups = effect_groups
        self.effect_types = effect_types

    def build(self):
        rows = {}
        for effect_type in self.effect_groups():
            rows[effect_type] = self.build_row(effect_type)
        self.rows = rows

        rows = {}
        for effect_type in self.effect_types():
            rows[effect_type] = self.build_row(effect_type)
        self.rows.update(rows)
        self.clear_empty_rows()

    def precompute(self):
        self.build()

    def serialize(self):
        rows = zlib.compress(cPickle.dumps(self.rows))
        return {'rows': rows}

    def deserialize(self, data):
        rows = data['rows']
        self.rows = cPickle.loads(zlib.decompress(rows))
        self.clear_empty_rows()


class StudyVariantReports(ReportBase, Precompute):
    def __init__(self, study_name, study_description=None):
        super(StudyVariantReports, self).__init__(study_name)
        self.study_description = study_description
        self.families_report = None
        self.denovo_report = None

    def has_denovo(self):
        return any([st.has_denovo for st in self.studies])

    def build(self):
        self.families_report = FamiliesReport(self.study_name)
        self.families_report.build()

        if self.has_denovo():
            self.denovo_report = DenovoEventsReport(
                self.study_name,
                self.families_report)
            self.denovo_report.build()
        else:
            self.denovo_report = None

    def precompute(self):
        self.build()

    def serialize(self):
        return {'study_name': self.study_name,
                'families_report': self.families_report.serialize(),
                'denovo_report': self.denovo_report.serialize() if self.denovo_report else None}

    def deserialize(self, data):
        assert self.study_name == data['study_name']
        self.families_report = FamiliesReport(self.study_name)
        self.families_report.deserialize(data['families_report'])
        if 'denovo_report' in data and data['denovo_report']:
            self.denovo_report = DenovoEventsReport(self.study_name,
                                                    self.families_report)
            self.denovo_report.deserialize(data['denovo_report'])
        else:
            self.denovo_report = None

class VariantReports(Precompute):
    def __init__(self):
        self.data = None

    @property
    def studies(self):
        return get_denovo_studies_names() + get_transmitted_studies_names()

    def precompute(self):
        data = {}
        for (study_name, _) in self.studies:
            sr = StudyVariantReports(study_name)
            sr.precompute()
            data[study_name] = sr
        self.data = data

    def serialize(self):
        data = {}
        for (study_name, _) in self.studies:
            sr = self.data[study_name]
            sdict = sr.serialize()
            data[study_name] = zlib.compress(cPickle.dumps(sdict))
        return data

    def deserialize(self, data):
        res = {}
        for (study_name, study_description) in self.studies:
            assert study_name in data
            sr = StudyVariantReports(study_name, study_description)
            sdict = cPickle.loads(zlib.decompress(data[study_name]))
            sr.deserialize(sdict)
            res[study_name] = sr
        self.data = res

    def __getitem__(self, study_name):
        return self.data.get(study_name, None)
