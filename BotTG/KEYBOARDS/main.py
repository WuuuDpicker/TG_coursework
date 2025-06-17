from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Профиль 📋", callback_data='profile'),
            InlineKeyboardButton("Заявка 📝", callback_data='submit')
        ],
        [
            InlineKeyboardButton("Статус 📊", callback_data='status'),
            InlineKeyboardButton("FAQ ❓", callback_data='faq')
        ],
        [
            InlineKeyboardButton("Поддержка ⚙️", callback_data='support'),
            InlineKeyboardButton("О боте ℹ️", callback_data='about')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)