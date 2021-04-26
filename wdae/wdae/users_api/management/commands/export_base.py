from builtins import object


class ExportUsersBase(object):

    def get_visible_groups(self, user):
        groups = set(user.groups.values_list("name", flat=True).all())

        if user.is_superuser:
            groups.add("superuser")
        return groups
