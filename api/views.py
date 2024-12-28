import json
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

from .models import Fish, FishBase, User


# Create your views here.
def sign_in(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            # return HttpResponseRedirect(reverse("index"))
            return JsonResponse({"message": "Success"}, status=200)
        else:
            return JsonResponse(
                {"message": "Invalid email and/or password."},
            )
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
