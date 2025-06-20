# Enhanced WebSocket Manager for Automotive Service System

import json
import asyncio
from typing import List, Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}  # Store connection metadata
        self.dashboard_connections: Set[WebSocket] = set()  # Dashboard-specific connections
        self.admin_connections: Set[WebSocket] = set()  # Admin/supervisor connections

    async def connect(self, websocket: WebSocket, connection_type: str = "dashboard", user_info: Dict = None):
        """Connect a WebSocket with type and user information"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # Store connection metadata
        self.connection_info[websocket] = {
            "type": connection_type,
            "connected_at": datetime.utcnow(),
            "user_info": user_info or {},
            "last_ping": datetime.utcnow()
        }

        # Add to specific connection sets
        if connection_type == "dashboard":
            self.dashboard_connections.add(websocket)
        elif connection_type == "admin":
            self.admin_connections.add(websocket)

        logger.info(f"🔗 WebSocket connected [{connection_type}]. Total connections: {len(self.active_connections)}")

        # Send welcome message with connection info
        await self.send_personal_message(json.dumps({
            "type": "connection_established",
            "connection_type": connection_type,
            "server_time": datetime.utcnow().isoformat(),
            "total_connections": len(self.active_connections)
        }), websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket and clean up"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            # Get connection info before removing
            conn_info = self.connection_info.get(websocket, {})
            connection_type = conn_info.get("type", "unknown")

            # Remove from specific sets
            self.dashboard_connections.discard(websocket)
            self.admin_connections.discard(websocket)

            # Remove connection info
            if websocket in self.connection_info:
                del self.connection_info[websocket]

            logger.info(
                f"🔌 WebSocket disconnected [{connection_type}]. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, connection_type: str = None):
        """Broadcast message to all or specific type of connected clients"""
        if not self.active_connections:
            logger.debug("📡 No active connections to broadcast to")
            return

        # Determine target connections
        if connection_type == "dashboard":
            target_connections = list(self.dashboard_connections)
        elif connection_type == "admin":
            target_connections = list(self.admin_connections)
        else:
            target_connections = list(self.active_connections)

        if not target_connections:
            logger.debug(f"📡 No {connection_type or 'active'} connections to broadcast to")
            return

        disconnected = []
        successful_sends = 0

        for connection in target_connections:
            try:
                await connection.send_text(message)
                successful_sends += 1
            except Exception as e:
                logger.error(f"❌ Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

        logger.debug(f"📡 Broadcast sent to {successful_sends}/{len(target_connections)} connections")

    async def broadcast_transcript(self, call_id: str, speaker: str, message: str,
                                   timestamp: str, car_model: str = None, service_type: str = None):
        """Broadcast transcript message to all connected dashboard clients"""
        data = {
            "type": "transcript",
            "call_id": call_id,
            "speaker": speaker,
            "message": message,
            "timestamp": timestamp,
            "car_model": car_model,
            "service_type": service_type
        }
        await self.broadcast(json.dumps(data), connection_type="dashboard")

    async def broadcast_call_status(self, call_id: str, status: str, patient_name: str = None,
                                    car_model: str = None, service_type: str = None, phone_number: str = None):
        """Broadcast call status update to all connected dashboard clients"""
        data = {
            "type": "call_status",
            "call_id": call_id,
            "status": status,
            "patient_name": patient_name,
            "car_model": car_model,
            "service_type": service_type,
            "phone_number": phone_number,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(data), connection_type="dashboard")

    async def broadcast_service_update(self, update_type: str, data: Dict):
        """Broadcast service-specific updates (appointments, customer info, etc.)"""
        message = {
            "type": "service_update",
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message), connection_type="dashboard")

    async def broadcast_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Broadcast system alerts to admin connections"""
        alert_data = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,  # info, warning, error, critical
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(alert_data), connection_type="admin")

    async def send_connection_stats(self, websocket: WebSocket = None):
        """Send connection statistics to specific or all connections"""
        stats = {
            "type": "connection_stats",
            "total_connections": len(self.active_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "admin_connections": len(self.admin_connections),
            "timestamp": datetime.utcnow().isoformat()
        }

        if websocket:
            await self.send_personal_message(json.dumps(stats), websocket)
        else:
            await self.broadcast(json.dumps(stats))

    async def handle_ping_pong(self):
        """Handle ping-pong for connection health monitoring"""
        disconnected = []

        for websocket in list(self.active_connections):
            try:
                # Update last ping time
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_ping"] = datetime.utcnow()

                # Send ping
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(ping_message))

            except Exception as e:
                logger.error(f"❌ Error in ping-pong for connection: {e}")
                disconnected.append(websocket)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def start_periodic_tasks(self):
        """Start periodic maintenance tasks"""

        async def periodic_ping():
            while True:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await self.handle_ping_pong()

        async def periodic_stats():
            while True:
                await asyncio.sleep(60)  # Send stats every minute
                if self.active_connections:
                    await self.send_connection_stats()

        # Start tasks
        asyncio.create_task(periodic_ping())
        asyncio.create_task(periodic_stats())

    def get_connection_info(self, websocket: WebSocket = None) -> Dict:
        """Get information about connections"""
        if websocket:
            return self.connection_info.get(websocket, {})

        return {
            "total_connections": len(self.active_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "admin_connections": len(self.admin_connections),
            "connections": [
                {
                    "type": info.get("type", "unknown"),
                    "connected_at": info.get("connected_at").isoformat() if info.get("connected_at") else None,
                    "last_ping": info.get("last_ping").isoformat() if info.get("last_ping") else None,
                    "user_info": info.get("user_info", {})
                }
                for info in self.connection_info.values()
            ]
        }

    async def broadcast_appointment_confirmation(self, call_id: str, customer_name: str,
                                                 appointment_date: str, appointment_time: str,
                                                 car_model: str, service_type: str):
        """Broadcast appointment confirmation to dashboard"""
        data = {
            "type": "appointment_confirmed",
            "call_id": call_id,
            "customer_name": customer_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "car_model": car_model,
            "service_type": service_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(data), connection_type="dashboard")

    async def broadcast_customer_info(self, call_id: str, customer_data: Dict):
        """Broadcast customer information when call starts"""
        data = {
            "type": "customer_info",
            "call_id": call_id,
            "customer_data": customer_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(data), connection_type="dashboard")

    async def broadcast_service_metrics(self, metrics: Dict):
        """Broadcast service performance metrics"""
        data = {
            "type": "service_metrics",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(data), connection_type="dashboard")

    async def send_error_notification(self, error_type: str, error_message: str,
                                      call_id: str = None, websocket: WebSocket = None):
        """Send error notifications"""
        error_data = {
            "type": "error_notification",
            "error_type": error_type,
            "error_message": error_message,
            "call_id": call_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        if websocket:
            await self.send_personal_message(json.dumps(error_data), websocket)
        else:
            await self.broadcast(json.dumps(error_data), connection_type="admin")

    async def cleanup_stale_connections(self, timeout_minutes: int = 30):
        """Clean up connections that haven't responded to ping"""
        now = datetime.utcnow()
        stale_connections = []

        for websocket, info in self.connection_info.items():
            last_ping = info.get("last_ping")
            if last_ping:
                time_diff = (now - last_ping).total_seconds() / 60
                if time_diff > timeout_minutes:
                    stale_connections.append(websocket)

        for conn in stale_connections:
            logger.warning(f"⚠️ Cleaning up stale connection")
            self.disconnect(conn)

        if stale_connections:
            logger.info(f"🧹 Cleaned up {len(stale_connections)} stale connections")

    async def send_dashboard_update(self, update_data: Dict, websocket: WebSocket = None):
        """Send dashboard-specific updates"""
        message = {
            "type": "dashboard_update",
            **update_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if websocket:
            await self.send_personal_message(json.dumps(message), websocket)
        else:
            await self.broadcast(json.dumps(message), connection_type="dashboard")

    def get_active_calls_count(self) -> int:
        """Get count of currently active calls being monitored"""
        # This could be enhanced to track active calls specifically
        return len([conn for conn in self.connection_info.values()
                    if conn.get("type") == "dashboard"])


# Create a global instance
websocket_manager = WebSocketManager()
