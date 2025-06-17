from states import *
import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from HANDLERS import (
    start, get_name, get_email, get_age, get_gender,
    handle_profile_callback, edit_name, handle_upload_photo,
    handle_document, get_app_id, choose_specialty, handle_specialty_action,
    confirm_email, confirm_email_callback,
    edit_email, confirm_edit_email, confirm_edit_email_callback,
    send_main_menu, handle_main_menu_text, error_handler, fallback_text_handler,
    menu_command, handle_callback,
    handle_specialty_text_fallback, handle_faq_callback, handle_faq_text
)
from HANDLERS.admin import process_admin_response, show_pending_applications, handle_admin_callback
from functools import wraps
from database import get_user_by_telegram_id
from HANDLERS.application import handle_document_upload, handle_finish_upload
from UTILS import send_and_remember
from KEYBOARDS import get_main_menu_keyboard
from telegram import BotCommand
from HANDLERS.common import set_bot_commands_for_user

GET_NAME, GET_EMAIL, GET_AGE, GET_GENDER, MAIN_MENU, GET_APP_ID, SUBMIT_DOCUMENTS, PROFILE, EDIT_NAME, EDIT_EMAIL, UPLOAD_PHOTO, CONFIRM_EMAIL, CONFIRM_EDIT_EMAIL, CHOOSE_SPECIALTY, ABOUT, SUPPORT, FAQ, STATUS = range(18)

def with_state(state):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            context.user_data['current_state'] = state
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def main():
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token('8198184865:AAGZGJ9Zf9KQi5OprX5y3zzz9ZejlubMbrc').build()

    application.add_handler(CommandHandler('menu', menu_command))
    
    # Административные команды
    application.add_handler(CommandHandler('respond', process_admin_response))
    application.add_handler(CommandHandler('applications', show_pending_applications))
    
    # Обработчик callback'ов для административной панели
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", with_state(GET_NAME)(start))],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(GET_NAME)(get_name)), CallbackQueryHandler(with_state(GET_NAME)(handle_callback))],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(GET_EMAIL)(get_email)), CallbackQueryHandler(with_state(GET_EMAIL)(confirm_email_callback))],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(GET_AGE)(get_age)), CallbackQueryHandler(with_state(GET_AGE)(handle_callback))],
            GET_GENDER: [CallbackQueryHandler(with_state(GET_GENDER)(get_gender)), CallbackQueryHandler(with_state(GET_GENDER)(handle_callback))],
            MAIN_MENU: [
                CallbackQueryHandler(with_state(MAIN_MENU)(handle_callback)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(MAIN_MENU)(handle_main_menu_text)),
            ],
            GET_APP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(GET_APP_ID)(get_app_id)), CallbackQueryHandler(with_state(GET_APP_ID)(handle_callback))],
            SUBMIT_DOCUMENTS: [
                MessageHandler(filters.Document.ALL, with_state(SUBMIT_DOCUMENTS)(handle_document_upload)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(SUBMIT_DOCUMENTS)(handle_document_upload)),
                CommandHandler('finish', with_state(SUBMIT_DOCUMENTS)(handle_finish_upload)),
                CallbackQueryHandler(with_state(SUBMIT_DOCUMENTS)(handle_callback))
            ],
            PROFILE: [CallbackQueryHandler(with_state(PROFILE)(handle_profile_callback)), CallbackQueryHandler(with_state(PROFILE)(handle_callback))],
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(EDIT_NAME)(edit_name)), CallbackQueryHandler(with_state(EDIT_NAME)(handle_callback))],
            EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(EDIT_EMAIL)(edit_email)), CallbackQueryHandler(with_state(EDIT_EMAIL)(confirm_edit_email_callback))],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(CONFIRM_EMAIL)(confirm_email)), CallbackQueryHandler(with_state(CONFIRM_EMAIL)(confirm_email_callback))],
            CONFIRM_EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(CONFIRM_EDIT_EMAIL)(confirm_edit_email)), CallbackQueryHandler(with_state(CONFIRM_EDIT_EMAIL)(confirm_edit_email_callback))],
            UPLOAD_PHOTO: [MessageHandler(filters.PHOTO, with_state(UPLOAD_PHOTO)(handle_upload_photo)), CallbackQueryHandler(with_state(UPLOAD_PHOTO)(handle_callback))],
            CHOOSE_SPECIALTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(CHOOSE_SPECIALTY)(choose_specialty)), CallbackQueryHandler(with_state(CHOOSE_SPECIALTY)(handle_specialty_action)), MessageHandler(filters.ALL, with_state(CHOOSE_SPECIALTY)(handle_specialty_text_fallback))],
            ABOUT: [CallbackQueryHandler(with_state(ABOUT)(handle_callback))],
            SUPPORT: [CallbackQueryHandler(with_state(SUPPORT)(handle_callback))],
            FAQ: [
                CallbackQueryHandler(with_state(FAQ)(handle_faq_callback)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_state(FAQ)(handle_faq_text))
            ],
            STATUS: [CallbackQueryHandler(with_state(STATUS)(handle_callback))],
        },
        fallbacks=[CommandHandler("start", with_state(GET_NAME)(start))]
    )
    application.add_handler(conv_handler)

    application.add_error_handler(error_handler)
    # Добавляю fallback только для ABOUT, SUPPORT, STATUS (FAQ исключён!)
    for state in [ABOUT, SUPPORT, STATUS]:
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text_handler), group=state)
    
    # Устанавливаем команды для всех и для администратора
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_bot_commands_for_user(application, 0))
    loop.run_until_complete(set_bot_commands_for_user(application, 1595547276))
    application.run_polling()

async def menu_command(update, context):
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user:
        await update.message.reply_text('Сначала зарегистрируйтесь с помощью /start.')
        return MAIN_MENU
    # Устанавливаем команды для пользователя
    await set_bot_commands_for_user(context.application, update.effective_user.id)
    await send_and_remember(update, context, text="Главное меню:", reply_markup=get_main_menu_keyboard())
    await send_main_menu(update, context)
    return MAIN_MENU

if __name__ == '__main__':
    main()