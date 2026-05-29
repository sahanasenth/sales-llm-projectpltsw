from rest_framework import permissions

class IsDirector(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        return role in ('director', 'admin')

class IsSalesManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        return role in ('salesmanager', 'admin')

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin'
