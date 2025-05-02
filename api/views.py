from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Fish, FishBase, StaffProfile, FishingSession
from .permissions import *
from .serializers import *

from rest_framework import filters, generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from djoser.views import UserViewSet as DjoserUserViewSet


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

    def destroy(self, request, *args, **kwargs):
        staff_profile = self.get_object()
        user = staff_profile.user

        try:
            staff_group = Group.objects.get(name="Staff")
            user.groups.remove(staff_group)
        except Group.DoesNotExist:
            pass

        user.is_active = False
        user.save()

        staff_profile.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class FishBaseViewSet(viewsets.ModelViewSet):
    serializer_class = FishBaseSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        return FishBase.objects.filter(company=user.company).order_by("id")

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class FBFishesViewSet(viewsets.ModelViewSet):
    serializer_class = FBFishesSerializer
    permission_classes = [IsEntrepreneur]

    def get_queryset(self):
        user = self.request.user
        base_id = self.kwargs["base_id"]

        fish_base = get_object_or_404(FishBase, pk=base_id)

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


class UploadPhotoView(views.APIView):
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


class SearchFishBaseListView(generics.ListAPIView):
    serializer_class = FishBaseDetailSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "address", "fish__name"]

    def get_queryset(self):
        return FishBase.objects.all().distinct().order_by("id")


class FishingSessionViewSet(viewsets.ViewSet):
    """
    Handles fishing sessions for Fishers (create, list)
    and for Staff (start, close, active_sessions)
    """

    def get_permissions(self):
        if self.action in ["create", "list"]:
            permission_classes = [IsFisher]
        elif self.action in ["start_session", "close_session", "active_sessions"]:
            permission_classes = [IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ["create", "list"]:
            return FisherSessionSerializer
        return StaffSessionSerializer

    def list(self, request):
        """Fisher: list own sessions"""
        sessions = FishingSession.objects.filter(fisher=request.user)
        serializer = self.get_serializer_class()(sessions, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Fisher: create new session"""
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(fisher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def start_session(self, request, pk=None):
        """Staff: start a session"""
        session = get_object_or_404(FishingSession, pk=pk)

        if session.fish_base != request.user.staff_profile.fish_base:
            return Response({"detail": "Not your fish base."}, status=403)

        if session.status != 1:
            return Response(
                {"detail": "Session already started or closed."}, status=400
            )

        session.started_at = timezone.now()
        session.status = 2
        session.staff = request.user
        session.save()

        return Response({"detail": "Session started."})

    @action(detail=True, methods=["post"])
    def close_session(self, request, pk=None):
        """Staff: close a session"""
        session = get_object_or_404(FishingSession, pk=pk)

        if session.fish_base != request.user.staff_profile.fish_base:
            return Response({"detail": "Not your fish base."}, status=403)

        if session.status != 2:
            return Response(
                {"detail": "Only started sessions can be closed."}, status=400
            )

        data = {
            "closed_at": request.data.get("closed_at", timezone.now()),
            "fishes": request.data.get("fishes", []),
            "total_price": request.data.get("total_price", 0),
        }

        serializer = StaffSessionSerializer(
            session, data=data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Session closed."})
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=["get"])
    def active_sessions(self, request):
        """Staff: view unclosed sessions at their fish base"""
        fish_base = request.user.staff_profile.fish_base
        sessions = FishingSession.objects.filter(
            fish_base=fish_base,
            status__in=[FishingSession.Status.CREATED, FishingSession.Status.STARTED],
        )
        serializer = self.get_serializer_class()(sessions, many=True)
        return Response(serializer.data)
