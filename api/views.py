from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Fish, FishBase, User, StaffProfile
from .permissions import *
from .serializers import *

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class EntrepreneurViewSet(DjoserUserViewSet):
    def get_permissions(self):
        return [IsEntrepreneur()]

    def get_serializer_class(self):
        if self.action == "create":
            return EntrepreneurSerializer
        elif self.action == "destroy":
            return CustomUserDeleteSerializer
        #!
        elif self.action == "list":
            return EntrepreneurSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer, *args, **kwargs):
        super().perform_create(serializer, *args, **kwargs)

        user = serializer.instance
        entrepreneur_group, _ = Group.objects.get_or_create(name="Entrepreneur")
        user.groups.add(entrepreneur_group)


class FisherViewSet(DjoserUserViewSet):
    def perform_create(self, serializer, *args, **kwargs):
        super().perform_create(serializer, *args, **kwargs)

        user = serializer.instance
        fisher_group, _ = Group.objects.get_or_create(name="Fisher")
        user.groups.add(fisher_group)


class CompanyView(generics.RetrieveAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsEntrepreneur]

    def get_object(self):
        return self.request.user.company


class StaffViewSet(DjoserUserViewSet):
    def get_permissions(self):
        return [IsEntrepreneur()]

    def get_queryset(self):
        user = self.request.user

        fish_base_ids = FishBase.objects.filter(company=user.company).values_list(
            "id", flat=True
        )

        return (
            StaffProfile.objects.filter(fish_base_id__in=fish_base_ids)
            .select_related("user", "fish_base")
            .order_by("fish_base_id")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return StaffCreateSerializer
        elif self.action == "destroy":
            return CustomUserDeleteSerializer
        elif self.action == "list":
            return StaffSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer, *args, **kwargs):
        super().perform_create(serializer, *args, **kwargs)

        user = serializer.instance
        staff_group, _ = Group.objects.get_or_create(name="Staff")
        user.groups.add(staff_group)


class FishBaseViewSet(ModelViewSet):
    serializer_class = FishBaseSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        return FishBase.objects.filter(company=user.company).order_by("id")

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class FBFishesViewSet(ModelViewSet):
    serializer_class = FBFishesSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        base_id = self.kwargs["base_id"]

        try:
            fish_base = FishBase.objects.get(id=base_id)
        except FishBase.DoesNotExist:
            raise PermissionDenied("Fish base not found.")

        if fish_base.company != user.company:
            raise PermissionDenied("You do not have access to this fish base.")

        return FishInBase.objects.filter(fish_base_id=base_id)

    def perform_create(self, serializer):
        user = self.request.user
        base_id = self.kwargs["base_id"]

        try:
            fish_base = FishBase.objects.get(id=base_id, company=user.company)
        except FishBase.DoesNotExist:
            raise PermissionDenied(
                "You are not allowed to add fish to a base that does not belong to your company."
            )

        serializer.save(fish_base=fish_base)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        base_id = self.kwargs["base_id"]
        fish_id = self.kwargs["fish_id"]

        try:
            instance = FishInBase.objects.get(
                fish_base__id=base_id, fish_base__company=user.company, fish__id=fish_id
            )
        except FishInBase.DoesNotExist:
            raise PermissionDenied(
                "You are not allowed to remove fish from a base that does not belong to your company."
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FishListView(generics.ListAPIView):
    queryset = Fish.objects.all()
    serializer_class = FishSerializer
    permission_classes = [IsEntrepreneur]


class UploadPhotoView(APIView):
    serializer_class = FishBasePhotoSerializer
    permission_classes = [IsEntrepreneur]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk, *args, **kwargs):
        user = request.user

        try:
            fish_base = FishBase.objects.get(id=pk, company=user.company)
        except FishBase.DoesNotExist:
            raise PermissionDenied("You do not have access to this fish base.")

        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.lower().endswith((".png", ".jpg", ".jpeg")):
            return Response(
                {"error": "Invalid file format. Only .png and .jpg are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(
            instance=fish_base, data={"photo": file}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"Path": fish_base.photo.url}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
