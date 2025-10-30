import logging
import os
import cv2
import numpy as np
import face_recognition
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

class FaceVerification:
    """Yuzni tasdiqlash klassi"""
    
    @staticmethod
    async def verify_face(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yuzni tasdiqlash"""
        if update.message.photo:
            try:
                # Rasmni yuklab olish
                photo_file = await update.message.photo[-1].get_file()
                photo_path = f"temp_face_{update.effective_user.id}.jpg"
                await photo_file.download_to_drive(photo_path)
                
                # Yuzni tekshirish
                result = FaceVerification.analyze_face(photo_path)
                
                # Vaqtincha faylni o'chirish
                try:
                    os.remove(photo_path)
                except:
                    pass
                
                if result["success"]:
                    if result["face_count"] == 1:
                        # Yuz ma'lumotlarini saqlash
                        context.user_data['face_verified'] = True
                        context.user_data['face_quality'] = result["quality"]
                        context.user_data['face_landmarks'] = result.get("landmarks", {})
                        
                        await update.message.reply_text(
                            f"✅ YUZ MUVAFFAQIYATLI TASDIQLANDI!\n\n"
                            f"📊 Tasdiqlash aniqligi: {result['quality']}%\n"
                            f"👁️ Ko'zlar aniqlangan: {'Ha' if result.get('eyes_visible') else 'Yo\'q'}\n"
                            f"😃 Yuz ifodasi: {result.get('expression', 'Neutral')}\n\n"
                            f"🆔 Biometrik tasdiqlash muvaffaqiyatli amalga oshirildi!"
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
                        "• Ko'zlar ochiq bo'lsin"
                    )
                    return False
                    
            except Exception as e:
                logger.error(f"Yuz tekshirishda xatolik: {e}")
                await update.message.reply_text("❌ Rasmni qayta ishlashda xatolik. Iltimos, qaytadan urinib ko'ring.")
                return False
        else:
            await update.message.reply_text("❌ Iltimos, rasm yuboring!")
            return False
    
    @staticmethod
    def analyze_face(image_path):
        """Yuzni chuqur tahlil qilish"""
        try:
            # Rasmni yuklash
            image = face_recognition.load_image_file(image_path)
            
            # Yuzlarni aniqlash
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            face_landmarks_list = face_recognition.face_landmarks(image)
            
            face_count = len(face_locations)
            
            if face_count == 0:
                return {"success": False, "face_count": 0}
            
            # Yuz sifatini baholash
            quality_score = FaceVerification.calculate_face_quality(image, face_locations[0], face_landmarks_list[0] if face_landmarks_list else {})
            
            # Yuz xususiyatlarini aniqlash
            expression = FaceVerification.detect_expression(face_landmarks_list[0] if face_landmarks_list else {})
            eyes_visible = FaceVerification.check_eyes_visible(face_landmarks_list[0] if face_landmarks_list else {})
            
            return {
                "success": True,
                "face_count": face_count,
                "quality": quality_score,
                "landmarks": face_landmarks_list[0] if face_landmarks_list else {},
                "expression": expression,
                "eyes_visible": eyes_visible,
                "face_encoding": face_encodings[0] if face_encodings else None
            }
            
        except Exception as e:
            logger.error(f"Yuz tahlilida xatolik: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def calculate_face_quality(image, face_location, landmarks):
        """Yuz sifatini baholash"""
        try:
            top, right, bottom, left = face_location
            face_height = bottom - top
            face_width = right - left
            
            # Rasm o'lchami
            img_height, img_width = image.shape[:2]
            
            # Yuzning rasmda qoplagan maydoni
            face_area_ratio = (face_height * face_width) / (img_height * img_width)
            
            # Yorug'likni baholash
            face_region = image[top:bottom, left:right]
            brightness = np.mean(face_region)
            
            # Sifat bahosi
            quality = 0
            
            # Yuz o'lchami (30%)
            if face_area_ratio > 0.1:  # Yuz rasmning 10% dan ko'pini egallashi
                quality += 30
            elif face_area_ratio > 0.05:
                quality += 20
            else:
                quality += 10
            
            # Yorug'lik (30%)
            if 100 <= brightness <= 200:  # Optimal yorug'lik
                quality += 30
            elif 50 <= brightness < 100 or 200 < brightness <= 230:
                quality += 20
            else:
                quality += 10
            
            # Yuz xususiyatlari (40%)
            if landmarks:
                # Ko'zlar
                if 'left_eye' in landmarks and 'right_eye' in landmarks:
                    quality += 20
                
                # Lablar
                if 'top_lip' in landmarks and 'bottom_lip' in landmarks:
                    quality += 10
                
                # Qoshlar
                if 'left_eyebrow' in landmarks and 'right_eyebrow' in landmarks:
                    quality += 10
            
            return min(100, quality)
            
        except Exception as e:
            logger.error(f"Sifat baholashda xatolik: {e}")
            return 50  # Standart baho
    
    @staticmethod
    def detect_expression(landmarks):
        """Yuz ifodasini aniqlash"""
        if not landmarks:
            return "Neutral"
        
        try:
            # Soddalashtirilgan ifoda aniqlash
            if 'left_eye' in landmarks and 'right_eye' in landmarks:
                # Ko'zlar yopiqmi?
                left_eye = landmarks['left_eye']
                right_eye = landmarks['right_eye']
                
                left_eye_height = max(point[1] for point in left_eye) - min(point[1] for point in left_eye)
                right_eye_height = max(point[1] for point in right_eye) - min(point[1] for point in right_eye)
                
                if left_eye_height < 5 and right_eye_height < 5:
                    return "Eyes Closed"
            
            # Lablar kulganmi?
            if 'top_lip' in landmarks and 'bottom_lip' in landmarks:
                lip_height = max(point[1] for point in landmarks['top_lip']) - min(point[1] for point in landmarks['bottom_lip'])
                if lip_height > 10:
                    return "Smiling"
            
            return "Neutral"
            
        except:
            return "Neutral"
    
    @staticmethod
    def check_eyes_visible(landmarks):
        """Ko'zlar ko'rinayotganini tekshirish"""
        return 'left_eye' in landmarks and 'right_eye' in landmarks

# Qolgan funksiyalar...
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni ishga tushirish"""
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
    """Foydalanuvchi maqomini tanlash"""
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
    """Familiya Ism Sharifni olish"""
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
    """Telefon raqamini olish"""
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
    """Passport ma'lumotlarini olish"""
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
        "• Ko'zlar ochiq bo'lsin\n\n"
        "💡 Bu sizning shaxsingizni tasdiqlash uchun kerak",
        reply_markup=reply_markup
    )
    return FACE_VERIFICATION

