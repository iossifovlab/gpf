
from django.contrib.auth.models import AbstractUser


class ExportUsersBase:
    """Base class for exporting user-related data."""

    def get_visible_groups(self, user: AbstractUser) -> set[str]:
        """Get the groups visible to the user."""

        groups: set[str] = set(
            user.groups.values_list("name", flat=True).all(),
        )

        if user.is_superuser:
            groups.add("superuser")
        return groups
