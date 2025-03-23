from rest_framework.permissions import BasePermission

# Entrepreneur
# 	⁃	Add employee to fish base
# 	⁃	Add fish to fish base
# 	⁃	Add fish base
# 	⁃	Delete fish base
# 	⁃	View fish bases
# 	⁃	View staff
# 	⁃	View detail fish base

# Staff
# 	⁃	Start reserved session
# 	⁃	Close started session
# 	⁃	View sessions

# Fisherman
# 	⁃	View detail end session
# 	⁃	Reserve session <<include>> Find fish base
# 	⁃	View sessions

# Admin
# 	⁃	View companies
# 	⁃	Registration of company

# Anonymous
# 	⁃	Login
# 	⁃	Find fish base on map


class IsEntrepreneur(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name="Entrepreneur").exists()


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name="Staff").exists()


class IsFisherman(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name="Fisherman").exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name="Admin").exists()
