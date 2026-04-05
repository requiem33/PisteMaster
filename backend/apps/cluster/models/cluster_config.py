from django.db import models


class DjangoClusterConfig(models.Model):
    """
    Runtime cluster configuration.

    Stores cluster mode and settings that can be changed at runtime.
    Only one instance should exist (singleton pattern).
    """

    singleton_id = models.IntegerField(default=1, unique=True)
    mode = models.CharField(
        max_length=20, choices=[("single", "Single Node"), ("cluster", "Cluster")], default="single", verbose_name="Cluster Mode"
    )
    node_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Node ID")
    udp_port = models.IntegerField(default=9000, verbose_name="UDP Port")
    api_port = models.IntegerField(default=8000, verbose_name="API Port")
    heartbeat_interval = models.FloatField(default=5.0, verbose_name="Heartbeat Interval")
    heartbeat_timeout = models.FloatField(default=15.0, verbose_name="Heartbeat Timeout")
    sync_interval = models.FloatField(default=3.0, verbose_name="Sync Interval")
    replica_ack_required = models.IntegerField(default=1, verbose_name="Replica ACK Required")
    ack_timeout_ms = models.IntegerField(default=5000, verbose_name="ACK Timeout (ms)")
    master_ip = models.CharField(max_length=50, blank=True, null=True, verbose_name="Master IP")
    is_master = models.BooleanField(default=False, verbose_name="Is Master")
    master_url = models.CharField(max_length=200, blank=True, null=True, verbose_name="Master URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cluster_config"
        verbose_name = "Cluster Configuration"
        verbose_name_plural = "Cluster Configuration"

    @classmethod
    def get_config(cls) -> "DjangoClusterConfig":
        """Get or create the singleton config instance."""
        config, _ = cls.objects.get_or_create(singleton_id=1)
        return config

    def __str__(self):
        return f"Cluster Config ({self.mode})"
