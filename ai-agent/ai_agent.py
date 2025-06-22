import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import time
import threading
import sys
import random
import uuid
from config.database import get_collection
from datetime import datetime, timezone

class HealthcareAI:
    def __init__(self):
        # Initialize OpenAI client
        load_dotenv()
        token = os.environ.get("GITHUB_TOKEN")
        endpoint = "https://models.github.ai/inference"
        model = "openai/gpt-4o"
        
        self.client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        self.model = model
        self.conversation_history = []
        
        # Patient information tracking - ADDED NAME
        self.patient_info = {
            "name": None,  # NEW FIELD
            "age": None,
            "weight": None,
            "height": None,
            "gender": None,
            "medical_history": None,
            "current_medications": None,
            "allergies": None,
            "emergency_contact": None,
            "chief_complaint": None,
            "location": None,
            "selected_doctor_id": None,  # Track selected doctor ID
            "selected_doctor_name": None,  # Track selected doctor name
            "basic_info_collected": False,
            "symptom_analysis_started": False,
            "info_complete": False,
            "waiting_for_doctor_selection": False  # NEW FLAG
        }
        
        self.ai_name = "Dr. Sara"  # MediConnect AI Assistant name

        # Fake doctors database
        self.doctors = [
            {
                "id": 1,
                "name": "Dr. Michael Johnson",
                "specialty": "General Medicine",
                "experience": "12 years",
                "rating": 4.8,
                "reviews_count": 247,
                "consultation_fee": 45,
                "languages": ["English", "Spanish"],
                "availability": "Available now"
            },
            {
                "id": 2,
                "name": "Dr. Sarah Williams",
                "specialty": "Internal Medicine",
                "experience": "8 years",
                "rating": 4.6,
                "reviews_count": 189,
                "consultation_fee": 55,
                "languages": ["English", "French"],
                "availability": "Available in 30 mins"
            },
            {
                "id": 3,
                "name": "Dr. Ahmed Hassan",
                "specialty": "Emergency Medicine",
                "experience": "15 years",
                "rating": 4.9,
                "reviews_count": 312,
                "consultation_fee": 65,
                "languages": ["English", "Arabic"],
                "availability": "Available now"
            },
            {
                "id": 4,
                "name": "Dr. Emily Chen",
                "specialty": "Family Medicine",
                "experience": "6 years",
                "rating": 4.5,
                "reviews_count": 156,
                "consultation_fee": 40,
                "languages": ["English", "Mandarin"],
                "availability": "Available in 1 hour"
            },
            {
                "id": 5,
                "name": "Dr. Robert Martinez",
                "specialty": "General Practice",
                "experience": "20 years",
                "rating": 4.7,
                "reviews_count": 428,
                "consultation_fee": 50,
                "languages": ["English", "Spanish"],
                "availability": "Available now"
            }
        ]

        # Initialize MongoDB collections
        self.patients_collection = get_collection('PATIENTS')
        self.conversations_collection = get_collection('CONVERSATIONS')
        self.doctor_patients_collection = get_collection('DOCTOR_PATIENTS')  # NEW COLLECTION

        # UPDATED System prompt - now includes name collection
        self.system_prompt = """
You are Dr. Sara, MediConnect's AI healthcare assistant. You specialize in providing medical guidance through a structured approach.

CONVERSATION PHASES:

PHASE 1: BASIC INFO COLLECTION (if not collected)
Collect ALL basic information in ONE response:
"Hello! I'm Dr. Sara from MediConnect. To provide you with the best care, I need some basic information:
1. Your full name
2. Your age
3. Your weight (kg) and height (cm)
4. Your gender
5. Any chronic diseases or ongoing medical conditions
6. Current medications you're taking
7. Any known allergies
8. Emergency contact information

Please provide all this information so I can help you properly."

PHASE 2: CHIEF COMPLAINT (after basic info collected)
Ask: "Now, please tell me what's bothering you today. What symptoms are you experiencing?"

PHASE 3: SYMPTOM ANALYSIS (after chief complaint)
Ask detailed questions ONE BY ONE to understand the symptoms:
- When did it start?
- How severe is it (1-10 scale)?
- What makes it better/worse?
- Any associated symptoms?
- Have you tried anything for it?
- Is it getting better or worse?

ASSESSMENT LEVELS:
- SIMPLE: Common minor issues
- MODERATE: Needs professional evaluation  
- URGENT: Requires immediate medical attention

RESPONSE GUIDELINES:
- Always introduce yourself as Dr. Sara from MediConnect
- Be empathetic and professional
- Use collected patient information for personalized advice
- Ask ONE question at a time during symptom analysis
- Include medical disclaimers
- Prioritize patient safety

DOCTOR REFERRAL:
When symptoms require professional evaluation, say:
"Based on your symptoms and medical profile, I recommend connecting you with one of our qualified doctors. Let me show you our available doctors right now."

IMPORTANT: Do NOT list doctors in your response. The system will handle doctor display separately.

SAFETY: Always err on the side of caution.
"""

    def show_loading_animation(self, duration=3):
        """Show loading animation while AI processes"""
        loading_chars = "|/-\\"
        end_time = time.time() + duration
        
        sys.stdout.write(f"🤖 Dr. Sara is thinking")
        while time.time() < end_time:
            for char in loading_chars:
                sys.stdout.write(f"\r🤖 Dr. Sara is thinking {char}")
                sys.stdout.flush()
                time.sleep(0.2)
        
        sys.stdout.write("\r🤖 Dr. Sara: ")
        sys.stdout.flush()

    def get_patient_info_status(self):
        """Check which patient information is still needed"""
        required_fields = ["name", "age", "weight", "gender", "medical_history", "current_medications", "allergies", "emergency_contact"]
        collected_count = sum(1 for field in required_fields if self.patient_info[field] is not None)
        total_fields = len(required_fields)
        
        return collected_count, total_fields

    def update_patient_info(self, user_message, ai_response):
        """Extract and update patient information from conversation"""
        user_lower = user_message.lower()
        
        # Name detection - IMPROVED
        if not self.patient_info["name"]:
            # Look for patterns like "my name is", "I'm", "call me", etc.
            import re
            name_patterns = [
                r'my name is ([a-zA-Z\s]+)',
                r'i am ([a-zA-Z\s]+)',
                r"i'm ([a-zA-Z\s]+)",
                r'call me ([a-zA-Z\s]+)',
                r'name:\s*([a-zA-Z\s]+)',
                r'^([a-zA-Z\s]+)$'  # If message is just a name
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip().title()
                    # Validate name (contains letters, reasonable length)
                    if len(potential_name) >= 2 and len(potential_name.split()) <= 4 and potential_name.replace(' ', '').isalpha():
                        self.patient_info["name"] = potential_name
                        break

        # Age detection
        if not self.patient_info["age"] and any(word in user_lower for word in ["years old", "age", "born", "year old"]):
            import re
            age_match = re.search(r'\b(\d{1,3})\b', user_message)
            if age_match:
                age = int(age_match.group(1))
                if 1 <= age <= 120:
                    self.patient_info["age"] = age

        # Weight/Height detection
        if not self.patient_info["weight"]:
            import re
            weight_match = re.search(r'(\d+\.?\d*)\s*kg', user_message)
            if weight_match:
                self.patient_info["weight"] = float(weight_match.group(1))
            
            height_match = re.search(r'(\d+\.?\d*)\s*cm', user_message)
            if height_match:
                self.patient_info["height"] = float(height_match.group(1))
        
        # Gender detection
        if not self.patient_info["gender"] and any(word in user_lower for word in ["male", "female", "man", "woman", "boy", "girl"]):
            if any(word in user_lower for word in ["male", "man", "boy"]):
                self.patient_info["gender"] = "Male"
            elif any(word in user_lower for word in ["female", "woman", "girl"]):
                self.patient_info["gender"] = "Female"

        # Medical history detection
        if not self.patient_info["medical_history"] and any(word in user_lower for word in ["diabetes", "hypertension", "asthma", "heart", "cancer", "disease", "condition", "none", "no medical", "history"]):
            self.patient_info["medical_history"] = user_message

        # Medications detection
        if not self.patient_info["current_medications"] and any(word in user_lower for word in ["medication", "medicine", "pills", "tablets", "drug", "taking", "none", "no medication"]):
            self.patient_info["current_medications"] = user_message

        # Allergies detection
        if not self.patient_info["allergies"] and any(word in user_lower for word in ["allergy", "allergic", "reaction", "none", "no allergy"]):
            self.patient_info["allergies"] = user_message

        # Emergency contact detection
        if not self.patient_info["emergency_contact"] and any(word in user_lower for word in ["contact", "phone", "number", "emergency", "family", "friend"]):
            self.patient_info["emergency_contact"] = user_message

        # Chief complaint detection (after basic info is collected)
        if (self.patient_info["basic_info_collected"] and 
            not self.patient_info["chief_complaint"] and 
            any(word in user_lower for word in ["pain", "hurt", "sick", "problem", "issue", "feel", "symptom", "headache", "fever", "cough"])):
            self.patient_info["chief_complaint"] = user_message
            self.patient_info["symptom_analysis_started"] = True

        # Check if basic info is complete - UPDATED to include name
        required_basic_fields = ["name", "age", "weight", "gender", "medical_history", "current_medications", "allergies", "emergency_contact"]
        basic_info_complete = all(self.patient_info[field] is not None for field in required_basic_fields)
        
        if basic_info_complete and not self.patient_info["basic_info_collected"]:
            self.patient_info["basic_info_collected"] = True
        
        if basic_info_complete and self.patient_info["chief_complaint"]:
            self.patient_info["info_complete"] = True

    def should_show_doctors(self, ai_response):
        """Determine if we should show the doctor list based on AI response"""
        doctor_keywords = [
            "recommend connecting you with",
            "connect you with one of our qualified doctors",
            "show you our available doctors",
            "consult with a doctor",
            "see a doctor",
            "medical professional",
            "qualified doctors"
        ]
        
        return any(keyword in ai_response.lower() for keyword in doctor_keywords)

    def display_available_doctors(self):
        """Display available doctors with ratings and fees - ALWAYS WORKS"""
        print("\n" + "="*80)
        print("👨‍⚕️ AVAILABLE DOCTORS - MediConnect")
        print("="*80)
        
        for doctor in self.doctors:
            stars = "⭐" * int(doctor["rating"]) + "☆" * (5 - int(doctor["rating"]))
            print(f"\n{doctor['id']}. {doctor['name']}")
            print(f"   🩺 Specialty: {doctor['specialty']}")
            print(f"   📅 Experience: {doctor['experience']}")
            print(f"   {stars} {doctor['rating']}/5.0 ({doctor['reviews_count']} reviews)")
            print(f"   💰 Consultation Fee: ${doctor['consultation_fee']}")
            print(f"   🗣️  Languages: {', '.join(doctor['languages'])}")
            print(f"   🟢 {doctor['availability']}")
            print("-" * 80)
        
        print("\n🔥 Please select a doctor by entering their number (1-5):")
        self.patient_info["waiting_for_doctor_selection"] = True
        return True

    def handle_doctor_selection(self, user_input):
        """Handle doctor selection and save patient info - IMPROVED"""
        try:
            doctor_choice = int(user_input.strip())
            if 1 <= doctor_choice <= 5:
                selected_doctor = self.doctors[doctor_choice - 1]
                
                # Save selected doctor info
                self.patient_info["selected_doctor_id"] = selected_doctor["id"]
                self.patient_info["selected_doctor_name"] = selected_doctor["name"]
                
                print(f"\n✅ You selected: {selected_doctor['name']}")
                print(f"💰 Consultation Fee: ${selected_doctor['consultation_fee']}")
                print(f"⭐ Rating: {selected_doctor['rating']}/5.0")
                print(f"🟢 {selected_doctor['availability']}")
                
                # SAVE PATIENT INFO TO DATABASE IMMEDIATELY
                self.save_patient_info_to_db()
                self.save_doctor_patient_relationship()
                
                print(f"\n📋 {self.patient_info['name']}'s information has been saved and sent to {selected_doctor['name']}!")
                
                # Ask for consultation type
                print("\nSelect consultation type:")
                print("1. 📹 Video Consultation")
                print("2. 🏥 In-Person Appointment")
                
                consult_choice = input("\nYour choice (1 or 2): ")

                if consult_choice in ['1', '2']:
                    consultation_type = "video" if consult_choice == '1' else "in-person"
                    payment_info = self.generate_payment_link(doctor_choice, consultation_type)
                    
                    if payment_info:
                        print(f"\n💳 PAYMENT DETAILS - MediConnect")
                        print("="*50)
                        print(f"Patient: {self.patient_info['name']}")
                        print(f"Doctor: {payment_info['doctor']['name']}")
                        print(f"Consultation Type: {consultation_type.title()}")
                        print(f"Fee: ${payment_info['doctor']['consultation_fee']}")
                        print(f"Payment ID: {payment_info['payment_id']}")
                        print(f"🔗 Payment Link: {payment_info['payment_link']}")
                        print("="*50)
                        print(f"\n✅ {self.patient_info['name']}, here's your payment link to complete your booking.")
                        print("📋 Your medical information has been shared with the doctor.")
                        
                        self.patient_info["waiting_for_doctor_selection"] = False
                        return True
                    else:
                        print("❌ Error generating payment information. Please try again.")
                        return False
                else:
                    print("❌ Invalid choice. Please select 1 or 2.")
                    return False
            else:
                print("❌ Invalid doctor selection. Please choose a number between 1-5.")
                return False
        except ValueError:
            print("❌ Please enter a valid number.")
            return False

    def generate_payment_link(self, doctor_id, consultation_type="video"):
        """Generate a fake payment link for the selected doctor"""
        doctor = next((d for d in self.doctors if d["id"] == doctor_id), None)
        if doctor:
            # Generate a fake payment link
            payment_id = f"MC{random.randint(100000, 999999)}"
            payment_link = f"https://mediconnect.com/payment/{payment_id}"
            
            return {
                "doctor": doctor,
                "payment_link": payment_link,
                "payment_id": payment_id,
                "consultation_type": consultation_type
            }
        return None

    def get_ai_response(self, user_message):
        """Get response from AI based on user's health concern"""
        try:
            # Show loading animation in a separate thread
            loading_thread = threading.Thread(target=self.show_loading_animation, args=(2,))
            loading_thread.daemon = True
            loading_thread.start()
            
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message
            })
            
            # Create patient info context - UPDATED to include name
            collected_count, total_fields = self.get_patient_info_status()
            patient_context = f"""
PATIENT INFORMATION STATUS:
- Name: {self.patient_info['name'] or 'Not provided'}
- Age: {self.patient_info['age'] or 'Not provided'}
- Weight: {self.patient_info['weight'] or 'Not provided'} kg
- Height: {self.patient_info['height'] or 'Not provided'} cm
- Gender: {self.patient_info['gender'] or 'Not provided'}
- Medical History: {self.patient_info['medical_history'] or 'Not provided'}
- Current Medications: {self.patient_info['current_medications'] or 'Not provided'}
- Allergies: {self.patient_info['allergies'] or 'Not provided'}
- Emergency Contact: {self.patient_info['emergency_contact'] or 'Not provided'}
- Chief Complaint: {self.patient_info['chief_complaint'] or 'Not provided'}

CONVERSATION PHASE STATUS:
- Basic Info Collected: {self.patient_info['basic_info_collected']}
- Symptom Analysis Started: {self.patient_info['symptom_analysis_started']}
- Info Collection Complete: {self.patient_info['info_complete']}
"""
            
            # Create full conversation context
            messages = [
                {"role": "system", "content": self.system_prompt + "\n\n" + patient_context}
            ] + self.conversation_history
            
            response = self.client.chat.completions.create(
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                model=self.model,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Wait for loading animation to finish
            loading_thread.join()
            
            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Update patient info based on conversation
            self.update_patient_info(user_message, ai_response)
            
            return ai_response
            
        except Exception as e:
            return f"I'm sorry, I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"

    def display_patient_summary(self):
        """Display collected patient information - UPDATED"""
        print("\n" + "="*50)
        print("📋 PATIENT INFORMATION SUMMARY - MediConnect")
        print("="*50)
        for key, value in self.patient_info.items():
            if key not in ["info_complete", "basic_info_collected", "symptom_analysis_started", "waiting_for_doctor_selection"] and value:
                formatted_key = key.replace("_", " ").title()
                print(f"{formatted_key}: {value}")
        print("="*50 + "\n")

    def save_patient_info_to_db(self):
        """Save or update patient info in MongoDB - IMPROVED"""
        # Use name + emergency_contact as unique identifier
        patient_id = f"{self.patient_info.get('name', 'unknown')}_{self.patient_info.get('emergency_contact', str(uuid.uuid4())[:8])}"
        
        doc = {
            "patient_id": patient_id,
            "personal_info": {
                "name": self.patient_info.get("name"),
                "age": self.patient_info.get("age"),
                "weight": self.patient_info.get("weight"),
                "height": self.patient_info.get("height"),
                "gender": self.patient_info.get("gender"),
            },
            "medical_info": {
                "medical_history": self.patient_info.get("medical_history"),
                "current_medications": self.patient_info.get("current_medications"),
                "allergies": self.patient_info.get("allergies"),
            },
            "emergency_contact": self.patient_info.get("emergency_contact"),
            "chief_complaint": self.patient_info.get("chief_complaint"),
            "selected_doctor_id": self.patient_info.get("selected_doctor_id"),
            "selected_doctor_name": self.patient_info.get("selected_doctor_name"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        result = self.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": doc},
            upsert=True
        )
        
        print(f"💾 Patient information saved to database!")
        return patient_id

    def save_doctor_patient_relationship(self):
        """Save the doctor-patient relationship - NEW METHOD"""
        if self.patient_info.get("selected_doctor_id") and self.patient_info.get("name"):
            patient_id = f"{self.patient_info.get('name')}_{self.patient_info.get('emergency_contact', str(uuid.uuid4())[:8])}"
            
            doc = {
                "relationship_id": str(uuid.uuid4()),
                "doctor_id": self.patient_info["selected_doctor_id"],
                "doctor_name": self.patient_info["selected_doctor_name"],
                "patient_id": patient_id,
                "patient_name": self.patient_info["name"],
                "patient_age": self.patient_info.get("age"),
                "patient_gender": self.patient_info.get("gender"),
                "chief_complaint": self.patient_info.get("chief_complaint"),
                "assignment_date": datetime.now(timezone.utc),
                "status": "assigned"
            }
            
            self.doctor_patients_collection.insert_one(doc)
            print(f"🏥 {self.patient_info['name']} assigned to {self.patient_info['selected_doctor_name']}!")

    def save_message_to_db(self, role, content):
        """Save each message to the conversations collection"""
        patient_id = f"{self.patient_info.get('name', 'unknown')}_{self.patient_info.get('emergency_contact', str(uuid.uuid4())[:8])}"
        doc = {
            "conversation_id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "patient_name": self.patient_info.get("name"),
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        }
        self.conversations_collection.insert_one(doc)

    def start_conversation(self):
        """Start the healthcare conversation - UPDATED"""
        print("🏥 MediConnect - Healthcare AI Assistant")
        print("=" * 50)
        print("Hello! I'm Dr. Sara, your AI healthcare assistant from MediConnect.")
        print("I'm here to help you with your health concerns and connect you with")
        print("qualified doctors when needed.")
        print("\nLet's get started! Please tell me what's bothering you today.\n")
        
        while True:
            # Check if we're waiting for doctor selection
            if self.patient_info["waiting_for_doctor_selection"]:
                user_input = input("Select doctor (1-5): ").strip()
                if self.handle_doctor_selection(user_input):
                    print("\n" + "-"*50)
                    print("Is there anything else Dr. Sara can help you with?")
                    print("-"*50)
                continue
            
            # Regular input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                if any(self.patient_info.values()):
                    self.display_patient_summary()
                patient_name = self.patient_info.get('name', 'there')
                print(f"Thank you for using MediConnect, {patient_name}! Dr. Sara wishes you good health. Take care!")
                break
            
            if not user_input:
                continue
            
            # Get AI response
            ai_response = self.get_ai_response(user_input)
            
            # Save user and AI messages to database
            self.save_message_to_db("user", user_input)
            self.save_message_to_db("assistant", ai_response)
            
            # Print AI response with delay
            print("\n🤖 Dr. Sara is typing", end="")
            for _ in range(3):
                print(".", end="", flush=True)
                time.sleep(1)
            print("\n" + ai_response)
            
            # Check if AI response suggests showing doctors
            if self.should_show_doctors(ai_response):
                time.sleep(1)  # Brief pause
                self.display_available_doctors()
            
            # Special command to show patient info
            if user_input.lower() == 'info':
                self.display_patient_summary()
                continue

def main():
    """Main function to run the MediConnect healthcare AI assistant"""
    print("-" * 50)
    healthcare_ai = HealthcareAI()
    healthcare_ai.start_conversation()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    except KeyboardInterrupt:
        print("\n\nSession ended. Stay healthy with MediConnect!")