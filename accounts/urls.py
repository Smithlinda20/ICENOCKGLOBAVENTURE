from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.StoreLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("post-login/", views.post_login_redirect, name="post_login_redirect"),
    path("admin/reps/", views.rep_list, name="rep_list"),
    path("admin/reps/new/", views.rep_edit, name="rep_new"),
    path("admin/reps/<int:pk>/edit/", views.rep_edit, name="rep_edit"),
]
