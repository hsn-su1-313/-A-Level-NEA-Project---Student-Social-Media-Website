from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render , redirect
from django.views import View
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync # used to convert asynchronous layer functions to synchronus as we are writing in synchronusly
from django.contrib.auth import authenticate , login , logout
from django.contrib.auth.models import User # used to add user details to django administration database
from . import models
from django.db.models import Q
from .models import UserProfile
import json
import pandas # type: ignore    
import os
import base64
import random

script_dir = os.path.dirname(os.path.abspath(__file__)) 

file_path1 = os.path.join(script_dir, 'college_data.xlsx')
file_path2 = os.path.join(script_dir, 'flashcards.xlsx')

class Main(View):
    def get(self, request):

        if request.user.is_authenticated:
            return redirect("chats")

        return render(request=request, template_name="UniVerse/main.html")
    
class Login(View):
    def get(self, request):
        return render(request=request, template_name="UniVerse/login.html")  

    def post(self, request):

        # Get data from the form
        data = request.POST.dict()
        username = data.get("username")
        password = data.get("password")

        # Authenticate user using django's built-in authentication system
        user = authenticate(request=request, username=username, password=password)
        if user != None:
            login(request=request, user=user)
            return redirect("chats")

        # Error message
        context = {"error":"Incorrect login details."}
        return render(request=request, template_name="UniVerse/login.html", context=context)

class Register(View):
    def get(self, request):
        return render(request=request, template_name="UniVerse/register.html")  
    
    def post(self, request):

        context = {}
        
        # Get data from the form
        data = request.POST.dict()

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # Get data from student excel sheet
        student_data = pandas.read_excel(file_path1, sheet_name="Students")

        emails = list(student_data["Email"])
        first_names = list(student_data["First_name"])
        last_names = list(student_data["Last_name"])
        passwords = list(student_data["Password"])

        correct_email = False

        # Check if email entered is a school email address
        for student_email in emails:
            if email == student_email:
                correct_email = True
                break

        # Error messages
        if len(username) <= 6 or len(username) >= 20:
            context.update({"error":"Username must be between 6 and 20 characters."})
            return render(request=request, template_name="UniVerse/register.html", context=context)
        
        if not correct_email:
            context.update({"error":"You must use a valid student email address."})
            return render(request=request, template_name="UniVerse/register.html", context=context)
        
        student_index = emails.index(email)
        student_password = passwords[student_index]

        # Check if password is matching
        if password != student_password:
            context.update({"error":"Incorrect password."})
            return render(request=request, template_name="UniVerse/register.html", context=context)

        first_name = first_names[student_index]
        last_name = last_names[student_index]

        # Save user to database
        try:
            # Check if email is already registered
            if User.objects.filter(email=email).exists():
                context.update({"error": "Email already in use."})
            else:
                new_user = User()
                new_user.first_name = first_name
                new_user.last_name = last_name
                new_user.username = username
                new_user.email = email
                new_user.set_password(password)
                new_user.save()

                user = authenticate(request=request, username=username, password=password)
                if user != None:
                    login(request=request, user=user)
                    return redirect("interests")
        except:
            context.update({"error":"Username already in use."})

        return render(request=request, template_name="UniVerse/register.html", context=context)  
    
class Interests(View):
    def get(self, request):

        if request.user.is_authenticated:
             return render(request=request, template_name="UniVerse/interests.html")

        return render(request=request, template_name="UniVerse/main.html")
    
    def post(self, request):

        interests = request.POST.getlist("interests")
        other_interest = request.POST.get("other_interest", "").strip()

        me = request.user
        user_profile = UserProfile.objects.create(user=me)

        if other_interest:
            interests.remove('other')
            interests.append(other_interest)

        user_profile.interests = interests
        user_profile.save()

        return redirect("chats")

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("main")
    
class flashcard(View):
    def get(self, request):
        subject_data = pandas.read_excel(file_path1, sheet_name="Subjects")

        user_subjects = [f"{sub}" for sub in subject_data.columns[1:]]
        
        context = {"subjects":user_subjects}

        if request.user.is_authenticated:
             return render(request=request, template_name="UniVerse/flashcard.html", context=context)

        return render(request=request, template_name="UniVerse/main.html")
    
