from DAE import vDB
from collections import Counter, defaultdict
from helpers.logger import LOGGER
from precompute.register import Precompute
import preloaded
import cPickle
import zlib

from permissions import belongs_to_dataset


def family_buffer(studies):
    fam_buff = defaultdict(dict)
    for study in studies:
        for f in study.families.values():
            for p in f.memberInOrder:
                if p.personId in fam_buff[f.familyId]:
                    prev_p = fam_buff[f.familyId][p.personId]
                    if prev_p.role != p.role or prev_p.gender != p.gender:
                        LOGGER.error(
                            "study: (%s), familyId: (%s), personId: (%s),"
                            " role: (%s), prev: (%s)",
                            study.name,
                            f.familyId,
                            p.personId,
                            "%s:%s" % (p.role, p.gender),
                            "%s:%s" % (prev_p.role, prev_p.gender))
                else:
                    fam_buff[f.familyId][p.personId] = p
    return fam_buff


def build_header_summary(studies):
    child_cnt_hist = Counter()
    fam_type_cnt = Counter()
    child_type_cnt = Counter()

    fam_buff = family_buffer(studies)
    for fmd in fam_buff.values():
        child_cnt_hist[len(fmd)] += 1

        fam_conf = "".join([fmd[pid].role + fmd[pid].gender
                            for pid in sorted(fmd.keys(),
                                              key=lambda x: (fmd[x].role, x))])
        fam_type_cnt[fam_conf] += 1
        for p in fmd.values():
            child_type_cnt[p.role + p.gender] += 1
            child_type_cnt[p.role] += 1

    fam_total = len(fam_buff)

    return [fam_total, child_cnt_hist, child_type_cnt, fam_type_cnt]


def get_transmitted_studies_names():
    r = []
    for stN in vDB.get_study_names():
        if not belongs_to_dataset(stN):
            continue
        st = vDB.get_study(stN)
        if not st.has_transmitted:
            continue
        order = st.get_attr('wdae.production.order')
        if not order:
            continue
        r.append((int(order), stN, st.description))

    r = [(stN, dsc) for _o, stN, dsc in sorted(r)]
    return r


def get_denovo_studies_names():
    r = []

    for stGN in vDB.get_study_group_names():
        if not belongs_to_dataset(stGN):
            continue
        stG = vDB.get_study_group(stGN)
        order = stG.get_attr('wdae.production.order')
        if not order:
            continue
        r.append((int(order), stGN,
                  "%s (%s)" % (stG.description, ', '.join(stG.studyNames))))

    for stN in vDB.get_study_names():
        if not belongs_to_dataset(stN):
            continue
        st = vDB.get_study(stN)
        if not st.has_denovo:
            continue
        order = st.get_attr('wdae.production.order')
        if not order:
            continue
        r.append((int(order), stN, st.description))

    r = [(stN, dsc) for _o, stN, dsc in sorted(r)]
    return r


def get_sorted_datasets():
    datasets = preloaded.register.get('datasets').get_factory().get_datasets()
    return sorted(datasets,
                  key=lambda ds: ds.descriptor.get('wdae.production.order',
                                                   '0'))


def get_datasets_names():
    return [(dataset.descriptor['name'], '')
            for dataset in get_sorted_datasets()]


def get_all_studies_names():
    return get_datasets_names() + get_denovo_studies_names() + \
        get_transmitted_studies_names()


class StudiesSummaries(Precompute):
    def __init__(self):
        self.summaries = None

    def serialize(self):
        data = zlib.compress(cPickle.dumps(self.summaries))
        return {
            'data': data,
        }

    def deserialize(self, data):
        self.summaries = cPickle.loads(zlib.decompress(data['data']))

    def is_precomputed(self):
        return self.summaries is not None

    def precompute(self):
        self.summaries = self.build_studies_summaries()

    @classmethod
    def build_studies_summaries(cls):
        summaries = []
        seen = set()
        for summary in cls.__build_studies_summaries():
            if summary['study name'] in seen:
                continue
            summaries.append(summary)
            seen.add(summary['study name'])

        return {
            "columns": [
                "study name",
                "description",
                "phenotype",
                "study type",
                "study year",
                "PubMed",
                "families",
                "number of probands",
                "number of siblings",
                "denovo",
                "transmitted"
            ],
            "summaries": summaries
        }

    @classmethod
    def __build_studies_summaries(cls):
        result = [
            cls.__build_single_studies_summary(dataset.descriptor['name'], '',
                                               dataset.studies)
            for dataset in get_sorted_datasets()
        ]
        result += [cls.__build_single_studies_summary(name, description,
                                                      vDB.get_studies(name))
                   for name, description in get_all_studies_names()]
        return result

    @classmethod
    def __build_single_studies_summary(cls, name, description, studies):
        phenotype = set()
        study_type = set()
        study_year = set()

        has_denovo = False
        has_transmitted = False

        for study in studies:
            phenotype.update(study.phenotypes)
            if study.get_attr('study.type'):
                study_type.add(study.get_attr('study.type'))
            if study.get_attr('study.year'):
                study_year.add(study.get_attr('study.year'))

            # fams = fams.union(study.families.keys())
            has_denovo = has_denovo or study.has_denovo
            has_transmitted = has_transmitted or study.has_transmitted

        phenotype = list(phenotype)
        phenotype.sort()
        study_type = list(study_type)
        study_type.sort()
        study_year = list(study_year)
        study_year.sort()

        pub_med = ""
        if len(studies) == 1:
            study = studies[0]
            if study.get_attr('study.pmid'):
                pub_med = study.get_attr('study.pmid')

        fams_stat = build_header_summary(studies)

        return {
            "study name": name,
            "description": description,
            "phenotype": ', '.join(phenotype),
            "study type": ', '.join(study_type),
            "study year": ', '.join(study_year),
            "PubMed": pub_med,
            "families": fams_stat[0],
            "number of probands": fams_stat[2]['prb'],
            "number of siblings": fams_stat[2]['sib'],
            "denovo": has_denovo,
            "transmitted": has_transmitted,
        }
