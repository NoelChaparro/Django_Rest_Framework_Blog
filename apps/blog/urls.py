from django.urls import path

from .views import (
    PostlistView, 
    PostDetailView, 
    PostHeadingsView, 
    IncrementPostClickView
)

urlpatterns = [
    path('posts/', PostlistView.as_view(), name='post-list'),
    path('posts/<slug>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<slug>/headings/', PostHeadingsView.as_view(), name='post-headings'),
    path('post/increment_clicks/', IncrementPostClickView.as_view(), name='increment-post-click'),
]
