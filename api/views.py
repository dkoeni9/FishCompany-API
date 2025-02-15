import json
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Fish, FishBase, User


# Create your views here.


# Функция для генерации токена
# Эндпоинт для входа
def authenticate_custom(login, password):
    try:
        # Ищем пользователя по полю login (вместо username)
        user = User.objects.get(login=login)
        # Проверяем пароль
        if user.password == password:  # В реальной жизни пароль нужно хешировать
            return user
        else:
            return None
    except User.DoesNotExist:
        return None


@csrf_exempt
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@csrf_exempt
def sign_in(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method. POST required."}, status=405)

    try:
        # Получаем данные из тела запроса
        data = json.loads(request.body)

        login = data.get("Login")
        password = data.get("Password")

        if not login or not password:
            return JsonResponse(
                {"error": "One or more validation errors occurred"}, status=400
            )

        # Используем кастомную аутентификацию
        user = authenticate_custom(login, password)

        if user is None:
            return JsonResponse({"error": "Login or password incorrect"}, status=400)

        # Генерация токенов
        tokens = get_tokens_for_user(user)

        # Формируем данные для ответа
        user_data = {
            "Id": user.id,
            "Login": user.login,
            "FullName": f"{user.first_name} {user.last_name}",
            "Role": "Fisher",  # Можно добавить логику для определения роли
            "Token": tokens["access"],
        }

        return JsonResponse(user_data, status=200)

    except Exception as e:
        # Логирование ошибки для отладки
        print(f"Error during sign-in: {str(e)}")
        return JsonResponse({"error": "An error occurred during sign-in."}, status=400)


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

    # Получаем параметр WithBases (по умолчанию False)
    with_bases = request.GET.get("WithBases", "false").lower() == "true"

    # Получаем всех пользователей, которые являются компаниями
    companies = User.objects.filter(company_name__isnull=False).distinct()

    # Если нужно загрузить рыбные базы
    if with_bases:
        # Загрузим все рыбные базы с фильтрацией по company_name
        fish_bases_queryset = FishBase.objects.all()

        # Для каждой компании будем фильтровать рыбные базы по company_name
        companies_with_bases = []
        for company in companies:
            # Фильтруем рыбные базы по company_name компании
            fish_bases = fish_bases_queryset.filter(company_name=company.company_name)

            # Добавляем к компании атрибут с рыбными базами
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

        # Если рыбных баз не нужно, просто добавляем компании без фильтрации
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

    # Возвращаем результат в формате JSON
    return JsonResponse(result, safe=False)


# @csrf_exempt
# def sign_in(request):
#     if request.method == "POST":

#         # Attempt to sign user in
#         username = request.POST["username"]
#         password = request.POST["password"]
#         user = authenticate(request, username=username, password=password)

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


# def register(request):
#     if request.method == "POST":
#         email = request.POST["email"]

#         # Ensure password matches confirmation
#         password = request.POST["password"]
#         confirmation = request.POST["confirmation"]
#         if password != confirmation:
#             return render(
#                 request, "mail/register.html", {"message": "Passwords must match."}
#             )

#         # Attempt to create new user
#         try:
#             user = User.objects.create_user(email, email, password)
#             user.save()
#         except IntegrityError as e:
#             print(e)
#             return render(
#                 request,
#                 "mail/register.html",
#                 {"message": "Email address already taken."},
#             )
#         login(request, user)
#         return HttpResponseRedirect(reverse("index"))
#     else:
#         return render(request, "mail/register.html")


def get_fishes(request):
    if request.method == "GET":
        fishes = Fish.objects.all()

        return JsonResponse([fish.serialize() for fish in fishes], safe=False)

    return JsonResponse({"error": "GET request required."}, status=400)


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


# Эндпоинт для регистрации рыболова
@csrf_exempt
def register_fisher(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method. POST required."}, status=405)

    try:
        # Получаем данные из тела запроса
        data = json.loads(request.body)

        # Проверка на обязательные поля
        login = data.get("Login")
        password = data.get("Password")
        first_name = data.get("FirstName")
        middle_name = data.get(
            "MiddleName", ""
        )  # Если поле middle_name отсутствует, оно будет пустым
        last_name = data.get("LastName")

        if not login or not password or not first_name or not last_name:
            return JsonResponse({"error": "Missing required fields."}, status=400)

        # Проверка, что логин не занят
        if User.objects.filter(login=login).exists():
            return JsonResponse({"error": "Login is already in use"}, status=400)

        # Валидация пароля
        validate_password(password)

        # Создаем пользователя
        user = User.objects.create(
            login=login,
            password=password,  # Пароль сохраняется в открытом виде (небезопасно!)
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )

        # Возвращаем успешный ответ
        return JsonResponse({"message": "Registration successful"}, status=201)

    except ValidationError as e:
        return JsonResponse({"error": f"Validation Error: {str(e)}"}, status=400)

    except Exception as e:
        # Логируем ошибку для отладки
        print(f"Error during registration: {str(e)}")
        return JsonResponse(
            {"error": f"An error occurred during registration: {str(e)}"}, status=400
        )
