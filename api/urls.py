from django.urls import path, include
from rest_framework import routers, serializers, viewsets  # ?
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("auth/", include("rest_framework.urls")),
    path("Auth/RegisterFisher", views.register_fisher),
    path("Admin/AddCompany", views.add_company),
    path("Admin/GetCompanies", views.get_companies),
    path("Auth/SignIn", views.sign_in),
    path("Auth/RegisterFisher", views.register_fisher),
    path("Company/GetInfo", views.get_info),
    path("Fish/GetFishes", views.fish_list.as_view()),
    path("Search/GetFishBases", views.search),
]

urlpatterns = format_suffix_patterns(urlpatterns)
