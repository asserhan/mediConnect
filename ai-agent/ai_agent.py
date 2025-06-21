import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import time
import threading
import sys
import random

class HealthcareAI:
    def __init__(self):
        # Initialize OpenAI client
        load_dotenv()
        token = os.environ.get("GITHUB_TOKEN")
        endpoint = "https://models.github.ai/inference"
        model = "openai/gpt-4.1"
        
        self.client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        self.model = model
        self.conversation_history = []
        
        # Patient information tracking
        self.patient_info = {
            "age": None,
            "weight": None,
            "height": None,
            "gender": None,
            "medical_history": None,
            "current_medications": None,
            "allergies": None,
            "emergency_contact": None,
            "chief_complaint": None,
            "basic_info_collected": False,
            "symptom_analysis_started": False,
            "info_complete": False
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
        
        # System prompt for healthcare AI with patient info collection
        self.system_prompt = """
You are Dr. Sara, MediConnect's AI healthcare assistant. You specialize in providing medical guidance through a structured approach.

CONVERSATION PHASES:

PHASE 1: BASIC INFO COLLECTION (if not collected)
Collect ALL basic information in ONE response:
"Hello! I'm Dr. Sara from MediConnect. To provide you with the best care, I need some basic information:
1. Your age
2. Your weight (kg) and height (cm)
3. Your gender
4. Any chronic diseases or ongoing medical conditions
5. Current medications you're taking
6. Any known allergies
7. Emergency contact information

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
"Based on your symptoms and medical profile, I recommend connecting you with one of our qualified doctors. Would you like a video consultation or in-person appointment?"

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
        required_fields = ["age", "weight", "gender", "medical_history", "current_medications", "allergies", "emergency_contact"]
        collected_count = sum(1 for field in required_fields if self.patient_info[field] is not None)
        total_fields = len(required_fields)
        
        return collected_count, total_fields

    def update_patient_info(self, user_message, ai_response):
        """Extract and update patient information from conversation"""
        user_lower = user_message.lower()
        
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
        if not self.patient_info["medical_history"] and any(word in user_lower for word in ["diabetes", "hypertension", "asthma", "heart", "cancer", "disease", "condition", "none", "no medical"]):
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

        # Check if basic info is complete
        required_basic_fields = ["age", "weight", "gender", "medical_history", "current_medications", "allergies", "emergency_contact"]
        basic_info_complete = all(self.patient_info[field] is not None for field in required_basic_fields)
        
        if basic_info_complete and not self.patient_info["basic_info_collected"]:
            self.patient_info["basic_info_collected"] = True
        
        if basic_info_complete and self.patient_info["chief_complaint"]:
            self.patient_info["info_complete"] = True

    def display_available_doctors(self):
        """Display available doctors with ratings and fees"""
        print("\n" + "="*80)
        print("👨‍⚕️ AVAILABLE DOCTORS - MediConnect")
        print("="*80)
        
        for doctor in self.doctors:
            stars = "⭐" * int(doctor["rating"]) + "☆" * (5 - int(doctor["rating"]))
            print(f"\n{doctor['id']}. Dr. {doctor['name']}")
            print(f"   🩺 Specialty: {doctor['specialty']}")
            print(f"   📅 Experience: {doctor['experience']}")
            print(f"   {stars} {doctor['rating']}/5.0 ({doctor['reviews_count']} reviews)")
            print(f"   💰 Consultation Fee: ${doctor['consultation_fee']}")
            print(f"   🗣️  Languages: {', '.join(doctor['languages'])}")
            print(f"   🟢 {doctor['availability']}")
            print("-" * 80)
        
        print("\nPlease select a doctor by entering their number (1-5):")
        return True

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
            
            # Create patient info context
            collected_count, total_fields = self.get_patient_info_status()
            patient_context = f"""
PATIENT INFORMATION STATUS:
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

    def handle_doctor_selection(self, user_input):
        """Handle doctor selection and payment"""
        try:
            doctor_choice = int(user_input.strip())
            if 1 <= doctor_choice <= 5:
                selected_doctor = self.doctors[doctor_choice - 1]
                
                print(f"\n✅ You selected: {selected_doctor['name']}")
                print(f"💰 Consultation Fee: ${selected_doctor['consultation_fee']}")
                print(f"⭐ Rating: {selected_doctor['rating']}/5.0")
                print(f"🟢 {selected_doctor['availability']}")
                
                # Ask for consultation type
                print("\nSelect consultation type:")
                print("1. 📹 Video Consultation")
                print("2. 🏥 In-Person Appointment")
                
                consult_choice = input("\nYour choice (1 or 2): ").strip()
                
                if consult_choice in ['1', '2']:
                    consultation_type = "video" if consult_choice == '1' else "in-person"
                    payment_info = self.generate_payment_link(doctor_choice, consultation_type)
                    
                    if payment_info:
                        print(f"\n💳 PAYMENT DETAILS - MediConnect")
                        print("="*50)
                        print(f"Doctor: {payment_info['doctor']['name']}")
                        print(f"Consultation Type: {consultation_type.title()}")
                        print(f"Fee: ${payment_info['doctor']['consultation_fee']}")
                        print(f"Payment ID: {payment_info['payment_id']}")
                        print(f"🔗 Payment Link: {payment_info['payment_link']}")
                        print("="*50)
                        print("\n✅ Here's your payment link to complete your booking.")
                        print("📋 Your medical information will be shared with the doctor.")
                        
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

    def display_patient_summary(self):
        """Display collected patient information"""
        print("\n" + "="*50)
        print("📋 PATIENT INFORMATION SUMMARY - MediConnect")
        print("="*50)
        for key, value in self.patient_info.items():
            if key not in ["info_complete", "basic_info_collected", "symptom_analysis_started"] and value:
                formatted_key = key.replace("_", " ").title()
                print(f"{formatted_key}: {value}")
        print("="*50 + "\n")

    def start_conversation(self):
        """Start the healthcare conversation"""
        print("🏥 MediConnect - Healthcare AI Assistant")
        print("=" * 50)
        print("Hello! I'm Dr. Sara, your AI healthcare assistant from MediConnect.")
        print("I'm here to help you with your health concerns and connect you with")
        print("qualified doctors when needed.")
        print("\nLet's get started! Please tell me what's bothering you today.\n")
        
        doctor_selection_mode = False
        
        while True:
            # Get user input
            if doctor_selection_mode:
                user_input = input("Select doctor (1-5): ").strip()
            else:
                user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                if any(self.patient_info.values()):
                    self.display_patient_summary()
                print("Thank you for using MediConnect! Dr. Sara wishes you good health. Take care!")
                break
            
            if not user_input:
                continue
            
            # Handle doctor selection mode
            if doctor_selection_mode:
                if self.handle_doctor_selection(user_input):
                    doctor_selection_mode = False
                    print("\n" + "-"*50)
                    print("Is there anything else Dr. Sara can help you with?")
                    print("-"*50)
                continue
            
            # Check for doctor consultation requests
            if any(keyword in user_input.lower() for keyword in ['yes', 'doctor', 'appointment', 'consultation']):
                if len(self.conversation_history) > 2:  # If there's been a conversation
                    last_ai_response = self.conversation_history[-1]['content'].lower()
                    if 'connect you with' in last_ai_response or 'doctor consultation' in last_ai_response:
                        self.display_available_doctors()
                        doctor_selection_mode = True
                        continue
            
            # Special command to show patient info
            if user_input.lower() == 'info':
                self.display_patient_summary()
                continue
            
            # Get AI response with loading animation
            ai_response = self.get_ai_response(user_input)
            print(ai_response)
            
            print("-" * 50)

def main():
    """Main function to run the MediConnect healthcare AI assistant"""
    try:
        print("🚀 Starting MediConnect Healthcare AI Assistant...")
        healthcare_ai = HealthcareAI()
        healthcare_ai.start_conversation()
    except KeyboardInterrupt:
        print("\n\nSession ended. Stay healthy with MediConnect!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please restart MediConnect application.")

if __name__ == "__main__":
    main()