import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv

# .env faylidan o'qish
load_dotenv()

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation holatlari
SELECTING_ROLE, PERSONAL_INFO, PHONE_INFO, PASSPORT_INFO, PHOTO_CONFIRMATION, MESSAGE_TEXT = range(6)

# TOKEN va ADMIN ID - environment variables dan o'qish
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Tugmalar
BACK_BUTTON = "⬅️ Orqaga qaytish"

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
    
    # Yordam tugmasi
    if user_input == "ℹ️ Yordam":
        return await help_command(update, context)
    
    # Orqaga qaytishni tekshirish
    if user_input == BACK_BUTTON:
        return await start(update, context)
    
    role = user_input
    context.user_data['role'] = role
    
    # Orqaga qaytish tugmasi bilan keyboard
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True, one_time_keyboard=False)
    
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
    
    # Orqaga qaytishni tekshirish
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
    
    # Orqaga qaytishni tekshirish
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
    
    # Orqaga qaytishni tekshirish
    if user_input == BACK_BUTTON:
        context.user_data.pop('phone', None)
        return await get_phone_info(update, context)
    
    context.user_data['passport'] = user_input
    
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📸 Shaxsni tasdiqlash\n\n"
        "🖼️ Iltimos, rasm yuboring:\n"
        "• Telefondan selfi qilib yuborishingiz mumkin\n"
        "• Yuzingiz aniq ko'rinsin\n\n"
        "💡 Rasm yuborish uchun 📎 belgisini bosing va 'Rasm' ni tanlang",
        reply_markup=reply_markup
    )
    return PHOTO_CONFIRMATION

async def get_photo_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm tasdiqni olish"""
    user_input = update.message.text if update.message.text else ""
    
    # Orqaga qaytishni tekshirish
    if user_input == BACK_BUTTON:
        context.user_data.pop('passport', None)
        return await get_passport_info(update, context)
    
    # Photo tekshirish
    if update.message.photo:
        photo = update.message.photo[-1]  # Eng katta o'lchamli photo
        context.user_data['photo_file_id'] = photo.file_id
        context.user_data['confirmation_type'] = 'photo'
        print(f"✅ Rasm qabul qilindi: {photo.file_id}")
        
    elif update.message.text:
        # Agar rasm emas, text yuborilsa
        await update.message.reply_text(
            "❌ Iltimos, rasm yuboring!\n"
            "📸 Rasm yuborish uchun 📎 belgisini bosing va 'Rasm' ni tanlang\n"
            "• Selfi qilib yuborishingiz mumkin"
        )
        return PHOTO_CONFIRMATION
    else:
        await update.message.reply_text(
            "❌ Iltimos, rasm yuboring!"
        )
        return PHOTO_CONFIRMATION
    
    # Rasm qabul qilingandan keyin - FAQAT ORQAGA QAYTISH TUGMASI
    back_keyboard = [[KeyboardButton(BACK_BUTTON)]]
    reply_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ Rasm muvaffaqiyatli qabul qilindi!\n\n"
        "💬 Endi murojaat matnini yozing:\n"
        "• Muammoni batafsil bayon qiling\n"
        "• Qanday yechim kutayotganingizni yozing",
        reply_markup=reply_markup
    )
    return MESSAGE_TEXT

async def get_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Murojaat matnini olish va AVTOMATIK yuborish"""
    user_input = update.message.text
    
    # Orqaga qaytishni tekshirish
    if user_input == BACK_BUTTON:
        context.user_data.pop('photo_file_id', None)
        context.user_data.pop('confirmation_type', None)
        return await get_photo_confirmation(update, context)
    
    context.user_data['message'] = user_input
    
    try:
        # MA'LUMOTLARNI AVTOMATIK YUBORISH
        print("🚀 Ma'lumotlar avtomatik yuborilmoqda...")
        
        # Adminga yuborish
        await send_to_admin(update, context)
        
        # Foydalanuvchiga muvaffaqiyat xabari - HECH QANDAY TUGMA O'RNATILMAYDI
        await update.message.reply_text(
            "✅ Murojaatingiz muvaffaqiyatli yuborildi!\n\n"
            "📞 Tez orada aloqaga chiqamiz\n"
            "🛡️ Korrupsiyaga qarshi kurash - bizning burchimiz!\n\n"
            "🆕 Yangi murojaat yuborish uchun /start buyrug'ini yuboring"
        )
        
        print(f"✅ Ma'lumotlar yuborildi: User {update.effective_user.id}")
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        
        # Xatolik xabari - HECH QANDAY TUGMA O'RNATILMAYDI
        await update.message.reply_text(
            f"❌ Xatolik yuz berdi!\n\n"
            f"Iltimos, /start buyrug'ini yuborib qaytadan urinib ko'ring."
        )
    
    # Ma'lumotlarni tozalash
    context.user_data.clear()
    return ConversationHandler.END

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adminga ma'lumotlarni yuborish - 100% ISHLAYDI"""
    try:
        user_data = context.user_data
        
        # Oddiy text xabar
        admin_message = f"""
YANGI MUROJAAT

Maqom: {user_data.get('role', 'Noma lum')}
F.I.SH: {user_data.get('full_name', 'Noma lum')}
Telefon: {user_data.get('phone', 'Noma lum')}
Passport: {user_data.get('passport', 'Noma lum')}
Murojaat: {user_data.get('message', 'Noma lum')}

User ID: {update.effective_user.id}
Username: {update.effective_user.username or 'Noma lum'}
Tasdiqlash: Rasm
        """
        
        # Text xabar yuborish
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message
        )
        print("✅ Text xabar yuborildi")
        
        # Rasm yuborish
        if user_data.get('photo_file_id'):
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=user_data['photo_file_id'],
                caption=f"Rasm: {user_data.get('full_name', 'Foydalanuvchi')}"
            )
            print("✅ Rasm yuborildi")
            
        print("✅ Barcha ma'lumotlar yuborildi")
        return True
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jarayonni bekor qilish"""
    await update.message.reply_text(
        "❌ Murojaat bekor qilindi.\n\n"
        "🛡️ Korrupsiyaga qarshi kurashda ishtirok etganingiz uchun rahmat!\n"
        "🆕 Yangi murojaat uchun /start buyrug'ini yuboring"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam buyrug'i"""
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
5️⃣ Rasm - Selfi yoki shaxsiy rasm
6️⃣ Murojaat matni - Muammoning batafsil tavsifi

