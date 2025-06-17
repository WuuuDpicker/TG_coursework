from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from UTILS import send_confirmation_code, send_and_remember, is_valid_email, get_age_suffix
from database import get_user_by_telegram_id, connect_db, get_applications_by_user
from KEYBOARDS import get_email_confirm_keyboard, get_profile_keyboard
import random
import logging
from states import GET_EMAIL, EDIT_EMAIL, CONFIRM_EMAIL, CONFIRM_EDIT_EMAIL, GET_AGE, MAIN_MENU, PROFILE

logger = logging.getLogger(__name__)

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    from telegram.ext import ConversationHandler
    if not is_valid_email(email):
        # Показываем ошибку о кнопках только если ещё не показывали
        if not context.user_data.get('text_error_shown_1'):
            await update.message.reply_text("❗️Пожалуйста, используйте только кнопки или команды для работы с ботом.")
            context.user_data['text_error_shown_1'] = True
        await update.message.reply_text("❗️ Пожалуйста, введите корректный email.")
        return GET_EMAIL
    # Сбросить флаг ошибки для этого состояния
    context.user_data.pop('text_error_shown_1', None)
    context.user_data['email'] = email
    code = '{:03d}'.format(random.randint(0, 999))
    context.user_data['email_code'] = code
    context.user_data['resend_count'] = 0
    try:
        send_confirmation_code(email, code)
    except Exception as e:
        context.logger.error(f"Ошибка отправки email: {e}")
        await update.message.reply_text("❗️ Ошибка отправки письма. Попробуйте другой email.")
        return GET_EMAIL
    return await ask_email_code(update, context)

async def ask_email_code(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    email = context.user_data.get('email') if not edit else context.user_data.get('edit_email')
    text = f'📧 На почту {email} был отправлен код для подтверждения.\nВведите его ниже:'
    await send_and_remember(
        update, context,
        text=text,
        reply_markup=get_email_confirm_keyboard(edit=edit, resend=context.user_data.get('resend_count', 0) < 2)
    )
    return CONFIRM_EDIT_EMAIL if edit else CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code == context.user_data.get('email_code'):
        await update.message.reply_text('✅ Email подтверждён!')
        await update.message.reply_text('📝 Укажите ваш возраст в формате дд.мм.гггг (например: 01.01.2000).')
        return GET_AGE
    else:
        await update.message.reply_text('❗️ Неверный код. Попробуйте ещё раз.')
        return await ask_email_code(update, context)

async def confirm_email_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'change_email':
        await send_and_remember(update, context, text='Введите новый email:')
        return GET_EMAIL
    elif data == 'resend_code':
        email = context.user_data['email']
        code = '{:03d}'.format(random.randint(0, 999))
        context.user_data['email_code'] = code
        context.user_data['resend_count'] = context.user_data.get('resend_count', 0) + 1
        try:
            send_confirmation_code(email, code)
        except Exception as e:
            context.logger.error(f"Ошибка отправки email: {e}")
            await query.message.reply_text("❗️ Ошибка отправки письма. Попробуйте другой email.")
            return GET_EMAIL
        await query.message.reply_text('ℹ️ Код отправлен повторно.')
        return await ask_email_code(update, context)
    elif data == 'exit_email':
        from HANDLERS.common import send_main_menu
        await send_and_remember(update, context, text='ℹ️ Выход из подтверждения email. Для старта используйте /start.', reply_markup=None)
        await send_main_menu(update, context)
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    return CONFIRM_EMAIL

# Аналогично для редактирования email:
async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_email = update.message.text.strip()
    from telegram.ext import ConversationHandler
    if not is_valid_email(new_email):
        if not context.user_data.get('text_error_shown_8'):
            await update.message.reply_text("❗️Пожалуйста, используйте только кнопки или команды для работы с ботом.")
            context.user_data['text_error_shown_8'] = True
        await update.message.reply_text("❗️ Пожалуйста, введите корректный email.")
        return EDIT_EMAIL
    context.user_data.pop('text_error_shown_8', None)
    context.user_data['edit_email'] = new_email
    code = '{:03d}'.format(random.randint(0, 999))
    context.user_data['edit_email_code'] = code
    context.user_data['resend_count'] = 0
    try:
        send_confirmation_code(new_email, code)
    except Exception as e:
        context.logger.error(f"Ошибка отправки email: {e}")
        await update.message.reply_text("❗️ Ошибка отправки письма. Попробуйте другой email.")
        return EDIT_EMAIL
    return await ask_email_code(update, context, edit=True)

async def confirm_edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code == context.user_data.get('edit_email_code'):
        telegram_id = update.message.from_user.id
        new_email = context.user_data['edit_email']
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ? WHERE telegram_id = ?", (new_email, telegram_id))
            conn.commit()
            conn.close()
            await update.message.reply_text("✅ Email обновлен!")
        except Exception as e:
            context.logger.error(f"Ошибка обновления email: {e}")
            await update.message.reply_text("❗️ Произошла ошибка при изменении email. Попробуйте позже.")
        user = get_user_by_telegram_id(telegram_id)
        if user:
            applications = get_applications_by_user(user[0])
            apps_text = "Ваши заявки:\n" if applications else "Заявок нет.\n"
            for app in applications:
                apps_text += f"ID: {app[0]}, Статус: {app[1]}, Дата: {app[2]}\n"
            profile_text = f"Ваш профиль:\nИмя: {user[1]}\nEmail: {user[2]}\nВозраст: {user[3]} {get_age_suffix(user[3])}\nПол: {user[4]}\n{apps_text}"
            edit_keyboard = [
                [InlineKeyboardButton("Изменить имя", callback_data='edit_name')],
                [InlineKeyboardButton("Изменить email", callback_data='edit_email')],
                [InlineKeyboardButton("Добавить фото", callback_data='upload_photo')],
                [InlineKeyboardButton("Назад", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(edit_keyboard)
            await update.message.reply_text(profile_text, reply_markup=reply_markup)
            return PROFILE
        else:
            await update.message.reply_text("❗️ Ошибка обновления профиля.")
            return MAIN_MENU
    else:
        await update.message.reply_text('❗️ Неверный код. Попробуйте ещё раз.')
        return await ask_email_code(update, context, edit=True)

async def confirm_edit_email_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'change_email':
        await send_and_remember(update, context, text='Введите новый email:')
        return EDIT_EMAIL
    elif data == 'resend_code':
        email = context.user_data['edit_email']
        code = '{:03d}'.format(random.randint(0, 999))
        context.user_data['edit_email_code'] = code
        context.user_data['resend_count'] = context.user_data.get('resend_count', 0) + 1
        try:
            send_confirmation_code(email, code)
        except Exception as e:
            context.logger.error(f"Ошибка отправки email: {e}")
            await query.message.reply_text("❗️ Ошибка отправки письма. Попробуйте другой email.")
            return EDIT_EMAIL
        await query.message.reply_text('ℹ️ Код отправлен повторно.')
        return await ask_email_code(update, context, edit=True)
    elif data == 'exit_email':
        from HANDLERS.common import send_main_menu
        await send_and_remember(update, context, text='ℹ️ Выход из подтверждения email. Для старта используйте /start.', reply_markup=None)
        await send_main_menu(update, context)
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    return CONFIRM_EDIT_EMAIL