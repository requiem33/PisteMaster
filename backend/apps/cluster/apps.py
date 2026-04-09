from django.apps import AppConfig


class ClusterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.cluster"
    verbose_name = "Cluster Management"

    def ready(self):
        """Initialize cluster services and register models for sync."""
        # Import models and serializers
        try:
            from backend.apps.cluster.services.sync_manager import sync_manager
            from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
            from backend.apps.fencing_organizer.modules.event.models import DjangoEvent
            from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
            from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
            from backend.apps.fencing_organizer.modules.pool_bout.models import DjangoPoolBout
            from backend.apps.fencing_organizer.modules.piste.models import DjangoPiste
            from backend.apps.fencing_organizer.modules.rule.models import DjangoRule
            from backend.apps.fencing_organizer.modules.event_participant.models import DjangoEventParticipant
            from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment

            from backend.apps.fencing_organizer.modules.tournament.serializers import TournamentSerializer
            from backend.apps.fencing_organizer.modules.event.serializers import EventSerializer
            from backend.apps.fencing_organizer.modules.fencer.serializers import FencerSerializer
            from backend.apps.fencing_organizer.modules.pool.serializers import PoolSerializer
            from backend.apps.fencing_organizer.modules.pool_bout.serializers import PoolBoutSerializer
            from backend.apps.fencing_organizer.modules.piste.serializers import PisteSerializer
            from backend.apps.fencing_organizer.modules.rule.serializers import RuleSerializer
            from backend.apps.fencing_organizer.modules.event_participant.serializers import EventParticipantSerializer
            from backend.apps.fencing_organizer.modules.pool_assignment.serializers import PoolAssignmentSerializer

            import logging

            logger = logging.getLogger(__name__)

            # Map model to serializer and table name
            model_registry = [
                (DjangoTournament, TournamentSerializer, "tournament"),
                (DjangoEvent, EventSerializer, "event"),
                (DjangoFencer, FencerSerializer, "fencer"),
                (DjangoPool, PoolSerializer, "pool"),
                (DjangoPoolBout, PoolBoutSerializer, "pool_bout"),
                (DjangoPiste, PisteSerializer, "piste"),
                (DjangoRule, RuleSerializer, "rule"),
                (DjangoEventParticipant, EventParticipantSerializer, "event_participant"),
                (DjangoPoolAssignment, PoolAssignmentSerializer, "pool_assignment"),
            ]

            # Register each model
            for model_class, serializer_class, table_name in model_registry:
                try:
                    sync_manager.register_model(
                        table_name=table_name,
                        model_class=model_class,
                        serializer_class=serializer_class,
                        version_field="version",
                        last_modified_field="last_modified_at",
                    )
                    logger.info(f"Registered model for sync: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to register {table_name}: {e}")

            logger.info(
                f"SyncManager initialized with {len(sync_manager.get_registered_tables())} models: "
                f"{sync_manager.get_registered_tables()}"
            )

            # Start SyncWorker for follower nodes
            from backend.apps.cluster.services.sync_worker import sync_worker

            try:
                sync_worker.start()
            except Exception as e:
                logger.warning(f"Failed to start SyncWorker: {e}")
        except ImportError as e:
            # Models not available yet (during migrations)
            import logging

            logging.getLogger(__name__).warning(f"Could not register models for sync: {e}")
