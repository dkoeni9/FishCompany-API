from django.urls import path, include
from rest_framework import routers, serializers, viewsets

from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("auth/", include("rest_framework.urls")),
    path("Admin/AddCompany", views.add_company),
    path("Admin/GetCompanies", views.get_companies),
    path("Auth/SignIn", views.sign_in),
    path("Fish/GetFishes", views.get_fishes),
    path("Search/GetFishBases", views.search),
]
