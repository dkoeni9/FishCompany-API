import json
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from .models import Fish, FishBase, User
from .serializers import FishSerializer


# Create your views here.


def FishApiView(ListAPIView):
    pass


@api_view(["GET", "POST"])
def fish_list(request, format=None):
    if request.method == "GET":
        fishes = Fish.objects.all()
        serializer = FishSerializer(fishes, many=True)
        return JsonResponse(serializer.data, safe=False)

    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_fishes(request):
    if request.method == "GET":
        fishes = Fish.objects.all()

        return JsonResponse([fish.serialize() for fish in fishes], safe=False)

    return JsonResponse({"error": "GET request required."}, status=400)


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


# @csrf_exempt
# def sign_in(request):
#     if request.method == "POST":
@csrf_exempt
def sign_in(request):
    if request.method == "POST":

        #         # Attempt to sign user in
        #         username = request.POST["username"]
        #         password = request.POST["password"]
        #         user = authenticate(request, username=username, password=password)
        data = json.loads(request.body)

        login = data.get("Login")
        password = data.get("Password")
        user = authenticate(request, Login=login, Password=password)


#         # Check if authentication successful
#         if user is not None:
#             login(request, user)
#             # return HttpResponseRedirect(reverse("index"))
#             return JsonResponse({"message": "Success"}, status=200)
#         else:
#             return JsonResponse(
#                 {"message": "Invalid email and/or password."},
#             )
# else:
#     return render(request, "mail/login.html")


# def logout_view(request):
#     logout(request)
#     return HttpResponseRedirect(reverse("index"))


@csrf_exempt
def register_fisher(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method. POST required."}, status=405)

    try:
        data = json.loads(request.body)

        login = data.get("Login")
        password = data.get("Password")
        first_name = data.get("FirstName")
        middle_name = data.get(
            "MiddleName", ""
        )  # Если поле middle_name отсутствует, оно будет пустым
        last_name = data.get("LastName")

        if not login or not password or not first_name or not last_name:
            return JsonResponse({"error": "Missing required fields."}, status=400)

        if User.objects.filter(login=login).exists():
            return JsonResponse({"error": "Login is already in use"}, status=400)

        validate_password(password)

        user = User.objects.create(
            login=login,
            password=password,  # Пароль сохраняется в открытом виде (небезопасно!)
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )

        return JsonResponse({"message": "Registration successful"}, status=201)

    except ValidationError as e:
        return JsonResponse({"error": f"Validation Error: {str(e)}"}, status=400)

    except Exception as e:
        # Логируем ошибку для отладки
        print(f"Error during registration: {str(e)}")
        return JsonResponse(
            {"error": f"An error occurred during registration: {str(e)}"}, status=400
        )


def get_info(request):
    pass


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


# Функция для валидации пароля
def validate_password(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
