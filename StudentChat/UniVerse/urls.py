from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login', views.Login.as_view(), name="login"),
    path('', views.Main.as_view(), name="main"),
    path('login', views.Login.as_view(), name="login"),
    path('register', views.Register.as_view(), name="register"),
    path('interests', views.Interests.as_view(), name="interests"),
    path('logout', views.Logout.as_view(), name="logout"),
    path('chats', views.AllChats.as_view(), name="chats"),
    path('classes', views.Classes.as_view(), name="classes"),
    path('group_chats/<int:id>', views.GroupChats.as_view(), name="group_chats"),
    path('flashcard', views.flashcard.as_view(), name="flashcard"),
    path('account', views.account.as_view(), name="account"),
    path('logout/', views.account.logout_user, name="logout"),
    path('change_password', views.account.change_password, name="change_password"),
    path('delete_account/', views.account.delete_account, name='delete_account'),
    path('change_username', views.account.change_username, name='change_username'),
    path('edit_profile_picture', views.account.edit_profile_picture, name='edit_profile_picture'),
    path('friend_request', views.account.friend_request, name='friend_request'),
    path('remove_notification', views.AllChats.remove_notification, name='remove_notification'),
    path('friend_request_response', views.AllChats.requestResponse, name='friend_request_response'),
    path('change_bio', views.account.change_bio, name='change_bio'),
    path('chat_person/<int:id>', views.ChatPerson.as_view(), name="chat_person"),
    path('flashcardmode/<str:subject>', views.FlashcardMode.as_view(), name="flashcardmode"),
    path('update_points', views.QuizMode.update_points, name='update_points'),
    path('quizmode/<str:subject>', views.QuizMode.as_view(), name="quizmode"),
    path('create_group', views.Classes.create_group, name='create_group'),
    path('edit_group', views.Classes.edit_group, name='edit_group'),
    path('leaderboards/<int:id>', views.Leaderboards.as_view(), name="leaderboards")
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
