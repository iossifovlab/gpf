from DAE import vDB
from collections import Counter, defaultdict
from helpers.logger import LOGGER


def family_buffer(studies):
    fam_buff = defaultdict(dict)
    for study in studies:
        for f in study.families.values():
            for p in [f.memberInOrder[c]
                      for c in xrange(2, len(f.memberInOrder))]:
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
        stG = vDB.get_study_group(stGN)
        order = stG.get_attr('wdae.production.order')
        if not order:
            continue
        r.append((int(order), stGN, stG.description))

    for stN in vDB.get_study_names():
        st = vDB.get_study(stN)
        if not st.has_denovo:
            continue
        order = st.get_attr('wdae.production.order')
        if not order:
            continue
        r.append((int(order), stN, st.description))

    r = [(stN, dsc) for _o, stN, dsc in sorted(r)]
    return r


def __build_studies_summaries(studies):
    phenotype = set()
    study_type = set()
    study_year = set()

    has_denovo = False
    has_transmitted = False

    for study in studies:
        if study.get_attr('study.phenotype'):
            phenotype.add(study.get_attr('study.phenotype'))
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

    return [', '.join(phenotype),
            ', '.join(study_type),
            ', '.join(study_year),
            pub_med,
            fams_stat[0],
            fams_stat[2]['prb'],
            fams_stat[2]['sib'],
            has_denovo,
            has_transmitted]


def __build_denovo_studies_summaries():
    r = []

    for study_group_name in vDB.get_study_group_names():
        group = vDB.get_study_group(study_group_name)
        order = group.get_attr('wdae.production.order')
        if not order:
            continue
        studies_names = ','.join(group.studyNames)
        studies = vDB.get_studies(studies_names)
        summary = [study_group_name,
                   "%s (%s)" % (group.description,
                                studies_names.replace(',', ', '))]
        summary.extend(__build_studies_summaries(studies))

        r.append((int(order), summary))

    for study_name in vDB.get_study_names():
        study = vDB.get_study(study_name)
        if not study.has_denovo:
            continue
        order = study.get_attr('wdae.production.order')
        if not order:
            continue
        summary = [study_name, study.description]
        summary.extend(__build_studies_summaries([study]))

        r.append((int(order), summary))

    r = [s for _o, s in sorted(r)]
    return r


def __build_transmitted_studies_summaries():
    r = []

    for study_name in vDB.get_study_names():
        study = vDB.get_study(study_name)
        if not study.has_transmitted:
            continue

        order = study.get_attr('wdae.production.order')
        if not order:
            continue
        summary = [study_name, study.description]
        summary.extend(__build_studies_summaries([study]))

        r.append((int(order), summary))

    r = [s for _o, s in sorted(r)]
    return r


def get_studies_summaries():
    summaries = __build_denovo_studies_summaries()
    summaries.extend(__build_transmitted_studies_summaries())

    return {"columns": ["study name",
                        "description",
                        "phenotype",
                        "study type",
                        "study year",
                        "PubMed",
                        "families",
                        "number of probands",
                        "number of siblings",
                        "denovo",
                        "transmitted"],
            "summaries": summaries}
