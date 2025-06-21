"""
Database configuration and connection management for Healthcare AI MVC
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import logging
from datetime import datetime
from .settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Singleton database connection class"""
    _instance = None
    _client = None
    _database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get MongoDB configuration from settings
            mongodb_uri = settings.MONGODB_URI
            database_name = settings.DATABASE_NAME
            
            logger.info(f"Connecting to MongoDB: {database_name}")
            
            # Create MongoDB client with timeout settings
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second timeout
                maxPoolSize=50,                 # Maximum connection pool size
                retryWrites=True
            )
            
            # Test the connection
            self._client.admin.command('ping')
            
            # Get database
            self._database = self._client[database_name]
            
            # Create indexes and initialize collections
            self._initialize_database()
            
            logger.info(f"✅ Successfully connected to MongoDB: {database_name}")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout: {e}")
            logger.error("Please check your MongoDB URI and network connection")
            raise
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise
    
    def _initialize_database(self):
        """Initialize database with collections, indexes, and default data"""
        try:
            # Create collections if they don't exist
            existing_collections = self._database.list_collection_names()
            
            for collection_name in settings.COLLECTIONS.values():
                if collection_name not in existing_collections:
                    self._database.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
            
            # Create indexes for better performance
            self._create_indexes()
            
            # Insert default doctors if collection is empty
            self._insert_default_doctors()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Patient collection indexes
            patients_collection = self._database[settings.COLLECTIONS['PATIENTS']]
            patients_collection.create_index("patient_id", unique=True)
            patients_collection.create_index("personal_info.email")
            patients_collection.create_index("created_at")
            patients_collection.create_index("is_active")
            
            # Conversation collection indexes
            conversations_collection = self._database[settings.COLLECTIONS['CONVERSATIONS']]
            conversations_collection.create_index("conversation_id", unique=True)
            conversations_collection.create_index("patient_id")
            conversations_collection.create_index("session_id")
            conversations_collection.create_index("created_at")
            conversations_collection.create_index("conversation_summary.status")
            
            # Doctor collection indexes
            doctors_collection = self._database[settings.COLLECTIONS['DOCTORS']]
            doctors_collection.create_index("doctor_id", unique=True)
            doctors_collection.create_index("specialty")
            doctors_collection.create_index("availability.status")
            doctors_collection.create_index("is_active")
            doctors_collection.create_index("rating")
            
            # Appointment collection indexes
            appointments_collection = self._database[settings.COLLECTIONS['APPOINTMENTS']]
            appointments_collection.create_index("appointment_id", unique=True)
            appointments_collection.create_index("patient_id")
            appointments_collection.create_index("doctor_id")
            appointments_collection.create_index("appointment_details.scheduled_time")
            appointments_collection.create_index("appointment_details.status")
            appointments_collection.create_index("created_at")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to create some indexes: {e}")
    
    def _insert_default_doctors(self):
        """Insert default doctors if doctors collection is empty"""
        try:
            doctors_collection = self._database[settings.COLLECTIONS['DOCTORS']]
            
            # Check if doctors collection is empty
            if doctors_collection.count_documents({}) == 0:
                # Add timestamps to default doctors
                default_doctors = []
                for doctor in settings.DEFAULT_DOCTORS:
                    doctor_data = doctor.copy()
                    doctor_data['created_at'] = datetime.utcnow()
                    doctor_data['updated_at'] = datetime.utcnow()
                    default_doctors.append(doctor_data)
                
                # Insert default doctors
                result = doctors_collection.insert_many(default_doctors)
                logger.info(f"✅ Inserted {len(result.inserted_ids)} default doctors")
            else:
                logger.info("Doctors collection already has data, skipping default insertion")
                
        except Exception as e:
            logger.error(f"Error inserting default doctors: {e}")
    
    def get_database(self):
        """Get database instance"""
        if self._database is None:
            self.connect()
        return self._database
    
    def get_collection(self, collection_name):
        """Get specific collection"""
        database = self.get_database()
        
        # Check if collection_name is a key in COLLECTIONS settings
        if collection_name in settings.COLLECTIONS:
            actual_collection_name = settings.COLLECTIONS[collection_name]
        else:
            actual_collection_name = collection_name
            
        return database[actual_collection_name]
    
    def test_connection(self):
        """Test database connection and return status"""
        try:
            # Test connection
            self._client.admin.command('ping')
            
            # Get database stats
            db_stats = self._database.command('dbStats')
            
            # Get collection info
            collections = self._database.list_collection_names()
            
            return {
                'status': 'connected',
                'database_name': self._database.name,
                'collections': collections,
                'database_size': db_stats.get('dataSize', 0),
                'storage_size': db_stats.get('storageSize', 0),
                'indexes': db_stats.get('indexes', 0),
                'objects': db_stats.get('objects', 0)
            }
            
        except Exception as e:
            return {
                'status': 'disconnected',
                'error': str(e)
            }
    
    def close_connection(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Database connection closed")

# Singleton instance
db_connection = DatabaseConnection()

def get_database():
    """Get database instance"""
    return db_connection.get_database()

def get_collection(collection_name):
    """Get specific collection"""
    return db_connection.get_collection(collection_name)

def test_database_connection():
    """Test and display database connection status"""
    connection_status = db_connection.test_connection()
    
    if connection_status['status'] == 'connected':
        print("✅ Database Connection Status: CONNECTED")
        print(f"📊 Database: {connection_status['database_name']}")
        print(f"📁 Collections: {', '.join(connection_status['collections'])}")
        print(f"📈 Objects: {connection_status['objects']}")
        print(f"💾 Storage: {connection_status['storage_size']} bytes")
    else:
        print("❌ Database Connection Status: DISCONNECTED")
        print(f"Error: {connection_status['error']}")
    
    return connection_status

# Initialize database connection on module import
if __name__ != "__main__":
    try:
        # Test connection when module is imported
        db_connection.get_database()
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")