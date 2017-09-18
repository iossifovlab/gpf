from rest_framework import serializers


class ProtectedGroupsValidator(object):
    def __init__(self):
        self.is_update = False
        self.user_instance = None

    def __call__(self, value):
        if not self.is_update:
            return

        group_names = [g['name'] for g in value]
        missing_groups = []
        for group in self.user_instance.get_protected_group_names():
            if group not in group_names:
                message = 'The group {} cannot be removed.'.format(group)
                missing_groups.append(message)

        if len(missing_groups) > 0:
            raise serializers.ValidationError(missing_groups)

    def set_context(self, serializer_field):
        current = serializer_field
        while hasattr(current, 'parent') and current.parent is not None:
            current = current.parent

        instance = current.instance

        self.is_update = instance is not None
        self.user_instance = instance