class Leaderboards(View):
    def get(self, request, id):
        # Load subject names from Excel sheet
        subject_data = pandas.read_excel(file_path1, sheet_name="Subjects")
        user_subjects = [f"{sub}" for sub in subject_data.columns[1:]]

        # Skip superuser/admin if at index 0
        users = User.objects.filter(is_superuser=False)
        user_points = models.FlashcardPoints.objects.all()

        # Prepare leaderboard data
        leaderboard_data = []
        for entry in user_points:
            leaderboard_data.append({
                "first_name": entry.user.first_name,  # Access first name
                "last_name": entry.user.last_name,
                "all_time": entry.all_time_points,
                "weekly": entry.weekly_points,
                "monthly": entry.monthly_points
            })

        # Sort based on selected leaderboard type
        if id == 1:
            leaderboard_data = sorted(leaderboard_data, key=lambda x: x["all_time"], reverse=True)
        elif id == 2:
            leaderboard_data = sorted(leaderboard_data, key=lambda x: x["monthly"], reverse=True)
        elif id == 3:
            leaderboard_data = sorted(leaderboard_data, key=lambda x: x["weekly"], reverse=True)

        print(type(leaderboard_data))

        context = {
            "subjects": user_subjects,
            "leaderboard_id": id,
            "users": users,
            "leaderboard_data": leaderboard_data,
        }

        # Only show leaderboard if user is authenticated
        if request.user.is_authenticated:

             return render(request=request, template_name="UniVerse/leaderboards.html", context=context)

        return render(request=request, template_name="UniVerse/main.html")
    
class FlashcardMode(View):
    def get(self, request, subject):
        subject_data = pandas.read_excel(file_path1, sheet_name="Subjects")
        flashcard_data = pandas.read_excel(file_path2, sheet_name=subject)
        
        questions = flashcard_data['Question'].tolist()
        answers = flashcard_data['Answer'].tolist()

        flashcards = [{"question": q, "answer": a} for q, a in zip(questions, answers)]
        random.shuffle(flashcards)  # Shuffle flashcards 

        user_subjects = [f"{sub}" for sub in subject_data.columns[1:]]
        current_subject = subject
        
        context = {"subjects":user_subjects,
                   "current_subject":current_subject,
                   "flashcards": flashcards}

        if request.user.is_authenticated:
             return render(request=request, template_name="UniVerse/flashcardmode.html", context=context)

        return render(request=request, template_name="UniVerse/main.html")
    
class QuizMode(View):
    def get(self, request, subject):
        subject_data = pandas.read_excel(file_path1, sheet_name="Subjects")
        flashcard_data = pandas.read_excel(file_path2, sheet_name=subject)
        
        questions = flashcard_data['Question'].tolist()
        answers = flashcard_data['Answer'].tolist()

        flashcards = [{"question": q, "answer": a} for q, a in zip(questions, answers)]
        random.shuffle(flashcards)  # Shuffle flashcards 

        me = request.user
        points, created = models.FlashcardPoints.objects.get_or_create(user=me)

        user_subjects = [f"{sub}" for sub in subject_data.columns[1:]]
        current_subject = subject
        
        context = {"subjects":user_subjects,
                   "current_subject":current_subject,
                   "flashcards": flashcards,
                   "points":points}

        if request.user.is_authenticated:
             return render(request=request, template_name="UniVerse/quizmode.html", context=context)

        return render(request=request, template_name="UniVerse/main.html")
    
    # View to update the user's flashcard points
    def update_points(request):
        # Fetch the user's FlashcardPoints record
        me = request.user
        flashcard_points = models.FlashcardPoints.objects.get(user=me)

        # Call method to update points
        flashcard_points.update_flashcard_points()

        # Load the subject from the incoming JSON request
        data = json.loads(request.body)
        subject = data.get('subject')
        
        return redirect('quizmode' , subject=subject)
    
class classes(View):
    def get(self, request):

        if request.user.is_authenticated:
             return render(request=request, template_name="UniVerse/classes.html")

        return render(request=request, template_name="UniVerse/main.html")

