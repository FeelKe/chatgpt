from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:chat_id>/', views.index, name='index_with_chat'),
    path('create/', views.create_chat, name='create_chat'),
    path('delete/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('rename/<int:chat_id>/', views.rename_chat, name='rename_chat'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
