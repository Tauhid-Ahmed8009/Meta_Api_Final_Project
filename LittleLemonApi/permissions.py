from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import Group


class AllowManagerCrudReadAll(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Allow read-only methods (GET, HEAD, OPTIONS)
        manager_group = Group.objects.get(name='Manager')
        return manager_group in request.user.groups.all()


class AllowManagerOnly(BasePermission):
    def has_permission(self, request, view):
        manager_group = Group.objects.get(name='Manager')
        return manager_group in request.user.groups.all()


class AllowDeliveryCrewOnly(BasePermission):
    def has_permission(self, request, view):
        delivery_crew_group = Group.objects.get(name='Delivery crew')
        return delivery_crew_group in request.user.groups.all()


class AllowCustomerOnly(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is not in the "Manager" or "Delivery Crew" group
        return not (request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(
            name='Delivery crew').exists())


