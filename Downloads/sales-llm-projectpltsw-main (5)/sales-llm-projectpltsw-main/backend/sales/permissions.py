from rest_framework.permissions import BasePermission


class IsDirector(BasePermission):
    """
    Allows access only to users with the 'director' role.
    """
    message = "Only directors can access this API."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'director'
        )


class IsManager(BasePermission):
    """
    Allows access only to users with the 'manager' role.
    """
    message = "Only managers can access this API."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'manager'
        )


class IsSalesExecutive(BasePermission):
    """
    Allows access only to users with the 'sales_executive' role.
    """
    message = "Only sales executives can access this API."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'sales_executive'
        )


class IsManagerOrDirector(BasePermission):
    """
    Allows access to users with 'manager' or 'director' role.
    """
    message = "Only managers or directors can access this API."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('manager', 'director')
        )