from django.urls import path, include

urlpatterns = [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('fencers/', include('backend.apps.fencing_organizer.modules.fencer.urls')),
    path('tournament-statuses/', include('backend.apps.fencing_organizer.modules.tournament_status.urls')),
    path('tournaments/', include('backend.apps.fencing_organizer.modules.tournament.urls')),
]
