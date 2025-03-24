# voting_app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Poll, Option, Vote
from .serializers import PollSerializer, VoteSerializer, UserSerializer, OptionSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
class PollListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Update all polls' is_active status based on dates
        polls = Poll.objects.all()
        for poll in polls:
            poll.is_active = poll.start_date <= timezone.now() <= poll.end_date
            poll.save()

        # Filter active polls
        active_polls = Poll.objects.filter(is_active=True)
        serializer = PollSerializer(active_polls, many=True)
        return Response(serializer.data)
    permission_classes = [IsAuthenticated]
    def get(self, request):
        polls = Poll.objects.filter(is_active=True, end_date__gt=timezone.now())
        serializer = PollSerializer(polls, many=True)
        return Response(serializer.data)
class DeactivatedPollListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Update all polls' is_active status based on dates
        polls = Poll.objects.all()
        for poll in polls:
            poll.is_active = poll.start_date <= timezone.now() <= poll.end_date
            poll.save()

        # Filter deactivated polls
        deactivated_polls = Poll.objects.filter(is_active=False)
        serializer = PollSerializer(deactivated_polls, many=True)
        return Response(serializer.data)
class PollDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id, is_active=True, end_date__gt=timezone.now())
        serializer = PollSerializer(poll)
        return Response(serializer.data)

class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        # Update is_active status
        poll.is_active = poll.start_date <= timezone.now() <= poll.end_date
        poll.save()

        if not poll.is_active:
            return Response({"error": "This poll is no longer active and cannot be voted on"}, status=status.HTTP_400_BAD_REQUEST)

        option_id = request.data.get('option_id')
        option = get_object_or_404(Option, id=option_id, poll=poll)

        if Vote.objects.filter(poll=poll, user=request.user).exists():
            return Response({"error": "You have already voted in this poll"}, status=status.HTTP_400_BAD_REQUEST)

        vote_data = {'poll': poll.id, 'option': option.id, 'user': request.user.id}
        serializer = VoteSerializer(data=vote_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Vote recorded successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    permission_classes = [IsAuthenticated]
    def post(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id, is_active=True, end_date__gt=timezone.now())
        option_id = request.data.get('option_id')
        option = get_object_or_404(Option, id=option_id, poll=poll)
        
        if Vote.objects.filter(poll=poll, user=request.user).exists():
            return Response({"error": "You have already voted in this poll"}, status=status.HTTP_400_BAD_REQUEST)
        
        vote_data = {'poll': poll.id, 'option': option.id, 'user': request.user.id}
        serializer = VoteSerializer(data=vote_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Vote recorded successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PollResultsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        options = Option.objects.filter(poll=poll).order_by('-vote_count')
        winner = options.first() if options.exists() else None
        data = {
            'poll': PollSerializer(poll).data,
            'options': OptionSerializer(options, many=True).data,
            'winner': winner.text if winner else "No votes yet"
        }
        return Response(data)

# voting_app/views.py
# voting_app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Poll, Option, Vote
from .serializers import PollSerializer, VoteSerializer, UserSerializer, OptionSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime

class PollCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Parse start_date and end_date from request data
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        # Validate and parse dates
        start_date = parse_datetime(start_date_str) if start_date_str else timezone.now()
        end_date = parse_datetime(end_date_str) if end_date_str else timezone.now() + timedelta(days=7)

        if not start_date or not end_date:
            return Response({"error": "Invalid date format. Use ISO 8601 format (e.g., '2025-03-22T12:00:00Z')"}, status=status.HTTP_400_BAD_REQUEST)

        if end_date <= start_date:
            return Response({"error": "End date must be after start date"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare poll data
        poll_data = request.data.copy()
        poll_data['start_date'] = start_date
        poll_data['end_date'] = end_date
        poll_data['is_active'] = start_date <= timezone.now() <= end_date  # Set is_active based on dates

        serializer = PollSerializer(data=poll_data)
        if serializer.is_valid():
            poll = serializer.save(creator=request.user)
            options = request.data.get('options', [])
            for opt in options:
                Option.objects.create(poll=poll, text=opt)
            return Response(PollSerializer(poll).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PollEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        if poll.creator != request.user:
            return Response({"error": "You can only edit your own polls"}, status=status.HTTP_403_FORBIDDEN)

        # Parse start_date and end_date from request data
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        # Validate and parse dates if provided
        start_date = parse_datetime(start_date_str) if start_date_str else poll.start_date
        end_date = parse_datetime(end_date_str) if end_date_str else poll.end_date

        if start_date and end_date:
            if end_date <= start_date:
                return Response({"error": "End date must be after start date"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare poll data
        poll_data = request.data.copy()
        if start_date:
            poll_data['start_date'] = start_date
        if end_date:
            poll_data['end_date'] = end_date
            poll_data['is_active'] = start_date <= timezone.now() <= end_date  # Update is_active

        serializer = PollSerializer(poll, data=poll_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'options' in request.data:
                poll.options.all().delete()
                for opt in request.data['options']:
                    Option.objects.create(poll=poll, text=opt)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    permission_classes = [IsAuthenticated]
    def put(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        if poll.creator != request.user:
            return Response({"error": "You can only edit your own polls"}, status=status.HTTP_403_FORBIDDEN)
        
        if not poll.is_active or poll.end_date < timezone.now():
            return Response({"error": "Cannot edit inactive or expired polls"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PollSerializer(poll, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'options' in request.data:
                poll.options.all().delete()
                for opt in request.data['options']:
                    Option.objects.create(poll=poll, text=opt)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PollDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        if poll.creator != request.user:
            return Response({"error": "You can only delete your own polls"}, status=status.HTTP_403_FORBIDDEN)
        poll.delete()
        return Response({"message": "Poll deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_staff
        })
