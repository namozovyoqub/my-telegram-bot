import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Environment variables
BOT_TOKEN = os.environ.get('8421362951:AAGBErKWbZxSYDejERx-MXxEAKNOJZU3Ulo')
ADMIN_CHAT_ID = os.environ.get('5274895365')

# Conversation states
SELECTING_ROLE, STUDENT_INFO, TEACHER_INFO, MESSAGE_TEXT = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Talaba")],
        [KeyboardButton("O'qituvchi"), KeyboardButton("Universitet xodimi")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat botiga xush kelibsiz.\n"
        "Iltimos, o'zingizning maqomingizni tanlang:",
        reply_markup=reply_markup
    )
    return SELECTING_ROLE

async def select_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = update.message.text
    context.user_data['role'] = role
    
    if role == "Talaba":
        await update.message.reply_text("Iltimos, ism-sharifingizni kiriting:")
        return STUDENT_INFO
    else:
        await update.message.reply_text("Iltimos, F.I.SH ni kiriting:")
        return TEACHER_INFO

async def get_student_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'name' not in context.user_data:
        context.user_data['name'] = text
        await update.message.reply_text("Iltimos, telefon raqamingizni kiriting:")
        return STUDENT_INFO
    
    elif 'phone' not in context.user_data:
        context.user_data['phone'] = text
        await update.message.reply_text("Iltimos, fakultetingizni kiriting:")
        return STUDENT_INFO
    
    elif 'faculty' not in context.user_data:
        context.user_data['faculty'] = text
        await update.message.reply_text("Iltimos, guruh raqamingizni kiriting:")
        return STUDENT_INFO
    
    elif 'group' not in context.user_data:
        context.user_data['group'] = text
        await update.message.reply_text("Iltimos, murojaat matnini kiriting:")
        return MESSAGE_TEXT

async def get_teacher_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'name' not in context.user_data:
        context.user_data['name'] = text
        await update.message.reply_text("Iltimos, telefon raqamingizni kiriting:")
        return TEACHER_INFO
    
    elif 'phone' not in context.user_data:
        context.user_data['phone'] = text
        await update.message.reply_text("Iltimos, murojaat matnini kiriting:")
        return MESSAGE_TEXT

async def get_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text
    
    # Adminga xabar tayyorlash
    role = context.user_data['role']
    
    if role == "Talaba":
        admin_message = f"📋 YANGI MUROJAAT\n\n" \
                       f"👤 Maqom: {role}\n" \
                       f"📛 Ism-sharif: {context.user_data['name']}\n" \
                       f"📞 Telefon: {context.user_data['phone']}\n" \
                       f"🏛 Fakultet: {context.user_data['faculty']}\n" \
                       f"👥 Guruh: {context.user_data['group']}\n" \
                       f"📝 Murojaat: {context.user_data['message']}\n" \
                       f"🆔 User ID: {update.effective_user.id}"
    else:
        admin_message = f"📋 YANGI MUROJAAT\n\n" \
                       f"👤 Maqom: {role}\n" \
                       f"📛 F.I.SH: {context.user_data['name']}\n" \
                       f"📞 Telefon: {context.user_data['phone']}\n" \
                       f"📝 Murojaat: {context.user_data['message']}\n" \
                       f"🆔 User ID: {update.effective_user.id}"
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        await update.message.reply_text("✅ Murojaatingiz qabul qilindi! Tez orada siz bilan bog'lanamiz.")
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Murojaat bekor qilindi. /start bilan qaytadan boshlang.")
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Botdan foydalanish uchun /start buyrug'ini yuboring.")

def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN topilmadi!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_role)],
            STUDENT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_student_info)],
            TEACHER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_teacher_info)],
            MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message_text)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    application.run_polling()

if __name__ == '__main__':
    main()
