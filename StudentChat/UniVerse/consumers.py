# Imports
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync 
import json 
from . import models
from django.contrib.auth.models import User
from datetime import datetime

class ChatConsumer(WebsocketConsumer):
    
    def connect(self):

        # Get user and group IDs from URL
        self.person_id = self.scope.get("url_route").get("kwargs").get("id")
        self.group_id = self.scope.get("url_route").get("kwargs").get("group_id")

        # Accept the WebSocket connection
        self.accept()

        # If group chat exists, add user to group channel
        if self.group_id:
            self.room_group_name = f"group_{self.group_id}"

            async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
            )
            
        else:
            try:

                user_channel = models.UserChannel.objects.get(user=self.scope.get("user")) 
                user_channel.channel_name = self.channel_name
                user_channel.save()

            except:

                user_channel = models.UserChannel() 
                user_channel.user = self.scope.get("user")
                user_channel.channel_name = self.channel_name
                user_channel.save()


    def receive(self, text_data):
        # Load incoming message
        text_data = json.loads(text_data)

        # Get current date and time for message
        now = datetime.now()
        date = now.date()
        time = now.time()

        # Format date and time for display
        date_for_show = datetime.now().strftime('%B. %D, %Y')
        time_for_show = datetime.now().strftime('%I:%M %p').lower()

        if text_data.get("type") == "text":

            # If message from group chat
            if self.group_id:

                # Store group message in database
                new_message = models.GroupMessage.objects.create(
                    group_id=self.group_id,
                    sender=self.scope.get("user"),
                    message=text_data.get("message"),
                    date=date,
                    time=time
                )

                # Store message data in a dictionary
                data = {
                    "type": "recevier_function",
                    "type_of_data": "group_text",
                    "data": text_data.get("message"),
                    "sender": self.scope.get("user").username,
                    "date": date_for_show,
                    "time": time_for_show
                }

                # Send message to all users in the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    data
                )
            
            else:
                other_user = User.objects.get(id=self.person_id)

                new_message = models.Message()
                new_message.from_whom = self.scope.get("user")
                new_message.to_whom = other_user
                new_message.message = text_data.get("message")
                new_message.date = date
                new_message.time = time
                new_message.has_been_seen = False
                new_message.save()

                try:

                    user_channel_name = models.UserChannel.objects.get(user=other_user)
                    
                    data = {
                        "type":"recevier_function",
                        "type_of_data":"text",
                        "data":text_data.get("message"), 
                        "date":date_for_show,
                        "time":time_for_show
                    }

                    async_to_sync(self.channel_layer.send)(user_channel_name.channel_name, data)

                except:
                    pass

        elif text_data.get("type") == "i_have_seen_the_messages":

            try:

                user_channel_name = models.UserChannel.objects.get(user=other_user)

                data = {"type":"recevier_function",
                        "type_of_data":"the_messages_have_been_seen_from_the_other"}

                async_to_sync(self.channel_layer.send)(user_channel_name.channel_name, data)

                messages_have_not_been_seen = models.Message.objects.filter(from_whom=other_user, to_whom=self.scope.get("user"))
                messages_have_not_been_seen.update(has_been_seen=True)

            except:
                
                pass
        
        # If message is an image
        elif text_data.get("type") == "image":

                # Store group message in database
                new_message = models.GroupMessage.objects.create(
                    group_id=self.group_id,
                    sender=self.scope.get("user"),
                    image=text_data.get("image"),
                    date=date,
                    time=time
                )

                # Store message data in a dictionary
                data = {
                    "type": "recevier_function",
                    "type_of_data": "group_text",
                    "data": text_data.get("image"),
                    "sender": self.scope.get("user").username,
                    "date": date_for_show,
                    "time": time_for_show
                }

                # Send message to all users in the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    data
                )



    def recevier_function(self, data_from_layer):
        data = json.dumps(data_from_layer)
        self.send(data)
