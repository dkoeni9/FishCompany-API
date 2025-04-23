from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

from djoser.views import TokenCreateView, TokenDestroyView

urlpatterns = [
    # path("auth/", include("rest_framework.urls")),
    # re_path(r"^auth/", include("djoser.urls.authtoken")),
    # re_path(r"^auth/", include("djoser.urls")),
    # Admin
    path("Admin/AddCompany", views.EntrepreneurViewSet.as_view({"post": "create"})),
    path("Admin/GetCompanies", views.get_companies),
    # Auth
    path("Auth/SignIn", TokenCreateView.as_view()),
    path("Auth/Logout", TokenDestroyView.as_view()),
    path("Auth/RegisterFisher", views.FisherViewSet.as_view({"post": "create"})),
    # Company
    path("Company/GetInfo", views.CompanyView.as_view()),
    path("Company/GetFishBases", views.FishBaseViewSet.as_view({"get": "list"})),
    path("Company/GetStaff", views.StaffViewSet.as_view({"get": "list"})),
    path("Company/AddBase", views.FishBaseViewSet.as_view({"post": "create"})),
    path("Company/AddStaff", views.StaffViewSet.as_view({"post": "create"})),
    path(
        "Company/RemoveStaff/<int:id>",
        views.StaffViewSet.as_view({"delete": "destroy"}),
    ),
    # FishBase
    path(
        "FishBase/<int:pk>/RemoveBase",
        views.FishBaseViewSet.as_view({"delete": "destroy"}),
    ),
    path(
        "FishBase/<int:base_id>/GetAllFishes",
        views.FBFishesViewSet.as_view({"get": "list"}),
    ),
    path(
        "FishBase/<int:base_id>/AddFish",
        views.FBFishesViewSet.as_view({"post": "create"}),
    ),
    path(
        "FishBase/<int:base_id>/RemoveFish/<int:fish_id>",
        views.FBFishesViewSet.as_view({"delete": "destroy"}),
    ),
    path(
        "FishBase/<int:pk>/UploadPhoto",
        views.UploadPhotoView.as_view(),
    ),
    # Fish
    path("Fish/GetFishes", views.FishListView.as_view()),
    # Search
    path("Search/GetFishBases", views.search),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
