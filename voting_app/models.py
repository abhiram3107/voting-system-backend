# voting_app/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Poll(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField(default=timezone.now)  # Changed to default
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.title

class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=100)
    vote_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.text} ({self.poll.title})"

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('poll', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.option.vote_count += 1
        self.option.save()