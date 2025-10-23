from django.db import models
from django.contrib.auth.models import User  # Default User model provided by Django for authentication system
from django.utils.timezone import now
from datetime import timedelta

# Messages model
class Message(models.Model):
    from_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="from_user") 
    to_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="to_user") 
    message = models.TextField()
    date = models.DateField(null=True) 
    time = models.TimeField(null=True)
    has_been_seen = models.BooleanField(null=True, default=False)

# User channel model
class UserChannel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None) 
    channel_name = models.TextField()

# Group chat model
class groupChat(models.Model):
    name = models.CharField(max_length=20, default="")
    members = models.ManyToManyField(User)
    channel_name = models.TextField()

# Subject model
class Subject(models.Model):
    name = models.CharField(max_length=20, default="")

# User profile model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interests = models.JSONField(default=list, blank=True)  
    bio = models.TextField(blank=True, default="Bio:")   
    subjects = models.ManyToManyField(Subject)
    friends = models.ManyToManyField(
        'self', 
        symmetrical=True,  # Makes the relationship bidirectional (i.e., if A is friends with B, B is friends with A)
        blank=True  # Allows the field to be empty initially
    )
    profile_picture = models.ImageField(upload_to='images/', blank=True, null=True)
    
# Friend request model
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, default=None)

# Group message model
class GroupMessage(models.Model):
    group = models.ForeignKey('groupChat', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_messages')
    message = models.TextField(max_length=200)
    image = models.ImageField(upload_to='group_images/', blank=True, null=True) 
    date = models.DateField(null=True)
    time = models.TimeField(null=True)

# Flashcard points model
class FlashcardPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="flashcard_points")
    all_time_points = models.IntegerField(default=0)  # Total points
    weekly_points = models.IntegerField(default=0)    # Weekly points
    monthly_points = models.IntegerField(default=0)   # Monthly points
    last_reset = models.DateTimeField(default=now)    # Track last reset time

    # Add points to user
    def update_flashcard_points(self):
        self.all_time_points += 1
        self.weekly_points += 1
        self.monthly_points += 1
        self.save()

    # Reset weekly/monthly points if necessary
    def reset_points_if_needed(self):
        now_time = now()
        if now_time - self.last_reset >= timedelta(weeks=1):  # Weekly reset
            self.weekly_points = 0
        
        if now_time - self.last_reset >= timedelta(days=30):  # Monthly reset
            self.monthly_points = 0
        
        self.last_reset = now_time
        self.save()



    