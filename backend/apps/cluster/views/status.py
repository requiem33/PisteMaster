import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import models
from django.http import HttpRequest
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState, DjangoClusterConfig
from backend.apps.cluster.services.sync_manager import sync_manager
from backend.apps.fencing_organizer.permissions import IsSchedulerOrAdmin

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Information about a cluster node."""

    node_id: str
    role: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    last_heartbeat: Optional[datetime] = None
    last_sync_id: int = 0
    is_healthy: bool = True


@dataclass
class ClusterStatus:
    """Overall cluster status."""

    mode: str
    is_master: bool
    node_id: str
    master_url: Optional[str] = None
    peers: List[NodeInfo] = field(default_factory=list)
    sync_lag: int = 0
    pending_acks: int = 0
    last_sync_time: Optional[datetime] = None


class ClusterStatusViewSet(viewsets.GenericViewSet):
    """
    Cluster Status API.

    Provides endpoints for monitoring cluster health and status:
    - GET /api/cluster/status/ - Get overall cluster status
    - GET /api/cluster/health/ - Health check endpoint
    - GET /api/cluster/peers/ - List connected peers
    - GET /api/cluster/sync-status/ - Get synchronization status
    """

    permission_classes = [AllowAny]

    def _get_config(self) -> Dict[str, Any]:
        """Get cluster configuration from database first, then fall back to settings."""
        try:
            db_config = DjangoClusterConfig.get_config()
            mode = db_config.mode
            is_master = db_config.is_master

            if mode == "cluster" and not is_master and not db_config.master_url:
                is_master = True
                db_config.is_master = True
                db_config.save()

            return {
                "mode": mode,
                "node_id": db_config.node_id or "",
                "udp_port": db_config.udp_port,
                "api_port": db_config.api_port,
                "heartbeat_interval": db_config.heartbeat_interval,
                "heartbeat_timeout": db_config.heartbeat_timeout,
                "sync_interval": db_config.sync_interval,
                "replica_ack_required": db_config.replica_ack_required,
                "ack_timeout_ms": db_config.ack_timeout_ms,
                "master_ip": db_config.master_ip,
                "is_master": is_master,
                "master_url": db_config.master_url,
            }
        except Exception as e:
            logger.warning(f"Failed to get config from database: {e}")
            return getattr(settings, "CLUSTER_CONFIG", {})

    def _get_node_id(self) -> str:
        """Get current node ID."""
        config = self._get_config()
        return config.get("node_id", "unknown")

    def list(self, request: HttpRequest) -> Response:
        """
        Get overall cluster status.

        Returns:
        - mode: 'single' or 'cluster'
        - isMaster: whether this node is master
        - nodeId: current node identifier
        - masterUrl: URL of master node (if known)
        - syncLag: number of sync log entries not yet applied
        - pendingAcks: number of pending ACKs (master only)
        - lastSyncTime: timestamp of last successful sync
        """
        config = self._get_config()
        node_id = self._get_node_id()

        mode = config.get("mode", "single")
        is_master = config.get("is_master", False)

        sync_lag = 0
        pending_acks = 0
        last_sync_time = None

        if mode == "cluster":
            try:
                if is_master:
                    latest_id = DjangoSyncLog.objects.aggregate(max_id=models.Max("id"))["max_id"] or 0
                    acked_id = sync_manager.ack_queue.get_min_confirmed_id()
                    sync_lag = latest_id - acked_id if latest_id and acked_id else latest_id

                    pending_acks = len(sync_manager.ack_queue.pending_acks)
                else:
                    try:
                        state = DjangoSyncState.objects.get(node_id=node_id)
                        sync_lag = DjangoSyncLog.objects.filter(id__gt=state.last_synced_id).count()
                        last_sync_time = state.last_sync_time
                    except DjangoSyncState.DoesNotExist:
                        sync_lag = DjangoSyncLog.objects.count()

            except Exception as e:
                logger.error(f"Failed to get sync status: {e}")

        result = {
            "mode": mode,
            "isMaster": is_master,
            "nodeId": node_id,
            "masterUrl": config.get("master_url"),
            "syncLag": sync_lag,
            "pendingAcks": pending_acks,
            "lastSyncTime": last_sync_time.isoformat() if last_sync_time else None,
        }

        return Response(result)

    @action(detail=False, methods=["get"])
    def health(self, request: HttpRequest) -> Response:
        """
        Health check endpoint for load balancers and monitoring.

        Returns:
        - status: 'healthy' or 'unhealthy'
        - nodeId: current node identifier
        - mode: 'single' or 'cluster'
        - role: 'master' or 'follower' or 'single'
        - lastSyncId: last applied sync log ID
        """
        config = self._get_config()
        node_id = self._get_node_id()

        mode = config.get("mode", "single")
        is_master = config.get("is_master", False)

        if mode == "single":
            role = "single"
        elif is_master:
            role = "master"
        else:
            role = "follower"

        last_sync_id = 0

        try:
            if is_master:
                last_sync_id = DjangoSyncLog.objects.aggregate(max_id=models.Max("id"))["max_id"] or 0
            else:
                try:
                    state = DjangoSyncState.objects.get(node_id=node_id)
                    last_sync_id = state.last_synced_id
                except DjangoSyncState.DoesNotExist:
                    pass

        except Exception as e:
            logger.error(f"Failed to get last_sync_id: {e}")

        return Response(
            {
                "status": "healthy",
                "nodeId": node_id,
                "mode": mode,
                "role": role,
                "lastSyncId": last_sync_id,
            }
        )

    @action(detail=False, methods=["get"])
    def peers(self, request: HttpRequest) -> Response:
        """
        List connected peer nodes.

        Returns:
        - peers: List of peer node information
        - count: Number of peers
        """
        config = self._get_config()
        node_id = self._get_node_id()
        is_master = config.get("is_master", False)

        peers = []

        if config.get("mode") == "cluster":
            try:
                states = DjangoSyncState.objects.exclude(node_id=node_id)
                for state in states:
                    peers.append(
                        {
                            "nodeId": state.node_id,
                            "lastSyncId": state.last_synced_id,
                            "lastSyncTime": (state.last_sync_time.isoformat() if state.last_sync_time else None),
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to get peers: {e}")

        return Response(
            {
                "peers": peers,
                "count": len(peers),
                "isMaster": is_master,
            }
        )

    @action(detail=False, methods=["get"])
    def sync_status(self, request: HttpRequest) -> Response:
        """
        Get detailed synchronization status.

        Query params:
        - nodeId: Filter by specific node (optional)

        Returns:
        - currentNode: Current node's last synced ID
        - isMaster: whether this node is master
        - followers: List of followers with their sync status
        - uncommittedChanges: Count of changes not yet ACKed by all followers
        """
        config = self._get_config()
        node_id = self._get_node_id()
        is_master = config.get("is_master", False)

        current_node = {"nodeId": node_id, "lastSyncId": 0}

        try:
            if is_master:
                current_node["lastSyncId"] = DjangoSyncLog.objects.aggregate(max_id=models.Max("id"))["max_id"] or 0
            else:
                state = DjangoSyncState.objects.get(node_id=node_id)
                current_node["lastSyncId"] = state.last_synced_id
        except Exception:
            pass

        target_node_id = request.query_params.get("node_id")
        followers = []

        try:
            query = DjangoSyncState.objects.all()
            if target_node_id:
                query = query.filter(node_id=target_node_id)

            for state in query:
                followers.append(
                    {
                        "nodeId": state.node_id,
                        "lastSyncId": state.last_synced_id,
                        "lastSyncTime": (state.last_sync_time.isoformat() if state.last_sync_time else None),
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get follower status: {e}")

        uncommitted_changes = 0
        if is_master and followers:
            try:
                latest_id = DjangoSyncLog.objects.aggregate(max_id=models.Max("id"))["max_id"] or 0
                min_follower_id = min(f["lastSyncId"] for f in followers) if followers else 0
                uncommitted_changes = max(0, latest_id - min_follower_id)
            except Exception:
                pass

        return Response(
            {
                "currentNode": current_node,
                "isMaster": is_master,
                "followers": followers,
                "uncommittedChanges": uncommitted_changes,
            }
        )

    @action(detail=False, methods=["post"])
    def announce(self, request: HttpRequest) -> Response:
        """
        Announce node presence to the cluster.

        Request body:
        - node_id: Node identifier
        - ip: Node IP address
        - port: Node API port
        - is_master: Whether this node is master

        Used for manual cluster configuration when UDP broadcast is not available.
        """
        node_id = request.data.get("node_id")
        ip = request.data.get("ip")
        port = request.data.get("port", 8000)
        is_master = request.data.get("is_master", False)

        if not node_id:
            return Response({"detail": "node_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sync_manager.update_sync_state(node_id, 0)

            logger.info(f"Node announced: id={node_id}, ip={ip}, port={port}, is_master={is_master}")

            return Response(
                {
                    "status": "announced",
                    "node_id": node_id,
                }
            )

        except Exception as e:
            logger.error(f"Failed to process announce: {e}")
            return Response(
                {"detail": "Failed to process announcement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def goodbye(self, request: HttpRequest) -> Response:
        """
        Graceful departure from cluster.

        Request body:
        - node_id: Node identifier leaving the cluster
        """
        node_id = request.data.get("node_id")

        if not node_id:
            return Response({"detail": "node_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            DjangoSyncState.objects.filter(node_id=node_id).delete()

            logger.info(f"Node departed: id={node_id}")

            return Response(
                {
                    "status": "goodbye",
                    "node_id": node_id,
                }
            )

        except Exception as e:
            logger.error(f"Failed to process goodbye: {e}")
            return Response(
                {"detail": "Failed to process departure"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def config(self, request: HttpRequest) -> Response:
        """
        Get current cluster configuration (read-only).

        Returns:
        - mode: 'single' or 'cluster'
        - isMaster: whether this node is master
        - nodeId: current node identifier
        - masterUrl: URL of master node (if configured)
        """
        config = self._get_config()

        return Response(
            {
                "mode": config.get("mode", "single"),
                "isMaster": config.get("is_master", False),
                "nodeId": config.get("node_id", "unknown"),
                "masterUrl": config.get("master_url"),
                "replicaAckRequired": config.get("replica_ack_required", 1),
                "ackTimeoutMs": config.get("ack_timeout_ms", 5000),
            }
        )

    @action(detail=False, methods=["put"], permission_classes=[IsSchedulerOrAdmin])
    def update_config(self, request: HttpRequest) -> Response:
        """
        Update cluster configuration.

        Request body (snake_case for backward compatibility):
        - mode: 'single' or 'cluster'
        - node_id: Node identifier (optional)
        - udp_port: UDP port (optional)
        - api_port: API port (optional)
        - heartbeat_interval: Heartbeat interval in seconds (optional)
        - heartbeat_timeout: Heartbeat timeout in seconds (optional)
        - master_ip: Fixed master IP (optional)

        Returns (camelCase):
        - Updated configuration
        """
        try:
            db_config = DjangoClusterConfig.get_config()

            if "mode" in request.data:
                mode = request.data["mode"]
                if mode not in ("single", "cluster"):
                    return Response(
                        {"detail": "Invalid mode. Must be 'single' or 'cluster'."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                db_config.mode = mode
                if mode == "single":
                    db_config.is_master = False
                    db_config.master_url = None
                    db_config.master_ip = None

            if "node_id" in request.data:
                db_config.node_id = request.data["node_id"]

            if "udp_port" in request.data:
                db_config.udp_port = request.data["udp_port"]

            if "api_port" in request.data:
                db_config.api_port = request.data["api_port"]

            if "heartbeat_interval" in request.data:
                db_config.heartbeat_interval = request.data["heartbeat_interval"]

            if "heartbeat_timeout" in request.data:
                db_config.heartbeat_timeout = request.data["heartbeat_timeout"]

            if "master_ip" in request.data:
                master_ip = request.data["master_ip"]
                db_config.master_ip = master_ip
                if master_ip:
                    db_config.master_url = f"http://{master_ip}:{db_config.api_port}"
                    db_config.is_master = False
                else:
                    db_config.master_url = None

            if db_config.mode == "cluster" and not db_config.master_url and not db_config.master_ip:
                db_config.is_master = True

            db_config.save()

            logger.info(f"Cluster config updated: mode={db_config.mode}, " f"is_master={db_config.is_master}, node_id={db_config.node_id}")

            return Response(
                {
                    "mode": db_config.mode,
                    "isMaster": db_config.is_master,
                    "nodeId": db_config.node_id,
                    "udpPort": db_config.udp_port,
                    "apiPort": db_config.api_port,
                    "heartbeatInterval": db_config.heartbeat_interval,
                    "heartbeatTimeout": db_config.heartbeat_timeout,
                    "masterIp": db_config.master_ip,
                    "masterUrl": db_config.master_url,
                    "syncInterval": db_config.sync_interval,
                    "replicaAckRequired": db_config.replica_ack_required,
                    "ackTimeoutMs": db_config.ack_timeout_ms,
                }
            )

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return Response(
                {"detail": "Failed to update configuration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
