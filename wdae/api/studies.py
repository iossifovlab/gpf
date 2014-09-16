from DAE import vDB
from report_variants import build_header_summary

def get_transmitted_studies_names():
    r = []
    for stN in vDB.get_study_names():
        st = vDB.get_study(stN)
        if not st.has_transmitted:
            continue
        ord = st.get_attr('wdae.production.order')
        if not ord:
            continue
        r.append((int(ord), stN, st.description))

    r = [(stN, dsc) for ord, stN, dsc in sorted(r)]
    return r


def get_denovo_studies_names():
    r = []

    for stGN in vDB.get_study_group_names():
        stG = vDB.get_study_group(stGN)
        ord = stG.get_attr('wdae.production.order')
        if not ord:
            continue
        r.append((int(ord), stGN, stG.description))

    for stN in vDB.get_study_names():
        st = vDB.get_study(stN)
        if not st.has_denovo:
            continue
        ord = st.get_attr('wdae.production.order')
        if not ord:
            continue
        r.append((int(ord), stN, st.description))

    r = [(stN, dsc) for ord, stN, dsc in sorted(r)]
    return r

def __build_studies_family_stats(fams):
    
    fam_buff = defaultdict(dict)
    for study in studies:
        for f in study.families.values():
            for p in [f.memberInOrder[c] for c in xrange(2, len(f.memberInOrder))]:
                if p.personId not in fam_buff[f.familyId]:
                    fam_buff[f.familyId][p.personId] = p
    return fam_buff


def __build_studies_summaries(studies):
    phenotype = set()
    study_type = set()
    study_year = set()
    pmids = list()

    # fams = set()
    # prbs = set()
    # sibs = set()

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


    return [','.join(phenotype),
            ','.join(study_type),
            ','.join(study_year),
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
        ord = group.get_attr('wdae.production.order')
        if not ord:
            continue
        studies_names = ','.join(group.studyNames)
        studies = vDB.get_studies(studies_names)
        summary = [study_group_name,
                   "%s (%s)" % (group.description, studies_names)]
        summary.extend(__build_studies_summaries(studies))
        
        r.append((int(ord), summary))

    for study_name in vDB.get_study_names():
        study = vDB.get_study(study_name)
        if not study.has_denovo:
            continue
        ord = study.get_attr('wdae.production.order')
        if not ord:
            continue
        summary = [study_name, study.description]
        summary.extend(__build_studies_summaries([study]))

        r.append((int(ord), summary))

    r = [summary for ord, summary in sorted(r)]
    return r
    

def __build_transmitted_studies_summaries():
    r = []

    for study_name in vDB.get_study_names():
        study = vDB.get_study(study_name)
        if not study.has_transmitted:
            continue

        ord = study.get_attr('wdae.production.order')
        if not ord:
            continue
        summary = [study_name, study.description]
        summary.extend(__build_studies_summaries([study]))

        r.append((int(ord), summary))

    r = [summary for ord, summary in sorted(r)]
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

