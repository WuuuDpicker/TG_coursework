from telegram import Update, Document, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_by_telegram_id, create_application, get_application_status, get_application_details, check_user_has_application_for_specialty
from UTILS import send_and_remember
from HANDLERS.common import send_main_menu
from states import *
import os
from UTILS.emails import send_documents_to_admin, send_documents_to_admin_with_user_data

ALLOWED_EXTENSIONS = {'.jpeg', '.jpg', '.png', '.doc', '.docx', '.pdf'}
ADMIN_EMAIL = 'WuuuDpicker@gmail.com'  # Можно вынести в конфиг

# Перечни документов по специальностям
SPECIAL_DOCS = {
    '13.02.07': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)'
    ],
    '44.02.02': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)'
    ],
    '09.02.07': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)',
        '🔬 Справка о прохождении медосмотра'
    ],
    '15.02.08': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)',
        '🔧 Справка о техническом состоянии оборудования'
    ],
    '23.02.07': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)',
        '🚗 Водительское удостоверение (копия)'
    ],
    '43.02.15': [
        '🆔 Паспорт/удостоверение личности (оригинал и копия)',
        '📜 Документ об образовании (оригинал и копия)',
        '📸 Фотография 3х4',
        '📋 СНИЛС (оригинал и копия)',
        '🏥 Медицинская справка (форма 086/У)',
        '🍽️ Санитарная книжка'
    ]
}
DEFAULT_DOCS = [
    '🆔 Паспорт/удостоверение личности (оригинал и копия)',
    '📜 Документ об образовании (оригинал и копия)',
    '📸 Фотография 3х4',
    '📋 СНИЛС (оригинал и копия)'
]

def get_required_docs(specialty_code):
    return SPECIAL_DOCS.get(specialty_code, DEFAULT_DOCS)

async def start_documents_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['documents'] = []
    specialty = context.user_data.get('specialty', {})
    specialty_code = specialty.get('code', '')
    specialty_title = specialty.get('title', 'Не указана')
    required_docs = get_required_docs(specialty_code)
    context.user_data['required_docs'] = required_docs
    context.user_data['current_doc_idx'] = 0
    
    # Формируем красивый список документов
    doc_list = '\n'.join(f"{i+1}. {doc}" for i, doc in enumerate(required_docs))
    
    await update.callback_query.message.reply_text(
        f'📋 <b>Загрузка документов для специальности:</b>\n'
        f'🎓 {specialty_title} ({specialty_code})\n\n'
        f'📝 <b>Необходимые документы:</b>\n{doc_list}\n\n'
        f'📁 <b>Допустимые форматы:</b> .jpeg, .jpg, .png, .doc, .docx, .pdf\n\n'
        f'⬇️ <b>Отправьте первый документ:</b>\n{required_docs[0]}',
        parse_mode='HTML'
    )
    return SUBMIT_DOCUMENTS

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    idx = context.user_data.get('current_doc_idx', 0)
    required_docs = context.user_data.get('required_docs', DEFAULT_DOCS)
    
    if not document:
        await update.message.reply_text(f'❌ Пожалуйста, отправьте файл для: {required_docs[idx]}')
        return SUBMIT_DOCUMENTS
    
    file_name = document.file_name
    ext = os.path.splitext(file_name)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        await update.message.reply_text(
            '❌ Недопустимый формат файла!\n\n'
            '📁 Принимаются только: .jpeg, .jpg, .png, .doc, .docx, .pdf\n\n'
            f'⬇️ Пожалуйста, отправьте файл для: {required_docs[idx]}'
        )
        return SUBMIT_DOCUMENTS
    
    # Сохраняем файл
    file = await document.get_file()
    save_dir = 'data/user_docs'
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{update.message.from_user.id}_{idx}_{file_name}")
    await file.download_to_drive(file_path)
    
    # Добавляем документ в список
    context.user_data['documents'].append((file_path, file_name, required_docs[idx-1]))
    idx += 1
    
    # Показываем прогресс
    progress = f"{idx}/{len(required_docs)}"
    progress_bar = "🟢" * idx + "⚪" * (len(required_docs) - idx)
    
    if idx < len(required_docs):
        context.user_data['current_doc_idx'] = idx
        await update.message.reply_text(
            f'✅ <b>Документ принят!</b>\n\n'
            f'📊 <b>Прогресс:</b> {progress}\n'
            f'{progress_bar}\n\n'
            f'⬇️ <b>Отправьте следующий документ:</b>\n{required_docs[idx]}',
            parse_mode='HTML'
        )
        return SUBMIT_DOCUMENTS
    else:
        # Все документы загружены
        await update.message.reply_text(
            f'🎉 <b>Все документы загружены!</b>\n\n'
            f'📊 <b>Прогресс:</b> {progress}\n'
            f'{progress_bar}\n\n'
            f'📤 Для завершения подачи заявки нажмите /finish',
            parse_mode='HTML'
        )
        return SUBMIT_DOCUMENTS

