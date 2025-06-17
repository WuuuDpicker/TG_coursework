from telegram import Update
from telegram.ext import ContextTypes
from UTILS import send_and_remember, is_valid_specialty_code, specialty_exists, get_specialty_info_text
from KEYBOARDS import specialty_keyboard, get_specialty_action_keyboard
from HANDLERS.common import send_main_menu
from states import CHOOSE_SPECIALTY, MAIN_MENU

async def choose_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not is_valid_specialty_code(code):
        await update.message.reply_text('❗️ Код должен быть в формате xx.xx.xx (только цифры и точки). Попробуйте ещё раз!')
        return CHOOSE_SPECIALTY
    spec = specialty_exists(code)
    if not spec:
        await update.message.reply_text('❗️ Такой специальности не найдено. Проверьте код специальности.')
        return CHOOSE_SPECIALTY
    context.user_data['specialty'] = spec
    await update.message.reply_text(
        get_specialty_info_text(spec),
        reply_markup=get_specialty_action_keyboard(spec),
        parse_mode='HTML'
    )
    return CHOOSE_SPECIALTY

async def handle_specialty_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_specialty":
        await send_main_menu(update, context)
        return MAIN_MENU
    elif query.data == "submit_documents":
        # Запуск процесса загрузки документов
        from HANDLERS.application import start_documents_upload
        return await start_documents_upload(update, context)