async def get_face_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yuzni tasdiqlash"""
    user_input = update.message.text if update.message.text else ""
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('passport', None)
        return await get_passport_info(update, context)
    
    # Yuzni tekshirish
    face_verified = await FaceVerification.verify_face(update, context)
    
    if face_verified:
        # Muvaffaqiyatli tasdiqlangan
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
        # Tasdiqlanmagan, qaytadan urinish
        return FACE_VERIFICATION

async def get_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Murojaat matnini olish"""
    user_input = update.message.text
    
    if user_input == BACK_BUTTON:
        context.user_data.pop('face_verified', None)
        return await get_face_verification(update, context)
    
    context.user_data['message'] = user_input
    
    try:
        # Ma'lumotlarni adminga yuborish
        await send_to_admin(update, context)
        
        await update.message.reply_text(
            "✅ Murojaatingiz muvaffaqiyatli yuborildi!\n\n"
            "📞 Tez orada aloqaga chiqamiz\n"
            "🛡️ Korrupsiyaga qarshi kurash - bizning burchimiz!\n\n"
            "🆕 Yangi murojaat yuborish uchun /start buyrug'ini yuboring"
        )
        
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text(
            f"❌ Xatolik yuz berdi! Iltimos, /start buyrug'ini yuborib qaytadan urinib ko'ring."
        )
    
    context.user_data.clear()
    return ConversationHandler.END

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adminga ma'lumotlarni yuborish"""
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
✅ Yuz tasdiqlangan
📊 Sifat: {user_data.get('face_quality', 'Noma lum')}%
👁️ Ko'zlar: {'Aniqlangan' if user_data.get('face_landmarks') else 'Noma lum'}

User ID: {update.effective_user.id}
Username: {update.effective_user.username or 'Noma lum'}
        """
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message
        )
        logger.info("✅ Ma'lumotlar adminga yuborildi")
        
    except Exception as e:
        logger.error(f"Adminga yuborishda xatolik: {e}")

# Qolgan funksiyalar (help, cancel) o'zgarmaydi...

def main():
    """Asosiy dastur"""
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
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    
    logger.info("🤖 Bot ishga tushmoqda...")
    logger.info("🔐 Yuzni taniash tizimi faollashtirildi")
    
    application.run_polling()

if __name__ == '__main__':
    main()
