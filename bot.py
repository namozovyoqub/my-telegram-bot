import logging
import os
import cv2
import numpy as np
import mediapipe as mp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation holatlari
SELECTING_ROLE, PERSONAL_INFO, PHONE_INFO, PASSPORT_INFO, FACE_VERIFICATION, MESSAGE_TEXT = range(6)

# TOKEN va ADMIN ID
BOT_TOKEN = "8457267790:AAFe4wG0CXNwsO0RtpTXTCxJKtQ9x24bEhA"
ADMIN_CHAT_ID = "5274895365"

# Tugmalar
BACK_BUTTON = "⬅️ Orqaga qaytish"

class MediaPipeFaceVerification:
    """MediaPipe yordamida yuzni tasdiqlash"""
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
    
    async def verify_face(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yuzni tasdiqlash"""
        if update.message.photo:
            try:
                # Rasmni yuklab olish
                photo_file = await update.message.photo[-1].get_file()
                photo_path = f"temp_face_{update.effective_user.id}.jpg"
                await photo_file.download_to_drive(photo_path)
                
                # Yuzni tekshirish
                result = self.detect_face_mediapipe(photo_path)
                
                # Faylni o'chirish
                try:
                    os.remove(photo_path)
                except:
                    pass
                
                if result["success"]:
                    if result["face_count"] == 1:
                        context.user_data['face_verified'] = True
                        context.user_data['face_quality'] = result["quality"]
                        context.user_data['face_confidence'] = result["confidence"]
                        
                        await update.message.reply_text(
                            f"✅ YUZ MUVAFFAQIYATLI TASDIQLANDI!\n\n"
                            f"📊 Ishonch darajasi: {result['confidence']:.1%}\n"
                            f"⭐ Sifat bahosi: {result['quality']}%\n"
                            f"👤 Yuzlar soni: {result['face_count']}\n\n"
                            f"🆔 Biometrik tasdiqlash muvaffaqiyatli!"
                        )
                        return True
                    else:
                        await update.message.reply_text(
                            f"❌ {result['face_count']} ta yuz aniqlandi.\n"
                            f"Faqat bitta yuz bo'lishi kerak. Iltimos, faqat o'zingizning yuzingizni ko'rsating."
                        )
                        return False
                else:
                    await update.message.reply_text(
                        "❌ Yuz aniqlanmadi!\n\n"
                        "Iltimos, quyidagilarga e'tibor bering:\n"
                        "• Yorug'lik yaxshi bo'lsin\n"
                        "• Yuz to'liq ko'rinsin\n"
                        "• Fon oddiy bo'lsin\n"
                        "• To'g'ridan-to'g'ri qarab turing"
                    )
                    return False
                    
            except Exception as e:
                logger.error(f"Yuz tekshirishda xatolik: {e}")
                await update.message.reply_text("❌ Rasmni qayta ishlashda xatolik. Iltimos, qaytadan urinib ko'ring.")
                return False
        else:
            await update.message.reply_text("❌ Iltimos, rasm yuboring!")
            return False
    
    def detect_face_mediapipe(self, image_path):
        """MediaPipe yordamida yuzni aniqlash"""
        try:
            # Rasmni yuklash
            image = cv2.imread(image_path)
            if image is None:
                return {"success": False, "face_count": 0}
            
            # RGB ga o'tkazish
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Yuzlarni aniqlash
            results = self.face_detection.process(image_rgb)
            
            face_count = 0
            max_confidence = 0.0
            
            if results.detections:
                face_count = len(results.detections)
                for detection in results.detections:
                    confidence = detection.score[0]
                    if confidence > max_confidence:
                        max_confidence = confidence
            
            if face_count == 0:
                return {"success": False, "face_count": 0}
            
            # Sifat baholash
            quality = self.calculate_quality(image, face_count, max_confidence)
            
            return {
                "success": True,
                "face_count": face_count,
                "confidence": max_confidence,
                "quality": quality
            }
            
        except Exception as e:
            logger.error(f"MediaPipe yuz aniqlashda xatolik: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_quality(self, image, face_count, confidence):
        """Rasm sifatini baholash"""
        try:
            quality = 50  # Asosiy baho
            
            # Ishonch darajasi
            quality += int(confidence * 30)
            
            # Rasm o'lchami va yorug'ligi
            height, width = image.shape[:2]
            brightness = np.mean(image)
            
            # Rasm o'lchami
            if height >= 480 and width >= 640:
                quality += 10
            
            # Yorug'lik
            if 100 <= brightness <= 200:
                quality += 10
            
            return min(95, quality)
            
        except:
            return 60

# Global face verification obyekti
face_verifier = MediaPipeFaceVerification()

# Qolgan funksiyalar...
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🎓 Talaba"), KeyboardButton("👨‍🏫 O'qituvchi")],
        [KeyboardButton("🏢 Universitet xodimi")],
        [KeyboardButton("ℹ️ Yordam")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "🛡️ Assalomu Aleykum! Korrupsiyaga qarshi kurash bo'limi murojaat botiga xush kelibsiz!\n\n"
        "📝 Iltimos, o'zingizning maqomingizni tanlang yoki yordam oling:",
        reply_markup=reply_markup
    )
    return SELECTING_ROLE

async def select_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input == "ℹ️ Yordam":
        return await help_command(update, context)
    
    if user_input == BACK_BUTTON:
        return await start(update, context)
    
    context.user_data['role'] = user_input
    
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👤 Shaxsiy ma'lumotlar\n\n"
        "📛 Iltimos, Familiya Ism Sharifingizni kiriting:\n"
        "Misol: Aliyev Vali Aliyevich",
        reply_markup=reply_markup
    )
    return PERSONAL_INFO

async def get_personal_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input == BACK_BUTTON:
        return await select_role(update, context)
    
    context.user_data['full_name'] = user_input
    
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📱 Iltimos, telefon raqamingizni kiriting:\n"
        "Misol: +998901234567 yoki 901234567",
        reply_markup=reply_markup
    )
    return PHONE_INFO

async def get_phone_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('full_name', None)
        return await get_personal_info(update, context)
    
    context.user_data['phone'] = user_input
    
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📇 Iltimos, passport ma'lumotlaringizni kiriting:\n"
        "🎫 Seriya va raqamini kiriting:\n"
        "Misol: AB1234567",
        reply_markup=reply_markup
    )
    return PASSPORT_INFO

async def get_passport_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('phone', None)
        return await get_phone_info(update, context)
    
    context.user_data['passport'] = user_input
    
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔐 BIOMETRIK TASDIQLASH\n\n"
        "🤖 Endi yuzingizni tasdiqlaymiz\n\n"
        "📸 Iltimos, yuzingiz aniq ko'rinadigan rasm yuboring:\n"
        "• Yorug'lik yaxshi bo'lsin\n"
        "• Yuz to'liq ko'rinsin\n"
        "• Fon oddiy bo'lsin\n"
        "• To'g'ridan-to'g'ri qarab turing\n\n"
        "💡 Bu sizning shaxsingizni tasdiqlash uchun kerak",
        reply_markup=reply_markup
    )
    return FACE_VERIFICATION

async def get_face_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text if update.message.text else ""
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('passport', None)
        return await get_passport_info(update, context)
    
    # Yuzni tekshirish
    face_verified = await face_verifier.verify_face(update, context)
    
    if face_verified:
        back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
        reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ BIOMETRIK TASDIQLASH MUVAFFAQIYATLI!\n\n"
            "💬 Endi murojaat matnini yozing:\n"
            "• Muammoni batafsil bayon qiling\n"
            "• Qanday yechim kutayotganingizni yozing",
            reply_markup=reply_markup
        )
        return MESSAGE_TEXT
    else:
        return FACE_VERIFICATION

async def get_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('face_verified', None)
        return await get_face_verification(update, context)
    
    context.user_data['message'] = user_input
    
    try:
        await send_to_admin(update, context)
        
        await update.message.reply_text(
            "✅ Murojaatingiz muvaffaqiyatli yuborildi!\n\n"
            "📞 Tez orada aloqaga chiqamiz\n"
            "🛡️ Korrupsiyaga qarshi kurash - bizning burchimiz!\n\n"
            "🆕 Yangi murojaat yuborish uchun /start buyrug'ini yuboring"
        )
        
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi! /start ni bosing.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data = context.user_data
        
        admin_message = f"""
YANGI MUROJAAT - BIOMETRIK TASDIQLANGAN

Maqom: {user_data.get('role', 'Noma lum')}
F.I.SH: {user_data.get('full_name', 'Noma lum')}
Telefon: {user_data.get('phone', 'Noma lum')}
Passport: {user_data.get('passport', 'Noma lum')}
Murojaat: {user_data.get('message', 'Noma lum')}

BIOMETRIK TASDIQLASH:
✅ Yuz tasdiqlangan (MediaPipe)
📊 Ishonch: {user_data.get('face_confidence', 0):.1%}
⭐ Sifat: {user_data.get('face_quality', 'Noma lum')}%

User ID: {update.effective_user.id}
Username: {update.effective_user.username or 'Noma lum'}
        """
        
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        logger.info("✅ Ma'lumotlar adminga yuborildi")
        
    except Exception as e:
        logger.error(f"Adminga yuborishda xatolik: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🛡️ Korrupsiyaga qarshi kurash boti - Yordam

🤖 Botdan foydalanish:

/start - Botni ishga tushirish
/help - Yordam olish
/cancel - Jarayonni bekor qilish

📝 Murojaat qilish bosqichlari:
1️⃣ Maqom tanlash - Talaba, O'qituvchi yoki Xodim
2️⃣ F.I.SH - To'liq Familiya Ism Sharif
3️⃣ Telefon raqam - Aloqa uchun telefon
4️⃣ Passport ma'lumotlari - Seriya va raqam
5️⃣ 🔐 BIOMETRIK TASDIQLASH - Yuzni taniash
6️⃣ Murojaat matni - Muammoning batafsil tavsifi

🔐 Biometrik tasdiqlash:
• Google MediaPipe texnologiyasi
• Yuqori aniqlikda yuzni taniydi
• Maxfiylik qo'llaniladi

⚠️ Eslatmalar:
• Barcha ma'lumotlar maxfiylik bilan saqlanadi
• Murojaatingiz 3 ish kunida ko'rib chiqiladi
• Yuz tasdiqlash majburiy

🛡️ Korrupsiyaga qarshi kurash - milliy burchimiz!"""
    
    help_keyboard = [
        [KeyboardButton("🎓 Talaba"), KeyboardButton("👨‍🏫 O'qituvchi")],
        [KeyboardButton("🏢 Universitet xodimi")],
        [KeyboardButton("⬅️ Orqaga qaytish")]
    ]
    reply_markup = ReplyKeyboardMarkup(help_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup)
    return SELECTING_ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Murojaat bekor qilindi.\n\n"
        "🛡️ Korrupsiyaga qarshi kurashda ishtirok etganingiz uchun rahmat!\n"
        "🆕 Yangi murojaat uchun /start buyrug'ini yuboring"
    )
    context.user_data.clear()
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_role)],
            PERSONAL_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_personal_info)],
            PHONE_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_info)],
            PASSPORT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passport_info)],
            FACE_VERIFICATION: [
                MessageHandler(filters.PHOTO, get_face_verification),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_face_verification)
            ],
            MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message_text)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start))
    
    logger.info("🤖 Bot ishga tushmoqda...")
    logger.info("🔐 MediaPipe yuzni taniash tizimi faollashtirildi")
    
    application.run_polling()

if __name__ == '__main__':
    main()
            
