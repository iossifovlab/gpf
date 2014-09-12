from DAE import vDB


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



def __build_studies_summaries(studies):
    fams = set()
    has_denovo = False
    has_transmitted = False

    for study in studies:
        fams = fams.union(study.families.keys())
        has_denovo = has_denovo or study.has_denovo
        has_transmitted = has_transmitted or study.has_transmitted

    return [len(fams), has_denovo, has_transmitted]

def __build_denovo_studies_summaries():
    r = []

    for study_group_name in vDB.get_study_group_names():
        group = vDB.get_study_group(study_group_name)
        ord = group.get_attr('wdae.production.order')
        if not ord:
            continue
        studies = vDB.get_studies(','.join(group.studyNames))
        summary = [study_group_name, group.description]
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

    return {"columns": ["Study Name",
                        "Description",
                        "Families",
                        "Denovo",
                        "Transmitted"],
            "studies": summaries}

