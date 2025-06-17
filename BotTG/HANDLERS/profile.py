from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_by_telegram_id, get_applications_by_user, update_user_photo, connect_db
from KEYBOARDS import get_profile_keyboard
from KEYBOARDS import get_main_menu_keyboard
from UTILS import send_and_remember, get_age_suffix
import os
import logging
from states import *
from HANDLERS.common import send_main_menu

logger = logging.getLogger(__name__)

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'profile':
        user = get_user_by_telegram_id(query.from_user.id)
        if user:
            applications = get_applications_by_user(user[0])
            profile_text, reply_markup = build_profile_text_and_keyboard(user, applications)
            # Отправляем фото профиля (стоковое, если нет своего)
            photo_path = user[5] if user[5] and os.path.exists(user[5]) else 'images/logo_user.jpg'
            try:
                with open(photo_path, 'rb') as photo:
                    await query.message.reply_photo(photo=photo, caption=profile_text, reply_markup=reply_markup, parse_mode='HTML')
            except Exception:
                await query.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
            return PROFILE
        else:
            await query.message.reply_text("❗️ Профиль не найден.")
            return MAIN_MENU
    elif data == 'edit_name':
        await send_and_remember(update, context, text="Введите новое имя:")
        return EDIT_NAME
    elif data == 'edit_email':
        await send_and_remember(update, context, text="Введите новый email:")
        return EDIT_EMAIL
    elif data == 'upload_photo':
        await send_and_remember(update, context, text="Пожалуйста, отправьте ваше фото.")
        return UPLOAD_PHOTO
    elif data == 'back_profile':
        await send_and_remember(update, context, text="Возвращаемся в главное меню...", reply_markup=get_main_menu_keyboard())
        await send_main_menu(update, context)
        return MAIN_MENU

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    if len(new_name.split()) < 3:
        await update.message.reply_text("❗️ Пожалуйста, введите полное ФИО (Ваше фамилия имя отчество).")
        return EDIT_NAME
    if not all(word[0].isupper() for word in new_name.split()):
        await update.message.reply_text("❗️ Первые буквы каждого слова должны быть заглавными.")
        return EDIT_NAME
    telegram_id = update.message.from_user.id
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = ? WHERE telegram_id = ?", (new_name, telegram_id))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Имя обновлено!")
    except Exception as e:
        logger.error(f"Ошибка обновления имени: {e}")
        await update.message.reply_text("❗️ Произошла ошибка при изменении имени. Попробуйте позже.")
    user = get_user_by_telegram_id(telegram_id)
    if user:
        applications = get_applications_by_user(user[0])
        profile_text, reply_markup = build_profile_text_and_keyboard(user, applications)
        await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
        return PROFILE
    else:
        await update.message.reply_text("❗️ Ошибка обновления профиля.")
        return MAIN_MENU