class account(View):
    def get(self, request):

        # Get current user and their profile
        me = request.user
        me_profile = models.UserProfile.objects.get(user=me)

        # Get profile picture
        profile_picture = me_profile.profile_picture

        # Load subjects from Excel
        subject_data = pandas.read_excel(file_path1, sheet_name="Subjects")

        email = me.email
        
        user_subjects = []

        # Map subject names to emojis
        subjects_unicode = {
            "Chemistry": "⚗️",
            "Physics": "🔬",
            "Computer Science": "💻",
            "Philosophy": "🧘",
            "Psychology": "🧠",
            "Biology": "🌱",
            "History": "🏺",
            "Geography": "🌍",
            "English Literature": "📖",
            "Mathematics": "📊",
        }

        # Assign subjects based on Excel data
        for index, row in subject_data.iterrows():
            if row['Email'] == email:
                subjects_true = row.drop('Email')[row.drop('Email') == True].index.tolist()
                for subject_name in subjects_true:
                    unicode_char = subjects_unicode.get(subject_name, "")
                    try:
                        subject_instance = models.Subject.objects.get(name=f"{unicode_char} {subject_name}")
                    except:
                        subject_instance = models.Subject.objects.create(name=f"{unicode_char} {subject_name}")
                        
                    user_subjects.append(subject_instance)    
         
        # Update profile with subjects
        me_profile.subjects.set(user_subjects)
        me_profile.save()

        timetable_data = pandas.read_excel(file_path1, sheet_name="Timetable")

        blocks = ["block " + str(i) for i in range(1, 17)]
        lessons = []
        
        # Build timetable based on Excel
        for index, row in timetable_data.iterrows():
            if row['Email'] == email:
                lst = row.drop('Email').tolist()
                columns = [col for col in timetable_data.columns if col != 'Email']
                for i, subject in enumerate(lst):
                    if subject:
                        lessons.append("lesson")
                    else:
                        lessons.append("Free")

        timetable = [{"block": b, "lesson": l} for b, l in zip(blocks, lessons)]

        # Get non-friend users (excluding self and superusers)
        users = User.objects.filter(is_superuser=False).exclude(id__in=me_profile.friends.all().values('user_id')).exclude(id=me.id)

        users_dict = {}

        # Suggest users based on shared interests, subjects, mutual friends
        for user in users:
            user_profile = models.UserProfile.objects.get(user=user)
            suggestion_points = 0

            # 1. Points for shared interests (25 points per matching interest)
            my_interests = set(me_profile.interests)
            their_interests = set(user_profile.interests)
            common_interests = my_interests & their_interests
            suggestion_points += len(common_interests) * 25
            
            # 2. Points for shared subjects (20 points per subject)
            my_subjects = set(me_profile.subjects.all())
            their_subjects = set(user_profile.subjects.all())
            common_subjects = my_subjects & their_subjects
            suggestion_points += len(common_subjects) * 20
            
            # 3. Points for mutual friends (15 points per mutual friend)
            my_friends = set(me_profile.friends.all())
            their_friends = set(user_profile.friends.all())
            mutual_friends = my_friends & their_friends
            suggestion_points += len(mutual_friends) * 15
            
            users_dict[user.id] = {
                "details": user,
                "suggestion_points": suggestion_points
            }

        sorted_users = sorted(users_dict.items(), key=lambda x: x[1]['suggestion_points'], reverse=True)
        
        # Extract only the user objects in the sorted order
        sorted_user_objects = [user_data['details'] for user_id, user_data in sorted_users]

        if request.user.is_authenticated:
             
            context = {"me":me,
                       "me_profile":me_profile,
                       "sorted_users":sorted_user_objects,
                       "timetable":timetable,
                       "profile_picture":profile_picture,
                       "users":users}
            
            return render(request=request, template_name="UniVerse/account.html", context=context)

        return render(request=request, template_name="UniVerse/main.html")
    
    def edit_profile_picture(request):
        profile_picture = request.FILES['profile_picture']

        me = request.user
        user_profile = models.UserProfile.objects.get(user=me)
        user_profile.profile_picture = profile_picture
        user_profile.save()

        return redirect('account')
    
    def friend_request(request):
        data = json.loads(request.body)
        friend_username = data.get('username')

        if friend_username:
            to_user = User.objects.get(username=friend_username)
            models.FriendRequest.objects.create(from_user=request.user, to_user=to_user, status='Pending')
        
        return redirect('account')
    
    def change_username(request):
        data = json.loads(request.body)
        new_username = data.get('username')

        if new_username:
            user = request.user
            user.username = new_username
            user.save()

        return redirect('account')
    
    def change_bio(request):
        data = json.loads(request.body)
        new_bio = data.get('bio')

        if new_bio:
            me = request.user
            user_profile = models.UserProfile.objects.get(user=me)
            user_profile.bio = new_bio
            user_profile.save()

        return redirect('account')
    
    def logout_user(request):

        logout(request) 
        return redirect("main")
    
    def delete_account(request):
        
        user = request.user
        user.delete() 
        logout(request)
        return redirect("main")
    
    def change_password(request):
        # load data from front end
        data = json.loads(request.body)
        new_password = data.get('new_password')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)  # Keep user logged in

        return redirect('account')

    
