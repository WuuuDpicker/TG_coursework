import logging

logger = logging.getLogger(__name__)

async def send_and_remember(update, context, *, text=None, photo_path=None, caption=None, reply_markup=None):
    chat_id = update.effective_chat.id
    # Получаем список ID сообщений бота для этого пользователя
    bot_message_ids = context.user_data.get('bot_message_ids', [])
    
    # Сначала отправляем новое сообщение
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                msg = await update.effective_chat.send_photo(photo=photo, caption=caption, reply_markup=reply_markup)
        elif text:
            msg = await update.effective_chat.send_message(text=text, reply_markup=reply_markup)
        else:
            return
        
        # Сохраняем ID нового сообщения
        context.user_data['bot_message_ids'] = [msg.message_id]
        
        # Теперь удаляем все предыдущие сообщения бота
        for msg_id in bot_message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.debug(f"Не удалось удалить сообщение {msg_id}: {e}")
                # Если не удалось удалить сообщение, очищаем ID
                clear_bot_message_ids(context)
                break
                
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        clear_bot_message_ids(context)

def clear_bot_message_ids(context):
    if 'bot_message_ids' in context.user_data:
        context.user_data['bot_message_ids'] = []