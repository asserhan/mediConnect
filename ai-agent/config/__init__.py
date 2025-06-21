"""
Configuration package for Healthcare AI MVC

This package contains all configuration files and settings for the application.
"""

from .settings import settings, Settings
from .database import get_database, get_collection, db_connection

__all__ = [
    'settings',
    'Settings', 
    'get_database',
    'get_collection',
    'db_connection'
]

# Package version
__version__ = '1.0.0'

# Configuration validation on package import
def validate_config():
    """Validate configuration on package import"""
    print("🔧 Loading Healthcare AI Configuration...")
    
    validation_result = settings.validate_required_env_vars()
    
    if validation_result['is_valid']:
        print("✅ Configuration loaded successfully!")
    else:
        print(f"❌ Configuration errors found!")
        print(f"Missing variables: {validation_result['missing_vars']}")
    
    if validation_result['warnings']:
        for warning in validation_result['warnings']:
            print(f"⚠️  {warning}")
    
    return validation_result['is_valid']

# Run validation when package is imported
_config_valid = validate_config()

if not _config_valid:
    print("Please check your .env file and ensure all required variables are set.")