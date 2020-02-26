def select_people_groups(available_groups, specified_groups):
    if len(available_groups) == 0:
        return None

    result = {
        pg.section_id(): {
            "name": pg.name,
            "source": pg.source,
            "domain": pg.domain,
        }
        for pg in available_groups
        if pg.section_id() in specified_groups
    }

    return result
