from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('add/', views.add_book, name='add_book'),
    path('category/add/', views.add_category, name='add_category'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/delete/', views.delete_book, name='delete_book'),
]
