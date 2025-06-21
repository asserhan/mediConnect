"""
Application settings and configuration for Healthcare AI MVC
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Settings:
    """Application settings configuration"""
    
    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://asseraouhanane:aZU2i84lamOMnQoW@cluster0.rtdx6ot.mongodb.net/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'healthcare_ai_db')
    
    # Collection Names
    COLLECTIONS = {
        'PATIENTS': 'patients',
        'CONVERSATIONS': 'conversations',
        'DOCTORS': 'doctors',
        'APPOINTMENTS': 'appointments'
    }
    
    # AI Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'openai/gpt-4.1')
    AI_ASSISTANT_NAME = os.getenv('AI_ASSISTANT_NAME', 'Dr. Sara')
    OPENAI_ENDPOINT = "https://models.github.ai/inference"
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Conversation Settings
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '20'))
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
    
    # Patient Information Requirements
    REQUIRED_PATIENT_FIELDS = {
        'personal_info': ['age', 'weight', 'height', 'gender'],
        'medical_info': ['medical_history', 'current_medications', 'allergies'],
        'emergency_contact': ['name', 'phone']
    }
    
    # Doctor Configuration
    DEFAULT_DOCTORS = [
        {
            "doctor_id": "doc_001",
            "name": "Dr. Michael Johnson",
            "specialty": "General Medicine",
            "experience_years": 12,
            "rating": 4.8,
            "reviews_count": 247,
            "consultation_fee": 45.0,
            "languages": ["English", "Spanish"],
            "availability": {
                "status": "available",
                "next_available": None
            },
            "contact_info": {
                "email": "michael.johnson@mediconnect.com",
                "phone": "+1-555-0101"
            },
            "is_active": True
        },
        {
            "doctor_id": "doc_002",
            "name": "Dr. Sarah Williams",
            "specialty": "Internal Medicine",
            "experience_years": 8,
            "rating": 4.6,
            "reviews_count": 189,
            "consultation_fee": 55.0,
            "languages": ["English", "French"],
            "availability": {
                "status": "busy",
                "next_available": None
            },
            "contact_info": {
                "email": "sarah.williams@mediconnect.com",
                "phone": "+1-555-0102"
            },
            "is_active": True
        },
        {
            "doctor_id": "doc_003",
            "name": "Dr. Ahmed Hassan",
            "specialty": "Emergency Medicine",
            "experience_years": 15,
            "rating": 4.9,
            "reviews_count": 312,
            "consultation_fee": 65.0,
            "languages": ["English", "Arabic"],
            "availability": {
                "status": "available",
                "next_available": None
            },
            "contact_info": {
                "email": "ahmed.hassan@mediconnect.com",
                "phone": "+1-555-0103"
            },
            "is_active": True
        },
        {
            "doctor_id": "doc_004",
            "name": "Dr. Emily Chen",
            "specialty": "Family Medicine",
            "experience_years": 6,
            "rating": 4.5,
            "reviews_count": 156,
            "consultation_fee": 40.0,
            "languages": ["English", "Mandarin"],
            "availability": {
                "status": "available",
                "next_available": None
            },
            "contact_info": {
                "email": "emily.chen@mediconnect.com",
                "phone": "+1-555-0104"
            },
            "is_active": True
        },
        {
            "doctor_id": "doc_005",
            "name": "Dr. Robert Martinez",
            "specialty": "General Practice",
            "experience_years": 20,
            "rating": 4.7,
            "reviews_count": 428,
            "consultation_fee": 50.0,
            "languages": ["English", "Spanish"],
            "availability": {
                "status": "available",
                "next_available": None
            },
            "contact_info": {
                "email": "robert.martinez@mediconnect.com",
                "phone": "+1-555-0105"
            },
            "is_active": True
        }
    ]
    
    # Validation Rules
    VALIDATION_RULES = {
        'age': {'min': 1, 'max': 120},
        'weight': {'min': 1.0, 'max': 500.0},
        'height': {'min': 30.0, 'max': 250.0},
        'phone': r'^\+?1?\d{9,15}$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    }
    
    # System Messages
    SYSTEM_MESSAGES = {
        'WELCOME': f"🏥 MediConnect - Healthcare AI Assistant\n{'=' * 50}\nHello! I'm {AI_ASSISTANT_NAME}, your AI healthcare assistant from MediConnect.\nI'm here to help you with your health concerns and connect you with\nqualified doctors when needed.\n",
        'GOODBYE': f"Thank you for using MediConnect! {AI_ASSISTANT_NAME} wishes you good health. Take care!",
        'ERROR': "I'm sorry, I'm experiencing technical difficulties. Please try again later.",
        'INFO_COLLECTION': f"Hello! I'm {AI_ASSISTANT_NAME} from MediConnect. To provide you with the best care, I need some basic information:",
        'DOCTOR_REFERRAL': "Based on your symptoms and medical profile, I recommend connecting you with one of our qualified doctors. Would you like a video consultation or in-person appointment?"
    }
    
    @classmethod
    def validate_required_env_vars(cls) -> Dict[str, Any]:
        """Validate that all required environment variables are set"""
        missing_vars = []
        warnings = []
        
        # Check critical environment variables
        if not cls.GITHUB_TOKEN:
            missing_vars.append('GITHUB_TOKEN')
        
        if not cls.MONGODB_URI or cls.MONGODB_URI == 'mongodb://localhost:27017/':
            warnings.append('MONGODB_URI - Using default local MongoDB')
        
        return {
            'missing_vars': missing_vars,
            'warnings': warnings,
            'is_valid': len(missing_vars) == 0
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'uri': cls.MONGODB_URI,
            'database_name': cls.DATABASE_NAME,
            'collections': cls.COLLECTIONS
        }
    
    @classmethod
    def get_ai_config(cls) -> Dict[str, Any]:
        """Get AI configuration"""
        return {
            'github_token': cls.GITHUB_TOKEN,
            'model': cls.OPENAI_MODEL,
            'endpoint': cls.OPENAI_ENDPOINT,
            'assistant_name': cls.AI_ASSISTANT_NAME
        }

# Create settings instance
settings = Settings()

# Validate configuration on import
validation_result = settings.validate_required_env_vars()
if not validation_result['is_valid']:
    print(f"⚠️  Missing required environment variables: {validation_result['missing_vars']}")
if validation_result['warnings']:
    print(f"⚠️  Configuration warnings: {validation_result['warnings']}")