from rest_framework.permissions import BasePermission


def user_in_group(user, group_name):
    return (
        user.is_authenticated
        and user.groups.filter(name=group_name).exists()
    )


class IsDirector(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_superuser
            or user_in_group(request.user, "Director")
        )


class IsSalesManager(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_superuser
            or user_in_group(request.user, "SalesManager")
        )


class IsCRMUser(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated
