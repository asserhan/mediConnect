import logging
import os
import random
import re
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# --- Configuration & Setup ---

# Enable logging to see errors and bot activity
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- IMPORTANT: TOKEN CONFIGURATION ---
# It is STRONGLY recommended to use environment variables instead of pasting keys here.
# For example: TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_TOKEN = "8058616440:AAGU2lHCA2fb1f6o0mcYmfAok8R8UMLDAho" # Your Telegram token
# This key is your GitHub Personal Access Token (PAT)
GITHUB_PAT = "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" # <-- Replace with your actual GitHub PAT

# --- HealthcareAI Class (Corrected for GitHub AI Endpoint) ---

class HealthcareAI:
    def __init__(self):
        """Initializes the HealthcareAI assistant for a single user session."""

        # --- THIS IS THE CORRECTED SECTION for GitHub AI ---
        endpoint_url = "https://models.github.ai/inference"
        # Use the specific model name required by the GitHub service
        self.model = "openai/gpt-4.1"

        # Initialize the OpenAI client with the custom base_url for GitHub
        self.client = OpenAI(
            base_url=endpoint_url,
            api_key=GITHUB_PAT,
        )
        # --- End of corrected section ---

        self.conversation_history = []
        self.patient_info = {
            "age": None, "weight": None, "height": None, "gender": None,
            "medical_history": None, "current_medications": None, "allergies": None,
            "emergency_contact": None, "chief_complaint": None,
            "basic_info_collected": False, "symptom_analysis_started": False, "info_complete": False
        }
        self.ai_name = "Dr. Sara"
        self.doctors = [
            {"id": 1, "name": "Dr. Michael Johnson", "specialty": "General Medicine", "experience": "12 years", "rating": 4.8, "reviews_count": 247, "consultation_fee": 45, "languages": ["English", "Spanish"], "availability": "Available now"},
            {"id": 2, "name": "Dr. Sarah Williams", "specialty": "Internal Medicine", "experience": "8 years", "rating": 4.6, "reviews_count": 189, "consultation_fee": 55, "languages": ["English", "French"], "availability": "Available in 30 mins"},
            {"id": 3, "name": "Dr. Ahmed Hassan", "specialty": "Emergency Medicine", "experience": "15 years", "rating": 4.9, "reviews_count": 312, "consultation_fee": 65, "languages": ["English", "Arabic"], "availability": "Available now"},
            {"id": 4, "name": "Dr. Emily Chen", "specialty": "Family Medicine", "experience": "6 years", "rating": 4.5, "reviews_count": 156, "consultation_fee": 40, "languages": ["English", "Mandarin"], "availability": "Available in 1 hour"},
            {"id": 5, "name": "Dr. Robert Martinez", "specialty": "General Practice", "experience": "20 years", "rating": 4.7, "reviews_count": 428, "consultation_fee": 50, "languages": ["English", "Spanish"], "availability": "Available now"}
        ]
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

    def update_patient_info(self, user_message):
        user_lower = user_message.lower()
        if not self.patient_info["age"] and any(word in user_lower for word in ["years old", "age", "born", "year old"]):
            age_match = re.search(r'\b(\d{1,3})\b', user_message)
            if age_match: self.patient_info["age"] = int(age_match.group(1))
        if not self.patient_info["weight"]:
            weight_match = re.search(r'(\d+\.?\d*)\s*kg', user_message)
            if weight_match: self.patient_info["weight"] = float(weight_match.group(1))
        if not self.patient_info["height"]:
            height_match = re.search(r'(\d+\.?\d*)\s*cm', user_message)
            if height_match: self.patient_info["height"] = float(height_match.group(1))
        if not self.patient_info["gender"]:
            if any(word in user_lower for word in ["male", "man", "boy"]): self.patient_info["gender"] = "Male"
            elif any(word in user_lower for word in ["female", "woman", "girl"]): self.patient_info["gender"] = "Female"
        if not self.patient_info["medical_history"] and any(word in user_lower for word in ["diabetes", "hypertension", "asthma", "heart", "cancer", "disease", "condition", "none", "no medical"]):
            self.patient_info["medical_history"] = user_message
        if not self.patient_info["current_medications"] and any(word in user_lower for word in ["medication", "medicine", "pills", "tablets", "drug", "taking", "none", "no medication"]):
            self.patient_info["current_medications"] = user_message
        if not self.patient_info["allergies"] and any(word in user_lower for word in ["allergy", "allergic", "reaction", "none", "no allergy"]):
            self.patient_info["allergies"] = user_message
        if not self.patient_info["emergency_contact"] and any(word in user_lower for word in ["contact", "phone", "number", "emergency", "family", "friend"]):
            self.patient_info["emergency_contact"] = user_message
        if (self.patient_info["basic_info_collected"] and not self.patient_info["chief_complaint"] and
            any(word in user_lower for word in ["pain", "hurt", "sick", "problem", "issue", "feel", "symptom", "headache", "fever", "cough"])):
            self.patient_info["chief_complaint"] = user_message
            self.patient_info["symptom_analysis_started"] = True
        required_basic_fields = ["age", "weight", "gender", "medical_history", "current_medications", "allergies", "emergency_contact"]
        if all(self.patient_info[field] is not None for field in required_basic_fields) and not self.patient_info["basic_info_collected"]:
            self.patient_info["basic_info_collected"] = True
        if self.patient_info["basic_info_collected"] and self.patient_info["chief_complaint"]:
            self.patient_info["info_complete"] = True

    def get_ai_response(self, user_message):
        try:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.update_patient_info(user_message)
            patient_context = f"""
PATIENT INFO: Age({self.patient_info['age']}), Weight({self.patient_info['weight']}kg), Height({self.patient_info['height']}cm), Gender({self.patient_info['gender']}), History({self.patient_info['medical_history']}), Meds({self.patient_info['current_medications']}), Allergies({self.patient_info['allergies']})
"""
            messages = [{"role": "system", "content": self.system_prompt + "\n\n" + patient_context}] + self.conversation_history
            response = self.client.chat.completions.create(
                messages=messages,
                temperature=0.7,
                model=self.model,
                max_tokens=500
            )
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            logger.error(f"GitHub AI API error: {e}")
            return "I'm sorry, I'm experiencing technical difficulties and cannot process your request right now. Please try again later."

    def display_available_doctors(self):
        response_text = "👨‍⚕️ *AVAILABLE DOCTORS - MediConnect*\n" + "="*30 + "\n\n"
        for doctor in self.doctors:
            stars = "⭐" * int(doctor["rating"]) + "☆" * (5 - int(doctor["rating"]))
            response_text += f"*{doctor['id']}. Dr. {doctor['name']}*\n"
            response_text += f"   🩺 Specialty: {doctor['specialty']}\n"
            response_text += f"   {stars} {doctor['rating']}/5.0 ({doctor['reviews_count']} reviews)\n"
            response_text += f"   💰 Fee: ${doctor['consultation_fee']}\n"
            response_text += f"   🗣️ Languages: {', '.join(doctor['languages'])}\n"
            response_text += f"   🟢 {doctor['availability']}\n" + "-"*30 + "\n"
        response_text += "\nPlease select a doctor by sending their number (e.g., '1', '2', etc.)."
        return response_text

    def generate_payment_link(self, doctor_id, consultation_type="video"):
        doctor = next((d for d in self.doctors if d['id'] == doctor_id), None)
        if not doctor:
            return "❌ Invalid doctor selection. Please try again."
        payment_id = f"MC{random.randint(100000, 999999)}"
        payment_link = f"https://mediconnect.com/payment/{payment_id}"
        response_text = f"💳 *PAYMENT DETAILS - MediConnect*\n" + "="*30 + "\n"
        response_text += f"Doctor: Dr. {doctor['name']}\n"
        response_text += f"Consultation Type: {consultation_type.title()}\n"
        response_text += f"Fee: ${doctor['consultation_fee']}\n"
        response_text += f"Payment ID: `{payment_id}`\n"
        response_text += f"🔗 *Payment Link*: {payment_link}\n" + "="*30 + "\n\n"
        response_text += "✅ Here is your payment link. Your medical information will be shared with the doctor upon confirmation."
        return response_text

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.chat_data['ai_instance'] = HealthcareAI()
    context.chat_data['state'] = None
    ai_instance = context.chat_data['ai_instance']
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    initial_greeting = ai_instance.get_ai_response("Hello")
    await update.message.reply_text(initial_greeting)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if 'ai_instance' not in context.chat_data:
        context.chat_data['ai_instance'] = HealthcareAI()
        context.chat_data['state'] = None
    ai_instance = context.chat_data.get('ai_instance')
    state = context.chat_data.get('state')

    if message.photo:
        await message.reply_text('This is a photo. I can only process text for medical analysis.')
        return
    elif message.document and "pdf" in message.document.mime_type:
        await message.reply_text('This is a PDF. I can only process text for medical analysis.')
        return
    elif message.voice:
        await message.reply_text('This is a voice message. Please describe your symptoms in text.')
        return
    elif not message.text:
        await message.reply_text("I can only handle text messages for our chat.")
        return

    user_text = message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if state == 'awaiting_doctor_selection':
        try:
            doctor_id = int(user_text.strip())
            if 1 <= doctor_id <= len(ai_instance.doctors):
                context.chat_data['selected_doctor_id'] = doctor_id
                context.chat_data['state'] = 'awaiting_consult_type'
                await message.reply_text(
                    f"Great, you've selected Dr. {ai_instance.doctors[doctor_id-1]['name']}.\n\nPlease choose the consultation type:\n1. 📹 Video\n2. 🏥 In-Person\n\nReply with '1' or '2'."
                )
            else:
                await message.reply_text("❌ Invalid number. Please select a doctor from the list (1-5).")
        except ValueError:
            await message.reply_text("❌ That's not a valid number. Please reply with the doctor's number.")
        return

    elif state == 'awaiting_consult_type':
        choice = user_text.strip()
        doctor_id = context.chat_data.get('selected_doctor_id')
        if choice in ['1', '2']:
            consult_type = "video" if choice == '1' else "in-person"
            payment_details = ai_instance.generate_payment_link(doctor_id, consult_type)
            await message.reply_text(payment_details, parse_mode='Markdown')
            context.chat_data['state'] = None
            await message.reply_text("Is there anything else I can help you with today?")
        else:
            await message.reply_text("❌ Invalid choice. Please reply with '1' for Video or '2' for In-Person.")
        return

    ai_response = ai_instance.get_ai_response(user_text)
    if "recommend connecting you with one of our qualified doctors" in ai_response:
        await message.reply_text(ai_response)
        doctor_list_text = ai_instance.display_available_doctors()
        await message.reply_text(doctor_list_text, parse_mode='Markdown')
        context.chat_data['state'] = 'awaiting_doctor_selection'
    else:
        await message.reply_text(ai_response)

def main() -> None:


    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VOICE | filters.Document.PDF, handle_message))
    logger.info("Bot is starting... Press Ctrl-C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
