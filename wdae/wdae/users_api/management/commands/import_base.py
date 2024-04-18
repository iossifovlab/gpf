from django.contrib.auth.models import BaseUserManager, Group

from users_api.models import WdaeUser


class ImportUsersBase:
    """Helper for users import."""

    def handle_user(self, res: dict[str, str]) -> WdaeUser:
        """Handle creation of user on import."""
        email = BaseUserManager.normalize_email(res["Email"])
        user = WdaeUser.objects.create_user(email=email)

        if "Groups" in res:
            groups = res["Groups"].split(":")
            groups = [g for g in groups if g != "superuser"]

            for group_name in set(groups):
                if group_name == "":
                    continue
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(user)  # type: ignore

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
