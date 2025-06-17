from states import *
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_by_telegram_id
from HANDLERS.common import set_bot_commands_for_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Очищаем предыдущие сообщения бота
    bot_message_ids = context.user_data.get('bot_message_ids', [])
    for msg_id in bot_message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    context.user_data['bot_message_ids'] = []
    telegram_id = update.message.from_user.id
    # Устанавливаем команды для пользователя
    await set_bot_commands_for_user(context.application, telegram_id)
    user = get_user_by_telegram_id(telegram_id)
    if user:
        # Импортируй send_main_menu только тут!
        from HANDLERS.common import send_main_menu
        await send_main_menu(update, context)
        return MAIN_MENU
    else:
        await update.message.reply_text('📝 Здравствуйте! Пожалуйста, укажите ваше полное ФИО (Ваше фамилия имя отчество).')
        context.user_data['telegram_id'] = telegram_id
        return GET_NAME