class AllChats(View):
    def get(self, request):

        # If user has logged in give him access
        if request.user.is_authenticated:   
            me = request.user
            me_profile = models.UserProfile.objects.get(user=me)

            # Getting a list of all the friends
            friends = list(me_profile.friends.all())

            users = []

            for friend in friends:
                friend_username = friend.user.username
                friend_user = User.objects.get(username=friend_username)

                # Appending user object of friend
                users.append(friend_user)

            # Getting accepted and rejected friend requests
            friend_requests = models.FriendRequest.objects.filter(to_user=me, status='Pending')
            accepted_friend_requests = models.FriendRequest.objects.filter(from_user=me, status='Accepted')
            rejected_friend_requests = models.FriendRequest.objects.filter(from_user=me, status='Rejected')

            profile_picture = me_profile.profile_picture

            # Returning the variables to be accessed by the front end
            context = {"user":request.user,
                       "users":users,
                       "friend_requests":friend_requests,
                       "accepted_friend_requests":accepted_friend_requests,
                       "rejected_friend_requests":rejected_friend_requests,
                       "profile_picture":profile_picture,
                       "me":me}

            return render(request=request, template_name="UniVerse/chats.html", context=context) 
        
        return redirect("main")
    
    # Function to respond to friend request
    def requestResponse(request):
        # Get data from the form
        data = json.loads(request.body)
        request_username = data.get('username')
        response = data.get('response')

        # Get friend request object
        from_user = User.objects.get(username=request_username)
        friend_request = models.FriendRequest.objects.get(from_user=from_user)

        # If request accepted update frien request and add friend to user profile
        if response == 'Accepted':
            friend_request.status = 'Accepted'
            friend_request.save()

            me = request.user
            friend = User.objects.get(username=request_username)
            friend_profile = models.UserProfile.objects.get(user=friend)
            me_profile = models.UserProfile.objects.get(user=me)

            me_profile.friends.add(friend_profile)
            me_profile.save()

        # Update friend request object
        elif response == "Rejected":
            friend_request.status = 'Rejected'
            friend_request.save()

        return redirect("chats")
    
    def remove_notification(request, response):
        data = json.loads(request.body)
        friend_request_username = data.get('username')

        if response == "Rejected":
            models.FriendRequest.objects.get(from_user=friend_request_username).delete()

        return redirect('chats')

