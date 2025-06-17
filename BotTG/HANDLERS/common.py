from states import *
from telegram import Update, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import ContextTypes, ConversationHandler
from UTILS import send_and_remember, clear_bot_message_ids
from KEYBOARDS import get_main_menu_keyboard, get_back_keyboard, get_submit_keyboard, get_status_keyboard, get_faq_keyboard, get_support_keyboard, get_about_keyboard, specialty_keyboard
import logging

logger = logging.getLogger(__name__)

ADMIN_TELEGRAM_ID = 1595547276

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сбросить все флаги ошибок при возврате в главное меню
    keys_to_remove = [k for k in context.user_data.keys() if k.startswith('text_error_shown_') or k == 'faq_error_shown']
    for k in keys_to_remove:
        context.user_data.pop(k, None)
    try:
        photo_path = 'images/menu.jpg'
        menu_caption = 'ГЛАВНОЕ МЕНЮ 🏠'
        await send_and_remember(update, context, photo_path=photo_path, caption=menu_caption, reply_markup=get_main_menu_keyboard())
    except (FileNotFoundError, AttributeError):
        await send_and_remember(update, context, text='ГЛАВНОЕ МЕНЮ 🏠', reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def handle_main_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.message.reply_text("❗️Пожалуйста, используйте только кнопки или команды для работы с ботом.")
    return MAIN_MENU

async def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Очищаем ID сообщений при ошибке
    if update and update.effective_chat:
        context.user_data['bot_message_ids'] = []
    # Можно отправлять уведомление админу или пользователю, если нужно

async def fallback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from states import GET_NAME, GET_EMAIL, GET_AGE, GET_GENDER, EDIT_NAME, EDIT_EMAIL, CONFIRM_EMAIL, CONFIRM_EDIT_EMAIL, UPLOAD_PHOTO, FAQ, STATUS
    manual_input_states = {GET_NAME, GET_EMAIL, GET_AGE, GET_GENDER, EDIT_NAME, EDIT_EMAIL, CONFIRM_EMAIL, CONFIRM_EDIT_EMAIL, UPLOAD_PHOTO}
    current_state = context.user_data.get('current_state')
    # Не показывать ошибку, если пользователь только что посмотрел заявку по ID
    if current_state == STATUS and context.user_data.get('just_viewed_status'):
        context.user_data['just_viewed_status'] = False
        return STATUS
    # Не показывать ошибку, если пользователь в состоянии, где ожидается ручной ввод
    if current_state in manual_input_states:
        return current_state
    if current_state == FAQ:
        if not context.user_data.get('faq_error_shown'):
            await update.message.reply_text("❗️Пожалуйста, используйте только кнопки или команды для работы с ботом.")
            context.user_data['faq_error_shown'] = True
        return FAQ
    error_flag = f'text_error_shown_{current_state}'
    if not context.user_data.get(error_flag):
        await update.message.reply_text("❗️Пожалуйста, используйте только кнопки или команды для работы с ботом.")
        context.user_data[error_flag] = True
    return current_state if current_state is not None else ConversationHandler.END

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_and_remember(update, context, text="Главное меню:", reply_markup=get_main_menu_keyboard())
    return await send_main_menu(update, context)

async def set_bot_commands_for_user(application, telegram_id):
    commands = [
        BotCommand("start", "Запустить бота/регистрацию"),
        BotCommand("menu", "Показать главное меню")
    ]
    if telegram_id == ADMIN_TELEGRAM_ID:
        commands += [
            BotCommand("applications", "Список заявок"),
            BotCommand("respond", "Ответить на заявку (/respond <id> <код>)")
        ]
        # Устанавливаем команды только для чата с админом (личный чат)
        await application.bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=telegram_id))
    else:
        # Для всех остальных — только базовые команды
        await application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'profile':
        from HANDLERS.profile import handle_profile_callback
        # Передаём update с query, чтобы корректно работал profile
        return await handle_profile_callback(update, context)
    elif data == 'submit':
        from KEYBOARDS import specialty_keyboard
        markup = specialty_keyboard() if callable(specialty_keyboard) else specialty_keyboard
        await send_and_remember(
            update, context,
            photo_path='images/специальность.jpg',
            caption='Выберите и введите код специальности (например, 08.02.01):',
            reply_markup=markup
        )
        return CHOOSE_SPECIALTY
    elif data == 'status':
        await send_and_remember(update, context, photo_path='images/status.jpg', caption="Пожалуйста, введите ID вашей заявки.", reply_markup=get_status_keyboard())
        return GET_APP_ID
    elif data == 'faq':
        from HANDLERS.faq import show_faq_page
        return await show_faq_page(update, context)
    elif data == 'support':
        await send_and_remember(update, context, photo_path='images/Support.jpg', caption="🛠️ Для технической поддержки напишите @WuuuDpicker", reply_markup=get_support_keyboard())
        return SUPPORT
    elif data == 'about':
        await send_and_remember(update, context, photo_path='images/TheBot.jpg', caption="О боте 🤖\nПривет! Я — AdmBOT , ваш помощник в поступлении!\n\n📚 Что я умею:\n✅ Подать документы на поступление (паспорт, аттестат, мед.справки и так далее.).\n✅ Проверить статус вашей заявки 🔍.\n✅ Ответы на часто задаваемые вопросы 💬.\n✅ Возможность подать документы в любом месте и 24/7 🕒.", reply_markup=get_about_keyboard())
        return ABOUT
    elif data.startswith('back'):
        return await send_main_menu(update, context)
    elif data == 'upload_photo':
        from HANDLERS.profile import handle_upload_photo
        return await handle_upload_photo(update, context)
    elif data == 'edit_name':
        from HANDLERS.profile import edit_name
        return await edit_name(update, context)
    elif data == 'edit_email':
        from HANDLERS.email import edit_email
        return await edit_email(update, context)
    else:
        await query.message.reply_text('Неизвестная команда.')
        return MAIN_MENU

async def handle_specialty_text_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Не отправлять ошибку, если choose_specialty уже обработал текст
    return CHOOSE_SPECIALTY