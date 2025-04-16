from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Fish, FishBase, User
from .permissions import *
from .serializers import *

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class CompanyView(generics.RetrieveAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsEntrepreneur]

    def get_object(self):
        return self.request.user.company


class CompanyViewSet(DjoserUserViewSet):
    serializer_class = CompanySerializer

    def get_permissions(self):
        # change to Admin
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return CompanyCreateSerializer
        elif self.action == "destroy":
            return CustomUserDeleteSerializer
        # elif self.action == "list":
        #     return CompanySerializer

        return super().get_serializer_class()


class StaffViewSet(DjoserUserViewSet):

    def get_permissions(self):
        return [IsEntrepreneur()]

    def get_queryset(self):
        user = self.request.user

        fish_base_ids = FishBase.objects.filter(company=user.company).values_list(
            "id", flat=True
        )

        return User.objects.filter(works_on_fish_base_id__in=fish_base_ids).order_by(
            "works_on_fish_base_id"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return StaffCreateSerializer
        elif self.action == "destroy":
            return CustomUserDeleteSerializer
        elif self.action == "list":
            return StaffSerializer

        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        fish_base_id = data.pop("fish_base_id", None)

        if fish_base_id:
            try:
                fish_base = FishBase.objects.get(id=fish_base_id)

                if fish_base.company != user.company:
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


class FishBaseViewSet(ModelViewSet):
    serializer_class = FishBaseSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        return FishBase.objects.filter(company=user.company).order_by("id")

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class FBFishesView(generics.RetrieveAPIView):
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        return FishBase.objects.filter(company=user.company).order_by("id")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        fish_in_base = instance.fish_in_base or []
        serializer = FBFishesSerializer(fish_in_base, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FishListView(generics.ListAPIView):
    queryset = Fish.objects.all()
    serializer_class = FishSerializer
    permission_classes = [IsEntrepreneur]


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
