# voting_app/urls.py
from django.urls import path
from .views import (
    RegisterView, PollListView, PollDetailView, VoteView, 
    PollResultsView, PollCreateView, UserProfileView,
    PollEditView, PollDeleteView,DeactivatedPollListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('polls/', PollListView.as_view(), name='poll_list'),
    path('polls/<int:poll_id>/', PollDetailView.as_view(), name='poll_detail'),
    path('polls/<int:poll_id>/vote/', VoteView.as_view(), name='vote'),
    path('polls/<int:poll_id>/results/', PollResultsView.as_view(), name='poll_results'),
    path('polls/create/', PollCreateView.as_view(), name='poll_create'),
    path('polls/<int:poll_id>/edit/', PollEditView.as_view(), name='poll_edit'),
    path('polls/<int:poll_id>/delete/', PollDeleteView.as_view(), name='poll_delete'),
    path('user/', UserProfileView.as_view(), name='user_profile'),
    
]