async def handle_upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, отправьте фото в формате .jpg, .jpeg или .png.")
        return UPLOAD_PHOTO
    file = await update.message.photo[-1].get_file()
    file_path_on_server = file.file_path
    ext = file_path_on_server.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        await update.message.reply_text("Неверный формат фото. Принимаются только .jpg, .jpeg, .png. Пожалуйста, отправьте фото в одном из этих форматов.")
        return UPLOAD_PHOTO
    os.makedirs('data/Logo_USERS', exist_ok=True)
    file_path = f"data/Logo_USERS/user_{update.effective_user.id}.{ext}"
    await file.download_to_drive(file_path)
    try:
        user = get_user_by_telegram_id(update.effective_user.id)
        if user:
            update_user_photo(user[0], file_path)
            await update.message.reply_text("✅ Фото успешно обновлено!")
            applications = get_applications_by_user(user[0])
            profile_text, reply_markup = build_profile_text_and_keyboard(user, applications)
            await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
            return PROFILE
    except Exception as e:
        logger.error(f"Ошибка обновления фото: {e}")
        await update.message.reply_text("❗️ Произошла ошибка при обновлении фото. Попробуйте позже.")
    return MAIN_MENU

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name.split()) < 3:
        await update.message.reply_text("❗️ Пожалуйста, введите полное ФИО (Ваше фамилия имя отчество).")
        return GET_NAME
    if not all(word[0].isupper() for word in name.split()):
        await update.message.reply_text("❗️ Первые буквы каждого слова должны быть заглавными.")
        return GET_NAME
    context.user_data['name'] = name
    await update.message.reply_text('📝 Пожалуйста, укажите ваш email.')
    return GET_EMAIL

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age_input = update.message.text.strip()
    try:
        day, month, year = map(int, age_input.split('.'))
        if year < 1900:
            await update.message.reply_text("Год рождения не может быть раньше 1900.")
            return GET_AGE
        import datetime
        today = datetime.date.today()
        birth_date = datetime.date(year, month, day)
        if birth_date > today:
            await update.message.reply_text("Дата рождения не может быть в будущем.")
            return GET_AGE
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 0:
            await update.message.reply_text("Возраст не может быть отрицательным.")
            return GET_AGE
        context.user_data['age'] = age
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        gender_keyboard = [
            [InlineKeyboardButton("♂️ Мужской", callback_data='gender_male')],
            [InlineKeyboardButton("♀️ Женский", callback_data='gender_female')]
        ]
        reply_markup = InlineKeyboardMarkup(gender_keyboard)
        await update.message.reply_text('♀️♂️ Выберите ваш пол:', reply_markup=reply_markup)
        return GET_GENDER
    except ValueError:
        await update.message.reply_text("❗️ Неверный формат даты. Используйте дд.мм.гггг.")
        return GET_AGE

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender_map = {'gender_male': 'Мужской', 'gender_female': 'Женский' }
    gender = gender_map.get(query.data, '')
    if not gender:
        return GET_GENDER
    context.user_data['gender'] = gender
    telegram_id = context.user_data['telegram_id']
    name = context.user_data['name']
    email = context.user_data['email']
    age = context.user_data['age']
    from database import create_user, update_user_photo, get_user_by_telegram_id, get_applications_by_user
    try:
        user_id = create_user(telegram_id, name, email, age, gender)
        update_user_photo(user_id, 'images/logo_user.jpg')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Ошибка создания пользователя: {e}")
        await query.message.reply_text("❗️ Произошла ошибка при регистрации. Попробуйте позже.")
        return MAIN_MENU
    from HANDLERS.common import send_main_menu
    await send_main_menu(update, context)
    return MAIN_MENU

def build_profile_text_and_keyboard(user, applications):
    apps_text = ""
    if applications:
        apps_text = "\n📋 <b>Ваши заявки:</b>\n"
        for app in applications:
            app_id, specialty_code, specialty_title, status, submission_date = app
            if submission_date:
                try:
                    from datetime import datetime
                    sub_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
                    formatted_date = sub_date.strftime('%d.%m.%Y %H:%M')
                except:
                    formatted_date = submission_date
            else:
                formatted_date = "Не указана"
            status_emoji = {
                'submitted': '📤',
                'approved': '✅',
                'rejected': '❌',
                'processing': '⏳'
            }.get(status, '📋')
            status_text = {
                'submitted': 'Подана',
                'approved': 'Одобрена',
                'rejected': 'Отклонена',
                'processing': 'В обработке'
            }.get(status, status)
            short_title = specialty_title[:30] + "..." if len(specialty_title) > 30 else specialty_title
            apps_text += f"{status_emoji} <b>ID {app_id}</b> - {status_text}\n"
            apps_text += f"🎓 {short_title} ({specialty_code})\n"
            apps_text += f"📅 {formatted_date}\n\n"
    else:
        apps_text = "\n🚫 <b>Заявок нет</b>"
    profile_text = (
        f"👤 <b>Ваш профиль:</b>\n"
        f"📝 Имя: {user[1]}\n"
        f"📧 Email: {user[2]}\n"
        f"🎂 Возраст: {user[3]} {get_age_suffix(user[3])}\n"
        f"♂️♀️ Пол: {user[4]}\n"
        f"{apps_text}"
    )
    from KEYBOARDS.profile import get_profile_keyboard
    reply_markup = get_profile_keyboard()
    return profile_text, reply_markup
