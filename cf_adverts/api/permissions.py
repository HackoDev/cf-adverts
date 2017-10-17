from rest_framework.permissions import BasePermission


class HasEstimatePermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.advert.owner.id == request.user.id
