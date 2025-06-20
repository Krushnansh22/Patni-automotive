"""
Enhanced Database Service for Automotive Service Call Transcripts
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from .models import (
    CallSession, TranscriptEntry,
    call_session_to_dict, transcript_entry_to_dict,
    dict_to_call_session, dict_to_transcript_entry
)
from settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Enhanced database service for automotive service call transcripts"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.MONGODB_DATABASE]

            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")

            # Create indexes
            await self._create_indexes()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False

    async def _create_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # Call sessions indexes
            await self.database.call_sessions.create_index("call_id", unique=True)
            await self.database.call_sessions.create_index("started_at")
            await self.database.call_sessions.create_index("customer_phone")  # Updated field name
            await self.database.call_sessions.create_index([("started_at", -1)])  # Recent calls first

            # Transcripts indexes
            await self.database.transcripts.create_index("entry_id", unique=True)
            await self.database.transcripts.create_index("call_id")
            await self.database.transcripts.create_index("timestamp")
            await self.database.transcripts.create_index("speaker")
            await self.database.transcripts.create_index([("call_id", 1), ("timestamp", 1)])  # Call timeline
            await self.database.transcripts.create_index([("call_id", 1), ("speaker", 1)])  # Speaker filtering

            # Service-specific indexes
            await self.database.call_sessions.create_index("car_model")  # Filter by car model
            await self.database.call_sessions.create_index("service_type")  # Filter by service type

            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create some indexes: {e}")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 Disconnected from MongoDB")

    # Call Session Operations
    async def create_call_session(self, customer_name: str, customer_phone: str,
                                call_id: str = None, car_model: str = None,
                                service_type: str = None) -> CallSession:
        """Create a new call session with automotive details"""
        try:
            session_data = {
                "customer_name": customer_name,  # Updated field name
                "customer_phone": customer_phone  # Updated field name
            }

            if call_id:
                session_data["call_id"] = call_id
            if car_model:
                session_data["car_model"] = car_model
            if service_type:
                session_data["service_type"] = service_type

            session = CallSession(**session_data)

            # Convert to dict for storage
            session_dict = call_session_to_dict(session)

            await self.database.call_sessions.insert_one(session_dict)
            logger.info(f"✅ Created automotive service call session: {session.call_id}")
            return session
        except Exception as e:
            logger.error(f"❌ Failed to create call session: {e}")
            raise

    async def get_call_session(self, call_id: str) -> Optional[CallSession]:
        """Get call session by ID"""
        try:
            session_data = await self.database.call_sessions.find_one({"call_id": call_id})
            if session_data:
                return dict_to_call_session(session_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get call session: {e}")
            return None

    async def get_calls_by_phone(self, phone_number: str, limit: int = 10) -> List[CallSession]:
        """Get call history for a specific customer phone number"""
        try:
            # Search in both old and new field names for backwards compatibility
            cursor = self.database.call_sessions.find({
                "$or": [
                    {"customer_phone": phone_number},
                    {"patient_phone": phone_number}  # For backwards compatibility
                ]
            }).sort("started_at", -1).limit(limit)

            sessions = []
            async for session_data in cursor:
                sessions.append(dict_to_call_session(session_data))

            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to get calls for phone {phone_number}: {e}")
            return []

    # Transcript Operations
    async def save_transcript(self, call_id: str, speaker: str, message: str) -> TranscriptEntry:
        """Save a transcript entry"""
        try:
            entry = TranscriptEntry(
                call_id=call_id,
                speaker=speaker,
                message=message
            )

            await self.database.transcripts.insert_one(transcript_entry_to_dict(entry))
            logger.info(f"✅ Saved transcript entry for automotive call: {call_id}")
            return entry
        except Exception as e:
            logger.error(f"❌ Failed to save transcript: {e}")
            raise

    async def get_call_transcripts(self, call_id: str) -> List[TranscriptEntry]:
        """Get all transcripts for a call, ordered by timestamp"""
        try:
            cursor = self.database.transcripts.find({"call_id": call_id}).sort("timestamp", 1)
            transcripts = []

            async for transcript_data in cursor:
                transcripts.append(dict_to_transcript_entry(transcript_data))

            return transcripts
        except Exception as e:
            logger.error(f"❌ Failed to get transcripts for call {call_id}: {e}")
            return []

    async def get_transcripts_by_speaker(self, call_id: str, speaker: str) -> List[TranscriptEntry]:
        """Get transcripts for a specific speaker in a call"""
        try:
            cursor = self.database.transcripts.find({
                "call_id": call_id,
                "speaker": speaker
            }).sort("timestamp", 1)

            transcripts = []
            async for transcript_data in cursor:
                transcripts.append(dict_to_transcript_entry(transcript_data))

            return transcripts
        except Exception as e:
            logger.error(f"❌ Failed to get {speaker} transcripts for call {call_id}: {e}")
            return []

    async def get_recent_calls(self, limit: int = 20) -> List[CallSession]:
        """Get recent call sessions"""
        try:
            cursor = self.database.call_sessions.find({}).sort("started_at", -1).limit(limit)
            sessions = []

            async for session_data in cursor:
                sessions.append(dict_to_call_session(session_data))

            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to get recent calls: {e}")
            return []

    # Automotive-specific queries
    async def get_calls_by_service_type(self, service_type: str, limit: int = 50) -> List[CallSession]:
        """Get calls filtered by service type (first_service, regular_service)"""
        try:
            cursor = self.database.call_sessions.find({
                "service_type": service_type
            }).sort("started_at", -1).limit(limit)

            sessions = []
            async for session_data in cursor:
                sessions.append(dict_to_call_session(session_data))

            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to get calls for service type {service_type}: {e}")
            return []

    async def get_calls_by_car_model(self, car_model: str, limit: int = 50) -> List[CallSession]:
        """Get calls filtered by car model"""
        try:
            cursor = self.database.call_sessions.find({
                "car_model": car_model
            }).sort("started_at", -1).limit(limit)

            sessions = []
            async for session_data in cursor:
                sessions.append(dict_to_call_session(session_data))

            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to get calls for car model {car_model}: {e}")
            return []

    async def get_call_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get call statistics for reporting"""
        try:
            # Build date filter
            date_filter = {}
            if start_date or end_date:
                date_filter["started_at"] = {}
                if start_date:
                    date_filter["started_at"]["$gte"] = start_date
                if end_date:
                    date_filter["started_at"]["$lte"] = end_date

            # Aggregate statistics
            pipeline = [
                {"$match": date_filter},
                {
                    "$group": {
                        "_id": None,
                        "total_calls": {"$sum": 1},
                        "first_service_calls": {
                            "$sum": {"$cond": [{"$eq": ["$service_type", "first_service"]}, 1, 0]}
                        },
                        "regular_service_calls": {
                            "$sum": {"$cond": [{"$eq": ["$service_type", "second_service"]}, 1, 0]}
                        }
                    }
                }
            ]

            result = await self.database.call_sessions.aggregate(pipeline).to_list(1)

            if result:
                stats = result[0]
                del stats["_id"]  # Remove the grouping field
                return stats
            else:
                return {
                    "total_calls": 0,
                    "first_service_calls": 0,
                    "regular_service_calls": 0
                }

        except Exception as e:
            logger.error(f"❌ Failed to get call statistics: {e}")
            return {}

    # Data cleanup and maintenance
    async def cleanup_old_data(self, days_old: int = 90):
        """Clean up old call data (optional maintenance function)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Get calls to be deleted
            old_calls = await self.database.call_sessions.find({
                "started_at": {"$lt": cutoff_date}
            }).to_list(None)

            call_ids = [call["call_id"] for call in old_calls]

            if call_ids:
                # Delete transcripts first
                transcript_result = await self.database.transcripts.delete_many({
                    "call_id": {"$in": call_ids}
                })

                # Delete call sessions
                session_result = await self.database.call_sessions.delete_many({
                    "call_id": {"$in": call_ids}
                })

                logger.info(f"🧹 Cleaned up {session_result.deleted_count} old calls and {transcript_result.deleted_count} transcripts")
                return {
                    "deleted_calls": session_result.deleted_count,
                    "deleted_transcripts": transcript_result.deleted_count
                }
            else:
                logger.info("🧹 No old data to clean up")
                return {"deleted_calls": 0, "deleted_transcripts": 0}

        except Exception as e:
            logger.error(f"❌ Failed to cleanup old data: {e}")
            return {"error": str(e)}

    async def update_call_session(self, call_id: str, updates: Dict[str, Any]) -> bool:
        """Update a call session with new information"""
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow()

            result = await self.database.call_sessions.update_one(
                {"call_id": call_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                logger.info(f"✅ Updated call session: {call_id}")
                return True
            else:
                logger.warning(f"⚠️ No updates made to call session: {call_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to update call session {call_id}: {e}")
            return False


# Global database service instance
db_service = DatabaseService()
