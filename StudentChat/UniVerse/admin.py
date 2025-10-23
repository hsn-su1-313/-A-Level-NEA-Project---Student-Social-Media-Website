from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Message) # To be able to view message and model in admin page
admin.site.register(models.UserChannel) # To be able to view user and user_channel in admin page
admin.site.register(models.UserProfile)
admin.site.register(models.Subject)
admin.site.register(models.FlashcardPoints)
admin.site.register(models.FriendRequest)
admin.site.register(models.groupChat)
admin.site.register(models.GroupMessage)