# voting_app/serializers.py
from rest_framework import serializers
from .models import Poll, Option, Vote
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'vote_count']

class PollSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    creator = serializers.SlugRelatedField(slug_field='username', read_only=True)
    start_date = serializers.DateTimeField(required=False)  # Optional
    end_date = serializers.DateTimeField(required=True)    # Required

    class Meta:
        model = Poll
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active', 'creator', 'options']

    def validate(self, data):
        """
        Validate that end_date is after start_date if start_date is provided.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("end_date must be after start_date.")
        return data

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['poll', 'option', 'user']