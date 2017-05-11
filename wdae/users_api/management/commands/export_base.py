class ExportUsersBase:
    def get_visible_groups(self, user):
        groups = set(user.groups.values_list('name', flat=True).all())
        skip_groups = list(user.DEFAULT_GROUPS_FOR_USER)
        skip_groups.append(user.email)

        groups.difference_update(skip_groups)

        if user.is_superuser:
            groups.add("superuser")
        return groups
