import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from states import FAQ
from UTILS import send_and_remember
from KEYBOARDS import get_back_keyboard

ITEMS_PER_PAGE = 5

def load_faq_data():
    try:
        with open('data/faq.json', 'r', encoding='utf-8') as file:
            return json.load(file)['faq_items']
    except FileNotFoundError:
        return []

def get_faq_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard = []
    
    # Добавляем кнопки навигации
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"faq_page_{current_page-1}"))
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"faq_page_{current_page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Добавляем кнопку возврата в главное меню
    keyboard.append([InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def format_faq_page(items: list, page: int) -> str:
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_items = items[start_idx:end_idx]
    
    text = f"📋 Часто задаваемые вопросы (страница {page + 1}):\n\n"
    for i, item in enumerate(page_items, start=start_idx + 1):
        text += f"{i}. {item['question']}\n"
    
    return text

async def show_faq_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    faq_items = load_faq_data()
    total_pages = (len(faq_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if not faq_items:
        await send_and_remember(
            update, context,
            text="Извините, FAQ временно недоступен.",
            reply_markup=get_back_keyboard()
        )
        return FAQ
    
    # Сохраняем все FAQ в контексте для последующего доступа
    context.user_data['faq_items'] = faq_items
    # Сбросить флаг ошибки при переходе по FAQ
    context.user_data['faq_error_shown'] = False
    
    text = format_faq_page(faq_items, page)
    keyboard = get_faq_keyboard(page, total_pages)
    
    await send_and_remember(
        update, context,
        photo_path='images/FAQ.jpg',
        caption=text,
        reply_markup=keyboard
    )
    return FAQ

async def handle_faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_menu":
        from HANDLERS.common import send_main_menu
        return await send_main_menu(update, context)
    
    if query.data.startswith("faq_page_"):
        page = int(query.data.split("_")[-1])
        return await show_faq_page(update, context, page)
    
    if query.data.startswith("faq_answer_"):
        item_index = int(query.data.split("_")[-1])
        faq_items = context.user_data.get('faq_items', [])
        
        if 0 <= item_index < len(faq_items):
            item = faq_items[item_index]
            answer_text = f"❓ Вопрос: {item['question']}\n\n✅ Ответ: {item['answer']}"
            
            # Создаем клавиатуру с кнопками
            keyboard = []
            
            # Добавляем кнопку "Ознакомиться подробнее", если есть URL
            if 'url' in item:
                keyboard.append([InlineKeyboardButton("🔗 Ознакомиться подробнее", url=item['url'])])
            
            # Добавляем кнопку возврата к списку вопросов
            keyboard.append([InlineKeyboardButton("🔙 К списку вопросов", callback_data=f"faq_page_{item_index // ITEMS_PER_PAGE}")])
            
            await query.edit_message_caption(
                caption=answer_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    return FAQ

async def handle_faq_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если пользователь вводит номер вопроса
    try:
        question_num = int(update.message.text)
        faq_items = context.user_data.get('faq_items', [])
        
        if 1 <= question_num <= len(faq_items):
            item = faq_items[question_num - 1]
            answer_text = f"❓ Вопрос: {item['question']}\n\n✅ Ответ: {item['answer']}"
            # Сбросить флаг ошибки, если был
            context.user_data['faq_error_shown'] = False
            # Создаем клавиатуру с кнопками
            keyboard = []
            # Добавляем кнопку "Ознакомиться подробнее", если есть URL
            if 'url' in item:
                keyboard.append([InlineKeyboardButton("🔗 Ознакомиться подробнее", url=item['url'])])
            # Добавляем кнопку возврата к списку вопросов
            current_page = (question_num - 1) // ITEMS_PER_PAGE
            keyboard.append([InlineKeyboardButton("🔙 К списку вопросов", callback_data=f"faq_page_{current_page}")])
            await send_and_remember(
                update, context,
                text=answer_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("❗️Пожалуйста, введите номер вопроса из списка.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите номер вопроса цифрами.")
    
    return FAQ 