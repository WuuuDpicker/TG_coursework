from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_specialty_action_keyboard(spec):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ Подробнее о специальности", url=spec["url"])],
        [InlineKeyboardButton("📄 Подать документы", callback_data="submit_documents")],
        [
            InlineKeyboardButton("🏠 В главное меню", callback_data="back_specialty")
        ]
    ])

def specialty_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Ознакомиться со специальностями 🌐', url='https://surpk.ru/enrollee/specialties')],
        [InlineKeyboardButton('Назад ◀️', callback_data='back_specialty')]
    ])