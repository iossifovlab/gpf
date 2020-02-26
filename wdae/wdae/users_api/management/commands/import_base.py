from builtins import object
from users_api.models import WdaeUser
from django.contrib.auth.models import BaseUserManager, Group


class ImportUsersBase(object):
    def handle_user(self, res):
        email = BaseUserManager.normalize_email(res["Email"])
        user = WdaeUser.objects.create_user(email=email)

        if "Groups" in res:
            groups = res["Groups"].split(":")
            groups = [g for g in groups if g != "superuser"]

            for group_name in set(groups):
                if group_name == "":
                    continue
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(user)

            if WdaeUser.SUPERUSER_GROUP in res["Groups"]:
                user.is_superuser = True
                user.is_staff = True

        if "Name" in res:
            user.name = res["Name"]

        if "Password" in res:
            user.password = res["Password"]
            if res["Password"] != "":
                user.is_active = True

        user.save()
        return user
