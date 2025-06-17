from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_back_keyboard(back_callback):
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data=back_callback)]])

def get_submit_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data='back_submit')]])

def get_status_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data='back_status')]])

def get_faq_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data='back_faq')]])

def get_support_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data='back_support')]])

def get_about_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Назад ➡️', callback_data='back_about')]])

def get_email_confirm_keyboard(edit=False, resend=True):
    buttons = [
        [InlineKeyboardButton('✏️ Изменить почту', callback_data='change_email')],
    ]
    if resend:
        buttons.append([InlineKeyboardButton('🔄 Отправить код заново', callback_data='resend_code')])
    buttons.append([InlineKeyboardButton('🚪 Выход', callback_data='exit_email')])
    return InlineKeyboardMarkup(buttons)