from django.urls import path
from .views import vocatus_chat, chat_page




urlpatterns = [
    path("", chat_page, name="chat_page"),          # hoofdpagina
    path("chat/", vocatus_chat, name="vocatus_chat") # API endpoint
]

