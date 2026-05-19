from rest_framework.permissions import BasePermission


class HasRolePermission(BasePermission):
    required_permissions = ()
    message = "You do not have permission to perform this action."

    @classmethod
    def require_any(cls, *permissions):
        return type(
            'RolePermission',
            (cls,),
            {
                'required_permissions': permissions,
            },
        )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_permissions = set(request.user.permissions)
        return any(
            permission in user_permissions
            for permission in self.required_permissions
        )


class IsDirector(BasePermission):
    message = "Only Directors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role_code == request.user.Role.DIRECTOR.value
        )
