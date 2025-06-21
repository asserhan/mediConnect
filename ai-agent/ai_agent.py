import os
from openai import OpenAI
from dotenv import load_dotenv
import json

class HealthcareAI:
    def __init__(self):
        # Initialize OpenAI client
        load_dotenv()
        token = os.environ.get("GITHUB_TOKEN")
        # print("---------TOKEN: ", token)
        endpoint = "https://models.github.ai/inference"
        model = "openai/gpt-4.1"
        
        self.client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        self.model = model
        self.conversation_history = []
        self.user_messages_count = 0
        self.max_free_messages = 10
        
        # System prompt for healthcare AI
        self.system_prompt = """
You are a healthcare AI assistant specialized in providing medical guidance. Follow these rules:

1. ASSESSMENT LEVELS:
   - SIMPLE: Common minor issues (cold, headache, minor cuts, basic nutrition questions)
   - MODERATE: Symptoms that need professional evaluation (persistent pain, unusual symptoms, medication questions)
   - URGENT: Serious symptoms requiring immediate medical attention

2. RESPONSE GUIDELINES:
   - For SIMPLE issues: Provide helpful advice, home remedies, when to see a doctor
   - For MODERATE issues: Give basic guidance, then ask if they want doctor consultation
   - For URGENT issues: Advise immediate medical attention and offer emergency consultation

3. ALWAYS:
   - Ask relevant follow-up questions to understand symptoms better
   - Be empathetic and supportive
   - Include disclaimers that you're not replacing professional medical advice
   - Suggest doctor consultation when appropriate
   - End responses with asking if they need anything else

4. DOCTOR REFERRAL FORMAT:
   When suggesting doctor consultation, say: "Would you like me to connect you with a qualified doctor for a video consultation or in-person appointment?"

5. SAFETY: Always err on the side of caution. If unsure, recommend professional consultation.
"""

    def get_ai_response(self, user_message):
        """Get response from AI based on user's health concern"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message
            })
            
            # Create full conversation context
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            
            response = self.client.chat.completions.create(
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                model=self.model,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response
            
        except Exception as e:
            return f"I'm sorry, I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"

    def check_message_limit(self):
        """Check if user has exceeded free message limit"""
        if self.user_messages_count >= self.max_free_messages:
            return False
        return True

    def handle_doctor_request(self, user_wants_doctor=True):
        """Handle doctor consultation request"""
        if user_wants_doctor:
            return {
                "message": "Great! I can help you with that. Please choose an option:\n\n1. 📹 Video Consultation ($25-50) - Available within 2 hours\n2. 🏥 In-Person Appointment ($40-80) - Available today or tomorrow\n\nWhich would you prefer?",
                "needs_payment": True,
                "consultation_type": "pending"
            }
        else:
            return {
                "message": "No problem! Is there anything else I can help you with regarding your health concern?",
                "needs_payment": False
            }

    def start_conversation(self):
        """Start the healthcare conversation"""
        print("🏥 Healthcare AI Assistant")
        print("=" * 40)
        print("Hello! I'm your personal healthcare assistant.")
        print(f"You have {self.max_free_messages - self.user_messages_count} free messages remaining.")
        print("Please describe your health concern, and I'll do my best to help you.\n")
        
        while True:
            # Check message limit
            if not self.check_message_limit():
                print("\n⚠️  You've reached your free message limit.")
                print("To continue chatting, please upgrade to our Basic Plan ($5/month) or pay $0.10 per message.")
                upgrade = input("Would you like to upgrade? (yes/no): ").lower().strip()
                if upgrade == 'yes':
                    print("Redirecting to payment... [Payment link would be generated here]")
                    self.max_free_messages += 50  # Simulate upgrade
                    print("✅ Upgraded successfully! You now have 50 more messages.")
                else:
                    print("Thank you for using our service. Have a healthy day!")
                    break
            
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Thank you for using Healthcare AI Assistant. Take care!")
                break
            
            if not user_input:
                continue
                
            self.user_messages_count += 1
            
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
                            elif choice == '2':
                                print("\n💳 Processing in-person appointment booking...")
                                print("Payment link: https://yourapp.com/pay/in-person-appointment")
                                print("Once payment is confirmed, you'll receive appointment details via WhatsApp.")
                            else:
                                print("Please choose 1 or 2.")
                        continue
            
            # Get AI response
            print("\n🤖 AI Assistant: ", end="")
            ai_response = self.get_ai_response(user_input)
            print(ai_response)
            print(f"\n💬 Messages remaining: {self.max_free_messages - self.user_messages_count}")
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