class Classes(View):

    def get(self, request):

        if request.user.is_authenticated:

            # Retrieve groups the user belongs to, excluding classes
            groups = models.groupChat.objects.filter(members=request.user).exclude(
                name__in=["Class_A", "Class_B", "Class_C"]
            )

            me = request.user
            me_profile = models.UserProfile.objects.get(user=me)

            # Getting a list of all the friends
            friends = list(me_profile.friends.all())
            users = []

            for friend in friends:
                friend_username = friend.user.username
                friend_user = User.objects.get(username=friend_username)

                users.append(friend_user)

            # Read class data from Excel sheet
            classes_data = pandas.read_excel(file_path1, sheet_name="Classes")

            # Initialize class member lists
            class_members = {
            "Class_A": [],
            "Class_B": [],
            "Class_C": []
            }

            classes = []

            # Step 1: Loop through the Excel data and group users by class
            for index, row in classes_data.iterrows():
                email = row['Email']
                user = User.objects.filter(email=email).first()

                if not user:
                    continue  # Skip if user does not exist

                # Check if the current user belongs to any class
                if email == request.user.email:  # Only include the current user's classes
                    # Append users to respective class lists
                    if row['Class_A']:
                        class_members['Class_A'].append(user)
                    if row['Class_B']:
                        class_members['Class_B'].append(user)
                    if row['Class_C']:
                        class_members['Class_C'].append(user)

            # Step 2: Create or update group chats only if the current user belongs to the class
            for class_name, members in class_members.items():
                if request.user in members:  # Proceed only if the user is in the class
                    group, created = models.groupChat.objects.get_or_create(name=class_name)

                    # Add all users to the group
                    group.members.add(*members)  # Bulk add users

                    # Append the group to the classes list
                    classes.append(group)

            context = {"groups":groups,
                       "users":users,
                       "classes":classes}

            return render(request=request, template_name="UniVerse/classes.html", context=context)
        
        return redirect("main")
    
    def create_group(request):
        # Load the incoming JSON data
        data = json.loads(request.body)
        group_name = data.get('name')
        group_members = data.get('members')

        # Add the creator to the group
        group_members.append(request.user.id)

        # Create a new group chat
        group_chat = models.groupChat.objects.create(name=group_name)
        
        # Add members to the group chat
        for member_id in group_members:
            member = User.objects.get(id=member_id)
            group_chat.members.add(member)

        return redirect('classes')
    
    def edit_group(request):
        # Load the incoming JSON data
        data = json.loads(request.body)
        old_group_name = data.get('old_name')
        new_group_name = data.get('new_name')
        group_members = data.get('members')

        # Get group chat
        group_chat = models.groupChat.objects.get(name=old_group_name)

        # Edit group name
        group_chat.name = new_group_name
        group_chat.save()

        # Remove existing members from group chat
        group_chat.members.clear()

        # Add the creator to the group
        group_members.append(request.user.id)
        
        # Add updated members to group chat
        for member_id in group_members:
            member = User.objects.get(id=member_id)
            group_chat.members.add(member)  

        return redirect('classes')
    
class GroupChats(View):

    def get(self, request, id):

        if request.user.is_authenticated:
            me = request.user

            groups = models.groupChat.objects.filter(members=request.user).exclude(
                name__in=["Class_A", "Class_B", "Class_C"]
            )

            group = models.groupChat.objects.get(id=id)
        
            # Fetch group messages ordered by date and time
            messages = models.GroupMessage.objects.filter(group=group).order_by("date", "time")

            me_profile = models.UserProfile.objects.get(user=me)
            friends = list(me_profile.friends.all())
            users = []
            for friend in friends:
                friend_username = friend.user.username
                friend_user = User.objects.get(username=friend_username)

                users.append(friend_user)

            context = {"groups":groups,
                        "group_id":id,
                        "messages":messages,
                        "me":me,
                        "users":users}

            return render(request=request, template_name="UniVerse/group_chats.html", context=context)

        return redirect("main")
        
class ChatPerson(View):

    def get(self, request, id): 

        person = User.objects.get(id=id)
        me = request.user
        messages = models.Message.objects.filter(Q(from_whom=me , to_whom=person) | Q(from_whom=person , to_whom=me)).order_by("date" , "time")

        try:
            other_user = models.UserChannel.objects.get(user=person)

            data = {"type":"recevier_function",
                    "type_of_data":"the_messages_have_been_seen_from_the_other"}
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(other_user.channel_name, data)

        except models.UserChannel.DoesNotExist:
            other_user = None

        messages_have_not_been_seen = models.Message.objects.filter(from_whom=person, to_whom=me)
        messages_have_not_been_seen.update(has_been_seen=True)

        if request.user.is_authenticated:

            me = request.user
            me_profile = models.UserProfile.objects.get(user=me)

            friends = list(me_profile.friends.all())

            users = []

            for friend in friends:
                friend_username = friend.user.username
                friend_user = User.objects.get(username=friend_username)

                users.append(friend_user)
            
            context = {"person":person,
                        "me":me,
                        "messages":messages,
                        "user":request.user,
                        "users":users}

            return render(request=request, template_name="UniVerse/chat_person.html", context=context)

        return redirect("main")

