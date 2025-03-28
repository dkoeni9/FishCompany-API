from django.urls import path, re_path, include
from rest_framework import routers, serializers, viewsets  # ?
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

from djoser.views import TokenCreateView, TokenDestroyView, UserViewSet

urlpatterns = [
    path("example/", views.ExampleView.as_view()),
    # path("auth/", include("rest_framework.urls")),
    # re_path(r"^auth/", include("djoser.urls.authtoken")),
    # re_path(r"^auth/", include("djoser.urls")),
    # Admin
    path("Admin/AddCompany", views.add_company),
    path("Admin/GetCompanies", views.get_companies),
    # Auth
    path("Auth/SignIn", TokenCreateView.as_view()),
    path("Auth/Logout", TokenDestroyView.as_view()),
    path("Auth/RegisterFisher", UserViewSet.as_view({"post": "create"})),
    # Company
    path("Company/GetInfo", views.UserCompanyView.as_view()),
    path("Company/GetFishBases", views.CompanyFishBaseView.as_view()),
    path("Company/GetStaff", views.CompanyStaffView.as_view()),
    # Fish
    path("Fish/GetFishes", views.FishListView.as_view()),
    # Search
    path("Search/GetFishBases", views.search),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
