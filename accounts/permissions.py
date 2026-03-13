from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOrganizerRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ORGANIZER'


class IsAttendeeRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ATTENDEE'


class IsApprovedOrganizer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'ORGANIZER'
            and request.user.is_organizer_approved
        )


class IsAdminOrApprovedOrganizer(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'ADMIN':
            return True
        return request.user.role == 'ORGANIZER' and request.user.is_organizer_approved
