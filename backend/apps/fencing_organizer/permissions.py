from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    message = 'Admin permission required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'ADMIN'
        )


class IsSchedulerOrAdmin(permissions.BasePermission):
    message = 'Scheduler or Admin permission required.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'role'):
            return False
        return request.user.role in ('ADMIN', 'SCHEDULER')


class IsTournamentEditor(permissions.BasePermission):
    message = 'You do not have permission to edit this tournament.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return False
        
        if request.user.role == 'ADMIN':
            return True
        
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        if hasattr(obj, 'schedulers'):
            if request.user in obj.schedulers.all():
                return True
        
        return False


class IsTournamentCreatorOrAdmin(permissions.BasePermission):
    message = 'Only Admin or Tournament Creator can manage schedulers.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return False
        
        if request.user.role == 'ADMIN':
            return True
        
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False