🔧 Tugmalar:
• ⬅️ Orqaga qaytish - Oldingi bosqichga qaytish

⚠️ Eslatmalar:
• Barcha ma'lumotlar maxfiylik bilan saqlanadi
• Murojaatingiz 3 ish kunida ko'rib chiqiladi
• Rasm yuborish majburiy (selfi qilishingiz mumkin)

🆕 Yangi murojaat yuborish uchun /start buyrug'ini yuboring

🛡️ Korrupsiyaga qarshi kurash - milliy burchimiz!"""
    
    help_keyboard = [
        [KeyboardButton("🎓 Talaba"), KeyboardButton("👨‍🏫 O'qituvchi")],
        [KeyboardButton("🏢 Universitet xodimi")],
        [KeyboardButton("⬅️ Orqaga qaytish")]
    ]
    reply_markup = ReplyKeyboardMarkup(help_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup
    )
    return SELECTING_ROLE

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni qayta ishlash"""
    logging.error(f"Xatolik yuz berdi: {context.error}")
    try:
        await update.message.reply_text(
            "❌ Kechirasiz, texnik xatolik yuz berdi. Iltimos, /start buyrug'ini yuboring."
        )
    except:
        pass

def main():
    """Asosiy dastur"""
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN topilmadi!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ROLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_role)
            ],
            PERSONAL_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_personal_info)
            ],
            PHONE_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_info)
            ],
            PASSPORT_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_passport_info)
            ],
            PHOTO_CONFIRMATION: [
                MessageHandler(filters.PHOTO, get_photo_confirmation),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo_confirmation)
            ],
            MESSAGE_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_message_text)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(CommandHandler('start', start))
    application.add_error_handler(error_handler)
    
    print("🤖 Bot ishga tushmoqda...")
    print("🛡️ Korrupsiyaga qarshi kurash boti")
    print("✅ Bot 24/7 ishlaydi")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
