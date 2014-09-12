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

def get_studies_summaries():
    r = []
    for stN in vDB.get_study_names():
        st = vDB.get_study(stN)

        ord = st.get_attr('wdae.production.order')
        if not ord:
            continue
        r.append((int(ord), [stN, 
                             st.description,
                             len(st.families),
                             st.has_denovo,
                             st.has_transmitted]))

    studies = [summary for ord, summary in sorted(r)]

    return {"columns": ["Study Name",
                        "Description",
                        "Families",
                        "Denovo",
                        "Transmitted"],
            "studies": studies}

