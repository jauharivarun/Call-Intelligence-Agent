from rest_framework.permissions import BasePermission


def is_admin_user(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def user_role(user) -> str:
    """MVP roles: admin can delete/reanalyze; viewer can upload and view all analyses."""
    return "admin" if is_admin_user(user) else "viewer"


class IsAdminRole(BasePermission):
    message = "Admin role required."

    def has_permission(self, request, view):
        return is_admin_user(request.user)
