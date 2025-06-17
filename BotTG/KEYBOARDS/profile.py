from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_profile_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Редактировать ФИО ✏️", callback_data='edit_name')],
        [InlineKeyboardButton("Изменить email 📧", callback_data='edit_email')],
        [InlineKeyboardButton("Добавить фото 🖼️", callback_data='upload_photo')],
        [InlineKeyboardButton("Назад ◀️", callback_data='back_profile')]
    ])