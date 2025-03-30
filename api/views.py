import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from .models import Fish, FishBase, User
from .permissions import *
from .serializers import *

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.authentication import (
    SessionAuthentication,
    BasicAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import AllowAny


# Create your views here.


class ExampleView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        content = {
            "user": str(request.user),  # `django.contrib.auth.User` instance.
            "auth": str(request.auth),  # None
        }
        return Response(content)


class UserCompanyView(generics.RetrieveAPIView):
    serializer_class = UserCompanySerializer
    permission_classes = [IsEntrepreneur]

    def get_object(self):
        return self.request.user


class CompanyFishBaseView(generics.ListAPIView):
    serializer_class = FishBaseSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        # user_profile = User.objects.select_related("company").get(user=self.request.user)
        # company = user_profile.company

        # return FishBase.objects.filter(company_name=company.name)

        user = self.request.user
        company_name = user.company_name

        return FishBase.objects.filter(company_name=company_name)


class CompanyStaffView(generics.ListAPIView):
    serializer_class = CompanyStaffSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        company_name = user.company_name

        fish_base_ids = FishBase.objects.filter(company_name=company_name).values_list(
            "id", flat=True
        )

        return User.objects.filter(works_on_fish_base_id__in=fish_base_ids)


class CompanyAddBaseView(generics.CreateAPIView):
    serializer_class = FishBaseSerializer
    permission_classes = [IsEntrepreneur]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data["company_name"] = user.company_name

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class CompanyAddStaffViewSet(DjoserUserViewSet):
    permission_classes = [IsEntrepreneur]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        fish_base_id = data.pop("fish_base_id", None)

        if fish_base_id:
            try:
                fish_base = FishBase.objects.get(id=fish_base_id)

                if fish_base.company_name != user.company_name:
                    return Response(
                        {"error": "Fish base does not belong to your company."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                data["works_on_fish_base"] = fish_base.id
            except FishBase.DoesNotExist:
                return Response(
                    {"error": "Fish base not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class CompanyRemoveStaffView(generics.DestroyAPIView):
    serializer_class = CompanyStaffSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        company_name = user.company_name

        fish_base_ids = FishBase.objects.filter(company_name=company_name).values_list(
            "id", flat=True
        )

        return User.objects.filter(
            works_on_fish_base_id__in=fish_base_ids, is_staff=True
        )


class FishListView(generics.ListAPIView):
    queryset = Fish.objects.all()
    serializer_class = FishSerializer
    permission_classes = [IsEntrepreneur]


@csrf_exempt
def add_company(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Invalid method specified in request. POST request required."},
            status=405,
        )

    data = json.loads(request.body)
    user = User(
        login=data.get("Login"),
        password=data.get("Password"),
        first_name=data.get("FirstName"),
        middle_name=data.get("MiddleName"),
        last_name=data.get("LastName"),
        company_name=data.get("Name"),
        company_address=data.get("Address"),
    )
    user.save()

    return JsonResponse({"Id": user.pk}, status=201)


@csrf_exempt
def get_companies(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Invalid method specified in request. GET request required."},
            status=405,
        )

    with_bases = request.GET.get("WithBases", "false").lower() == "true"

    companies = User.objects.filter(company_name__isnull=False).distinct()

    if with_bases:
        fish_bases = FishBase.objects.all()

        companies_with_bases = []
        for company in companies:
            fish_bases = fish_bases.filter(company_name=company.company_name)

            company_data = {
                "Id": company.pk,
                "Login": company.login,
                "Name": company.company_name,
                "Address": company.company_address,
                "FirstName": company.first_name,
                "MiddleName": company.middle_name,
                "LastName": company.last_name,
                "FishBases": [
                    {
                        "Id": fish_base.pk,
                        "Latitude": (
                            float(fish_base.latitude) if fish_base.latitude else None
                        ),
                        "Longitude": (
                            float(fish_base.longitude) if fish_base.longitude else None
                        ),
                        "Address": fish_base.address,
                        "Name": fish_base.name,
                        "Description": fish_base.description
                        or "",  # Пустое описание, если None
                        "PricePerHour": (
                            float(fish_base.price_per_hour)
                            if fish_base.price_per_hour
                            else None
                        ),
                        "EntryPrice": (
                            float(fish_base.entry_price)
                            if fish_base.entry_price
                            else None
                        ),
                    }
                    for fish_base in fish_bases
                ],
            }
            companies_with_bases.append(company_data)

        if not with_bases:
            for company in companies:
                company_data = {
                    "Id": company.pk,
                    "Login": company.login,
                    "Name": company.company_name,
                    "Address": company.company_address,
                    "FirstName": company.first_name,
                    "MiddleName": company.middle_name,
                    "LastName": company.last_name,
                    "FishBases": [],  # Пустой список рыбных баз
                }
                companies_with_bases.append(company_data)

        result = companies_with_bases

    return JsonResponse(result, safe=False)


def search(request):
    if request.method == "GET":
        search = request.GET.get("search", "")
        fish_bases = (
            FishBase.objects.filter(name__icontains=search)
            | FishBase.objects.filter(address__icontains=search)
            | FishBase.objects.filter(fish_in_base__icontains=search)
        )

        return JsonResponse([base.serialize() for base in fish_bases], safe=False)

    return JsonResponse({"error": "GET request required."}, status=400)
