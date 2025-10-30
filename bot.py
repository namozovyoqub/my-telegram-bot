import logging
import os
import cv2
import numpy as np
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

class SimpleFaceVerification:
    """Soddalashtirilgan yuzni tasdiqlash"""
    
    @staticmethod
    async def verify_face(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yuzni tasdiqlash va rasmni saqlash"""
        if update.message.photo:
            try:
                # Rasmni yuklab olish
                photo_file = await update.message.photo[-1].get_file()
                photo_path = f"face_{update.effective_user.id}.jpg"
                await photo_file.download_to_drive(photo_path)
                
                # Yuzni tekshirish
                result = SimpleFaceVerification.detect_face_simple(photo_path)
                
                if result["success"]:
                    if result["face_count"] == 1:
                        context.user_data['face_verified'] = True
                        context.user_data['face_quality'] = result["quality"]
                        context.user_data['face_photo_path'] = photo_path  # Rasmni saqlash
                        
                        await update.message.reply_text(
                            f"✅ YUZ MUVAFFAQIYATLI TASDIQLANDI!\n\n"
                            f"📊 Sifat bahosi: {result['quality']}%\n"
                            f"👤 Yuzlar soni: {result['face_count']}\n\n"
                            f"🆔 Biometrik tasdiqlash muvaffaqiyatli!"
                        )
                        return True
                    else:
                        # Rasmni o'chirish (tasdiqlanmagan)
                        try:
                            os.remove(photo_path)
                        except:
                            pass
                        
                        await update.message.reply_text(
                            f"❌ {result['face_count']} ta yuz aniqlandi.\n"
                            f"Faqat bitta yuz bo'lishi kerak."
                        )
                        return False
                else:
                    # Rasmni o'chirish (tasdiqlanmagan)
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                    
                    await update.message.reply_text(
                        "❌ Yuz aniqlanmadi!\n\n"
                        "Iltimos:\n"
                        "• Yorug'lik yaxshi bo'lsin\n"
                        "• Yuz to'liq ko'rinsin\n"
                        "• Boshqa odamlar bo'lmasin"
                    )
                    return False
                    
            except Exception as e:
                logger.error(f"Yuz tekshirishda xatolik: {e}")
                await update.message.reply_text("❌ Rasmni qayta ishlashda xatolik.")
                return False
        else:
            await update.message.reply_text("❌ Iltimos, rasm yuboring!")
            return False
    
    @staticmethod
    def detect_face_simple(image_path):
        """OpenCV yordamida soddalashtirilgan yuzni aniqlash"""
        try:
            # OpenCV ning oldingi yuz klassifikatorini yuklash
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Rasmni yuklash
            image = cv2.imread(image_path)
            if image is None:
                return {"success": False, "face_count": 0}
            
            # Gray scale ga o'tkazish
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Yuzlarni aniqlash
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            face_count = len(faces)
            
            if face_count == 0:
                return {"success": False, "face_count": 0}
            
            # Sifat baholash
            quality = SimpleFaceVerification.calculate_simple_quality(image, faces[0] if face_count > 0 else None)
            
            return {
                "success": True,
                "face_count": face_count,
                "quality": quality,
                "faces": faces
            }
            
        except Exception as e:
            logger.error(f"Yuz aniqlashda xatolik: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def calculate_simple_quality(image, face_rect):
        """Soddalashtirilgan sifat tekshiruvi"""
        try:
            quality = 60  # Asosiy baho
            
            if face_rect is not None:
                x, y, w, h = face_rect
                
                # Yuzning rasmda qoplagan maydoni
                img_height, img_width = image.shape[:2]
                face_area_ratio = (w * h) / (img_height * img_width)
                
                # Yuz o'lchami
                if face_area_ratio > 0.1:
                    quality += 20
                elif face_area_ratio > 0.05:
                    quality += 10
                
                # Yorug'likni tekshirish
                face_region = image[y:y+h, x:x+w]
                brightness = np.mean(face_region)
                
                # Yorug'lik
                if 100 <= brightness <= 200:
                    quality += 20
            
            return min(95, quality)
            
        except:
            return 70

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
        "• Boshqa odamlar bo'lmasin\n\n"
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
    face_verified = await SimpleFaceVerification.verify_face(update, context)
    
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
        context.user_data.pop('face_photo_path', None)
        return await get_face_verification(update, context)
    
    context.user_data['message'] = user_input
    
    try:
        # Ma'lumotlarni adminga yuborish (rasm bilan birga)
        await send_to_admin_with_photo(update, context)
        
        await update.message.reply_text(
            "✅ Murojaatingiz muvaffaqiyatli yuborildi!\n\n"
            "📞 Tez orada aloqaga chiqamiz\n"
            "🛡️ Korrupsiyaga qarshi kurash - bizning burchimiz!\n\n"
            "🆕 Yangi murojaat yuborish uchun /start buyrug'ini yuboring"
        )
        
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi! /start ni bosing.")
    
    # Ma'lumotlarni tozalash
    await cleanup_files(context)
    context.user_data.clear()
    return ConversationHandler.END

async def send_to_admin_with_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adminga ma'lumotlar va rasmni yuborish"""
    try:
        user_data = context.user_data
        
        # Text xabar
        admin_message = f"""
YANGI MUROJAAT - BIOMETRIK TASDIQLANGAN

👤 SHAXSIY MA'LUMOTLAR:
Maqom: {user_data.get('role', 'Noma lum')}
F.I.SH: {user_data.get('full_name', 'Noma lum')}
Telefon: {user_data.get('phone', 'Noma lum')}
Passport: {user_data.get('passport', 'Noma lum')}

🔐 BIOMETRIK TASDIQLASH:
✅ Yuz tasdiqlangan (OpenCV)
📊 Sifat: {user_data.get('face_quality', 'Noma lum')}%

💬 MUROJAAT MATNI:
{user_data.get('message', 'Noma lum')}

📋 QO'SHIMCHA:
User ID: {update.effective_user.id}
Username: {update.effective_user.username or 'Noma lum'}
        """
        
        # Avval text xabarni yuborish
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        
        # Keyin rasmni yuborish
        if user_data.get('face_photo_path') and os.path.exists(user_data['face_photo_path']):
            with open(user_data['face_photo_path'], 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=photo,
                    caption=f"📸 Biometrik tasdiqlash - {user_data.get('full_name', 'Foydalanuvchi')}"
                )
        
        logger.info("✅ Ma'lumotlar va rasm adminga yuborildi")
        
    except Exception as e:
        logger.error(f"Adminga yuborishda xatolik: {e}")

async def cleanup_files(context: ContextTypes.DEFAULT_TYPE):
    """Vaqtincha fayllarni tozalash"""
    user_data = context.user_data
    
    try:
        if user_data.get('face_photo_path') and os.path.exists(user_data['face_photo_path']):
            os.remove(user_data['face_photo_path'])
        logger.info("✅ Vaqtincha fayllar tozalandi")
    except Exception as e:
        logger.error(f"Fayllarni tozalashda xatolik: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🛡️ Korrupsiyaga qarshi kurash boti - Yordam

📝 Murojaat qilish bosqichlari:
1️⃣ Maqom tanlash
2️⃣ F.I.SH kiritish  
3️⃣ Telefon raqam
4️⃣ Passport ma'lumotlari
5️⃣ 🔐 BIOMETRIK TASDIQLASH (yuzni taniash)
6️⃣ Murojaat matni

🔐 Biometrik tasdiqlash:
• Yuzingizni aniq ko'rsating
• Yorug'lik yaxshi bo'lsin
• Faqat bitta yuz bo'lsin
• Rasm adminga yuboriladi"""
    
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
    # Fayllarni tozalash
    await cleanup_files(context)
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
    logger.info("🔐 OpenCV yuzni taniash tizimi faollashtirildi")
    logger.info("📸 Rasm adminga yuboriladi")
    
    application.run_polling()

if __name__ == '__main__':
    main()
            
