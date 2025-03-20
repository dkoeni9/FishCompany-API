from django.urls import path, include
from rest_framework import routers, serializers, viewsets  # ?
from rest_framework.urlpatterns import format_suffix_patterns

from . import views
from . import authtoken

urlpatterns = [
    path("example/", views.ExampleView.as_view()),
    path("auth/", include("rest_framework.urls")),
    path("Admin/AddCompany", views.add_company),
    path("Admin/GetCompanies", views.get_companies),
    path("Auth/SignIn", authtoken.CustomAuthToken.as_view()),
    path("Auth/RegisterFisher", views.register_fisher),
    path("Company/GetInfo", views.get_info),
    path("Fish/GetFishes", views.FishList.as_view()),
    path("Search/GetFishBases", views.search),
]

urlpatterns = format_suffix_patterns(urlpatterns)
