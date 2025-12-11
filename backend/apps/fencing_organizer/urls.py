from django.urls import path, include

urlpatterns = [
    path('fencers/', include('backend.apps.fencing_organizer.modules.fencer.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]