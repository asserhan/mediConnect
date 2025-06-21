import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import time
import threading
import sys

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
            "info_complete": False
        }
        
        # System prompt for healthcare AI with patient info collection
        self.system_prompt = """
You are a healthcare AI assistant specialized in providing medical guidance. You must collect essential patient information before providing any medical advice.

PATIENT INFO COLLECTION PHASE:
Before giving any medical advice, you MUST collect these details one by one in a conversational manner:
1. Age
2. Weight (kg) and Height (cm) 
3. Gender
4. Current chief complaint (main health concern)
5. Any chronic diseases or medical conditions
6. Current medications being taken
7. Known allergies (food, drug, environmental)
8. Emergency contact information

COLLECTION RULES:
- Ask for ONE piece of information at a time in a friendly, conversational way
- Don't overwhelm the patient with multiple questions at once
- Make the questions feel natural, not like a form
- Explain why you need each piece of information when relevant
- Be patient and understanding if they don't want to share certain information

ASSESSMENT LEVELS (only after info collection):
- SIMPLE: Common minor issues that can be managed with basic advice
- MODERATE: Symptoms needing professional evaluation
- URGENT: Serious symptoms requiring immediate medical attention

RESPONSE GUIDELINES (only after info collection):
- For SIMPLE issues: Provide personalized advice based on their profile
- For MODERATE issues: Give guidance, then offer doctor consultation
- For URGENT issues: Advise immediate medical attention

ALWAYS:
- Be empathetic and professional
- Use the patient's information to personalize your responses
- Include medical disclaimers
- Ask follow-up questions to understand symptoms better
- Consider their age, weight, medical history in your advice

DOCTOR REFERRAL:
When suggesting consultation: "Based on your symptoms and medical profile, I recommend connecting you with a qualified doctor. Would you like a video consultation or in-person appointment?"

SAFETY: Always prioritize patient safety and err on the side of caution.
"""

    def show_loading_animation(self, duration=3):
        """Show loading animation while AI processes"""
        loading_chars = "|/-\\"
        end_time = time.time() + duration
        
        sys.stdout.write("🤖 AI Assistant is thinking")
        while time.time() < end_time:
            for char in loading_chars:
                sys.stdout.write(f"\r🤖 AI Assistant is thinking {char}")
                sys.stdout.flush()
                time.sleep(0.2)
        
        sys.stdout.write("\r🤖 AI Assistant: ")
        sys.stdout.flush()

    def get_patient_info_status(self):
        """Check which patient information is still needed"""
        missing_info = []
        info_mapping = {
            "age": "your age",
            "weight": "your weight and height", 
            "gender": "your gender",
            "chief_complaint": "your main health concern",
            "medical_history": "any chronic conditions or past medical history",
            "current_medications": "current medications you're taking",
            "allergies": "any known allergies",
            "emergency_contact": "emergency contact information"
        }
        
        for key, description in info_mapping.items():
            if not self.patient_info[key]:
                missing_info.append(description)
        
        return missing_info

    def update_patient_info(self, user_message, ai_response):
        """Extract and update patient information from conversation"""
        user_lower = user_message.lower()
        
        # Age detection
        if not self.patient_info["age"] and any(word in user_lower for word in ["years old", "age", "born"]):
            import re
            age_match = re.search(r'\b(\d{1,3})\b', user_message)
            if age_match:
                age = int(age_match.group(1))
                if 1 <= age <= 120:
                    self.patient_info["age"] = age

        # Weight/Height detection
        if not self.patient_info["weight"] and any(word in user_lower for word in ["kg", "weight", "weigh"]):
            import re
            weight_match = re.search(r'(\d+\.?\d*)\s*kg', user_message)
            if weight_match:
                self.patient_info["weight"] = float(weight_match.group(1))
        
        # Gender detection
        if not self.patient_info["gender"] and any(word in user_lower for word in ["male", "female", "man", "woman"]):
            if any(word in user_lower for word in ["male", "man"]):
                self.patient_info["gender"] = "Male"
            elif any(word in user_lower for word in ["female", "woman"]):
                self.patient_info["gender"] = "Female"

        # Chief complaint (main concern)
        if not self.patient_info["chief_complaint"] and any(word in user_lower for word in ["pain", "hurt", "sick", "problem", "issue", "feel"]):
            self.patient_info["chief_complaint"] = user_message

        # Check if basic info is complete
        basic_info_complete = all([
            self.patient_info["age"],
            self.patient_info["gender"],
            self.patient_info["chief_complaint"]
        ])
        
        if basic_info_complete and len(self.get_patient_info_status()) <= 3:
            self.patient_info["info_complete"] = True

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
            patient_context = f"""
PATIENT INFORMATION COLLECTED:
- Age: {self.patient_info['age'] or 'Not provided'}
- Weight: {self.patient_info['weight'] or 'Not provided'} kg
- Height: {self.patient_info['height'] or 'Not provided'} cm
- Gender: {self.patient_info['gender'] or 'Not provided'}
- Chief Complaint: {self.patient_info['chief_complaint'] or 'Not provided'}
- Medical History: {self.patient_info['medical_history'] or 'Not provided'}
- Current Medications: {self.patient_info['current_medications'] or 'Not provided'}
- Allergies: {self.patient_info['allergies'] or 'Not provided'}
- Info Collection Complete: {self.patient_info['info_complete']}

Missing Information: {', '.join(self.get_patient_info_status()) if not self.patient_info['info_complete'] else 'None'}
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

    def handle_doctor_request(self, user_wants_doctor=True):
        """Handle doctor consultation request"""
        if user_wants_doctor:
            return {
                "message": f"Perfect! Based on your profile (Age: {self.patient_info['age']}, Gender: {self.patient_info['gender']}), I'll connect you with an appropriate specialist.\n\nPlease choose:\n\n1. 📹 Video Consultation ($25-50) - Available within 2 hours\n2. 🏥 In-Person Appointment ($40-80) - Available today or tomorrow\n\nWhich would you prefer?",
                "needs_payment": True,
                "consultation_type": "pending"
            }
        else:
            return {
                "message": "No problem! Is there anything else about your health that you'd like to discuss?",
                "needs_payment": False
            }

    def display_patient_summary(self):
        """Display collected patient information"""
        print("\n" + "="*50)
        print("📋 PATIENT INFORMATION SUMMARY")
        print("="*50)
        for key, value in self.patient_info.items():
            if key != "info_complete" and value:
                formatted_key = key.replace("_", " ").title()
                print(f"{formatted_key}: {value}")
        print("="*50 + "\n")

    def start_conversation(self):
        """Start the healthcare conversation"""
        print("🏥 Healthcare AI Assistant")
        print("=" * 40)
        print("Hello! I'm your personal healthcare assistant.")
        print("To provide you with the best possible care, I'll need to gather some important information about you first.")
        print("This helps me give you personalized and safe medical guidance.")
        print("Let's start - what brings you here today? What's your main health concern?\n")
        
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                if any(self.patient_info.values()):
                    self.display_patient_summary()
                print("Thank you for using Healthcare AI Assistant. Take care and stay healthy!")
                break
            
            if not user_input:
                continue
            
            # Check for doctor consultation requests
            if any(keyword in user_input.lower() for keyword in ['yes', 'doctor', 'appointment', 'consultation']):
                if len(self.conversation_history) > 2:  # If there's been a conversation
                    last_ai_response = self.conversation_history[-1]['content'].lower()
                    if 'connect you with' in last_ai_response or 'doctor consultation' in last_ai_response:
                        doctor_response = self.handle_doctor_request(True)
                        print(f"\n🤖 AI Assistant: {doctor_response['message']}")
                        
                        if doctor_response['needs_payment']:
                            choice = input("\nYour choice (1 or 2): ").strip()
                            if choice == '1':
                                print("\n💳 Processing video consultation booking...")
                                print("Payment link: https://yourapp.com/pay/video-consultation")
                                print("Once payment is confirmed, you'll receive a video call link within 2 hours.")
                                print("Your patient information will be shared with the doctor before the consultation.")
                            elif choice == '2':
                                print("\n💳 Processing in-person appointment booking...")
                                print("Payment link: https://yourapp.com/pay/in-person-appointment")
                                print("Once payment is confirmed, you'll receive appointment details via WhatsApp.")
                                print("Your patient information will be shared with the doctor before the appointment.")
                            else:
                                print("Please choose 1 or 2.")
                        continue
            
            # Special command to show patient info
            if user_input.lower() == 'info':
                self.display_patient_summary()
                continue
            
            # Get AI response with loading animation
            ai_response = self.get_ai_response(user_input)
            print(ai_response)
            
            # Show progress on info collection
            if not self.patient_info['info_complete']:
                missing_count = len(self.get_patient_info_status())
                print(f"\n📊 Information Progress: {8-missing_count}/8 collected")
            
            print("-" * 50)

def main():
    """Main function to run the healthcare AI assistant"""
    try:
        healthcare_ai = HealthcareAI()
        healthcare_ai.start_conversation()
    except KeyboardInterrupt:
        print("\n\nSession ended. Take care!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please restart the application.")

if __name__ == "__main__":
    main()