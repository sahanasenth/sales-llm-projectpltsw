from rest_framework.permissions import BasePermission


def get_user_role(user):
    if not (user and user.is_authenticated):
        return None
    if getattr(user, 'is_superuser', False):
        return 'admin'

    profile = getattr(user, 'profile', None)
    profile_role = getattr(profile, 'role', None)
    if profile_role and profile_role != 'sales':
        return profile_role

    role = getattr(user, 'role', None)
    return role or profile_role


def role_in(user, allowed_roles):
    role = get_user_role(user)
    if role == 'admin':
        return True
    return role in allowed_roles


class IsDirector(BasePermission):
    def has_permission(self, request, view):
        return role_in(request.user, ('director',))


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return role_in(request.user, ('manager', 'salesmanager'))


class IsSalesManager(IsManager):
    pass


class IsSalesExecutive(BasePermission):
    def has_permission(self, request, view):
        return role_in(request.user, ('sales_executive', 'sales'))


class IsManagerOrDirector(BasePermission):
    def has_permission(self, request, view):
        return role_in(request.user, ('manager', 'salesmanager', 'director'))


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == 'admin'