async def handle_finish_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.message.from_user.id)
    specialty = context.user_data.get('specialty', {})
    specialty_title = specialty.get('title', 'Не указана')
    specialty_code = specialty.get('code', '')
    files = context.user_data.get('documents', [])
    required_docs = context.user_data.get('required_docs', DEFAULT_DOCS)
    
    if len(files) < len(required_docs):
        await update.message.reply_text(
            '❌ Вы не отправили все необходимые документы!\n\n'
            f'📊 Загружено: {len(files)}/{len(required_docs)}\n'
            '⬇️ Пожалуйста, завершите загрузку всех документов.'
        )
        return SUBMIT_DOCUMENTS
    
    try:
        # Проверяем, есть ли уже заявка на эту специальность
        if check_user_has_application_for_specialty(user[0], specialty_code):
            await update.message.reply_text(
                f'⚠️ <b>У вас уже есть заявка на специальность:</b>\n'
                f'🎓 {specialty_title} ({specialty_code})\n\n'
                f'📝 Вы можете подать заявку на другую специальность.',
                parse_mode='HTML'
            )
            await send_main_menu(update, context)
            return MAIN_MENU
        
        # Формируем данные пользователя для email
        user_data = {
            'name': user[1],
            'email': user[2],
            'age': user[3],
            'gender': user[4],
            'telegram_id': update.message.from_user.id,
            'username': update.message.from_user.username or 'Не указан'
        }
        
        # Формируем список файлов для отправки
        files_to_send = [(file_path, file_name) for file_path, file_name, _ in files]
        
        # Отправка на email администратора с данными пользователя
        success = send_documents_to_admin_with_user_data(
            ADMIN_EMAIL, 
            user_data, 
            specialty_title, 
            specialty_code, 
            files_to_send
        )
        
        if success:
            # Сохраняем заявку в БД с информацией о специальности
            app_id = create_application(user[0], specialty_code, specialty_title)
            
            # Очищаем временные файлы
            for file_path, _, _ in files:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            
            context.user_data['documents'] = []
            context.user_data['current_doc_idx'] = 0
            
            # Создаем клавиатуру с кнопкой "отправить ещё раз"
            keyboard = [
                [InlineKeyboardButton("📤 Подать заявку на другую специальность", callback_data="submit")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f'🎉 <b>Заявка успешно подана!</b>\n\n'
                f'📋 <b>ID заявки:</b> {app_id}\n'
                f'🎓 <b>Специальность:</b> {specialty_title}\n'
                f'📊 <b>Статус:</b> в обработке\n\n'
                f'📧 Документы отправлены администратору\n'
                f'⏳ Ожидайте ответа в течение 24 часов\n\n'
                f'💡 <b>Отлично! Ваша заявка была одобрена на рассмотрение</b>',
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            return MAIN_MENU
        else:
            await update.message.reply_text(
                '❌ Произошла ошибка при отправке документов!\n\n'
                '🔄 Попробуйте подать заявку позже или обратитесь в поддержку.'
            )
            return SUBMIT_DOCUMENTS
            
    except Exception as e:
        print(f"Ошибка при завершении загрузки: {e}")
        await update.message.reply_text(
            '❌ Произошла ошибка при обработке заявки!\n\n'
            '🔄 Попробуйте подать заявку позже или обратитесь в поддержку.'
        )
        return SUBMIT_DOCUMENTS

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_id = document.file_id if document else None
    user = get_user_by_telegram_id(update.message.from_user.id)
    if user:
        try:
            app_id = create_application(user[0], file_id)
            await update.message.reply_text(f"✅ Ваша заявка подана с ID {app_id}. Документ обработан.")
        except Exception as e:
            context.logger.error(f"Ошибка создания заявки: {e}")
            await update.message.reply_text("❗️ Произошла ошибка при подаче заявки. Попробуйте позже.")
        await send_main_menu(update, context)
        return MAIN_MENU
    else:
        await update.message.reply_text("Сначала зарегистрируйтесь.")
        return MAIN_MENU

async def get_app_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        app_id = int(update.message.text)
        app_details = get_application_details(app_id)
        
        if app_details:
            app_id, specialty_code, specialty_title, status, submission_date, admin_response, response_date, user_name, user_email = app_details
            
            # Форматируем дату подачи
            if submission_date:
                try:
                    from datetime import datetime
                    sub_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
                    formatted_sub_date = sub_date.strftime('%d.%m.%Y %H:%M')
                except:
                    formatted_sub_date = submission_date
            else:
                formatted_sub_date = "Не указана"
            
            # Форматируем дату ответа
            if response_date:
                try:
                    from datetime import datetime
                    resp_date = datetime.fromisoformat(response_date.replace('Z', '+00:00'))
                    formatted_resp_date = resp_date.strftime('%d.%m.%Y %H:%M')
                except:
                    formatted_resp_date = response_date
            else:
                formatted_resp_date = "Не указана"
            
            # Формируем сообщение
            message = f"""
📋 <b>Информация о заявке #{app_id}</b>

👤 <b>Абитуриент:</b> {user_name}
📧 <b>Email:</b> {user_email}
🎓 <b>Специальность:</b> {specialty_title}
📋 <b>Код специальности:</b> {specialty_code}
📅 <b>Дата подачи:</b> {formatted_sub_date}
📊 <b>Статус:</b> {get_status_text(status)}
            """
            
            if admin_response:
                message += f"""
📅 <b>Дата ответа:</b> {formatted_resp_date}

💬 <b>Ответ администратора:</b>
{admin_response}
                """
            else:
                message += "\n⏳ <b>Ответ администратора:</b> Ожидается"
            
            await update.message.reply_text(message, parse_mode='HTML')
            # Сбросить флаг ошибки для STATUS, чтобы не было спама
            context.user_data.pop('text_error_shown_17', None)
            context.user_data['just_viewed_status'] = True
            return STATUS
        else:
            await update.message.reply_text('❌ Заявка не найдена.')
            return STATUS
    except ValueError:
        await update.message.reply_text('❌ ID должен быть числом.')
        return GET_APP_ID

def get_status_text(status):
    """Возвращает русский текст статуса с эмодзи"""
    status_dict = {
        'submitted': '📤 Подана',
        'approved': '✅ Одобрена',
        'rejected': '❌ Отклонена',
        'processing': '⏳ В обработке'
    }
    return status_dict.get(status, status)