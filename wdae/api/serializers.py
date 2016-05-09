from django.contrib.auth import get_user_model

from rest_framework import serializers

from models import Researcher


class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length='100')
    middle_name = serializers.CharField(max_length='100', required=False)
    last_name = serializers.CharField(max_length='100')
    email = serializers.EmailField()
    researcher_id = serializers.CharField(max_length='100')  # CHECK

    def validate(self, data):
        user_model = get_user_model()
        res_id = data['researcher_id']
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']

        try:
            res = Researcher.objects.get(email=email)
            researcher_ids = res.researcherid_set.all()
            researcher_id_set = set(
                [rid.researcher_id for rid in researcher_ids])
            if res_id not in researcher_id_set:
                raise Researcher.DoesNotExist

        except Researcher.DoesNotExist:
            raise serializers.ValidationError(
                'A researcher with these credentials was not found.')

        try:
            user_model.objects.get(email=data['email'])
            raise serializers.ValidationError(
                'A user with the same email already exists')
        except user_model().DoesNotExist:
            return data
