"""
Database Test Script for Healthcare AI MVC
Run this script to test your MongoDB connection and setup
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import test_database_connection, get_database, get_collection
from config.settings import settings
from datetime import datetime

def test_basic_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        # Test connection
        connection_status = test_database_connection()
        return connection_status['status'] == 'connected'
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_collections_creation():
    """Test collections creation and access"""
    print("\n" + "=" * 60)
    print("📁 TESTING COLLECTIONS")
    print("=" * 60)
    
    try:
        db = get_database()
        
        # Test each collection
        for collection_key, collection_name in settings.COLLECTIONS.items():
            collection = get_collection(collection_key)
            count = collection.count_documents({})
            print(f"✅ {collection_key} ({collection_name}): {count} documents")
        
        return True
    except Exception as e:
        print(f"❌ Collections test failed: {e}")
        return False

def test_crud_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 60)
    print("🔧 TESTING CRUD OPERATIONS")
    print("=" * 60)
    
    try:
        # Test with patients collection
        patients_collection = get_collection('PATIENTS')
        
        # Test document
        test_patient = {
            "patient_id": "test_patient_001",
            "personal_info": {
                "age": 30,
                "gender": "Male",
                "weight": 70.5,
                "height": 175.0
            },
            "medical_info": {
                "medical_history": "No significant medical history",
                "current_medications": "None",
                "allergies": "None"
            },
            "emergency_contact": {
                "name": "John Doe",
                "phone": "+1-555-0123",
                "relationship": "Brother"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # CREATE - Insert test document
        result = patients_collection.insert_one(test_patient)
        print(f"✅ CREATE: Inserted document with ID: {result.inserted_id}")
        
        # READ - Find the document
        found_patient = patients_collection.find_one({"patient_id": "test_patient_001"})
        if found_patient:
            print(f"✅ READ: Found patient: {found_patient['patient_id']}")
        else:
            print("❌ READ: Patient not found")
            return False
        
        # UPDATE - Update the document
        update_result = patients_collection.update_one(
            {"patient_id": "test_patient_001"},
            {"$set": {"personal_info.age": 31, "updated_at": datetime.utcnow()}}
        )
        print(f"✅ UPDATE: Modified {update_result.modified_count} document(s)")
        
        # DELETE - Remove the test document
        delete_result = patients_collection.delete_one({"patient_id": "test_patient_001"})
        print(f"✅ DELETE: Deleted {delete_result.deleted_count} document(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
        return False

def test_indexes():
    """Test database indexes"""
    print("\n" + "=" * 60)
    print("📊 TESTING DATABASE INDEXES")
    print("=" * 60)
    
    try:
        for collection_key, collection_name in settings.COLLECTIONS.items():
            collection = get_collection(collection_key)
            indexes = list(collection.list_indexes())
            print(f"✅ {collection_key}: {len(indexes)} indexes")
            for index in indexes:
                index_name = index.get('name', 'Unknown')
                index_keys = list(index.get('key', {}).keys())
                print(f"   - {index_name}: {', '.join(index_keys)}")
        
        return True
    except Exception as e:
        print(f"❌ Indexes test failed: {e}")
        return False

def test_default_data():
    """Test default data insertion"""
    print("\n" + "=" * 60)
    print("👨‍⚕️ TESTING DEFAULT DATA")
    print("=" * 60)
    
    try:
        doctors_collection = get_collection('DOCTORS')
        doctor_count = doctors_collection.count_documents({})
        
        if doctor_count > 0:
            print(f"✅ Found {doctor_count} doctors in database")
            
            # Show first doctor as example
            first_doctor = doctors_collection.find_one({})
            if first_doctor:
                print(f"   Example: {first_doctor.get('name')} - {first_doctor.get('specialty')}")
        else:
            print("❌ No doctors found in database")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Default data test failed: {e}")
        return False

def run_all_tests():
    """Run all database tests"""
    print("🏥 HEALTHCARE AI - DATABASE TESTS")
    print("=" * 60)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Collections Creation", test_collections_creation),
        ("CRUD Operations", test_crud_operations),
        ("Database Indexes", test_indexes),
        ("Default Data", test_default_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} test failed")
        except Exception as e:
            print(f"\n❌ {test_name} test error: {e}")
            
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your database is ready to use.")
    else:
        print(f"\n⚠️ Some tests failed. Please check the output for details and fix any issues before proceeding.")
    print("=" * 60)
    print("\n🔧 Running all database tests...\n")

if __name__ == "__main__":
    run_all_tests()
