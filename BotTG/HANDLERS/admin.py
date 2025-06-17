from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_application_details, update_application_status
from UTILS.emails import send_admin_response_to_user
from states import *
import re

ADMIN_TELEGRAM_ID = 1595547276

async def process_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ответ администратора на заявку
    Новый формат: /respond <app_id> <response_code>
    Коды ответов:
    1 - Заявка одобрена
    0 - Заявка принята в обработку  
    9 - Заявка отклонена
    """
    if update.message.from_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text('⛔️ У вас нет прав для выполнения этой команды.')
        return ConversationHandler.END
    
    text = update.message.text.strip()
    
    # Проверяем, что это команда администратора
    if not text.startswith('/respond'):
        return ConversationHandler.END  # Не обрабатываем обычные сообщения
    
    # Парсим команду
    parts = text.split(' ', 2)  # Разделяем на 3 части: /respond, app_id, response_code
    if len(parts) < 3:
        await update.message.reply_text(
            '❌ Неверный формат команды!\n\n'
            '📝 Используйте: /respond <app_id> <response_code>\n\n'
            '📊 Коды ответов:\n'
            '1️⃣ - Заявка одобрена\n'
            '0️⃣ - Заявка принята в обработку\n'
            '9️⃣ - Заявка отклонена\n\n'
            '📋 Пример: /respond 123 1'
        )
        return ConversationHandler.END
    
    try:
        app_id = int(parts[1])
        response_code = parts[2]
        
        # Определяем статус и ответ по коду
        response_config = {
            '1': {
                'status': 'approved',
                'response': '✅ Заявка одобрена, отслеживайте рейтинг своей специальности.'
            },
            '0': {
                'status': 'processing',
                'response': '⏳ Заявка принята в обработку. Ожидайте ответа в течение 1-5 рабочих дней.'
            },
            '9': {
                'status': 'rejected',
                'response': '❌ К сожалению, ваша заявка была отклонена. Перепроверьте все документы.'
            }
        }
        
        if response_code not in response_config:
            await update.message.reply_text(
                f'❌ Неверный код ответа: {response_code}\n\n'
                f'📊 Допустимые коды:\n'
                f'1️⃣ - Заявка одобрена\n'
                f'0️⃣ - Заявка принята в обработку\n'
                f'9️⃣ - Заявка отклонена'
            )
            return ConversationHandler.END
        
        status = response_config[response_code]['status']
        response = response_config[response_code]['response']
        
        # Получаем данные заявки
        app_details = get_application_details(app_id)
        if not app_details:
            await update.message.reply_text(f'❌ Заявка #{app_id} не найдена!')
            return ConversationHandler.END
        
        app_id, specialty_code, specialty_title, old_status, submission_date, old_response, response_date, user_name, user_email = app_details
        
        # Обновляем статус в базе данных
        update_application_status(app_id, status, response)
        
        # Отправляем ответ пользователю на email
        email_success = send_admin_response_to_user(user_email, app_id, response)
        
        # Формируем сообщение для администратора
        status_emoji = {
            'approved': '✅',
            'rejected': '❌',
            'processing': '⏳'
        }.get(status, '📋')
        
        status_text = {
            'approved': 'Одобрена',
            'rejected': 'Отклонена',
            'processing': 'В обработке'
        }.get(status, status)
        
        admin_message = f"""
{status_emoji} <b>Ответ отправлен!</b>

📋 <b>ID заявки:</b> {app_id}
👤 <b>Абитуриент:</b> {user_name}
📧 <b>Email:</b> {user_email}
🎓 <b>Специальность:</b> {specialty_title} ({specialty_code})
📊 <b>Статус:</b> {status_text}
💬 <b>Ответ:</b> {response}

📧 Email отправлен: {'✅' if email_success else '❌'}
        """
        
        await update.message.reply_text(admin_message, parse_mode='HTML')
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text('❌ ID заявки должен быть числом!')
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f'❌ Ошибка: {str(e)}')
        return ConversationHandler.END

async def show_pending_applications(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """
    Показывает список заявок в обработке с пагинацией
    """
    # Определяем источник вызова (message или callback_query)
    message = getattr(update, 'message', None)
    if message is None and hasattr(update, 'callback_query') and update.callback_query:
        message = update.callback_query.message
    if message is None or message.from_user.id != ADMIN_TELEGRAM_ID:
        if message:
            await message.reply_text('⛔️ У вас нет прав для просмотра заявок.')
        else:
            await update.callback_query.answer('⛔️ У вас нет прав для просмотра заявок.', show_alert=True)
        return
    
    from database import connect_db
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Получаем общее количество заявок
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]
    
    # Настройки пагинации
    ITEMS_PER_PAGE = 10
    total_pages = (total_applications + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Получаем заявки для текущей страницы
    offset = page * ITEMS_PER_PAGE
    cursor.execute("""
        SELECT a.id, a.specialty_code, a.specialty_title, a.status, a.submission_date, u.name, u.email
        FROM applications a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.submission_date DESC
        LIMIT ? OFFSET ?
    """, (ITEMS_PER_PAGE, offset))
    applications = cursor.fetchall()
    conn.close()
    
    if not applications:
        await message.reply_text('📋 Заявок нет.')
        return
    
    # Формируем сообщение
    message.text = f"📋 <b>Заявки (страница {page + 1} из {total_pages}):</b>\n\n"
    
    for app in applications:
        app_id, specialty_code, specialty_title, status, submission_date, user_name, user_email = app
        
        # Форматируем дату
        if submission_date:
            try:
                from datetime import datetime
                sub_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
                formatted_date = sub_date.strftime('%d.%m.%Y %H:%M')
            except:
                formatted_date = submission_date
        else:
            formatted_date = "Не указана"
        
        # Эмодзи для статуса
        status_emoji = {
            'submitted': '📤',
            'approved': '✅',
            'rejected': '❌',
            'processing': '⏳'
        }.get(status, '📋')
        
        # Русские названия статусов
        status_text = {
            'submitted': 'Подана',
            'approved': 'Одобрена',
            'rejected': 'Отклонена',
            'processing': 'В обработке'
        }.get(status, status)
        
        # Сокращаем название специальности
        short_title = specialty_title[:25] + "..." if len(specialty_title) > 25 else specialty_title
        
        message.text += f"{status_emoji} <b>#{app_id}</b> - {user_name} ({status_text})\n"
        message.text += f"🎓 {short_title} ({specialty_code})\n"
        message.text += f"📧 {user_email} | 📅 {formatted_date}\n\n"
    
    # Создаем клавиатуру с навигацией
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = []
    
    # Добавляем кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"admin_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"admin_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Добавляем кнопку обновления
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data="admin_refresh")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(message.text, parse_mode='HTML', reply_markup=reply_markup)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback'и для административной панели
    """
    user_id = update.effective_user.id
    if user_id != ADMIN_TELEGRAM_ID:
        await update.callback_query.answer('⛔️ У вас нет прав для этой операции.', show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("admin_page_"):
        page = int(query.data.split("_")[-1])
        await show_pending_applications(update, context, page)
    elif query.data == "admin_refresh":
        await show_pending_applications(update, context, 0)
    
    return ConversationHandler.END 