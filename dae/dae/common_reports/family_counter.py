import itertools


class FamilyCounter(object):

    def __init__(self, families, pedigree, family_label):
        self.families = families
        self.pedigree = pedigree
        self.pedigrees_label = family_label

    @property
    def family(self):
        return self.families[0]

    def to_dict(self):
        return {
            'pedigree': self.pedigree,
            'pedigrees_count': self.pedigrees_label,
        }


class FamiliesGroupCounters(object):

    def __init__(
            self, families_groups, selected_families_group, draw_all_families,
            families_count_show_id):
        self.families_groups = families_groups
        self.selected_families_group = selected_families_group
        self.families = self.selected_families_group.families
        assert len(self.selected_families_group.families) == \
            len(self.families_groups.families)

        self.draw_all_families = draw_all_families
        self.families_count_show_id = families_count_show_id

        self.counters = self._build_counters()

    def _build_counters(self):
        if self.draw_all_families is True:
            result = {}
            for family in self.families.values():
                fc = FamilyCounter(
                    [family],
                    self.selected_families_group.family_pedigree(family),
                    family.family_id)
                result[family.family_id] = fc
            assert len(self.families) == len(result)
            return result
        else:
            available_types = list(itertools.product(*[
                self.selected_families_group.available_families_types,
                self.families_groups['family_size'].available_families_types,
                self.families_groups['role.sex'].available_families_types,
                self.families_groups['status'].available_families_types,
            ]))

            families_types_counters = {
                ft: [] for ft in available_types
            }
            assert len(self.families) == \
                len(self.families_groups['status'].families_types)
            assert len(self.families) == \
                len(self.families_groups['role'].families_types)
            assert len(self.families) == \
                len(self.families_groups['sex'].families_types)
            assert len(self.families) == \
                len(self.families_groups['family_size'].families_types)

            families_types = list(zip(
                self.selected_families_group.families_types,
                self.families_groups['family_size'].families_types,
                self.families_groups['role.sex'].families_types,
                self.families_groups['status'].families_types,
            ))
            assert len(families_types) == len(self.families)
            for family, family_type in zip(
                    self.families.values(), families_types):
                assert family_type in families_types_counters, family_type
                families_types_counters[family_type].append(family)
            sorted_families_types = [
                (family_type, families)
                for family_type, families in families_types_counters.items()
            ]
            sorted_family_types = sorted(
                sorted_families_types, key=lambda item: - len(item[1])
            )
            result = {}
            for family_type, families in sorted_family_types:
                if len(families) == 0:
                    continue
                if self.families_count_show_id and \
                        len(families) <= self.families_count_show_id:
                    pedigree_label = ", ".join([
                        fam.family_id for fam in families])
                else:
                    pedigree_label = str(len(families))
                family = families[0]
                fc = FamilyCounter(
                    families,
                    self.selected_families_group.family_pedigree(family),
                    pedigree_label)

                result[family_type] = fc

            return result

    def to_dict(self):
        return {
            'group_name': self.selected_families_group.name,
            'phenotypes': self.selected_families_group.available_values,
            'counters': [
                {
                    'counters': [
                        counter.to_dict() for counter in self.counters.values()
                    ],
                }
            ],
            'legend': self.selected_families_group.legend
        }
